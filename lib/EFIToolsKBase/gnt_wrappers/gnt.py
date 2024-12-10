import os
import json
import logging
import uuid
import zipfile

from jinja2 import DictLoader, Environment, select_autoescape

from ..nextflow import NextflowRunner
from ..const import *

from base import Core

# temp preamble for stand-in code
import urllib3
import sqlite3

BLOCKSIZE=1024
INPUT_METHODS = {"seqlookup": "User provided input was a list of sequence IDS."
                }


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
        take in validated input parameters, run the nextflow pipeline for 
        the GNT tool, save necessary output files to the workspace. 

        design idea: this method takes in a standardized input. need to create
        separate methods for the various input paths (FASTA Sequence Lookup, 
        Sequence ID Lookup, Single Sequence BLAST, or SSN File) that handles 
        those diverse input types and then feeds into this method to output a 
        standard out format. This is the app that calls nextflow.
        # NOTE: THIS IS MAY OR MAY NOT BE HOW THE GNT NF PIPELINE WORKS SO WAIT
        AND SEE

        :params mapping: dict, user-provided input
                            "final_output_dir": string, self.shared_folder
                            "ids_file": string, path to file with user-provided
                                        accession ids list
                            "nIDs": int, just a temp value to pass on
                            "sequence_database": string, only possible values 
                                                 are set in the input dropdown 
                                                 menu
                            "description": string, just a temp value to pass on
                            "gnt_input": string, just a temp value that might be
                                         used to control the GNT pipeline
                            - this mapping dict is used to do string 
                              substitution on the yml parameter template (yet to
                              be implemented)


        :params workspace_name: string, passed in from params dict in runner 
                                        (params["workspace_name"])
        :return: dict, 
                 - "gnd_ref" key maps to the object reference string created for
                   the GNDViewFile object written to the workspace
                 - NOTE: add other key:value pairs for passing info from this
                   method to the generate_report() method
        """
        logging.info(f"Working in {workspace_name} Workspace.")
        logging.info(f"shared folder ({self.shared_folder}) contains:\n{os.listdir(self.shared_folder)}")
        logging_str = "parameters for running the GNT:\n"
        for key, value in mapping.items():
            logging_str += f"{key}: {value}\n"
        logging.info(logging_str)

        logging_str = INPUT_METHODS.get(mapping["gnt_input"].lower())
        if not logging_str:
            raise SystemExit("Unexpected input type. Exiting.")
        logging.info(logging_str)

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
        #URL = "https://raw.githubusercontent.com/sahasramesh/kb_gnd_demo/refs/heads/master/30086.sqlite"
        URL = "https://raw.githubusercontent.com/sahasramesh/kb_gnd_demo/refs/heads/master/sahasWidget.spec"
        # download the URL object
        with http.request("GET",URL,preload_content=False) as response:
            gnd_view_file_path = os.path.join(self.shared_folder, "test.sqlite")
            with open(gnd_view_file_path,"wb") as out: 
                while True:
                    data = response.read(BLOCKSIZE)
                    if not data:
                        break
                    out.write(data)

        # test the sqlite actually is readable
        print(gnd_view_file_path)
        try:
            with sqlite3.connect(gnd_view_file_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM attributes')
                results = cursor.fetchall()
                print(results[0])
        except DatabaseError: 
            print(f"for some reason downloaded file isn't recognized as a sqlite file: {e}")
            pass
        except Exception as e: 
            print(f"some other funky stuff is happening")

        ###########################################################

        # attach the file to the workspace and get the GNDViewFile UPA
        print("trying to attach the downloaded file to a GNDViewFile object")
        data_ref = self.save_gnd_view_file_to_workspace(workspace_name, 
                                                        gnd_view_file_path)[0]

        return {"gnd_ref": data_ref, "nIDs": mapping["nIDs"]}

    def gather_sequence_data(self, mapping, workspace_name):
        """
        #### NOTE, MAY NOT FIT INTO DESIGN OF THE GNT NF CODE
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
        mapping["id_data"] = []

        return self.run_gnt_pipeline(mapping, workspace_name)

    def _create_file_links(self, inlcude_zip=True):
        """
        NOTE: replace hardcoded file paths/names to be dynamic or use a 
              stem that is defined in user-input
        """
        # hard coded for now since no stem variable is given
        output_file_names = [
            "GNDViewFile.sqlite"
        ]

        file_links = [
                {
                    "path": os.path.join(self.shared_folder, 
                                         output_file_names[0]),
                    "name": output_file_names[0],
                    "label":output_file_names[0],
                    "description": "Genome Neighborhood Diagram view file",
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

    def generate_report(self, params, template_var_dict):
        """
        Take in the results dict from run_gnt_pipeline() method, write the 
        associated html report, link files, ...

        runs the _create_file_links() method
        :param params: dict, app input info
        :param template_var_dict: dict, keys are variables in the 
                                  jinja2-readable template source file. Values
                                  are strings pasted in the template. 

        :param objects_created: dict, the `gnd_ref` key maps to the GNDViewFile
                                UPA string. 

        :returns: dict, filled with information about the report object but 
                        doesn"t return the actual dict report_info...
        """
        # get the workspace_id
        workspace_id = self.dfu.ws_name_to_id(params["workspace_name"])

        # output_files is a list of dicts, each element mapping to a file
        # created by the app. 
        # only the GNDViewFile sqlite file is created so no need to zip
        output_files = self._create_file_links(include_zip=False)

        # hand make the reports_path and file io variables
        # ... not sure why we need a new subdir? 
        reports_path = os.path.join(self.shared_folder, "reports")
        os.makedirs(reports_path, exist_ok=True)
        report_uuid = str(uuid.uuid4())
        report_name = f"EFI_GNT_{report_uuid}"
        report_path = os.path.join(reports_path, 
                                   f"{report_name}.html")

        # fill the KBaseReport configuration dictionary
        kbr_config = {"workspace_id": workspace_id,
                      "file_links": output_files,
                      "objects_created": [
                          {"ref": template_var_dict["gnd_ref"],
                           "description": "GND View File"}
                          ],
                      "direct_html_link_index": 0,
                      "html_links": [
                          {"description": "HTML report for GNT Sequence ID Lookup",
                           "name": f"{report_name}.html",
                           "path": reports_path}
                          ],
                      "html_window_height": 375,
                      "report_object_name": report_name,
                      "message": "A sample report." # the summary tab
                      }
        
        # Create report from template
        logging.info("Creating report...")
        template_path = os.path.join(TEMPLATES_DIR, "gnt_report.html")
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
        
        # return the name and UPA for the report file
        return {
            "report_name": report_info["name"],
            "report_ref": report_info["ref"],
        }

    def save_gnd_view_file_to_workspace(self, 
                                        workspace_name, 
                                        gnd_view_file_path):
        """
        save the GNDViewFile file to the workspace and return its object UPA
        """
        # get the ID instead of the name. apparently there's some race 
        # conditions to be considered.
        workspace_id = self.dfu.ws_name_to_id(workspace_name)
        print(type(workspace_id))
        # move file to the blobstore and get its ID
        print(f'trying to get shock id of the gnd view file {gnd_view_file_path}')
        gnd_view_file_shock_id = self.dfu.file_to_shock({"file_path": gnd_view_file_path})["shock_id"]
        # prep the save_objects() parameter dictionary
        save_object_params = {
            "id": workspace_id,
            # objects is a list of dicts, where each element contains info about
            # the object to be saved/created
            "objects": [{
                        "type": "EFIToolsKBase.GNDViewFile",
                        "data": {
                                "gnd_view_file_handle": gnd_view_file_shock_id,
                                },
                        "name": "gnd_view_file"}
                        # TODO: RBD
                        # change this to name the object, take user input into
                        # account here or use "id" instead... need to look at 
                        # DataFileUtil save_objects() method for more details
                        ]
            }
        # save file(s) to the workspace, given the parameters defined above
        # dfu.save_objects returns a list of length 
        # len(save_object_params["objects"]), each element being a tuple of 
        # len 11. See DataFileUtil client for more information
        
        # since only one object is being created, just grab the zeroth element
        # and parse its tuple
        print('grabbing the datafileutil object information')
        dfu_oi = self.dfu.save_objects(save_object_params)[0]
        # creates a str of f"{wsid}/{objid}/{version}" that is the object's UPA
        gnd_object_reference = str(dfu_oi[6]) + "/" + str(dfu_oi[0]) + "/" + str(dfu_oi[4])
        return [gnd_object_reference]
