"""
This ExampleReadsApp demonstrates how to use best practices for KBase App
development using the SFA base package.
"""
import os
import logging
import uuid
import zipfile

from jinja2 import DictLoader, Environment, select_autoescape
import pandas as pd

# This is the SFA base package which provides the Core app class.
from base import Core
from installed_clients.DataFileUtilClient import DataFileUtil


from ..nextflow import NextflowRunner
from ..const import *

class SSNCreation(Core):
    def __init__(self, ctx, config, clients_class=None):
        """
        This is required to instantiate the Core App class with its defaults
        and allows you to pass in more clients as needed.
        """
        super().__init__(ctx, config, clients_class)
        # Here we adjust the instance attributes for our convenience.
        self.report = self.clients.KBaseReport
        self.dfu = self.clients.DataFileUtil
        self.flow = NextflowRunner("ssn.nf")


    def do_analysis(self, params):
        edge_file_obj = self.dfu.get_objects({"object_refs": [params["blast_edge_file"]]})["data"][0]
        print(edge_file_obj)
        self.dfu.shock_to_file({
            "shock_id": edge_file_obj["data"]["edgefile_handle"], 
            "file_path": os.path.join(self.shared_folder, "1.out.parquet"), 
            "unpack": "unpack"}
        )
        self.dfu.shock_to_file({
            "shock_id": edge_file_obj["data"]["fasta_handle"], 
            "file_path": os.path.join(self.shared_folder, "sequences.fa"), 
            "unpack": "unpack"}
        )

        print(params)
        mapping = {
            "blast_parquet": os.path.join(self.shared_folder, "1.out.parquet"),
            "fasta_file": os.path.join(self.shared_folder, "sequences.fa"),
            "final_output_dir": self.shared_folder,
            "filter_parameter": "alignment_score",
            "filter_min_val": params["alignment_score"],
            "min_length": params["min_length"],
            "max_length": params["max_length"],
            "ssn_name": "kbase_ssn",
            "ssn_title": "kbase_ssn",
            "maxfull": 0,
            "uniref_version": 90,
            "efi_config": "/EST/efi.config",
            "db_version": 100,
            "job_id": 131,
            "efi_db": "/data/efi_db.sqlite"
        }
        self.flow.write_params_file(mapping)
        self.flow.generate_run_command()
        retcode, stdout, stderr = self.flow.execute()
        # if retcode != 0:
        #     raise ValueError(f"Failed to execute Nextflow pipeline\n{stderr}")
        print(self.shared_folder, os.listdir(self.shared_folder))
        stats = pd.read_csv(os.path.join(self.shared_folder, "stats.tab"), sep="\t").to_html()
        report_data = {
            "stats": stats,
            "workspace_name": params["workspace_name"]
        }
        output = self.generate_report(report_data)
        return output

    def _create_file_links(self, inlcude_zip=True):
        output_file_names = [
            "2.out",
            "filtered_sequences.fasta",
            "full_ssn.xgmml",
            "struct.filtered.out"
        ]

        file_links = [
            {
                "path": os.path.join(self.shared_folder, output_file_names[0]),
                "name": output_file_names[0],
                "label": output_file_names[0],
                "description": "File containing filtered edges"
            },
            {
                "path": os.path.join(self.shared_folder, output_file_names[1]),
                "name": output_file_names[1],
                "label": output_file_names[1],
                "description": "Filtered FASTA file containing sequences present int network"
            },
            {
                "path": os.path.join(self.shared_folder, output_file_names[2]),
                "name": output_file_names[2],
                "label": output_file_names[2],
                "description": "The Sequence Similarity Network"
            },
            {
                "path": os.path.join(self.shared_folder, output_file_names[3]),
                "name": output_file_names[3],
                "label": output_file_names[3],
                "description": "Taxonomy and other metadata about each sequence in filtered_sequences.fasta"
            }
        ]

        if inlcude_zip:
            zip_path = os.path.join(self.shared_folder, "all_files.zip")
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
                for name in output_file_names:
                    zf.write(os.path.join(self.shared_folder, name), name)

            zip_file_link = {
                "path": zip_path,
                "name": "all_files.zip",
                "label": "all_files.zip",
                "description": "All files created by the analysis collected in a zip zrchive"
            }
            file_links = [zip_file_link] + file_links

        return file_links


    def generate_report(self, params):
        reports_path = os.path.join(self.shared_folder, "reports")
        template_path = os.path.join(TEMPLATES_DIR, "ssn_creation_report.html")
        template_variables = params
        # The KBaseReport configuration dictionary

        config = dict(
            report_name=f"SSN_Creation_{str(uuid.uuid4())}",
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

    def save_file_to_workspace(self, workspace_name, filepath, description):
        workspace_id = self.dfu.ws_name_to_id(workspace_name)
        output_file_shock_id = self.dfu.file_to_shock({"file_path": filepath})["shock_id"]
        print(f"Uploaded filepath {filepath} to shock and got id {output_file_shock_id}")
        save_object_params = {
            'id': workspace_id,
            'objects': [{
                'type': 'EFIToolsKBase.EdgeFileBLAST',
                'data': output_file_shock_id,
                'name': f"{os.path.basename(filepath)}_shock_id"
            }]
        }
        dfu_oi = self.dfu.save_objects(save_object_params)[0]
        object_reference = str(dfu_oi[6]) + '/' + str(dfu_oi[0]) + '/' + str(dfu_oi[4])
        return {"shock_id": object_reference,
                "name": os.path.basename(filepath),
                "label": os.path.basename(filepath),
                "description": description}
    
    def save_sequences_to_workspace(self, filepath, workspace_name):
        return self.au.save_assembly_from_fasta({
            'file': {'path': filepath},
            'workspace_name': workspace_name,
            'assembly_name': 'all_sequences.fasta'
        })