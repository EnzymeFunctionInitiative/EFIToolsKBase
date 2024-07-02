"""
This ExampleReadsApp demonstrates how to use best practices for KBase App
development using the SFA base package.
"""
import os
import logging
import uuid

from shutil import copyfile

import pandas as pd

from Bio import SeqIO

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
        self.flow = NextflowRunner("ssn.nf")


    def do_analysis(self, params):
        logging.info(params)
        mapping = {
            "blast_parquet": "/results/1.out.parquet",
            "fasta_file": "/results/sequences.fasta",
            "output_dir": self.shared_folder,
            "filter_parameter": "alignment_score",
            "filter_min_val": params["alignment_score"],
            "min_length": 0,
            "max_length": 50000,
            "ssn_name": "kbase_ssn",
            "ssn_title": "kbase_ssn",
            "maxfull": 0,
            "uniref_version": 90,
            "efi_config": "",
            "db_version": 100
        }
        self.flow.render_params_file(mapping, "ssn-params-template.yml")
        self.flow.generate_run_command(stub=True)
        retcode, stdout, stderr = self.flow.execute()
        # if retcode != 0:
        #     raise ValueError(f"Failed to execute Nextflow pipeline\n{stderr}")
        print(self.shared_folder, os.listdir(self.shared_folder))
        stats = pd.read_csv(os.path.join(self.shared_folder, "stats.tab"), sep="\t").to_html()
        report_data = {
            "stats": stats,
            "workspace_name": params["workspace_name"]
        }
        output = self.generate_report(report_data, ["edge_ref", "fasta_ref"])
        output["edge_ref"] = "edge_ref"#edge_ref["shock_id"]
        output["fasta_ref"] = "fasta_ref"#fasta_ref
        return output

    def generate_report(self, params, objects_created):
        reports_path = os.path.join(self.shared_folder, "reports")
        template_path = os.path.join(TEMPLATES_DIR, "ssn_creation_report.html")
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