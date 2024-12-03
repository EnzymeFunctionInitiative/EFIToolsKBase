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

# temp preamble for stand-in code
import urllib3


class EFIGNT(Core):
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
        
        ###########################################################
        # commenting out since no NF pipeline currently implemented
        ###########################################################
        #self.flow = NextflowRunner("pipelines/est/gnt.nf", "gnt/kbase.config")

    def do_analysis(self, params):
        """
        child classes should use this to render parameter files
        """
        raise NotImplementedError("Please Implement this method")

    def run_gnt_pipeline(self, mapping, workspace_name):
        """
        design idea: this method takes in a standardized input. create 
        separate methods for the various input paths (FASTA Sequence Lookup, 
        Sequence ID Lookup, Single Sequence BLAST, or SSN File) that handles 
        those diverse input types and then feeds into this method to output a 
        standard out format. This is the app that calls nextflow.

        :params mapping: dict, used to do string substitution on the yml 
                               parameter template, see subclass do_analysis() 
                               method for documentation on `mapping` key/values
        :params workspace_name: string, passed in from params dict in runner 
                                        (params["workspace_name"])
        :return: ...
        :rtype:  dict, created from the generate_report() method 
                       what are the key/value pairs in this object? 
        """
        logging.info(f'shared folder ({self.shared_folder}) contains:\n{os.listdir(self.shared_folder)}')
        logging_str = 'parameters:\n'
        for key, value in mapping.items():
            logging_str += f'{key}: {value}\n'
        logging.info(logging_str)

        if lower(mapping['gnt_input']) == 'seqlookup':
            logging.info('Input was gathered from a list of sequence IDs that were gathered')
        else:
            raise SystemExit('Unexpected input type. Exiting.')

        ###########################################################
        # commenting out since no NF pipeline currently implemented
        # see line(s) in __init__() method
        ###########################################################
        #self.flow.write_params_file(mapping)
        #self.flow.generate_run_command()
        #retcode, stdout, stderr = self.flow.execute()
        #if retcode != 0:
        #   raise ValueError(f"Failed to execute Nextflow pipeline\n{stderr}")
        ###########################################################

        ###########################################################
        # temp pipeline: 
        # download a (sqlite) file from sahasWidget github repo, e.g.
        # https://github.com/sahasramesh/kb_gnd_demo/blob/master/30086.sqlite
        # and then save this file as a data object so that it can be visualized
        # by sahasWidget
        http = urllib3.PoolManager()
        URL = "https://raw.githubusercontent.com/sahasramesh/kb_gnd_demo/refs/heads/master/sahasWidget.spec"
        # downloading this sqlite file is not working even on my local desktop. not sure why
        #URL = "https://raw.githubusercontent.com/sahasramesh/kb_gnd_demo/refs/heads/master/30086.sqlite"
        # download the URL object
        response = http.request('GET',URL)
        gnd_view_file_path = os.path.join(self.shared_folder, "test.txt")   # shouldn't use a static file name
        # write downloaded URL file to storage
        with open(gnd_view_file_path,'w') as out:
            out.write(response.data.decode('utf-8'))
        ###########################################################

        # attach the file to the workspace
        data_ref = self.save_gnd_view_file_to_workspace(workspace_name, 
                                                        gnd_view_file_path)
        report_data = {
            "workspace_name": workspace_name,
            "":,
            "":,
        }

        output = self.generate_report(report_data, 
                                      [{"description": "placeholder for actual results",
                                        "ref": data_ref}])

        return output

    def gather_sequence_data(self, mapping, workspace_name):
        """
        Gather sequence data associated with accession IDs provided by the user.
        if not already stored in a user-provided 
        ssn data object. 
        Then daisy-chained into running the `run_gnt_pipeline()` method.

        :params mapping: dict, see subclass do_analysis() method for 
                               documentation on `mapping` key/values
        :params workspace_name: string, passed in from params dict in runner 
                                        (params["workspace_name"])
        :return: ...
        :rtype:  results from the `run_gnt_pipeline()` method 
        """

        # place holder for code to grab sequence data associated with 
        # user-provided IDs
        mapping['id_data'] = []

        return self.run_gnt_pipeline(mapping, workspace_name)

    def _create_file_links(self, inlcude_zip=True):
        """
        NOTE: replace hardcoded file paths/names to be dynamic or use a 
              stem that is defined in user-input
        """
        output_file_names = [
        ]

        file_links = [
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
        """
        NOTE: NEED TO DEVELOP THE REPORT HTML FILE
        runs the _create_file_links() method 
        
        :returns: dict, filled with information about the report object but doesn't return the actual dict report_info...
        """
        reports_path = os.path.join(self.shared_folder, "reports")
        ###########################################################
        # commenting out since no report html currently implemented
        ###########################################################
        #template_path = os.path.join(TEMPLATES_DIR, "gnt_report.html")

        # The KBaseReport configuration dictionary
        config = dict(
            report_name=f"EFI_GNT_{str(uuid.uuid4())}",
            reports_path=reports_path,
            template_variables=params,
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

    def save_gnd_view_file_to_workspace(self, 
                                        workspace_name, 
                                        gnd_view_filepath):
        """
        NOTE: the GNDViewFile is not an object defined in the root spec file
        Need to update, commenting out the old est code for now
        """
        workspace_id = self.dfu.ws_name_to_id(workspace_name)
        gnd_view_file_shock_id = self.dfu.file_to_shock({"file_path": gnd_view_filepath})["shock_id"]
        

        #fasta_handle_shock_id = self.dfu.file_to_shock({"file_path": fasta_filepath})["shock_id"]
        #evalue_shock_id = self.dfu.file_to_shock({"file_path": evalue_filepath})["shock_id"]
        save_object_params = {
        'id': workspace_id,
        'objects': [{
            'type': 'EFIToolsKBase.GNDViewFile',
            'data': {
                "gnd_view_handle": gnd_view_file_shock_id
            },
            'name': "gnd_view_file"     # change this to name the object, take user input into account here 
        }]
        }
        dfu_oi = self.dfu.save_objects(save_object_params)[0]
        object_reference = str(dfu_oi[6]) + '/' + str(dfu_oi[0]) + '/' + str(dfu_oi[4])
        return object_reference
