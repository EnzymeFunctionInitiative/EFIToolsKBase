"""
This ExampleReadsApp demonstrates how to use best practices for KBase App
development using the SFA base package.
"""
import json
import logging
import os
import uuid

from shutil import copyfile

from Bio import SeqIO

# This is the SFA base package which provides the Core app class.
from base import Core
from installed_clients.DataFileUtilClient import DataFileUtil


from ..nextflow import NextflowRunner
from ..utils import png_to_base64
from ..const import *

class EFIFasta(Core):
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
        self.flow = NextflowRunner("est.nf")


    def do_analysis(self, params):
        mapping = {
            "fasta_file": "/results/sequences.fasta",#params["fasta_sequences_file"],
            "output_dir": self.shared_folder,
            "duckdb_mem": "64GB",
            "duckdb_threads": 1,
            "fasta_shards": 1,
            "blast_matches": 250,
            "job_id": 0,
        }
        self.flow.render_params_file(mapping, "est-params-template.yml")
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

        data_ref = self.save_edge_file_to_workspace(params["workspace_name"], 
                                                    os.path.join(self.shared_folder, "1.out.parquet"), 
                                                    os.path.join(self.shared_folder, "sequences.fa"),
                                                    os.path.join(self.shared_folder, "evalue.tab"),
                                                    acc_data)
        report_data = {
            "pident_img": pident_dataurl, 
            "length_img": length_dataurl, 
            "edge_img": edge_dataurl, 
            "convergence_ratio": f"{acc_data['ConvergenceRatio']:.3f}",
            "edge_count": acc_data["EdgeCount"],
            "unique_seqs": acc_data["UniqueSeq"],
            "workspace_name": params["workspace_name"]
        }
        output = self.generate_report(report_data, ["edge_ref"])
        output["edge_ref"] = data_ref

        return output

    def generate_report(self, params, objects_created):
        reports_path = os.path.join(self.shared_folder, "reports")
        template_path = os.path.join(TEMPLATES_DIR, "est_fasta_report.html")
        template_variables = params
        # The KBaseReport configuration dictionary
        config = dict(
            report_name=f"EFI_EST_FASTA_{str(uuid.uuid4())}",
            reports_path=reports_path,
            template_variables=template_variables,
            workspace_name=params["workspace_name"],
            objects_created=objects_created
        )
        return self.create_report_from_template(template_path, config)

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
                'name': f"{os.path.basename(edge_filepath)}_shock_id"
            }]
        }
        dfu_oi = self.dfu.save_objects(save_object_params)[0]
        object_reference = str(dfu_oi[6]) + '/' + str(dfu_oi[0]) + '/' + str(dfu_oi[4])
        return object_reference