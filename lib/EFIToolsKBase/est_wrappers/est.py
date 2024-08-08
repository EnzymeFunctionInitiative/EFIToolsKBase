import os
import json
import logging
import uuid
import zipfile

from jinja2 import DictLoader, Environment, select_autoescape

from ..nextflow import NextflowRunner
from ..utils import png_to_base64
from ..const import *

from base import Core


class EFIEST(Core):
    def __init__(self, ctx, config, clients_class=None):
        """
        This is required to instantiate the Core App class with its defaults
        and allows you to pass in more clients as needed.
        """
        super().__init__(ctx, config, clients_class)
        # Here we adjust the instance attributes for our convenience.
        self.report = self.clients.KBaseReport
        self.dfu = self.clients.DataFileUtil
        self.au = self.clients.AssemblyUtil
        self.wsClient = self.clients.Workspace
        self.flow = NextflowRunner("pipelines/est/est.nf", "est/kbase.config")

    def do_analysis(self, params):
        """
        child classes should use this to render parameter files
        """
        raise NotImplementedError("Please Implement this method")

    def run_est_pipeline(self, mapping, workspace_name):
        """
        This should be called in do_analysis after rendering parameters

        pipeline: string
        filename of pipeline to run. ex: "est.nf", "ssn.nf"
        mapping: dict
        used to do string substitution on the yml parameter template
        workspace_name: string
        passed in from params dict in runner (params["workspace_name"])
        """
        self.flow.write_params_file(mapping)
        self.flow.generate_run_command()
        retcode, stdout, stderr = self.flow.execute()
        # if retcode != 0:
        #     raise ValueError(f"Failed to execute Nextflow pipeline\n{stderr}")
        print(self.shared_folder, os.listdir(self.shared_folder))
        pident_dataurl = png_to_base64(os.path.join(self.shared_folder, "pident_sm.png"))
        length_dataurl = png_to_base64(os.path.join(self.shared_folder, "length_sm.png"))
        edge_dataurl = png_to_base64(os.path.join(self.shared_folder, "edge_sm.png"))

        with open(os.path.join(self.shared_folder, "acc_counts.json")) as f:
            acc_data = json.load(f)

        data_ref = self.save_edge_file_to_workspace(workspace_name, 
                                                os.path.join(self.shared_folder, "1.out.parquet"), 
                                                os.path.join(self.shared_folder, "all_sequences.fasta"),
                                                os.path.join(self.shared_folder, "evalue.tab"),
                                                acc_data)
        report_data = {
            "pident_img": pident_dataurl, 
            "length_img": length_dataurl, 
            "edge_img": edge_dataurl, 
            "convergence_ratio": f"{acc_data['ConvergenceRatio']:.3f}",
            "edge_count": acc_data["EdgeCount"],
            "unique_seqs": acc_data["UniqueSeq"],
            "workspace_name": workspace_name
        }
        output = self.generate_report(report_data, [{"ref": data_ref, "description": "Edge file and other metadata"}])
        output["edge_ref"] = data_ref

        return output

    def _create_file_links(self, inlcude_zip=True):
        output_file_names = [
            "1.out.parquet",
            "all_sequences.fasta",
            "evalue.tab",
            "sequence_metadata.tab",
            "sunburst_ids.tab",
            "length.png",
            "pident.png",
            "edge.png"
        ]

        file_links = [
            {
                "path": os.path.join(self.shared_folder, output_file_names[0]),
                "name": output_file_names[0],
                "label": output_file_names[0],
                "description": "Parquet file containing edges"
            },
            {
                "path": os.path.join(self.shared_folder, output_file_names[1]),
                "name": output_file_names[1],
                "label": output_file_names[1],
                "description": "All sequences used in analysis"
            },
            {
                "path": os.path.join(self.shared_folder, output_file_names[2]),
                "name": output_file_names[2],
                "label": output_file_names[2],
                "description": "Table of E values"
            },
            {
                "path": os.path.join(self.shared_folder, output_file_names[3]),
                "name": output_file_names[3],
                "label": output_file_names[3],
                "description": "Sequence metadata"
            },
            {
                "path": os.path.join(self.shared_folder, output_file_names[4]),
                "name": output_file_names[4],
                "label": output_file_names[4],
                "description": "Sunburst IDs in all 3 databases"
            },
            {
                "path": os.path.join(self.shared_folder, output_file_names[5]),
                "name": output_file_names[5],
                "label": output_file_names[5],
                "description": "Full resolution Length plot"
            },
            {
                "path": os.path.join(self.shared_folder, output_file_names[6]),
                "name": output_file_names[6],
                "label": output_file_names[6],
                "description": "Full resolution Percent Identity plot"
            },
            {
                "path": os.path.join(self.shared_folder, output_file_names[7]),
                "name": output_file_names[7],
                "label": output_file_names[7],
                "description": "Full resolution Edge plot"
            },
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

    def generate_report(self, params, objects_created):
        reports_path = os.path.join(self.shared_folder, "reports")
        template_path = os.path.join(TEMPLATES_DIR, "est_report.html")
        template_variables = params

        # The KBaseReport configuration dictionary
        config = dict(
            report_name=f"EFI_EST_{str(uuid.uuid4())}",
            reports_path=reports_path,
            template_variables=template_variables,
            workspace_name=params["workspace_name"],
            objects_created=objects_created
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
                "file_links": output_files,
                "objects_created": config["objects_created"]
            }
        )
        return {
            "report_name": report_info["name"],
            "report_ref": report_info["ref"],
        }

    def save_edge_file_to_workspace(self, workspace_name, edge_filepath, fasta_filepath, evalue_filepath, acc_data):
        workspace_id = self.dfu.ws_name_to_id(workspace_name)
        edge_file_shock_id = self.dfu.file_to_shock({"file_path": edge_filepath})["shock_id"]
        fasta_handle_shock_id = self.dfu.file_to_shock({"file_path": fasta_filepath})["shock_id"]
        evalue_shock_id = self.dfu.file_to_shock({"file_path": evalue_filepath})["shock_id"]
        save_object_params = {
        'id': workspace_id,
        'objects': [{
            'type': 'EFIToolsKBase.BlastEdgeFile',
            'data': {
                "edgefile_handle": edge_file_shock_id,
                "fasta_handle": fasta_handle_shock_id,
                "evalue_handle": evalue_shock_id,
                "edge_count": acc_data["EdgeCount"],
                "unique_seq": acc_data["UniqueSeq"],
                "convergence_ratio": acc_data['ConvergenceRatio'],
            },
            'name': "blast_edge_file"
        }]
        }
        dfu_oi = self.dfu.save_objects(save_object_params)[0]
        object_reference = str(dfu_oi[6]) + '/' + str(dfu_oi[0]) + '/' + str(dfu_oi[4])
        return object_reference