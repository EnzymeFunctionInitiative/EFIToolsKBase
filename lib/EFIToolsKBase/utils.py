"""
This ExampleReadsApp demonstrates how to use best practices for KBase App
development using the SFA base package.
"""
import base64
import json
import logging
import os
import subprocess
import uuid

from collections import Counter
from shutil import copyfile

import pandas as pd

from Bio import SeqIO

# This is the SFA base package which provides the Core app class.
from base import Core
from installed_clients.DataFileUtilClient import DataFileUtil


from .nextflow import NextflowRunner


MODULE_DIR = "/kb/module"
TEMPLATES_DIR = os.path.join(MODULE_DIR, "lib/templates")


def png_to_base64(filepath):
    content = open(filepath, "rb").read()
    base64_utf8_str = base64.b64encode(content).decode("utf-8")
    dataurl = f"data:image/png;base64,{base64_utf8_str}"
    return dataurl

class EFITools(Core):
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
        self.flow = NextflowRunner()


    def est_fasta(self, params):
        self.flow.render_params_file(params['fasta_sequences_file'], output_dir=self.shared_folder)
        self.flow.generate_run_command()
        retcode, stdout, stderr = self.flow.execute()
        # if retcode != 0:
        #     raise ValueError(f"Failed to execute Nextflow pipeline\n{stderr}")
        print(self.shared_folder, os.listdir(self.shared_folder))
        pident_dataurl = png_to_base64(os.path.join(self.shared_folder, "pident_sm.png"))
        length_dataurl = png_to_base64(os.path.join(self.shared_folder, "length_sm.png"))
        edge_dataurl = png_to_base64(os.path.join(self.shared_folder, "edge_sm.png"))
        edge_ref = self.save_file_to_workspace(os.path.join(self.shared_folder, "1.out.parquet"), "All edges found by BLAST")
        # fasta_ref = self.save_sequences_to_workspace(os.path.join(self.shared_folder, "sequences.fasta"), params["workspace_name"])
        with open(os.path.join(self.shared_folder, "acc_counts.json")) as f:
            acc_data = json.load(f)
        report_data = {
            "pident_img": pident_dataurl, 
            "length_img": length_dataurl, 
            "edge_img": edge_dataurl, 
            "convergence_ratio": f"{acc_data['ConvergenceRatio']:.3f}",
            "edge_count": acc_data["EdgeCount"],
            "unique_seqs": acc_data["UniqueSeq"],
            "workspace_name": params["workspace_name"]
        }
        output = self.generate_report(report_data)
        output["edge_ref"] = edge_ref["shock_id"]
        output["fasta_ref"] = "dummy_ref"#fasta_ref
        return output

    def generate_report(self, params):
        reports_path = os.path.join(self.shared_folder, "reports")
        template_path = os.path.join(TEMPLATES_DIR, "report.html")
        template_variables = params
        # The KBaseReport configuration dictionary
        config = dict(
            report_name=f"EFI_EST_FASTA_{str(uuid.uuid4())}",
            reports_path=reports_path,
            template_variables=template_variables,
            workspace_name=params["workspace_name"],
        )
        return self.create_report_from_template(template_path, config)

    def save_file_to_workspace(self, filepath, description):
        output_file_shock_id = self.dfu.file_to_shock({"file_path": filepath})["shock_id"]
        print(f"Uploaded filepath {filepath} to shock and got id {output_file_shock_id}")
        return {"shock_id": output_file_shock_id,
                "name": os.path.basename(filepath),
                "label": os.path.basename(filepath),
                "description": description}
    
    def save_sequences_to_workspace(self, filepath, workspace_name):
        return self.au.save_assembly_from_fasta({
            'file': {'path': filepath},
            'workspace_name': workspace_name,
            'assembly_name': 'all_sequences.fasta'
        })

class ExampleReadsApp(Core):
    def __init__(self, ctx, config, clients_class=None):
        """
        This is required to instantiate the Core App class with its defaults
        and allows you to pass in more clients as needed.
        """
        super().__init__(ctx, config, clients_class)
        # Here we adjust the instance attributes for our convenience.
        self.report = self.clients.KBaseReport
        self.ru = self.clients.ReadsUtils
        # self.shared_folder is defined in the Core App class.
        # TODO Add a self.wsid = a conversion of self.wsname

    def do_analysis(self, params: dict):
        """
        This method is where the main computation will occur.
        """
        read_refs = params["reads_ref"]
        # Download the reads from KBase
        ret = self.download_reads(read_refs)
        # We use these downloaded reads and biopython to collect the first 10
        # reads and their phred quality scores to create a new fastq file to
        # upload to KBase.
        for file_ref, file_info in ret["files"].items():
            file_path = file_info["files"]["fwd"]
            basename = os.path.basename(file_path)
            with open(file_path) as reads:
                record_iter = SeqIO.parse(reads, "fastq")
                limit = 10
                head = []
                scores = []
                counts = Counter()
                for ix, record in enumerate(record_iter):
                    if ix >= limit:
                        break
                    head.append(record)
                    counts.update(str(record.seq))
                    scores.append(record.letter_annotations["phred_quality"])
                filename = f"{basename}.head.fastq"
                out_path = os.path.join(self.shared_folder, filename)
                with open(out_path, "w") as out_reads:
                    SeqIO.write(head, out_reads, "fastq")

        # This method runs the process first and then returns the stdout and
        # stderr all at once, so take care if your process produces a large
        # amount of output.
        process = subprocess.Popen(
            ["/kb/module/scripts/random_logger.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        stdout, stderr = self.get_streams(process)
        # We are logging everything because the script we are running does not
        # have a lot of output, but if what you run does then you might not
        # want to log *everything* to the user.
        logging.info(stdout)
        if stderr:
            logging.warning(stderr)
        output_value = stdout.split("\n")[0].split(" ")[-2]
        count_df = pd.DataFrame(sorted(counts.items()), columns=["base", "count"])

        # Upload the first 10 reads back to kbase as an object
        upa = self.upload_reads(
            name=params["output_name"], reads_path=out_path, wsname=params["workspace_name"]
        )

        # Pass new data to generate the report.
        params["count_df"] = count_df
        params["output_value"] = output_value
        params["scores"] = scores
        params["upa"] = upa  # Not currently used, but the ID of the uploaded reads
        # This is the method that generates the HTML report
        return self.generate_report(params)

    @staticmethod
    def get_streams(process):
        """
        Returns decoded stdout,stderr after loading the entire thing into memory
        """
        stdout, stderr = process.communicate()
        return (stdout.decode("utf-8", "ignore"), stderr.decode("utf-8", "ignore"))

    def upload_reads(self, name, reads_path, wsname):
        """
        Upload reads back to the KBase Workspace. This method only uses the
        minimal parameters necessary to provide a demonstration. There are many
        more parameters which reads can provide, for example, interleaved, etc.
        By default, non-interleaved objects and those uploaded without a
        reverse file are saved as KBaseFile.SingleEndLibrary. See:
        https://github.com/kbaseapps/ReadsUtils/blob/master/lib/ReadsUtils/ReadsUtilsImpl.py#L115-L119
        param: filepath_to_reads - A filepath to a fastq fastq file to upload reads from
        param: wsname - The name of the workspace to upload to
        """
        ur_params = {
            "fwd_file": reads_path,
            "name": name,
            "sequencing_tech": "Illumina",
            "wsname": wsname,
        }
        # It is often useful to log parameters as they are passed.
        logging.warning(f">>>>>>>>>>>>>>>>>>>>{ur_params}")
        return self.ru.upload_reads(ur_params)

    def download_reads(self, reads_ref, interleaved=False):
        """
        Download a list of reads objects
        param: reads_ref - A list of reads references/upas
        """
        dr_params = {"read_libraries": [reads_ref], "interleaved": None}
        # This uses the ReadsUtils client to download a specific workspace
        # object, saving it into the shared_folder and making it available to
        # the user.
        return self.ru.download_reads(dr_params)

    def generate_report(self, params: dict):
        """
        This method is where to define the variables to pass to the report.
        """
        # This path is required to properly use the template.
        reports_path = os.path.join(self.shared_folder, "reports")
        # Path to the Jinja template. The template can be adjusted to change
        # the report.
        template_path = os.path.join(TEMPLATES_DIR, "report.html")
        # A sample multiplication table to use as output
        table = [[i * j for j in range(10)] for i in range(10)]
        headers = "one two three four five six seven eight nine ten".split(" ")
        # A count of the base calls in the reads
        count_df_html = params["count_df"].to_html()
        # Calculate a correlation table determined by the quality scores of
        # each base read. This requires pandas and matplotlib, and these are
        # listed in requirements.txt. You can see the resulting HTML file after
        # runing kb-sdk test in ./test_local/workdir/tmp/reports/index.html
        scores_df_html = (
            pd.DataFrame(params["scores"]).corr().style.background_gradient().render()
        )
        # The keys in this dictionary will be available as variables in the
        # Jinja template. With the current configuration of the template
        # engine, HTML output is allowed.
        template_variables = dict(
            count_df_html=count_df_html,
            headers=headers,
            scores_df_html=scores_df_html,
            table=table,
            upa=params["upa"],
            output_value=params["output_value"],
        )
        # The KBaseReport configuration dictionary
        config = dict(
            report_name=f"ExampleReadsApp_{str(uuid.uuid4())}",
            reports_path=reports_path,
            template_variables=template_variables,
            workspace_name=params["workspace_name"],
        )
        return self.create_report_from_template(template_path, config)
