import os
from pathlib import Path
import logging
import uuid

from jinja2 import DictLoader, Environment, select_autoescape
import pandas as pd

from base import Core
from ..nextflow import NextflowRunner
from ..const import *

class ColorSSN(Core):
    def __init__(self, ctx, config, clients_class=None):
        """
        This is required to instantiate the Core App class with its defaults
        and allows you to pass in more clients as needed.
        """
        super().__init__(ctx, config, clients_class)
        # Here we adjust the instance attributes for our convenience.
        self.report = self.clients.KBaseReport
        self.dfu = self.clients.DataFileUtil
        self.flow = NextflowRunner("colorssn.nf")

    def do_analysis(self, params):
        ssn_file_obj = self.dfu.get_objects({"object_refs": [params["ssn_file"]]})["data"][0]
        self.dfu.shock_to_file({
            "shock_id": ssn_file_obj["data"]["ssn_xgmml_handle"], 
            "file_path": os.path.join(self.shared_folder, "full_ssn.xgmml"), 
            "unpack": "unpack"}
        )
        mapping = {
            "ssn_input": os.path.join(self.shared_folder, "full_ssn.xgmml"),
            "efi_config": EFI_CONFIG_PATH,
            "efi_db": EFI_DB_PATH,
            "final_output_dir": self.shared_folder
        }
        self.flow.write_params_file(mapping)
        self.flow.generate_run_command()

        retcode, stdout, stderr = self.flow.execute()
        print(self.shared_folder, os.listdir(self.shared_folder))

        stats = pd.read_csv(os.path.join(self.shared_folder, "stats.txt"), sep="\t")
        try:
            cluster_sizes = pd.read_csv(os.path.join(self.shared_folder, "cluster_sizes.txt"), sep="\t").to_html(index=False)
        except:
            cluster_sizes = "No data"
        
        try:
            conv_ratios = pd.read_csv(os.path.join(self.shared_folder, "conv_ratio.txt"), sep="\t").to_html(index=False)
        except:
            conv_ratios = "No data"

        output = self.generate_report({
            "stats_tab": stats.to_html(index=False),
            "cluster_sizes_tab": cluster_sizes,
            "conv_ratios_tab": conv_ratios,
            "workspace_name": params["workspace_name"]
        })

        return output

    def _create_file_links(self):
        output_file_names = [
            "ssn_out.xgmml",
            "mapping_table.txt"
        ]
        file_links = [
            {
                "path": os.path.join(self.shared_folder, output_file_names[0]),
                "name": output_file_names[0],
                "label": output_file_names[0],
                "description": "New SSN file"
            },
            {
                "path": os.path.join(self.shared_folder, output_file_names[1]),
                "name": output_file_names[1],
                "label": output_file_names[1],
                "description": "New SSN file"
            },
        ]

        return file_links

    def generate_report(self, params):
        reports_path = os.path.join(self.shared_folder, "reports")
        template_path = os.path.join(TEMPLATES_DIR, "colorssn_report.html")
        template_variables = params
        # The KBaseReport configuration dictionary

        config = dict(
            report_name=f"Color_SSN_{str(uuid.uuid4())}",
            reports_path=reports_path,
            template_variables=template_variables,
            workspace_name=params["workspace_name"],
        )

        logging.info("Creating report...")
        # Create report from template
        with open(template_path) as tpf:
            template_source = tpf.read()
        env = Environment(
            loader=DictLoader(dict(template=template_source)),
            autoescape=select_autoescape(default=False)
        )
        template = env.get_template("template")
        report = template.render(**config["template_variables"])
        # Create report object including report
        report_name = config["report_name"]
        reports_path = config["reports_path"]
        workspace_name = config["workspace_name"]
        os.makedirs(reports_path, exist_ok=True)
        report_path = os.path.join(reports_path, "index.html")
        with open(report_path, "w") as report_file:
            report_file.write(report)
        html_links = [
            {
                "description": "report",
                "name": "index.html",
                "path": reports_path,
            },
        ]

        output_files = self._create_file_links()

        report_info = self.report.create_extended_report(
            {
                "direct_html_link_index": 0,
                "html_links": html_links,
                "message": "A sample report.",
                "report_object_name": report_name,
                "workspace_name": workspace_name,
                "file_links": output_files
            }
        )
        return {
            "report_name": report_info["name"],
            "report_ref": report_info["ref"],
        }
