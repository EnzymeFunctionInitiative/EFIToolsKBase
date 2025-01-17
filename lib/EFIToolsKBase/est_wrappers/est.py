
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
        pident_dataurl = png_to_base64(os.path.join(self.shared_folder, 
                                                    "pident_sm.png"))
        length_dataurl = png_to_base64(os.path.join(self.shared_folder, 
                                                    "length_sm.png"))
        edge_dataurl = png_to_base64(os.path.join(self.shared_folder, 
                                                  "edge_sm.png"))

        with open(os.path.join(self.shared_folder, "acc_counts.json")) as f:
            acc_data = json.load(f)

        print("Create the BlastEdgeFile object")
        data_ref = self.save_edge_file_to_workspace(
            workspace_name, 
            os.path.join(self.shared_folder, "1.out.parquet"), 
            os.path.join(self.shared_folder, "all_sequences.fasta"),
            os.path.join(self.shared_folder, "evalue.tab"),
            os.path.join(self.shared_folder, "sequence_metadata.tab"),
            acc_data
        )
        
        print("Create the HTML report")
        report_data = {
            "pident_img": pident_dataurl, 
            "length_img": length_dataurl, 
            "edge_img": edge_dataurl, 
            "convergence_ratio": f"{acc_data['ConvergenceRatio']:.3f}",
            "edge_count": acc_data["EdgeCount"],
            "unique_seqs": acc_data["UniqueSeq"]
        }
        # only one object created (the GNDViewFile) so list of len 1
        objects_created_list = [
            {
                "ref": data_ref, 
                "description": "Edge file and other metadata"
            }
        ]
        output = self.generate_report(workspace_name, report_data, 
                                      objects_created_list)
        
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
            with zipfile.ZipFile(zip_path, 
                    "w", zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
                # loop over files in list and stash in the zip
                for name in output_file_names:
                    zf.write(os.path.join(self.shared_folder, name), name)

            zip_file_link = {
                "path": zip_path,
                "name": "all_files.zip",
                "label": "all_files.zip",
                "description": "All files created by the analysis collected"
                                + " in a zip archive"
            }
            file_links = [zip_file_link] + file_links

        return file_links

    def generate_report(self, ws_name, template_var_dict, objects_created):
        """
        """
        # get the workspace_id
        workspace_id = self.dfu.ws_name_to_id(ws_name)

        # output_files is a list of dicts, each element mapping to a file
        # created by the app. 
        output_files = self._create_file_links()

        # hand make the reports_path and file io variables
        # ... not sure why we need a new subdir?
        reports_path = os.path.join(self.shared_folder, "reports")
        os.makedirs(reports_path, exist_ok=True)
        report_uuid = str(uuid.uuid4())
        report_name = f"EFI_EST_{report_uuid}"
        report_path = os.path.join(reports_path, f"{report_name}.html")

        # fill KBaseReport configuration dictionary
        kbr_config = {
            "workspace_id": workspace_id,
            "file_links": output_files,
            "objects_created": objects_created,
            "direct_html_link_index": 0,
            "html_links": [
                {
                    "description": "HTML report for EST analysis",
                    "name": f"{report_name}.html",
                    "path": reports_path
                }
            ],
            "html_window_height": 375,
            "report_object_name": report_name,
            "message": "A sample report." # update!
        }

        # Create report from template
        logging.info("Creating report...")
        template_path = os.path.join(TEMPLATES_DIR, "est_report.html")
        with open(template_path) as tpf:
            template_source = tpf.read()
        # set up the jinja2 template environment
        env = Environment(
            loader=DictLoader(dict(template=template_source)),
            autoescape=select_autoescape(default=False)
        )
        template = env.get_template("template")
        # feed in the template_var_dict data and save the text in report
        report = template.render(**template_var_dict)
        
        # Create report file using the uuid'd "report_object_name"
        with open(report_path, "w") as report_file:
            report_file.write(report)

        # run the KBaseReport method to create the report to be shown
        report_info = self.report.create_extended_report(kbr_config)
        
        return {
            "report_name": report_info["name"],
            "report_ref": report_info["ref"],
        }

    def save_edge_file_to_workspace(
            self, 
            workspace_name, 
            edge_filepath, 
            fasta_filepath, 
            evalue_filepath, 
            seq_meta_filepath, 
            acc_data):
        """
        """
        workspace_id = self.dfu.ws_name_to_id(workspace_name)
        edge_file_shock_id = self.dfu.file_to_shock(
                {"file_path": edge_filepath})["shock_id"]
        fasta_handle_shock_id = self.dfu.file_to_shock(
                {"file_path": fasta_filepath})["shock_id"]
        evalue_shock_id = self.dfu.file_to_shock(
                {"file_path": evalue_filepath})["shock_id"]
        seq_meta_shock_id = self.dfu.file_to_shock(
                {"file_path": seq_meta_filepath})["shock_id"]
        # prep the save_objects() parameter dictionary
        save_object_params = {
            "id": workspace_id,
            # objects is a list of dicts, where each dict element contains info 
            # about the object to be saved/created
            "objects": [
                {
                    "type": "EFIToolsKBase.BlastEdgeFile",
                    'name': "blast_edge_file",
                    "data": {
                        "edgefile_handle": edge_file_shock_id,
                        "fasta_handle": fasta_handle_shock_id,
                        "evalue_handle": evalue_shock_id,
                        "seq_meta_handle": seq_meta_shock_id,
                        "edge_count": acc_data["EdgeCount"],
                        "unique_seq": acc_data["UniqueSeq"],
                        "convergence_ratio": acc_data['ConvergenceRatio'],
                    }
                }
            ]
        }
        # since only one object is being created, just grab the zeroth element
        # and parse its tuple
        dfu_oi = self.dfu.save_objects(save_object_params)[0]
        object_reference = f"{dfu_oi[6]}/{dfu_oi[0]}/{dfu_oi[4]}"
        return object_reference
