
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
import sqlite3


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
        self.wsClient = self.clients.Workspace
        self.flow = NextflowRunner("pipelines/est/gnt.nf", "gnt/kbase.config")


    def run_gnt_pipeline(self, params, workspace_name):
        """
        take in App input parameters, validate them, run the nextflow pipeline
        for the GNT tool, save necessary output files to the workspace. 

        PARAMETERS
        ----------
        params, 
            dict, keys from the UI input fields
                "ssn_data_object": data object reference string
                "nb_size": int, number of neighbors from up and down
                                     stream to be gathered and analyzed.
                "cooc_threshold": float, lower limit for the 
                                               co-occurrence of Pfam families 
                                               in the SSN clusters' 
                                               neighborhoods.
                "gnd_object_name": str, name to be used for the GNDViewFile 
                                   data object to be created from this App.
        workspace_name,
            string, passed in from params dict in runner 
            (params["workspace_name"])
        

        RETURNS
        -------
        output_dict, 
            dict filled with keys as defined by the UI output mapping
                "gnd_ref" key maps to the object reference string created for
                the GNDViewFile object written to the workspace




        nextflow input parameters as keys associated values. Keys:
            "ids_file": string, path to file with user-provided
                        accession ids list
            "description": string, just a temp value to pass on
            "gnt_input": string, just a temp value that might be
                         used to control the GNT pipeline
            - this mapping dict is used to do string 
              substitution on the yml parameter template (yet to
              be implemented)

        """
        # adding hardcoded input parameters
        params["final_output_dir"] = self.shared_folder
        params["efi_config"] = EFI_CONFIG_PATH
        params["efi_db"] = EFI_DB_PATH
        params["fasta_db"] = "/data/blastdb/combined.fasta" 

        # grab the "ssn_input" sqlite file from the input ssn data object

        
        
        # log the start of the app
        logging.info(f"Working in {workspace_name} Workspace.")
        logging.info(f"shared folder ({self.shared_folder}) contains:\n{os.listdir(self.shared_folder)}")
        logging_str = "parameters for running the GNT:\n"
        for key, value in params.items():
            logging_str += f"{key}: {value}\n"
        logging.info(logging_str)

        if not logging_str:
            raise SystemExit("Unexpected input type. Exiting.")
        logging.info(logging_str)

        self.flow.write_params_file(mapping)
        self.flow.generate_run_command()
        retcode, stdout, stderr = self.flow.execute()
        if retcode != 0:
           raise ValueError(f"Failed to execute Nextflow pipeline\n{stderr}")

        
        #if not os.path.isfile(gnd_view_file_path):
        #    raise FileNotFoundError("The expected sqlite file was not" + 
        #                            "successfully downloaded")

        ## test the sqlite actually is readable
        #print(gnd_view_file_path)
        #try:
        #    with sqlite3.connect(gnd_view_file_path) as conn:
        #        cursor = conn.cursor()
        #        cursor.execute("SELECT * FROM attributes")
        #        results = cursor.fetchall()
        #        print(results[0])
        #except Exception as e: 
        #    print(f"Unexpected error: {e=}, {type(err)=}")
        #    raise

        ############################################################




        # attach the file to the workspace and get the GNDViewFile UPA
        print("Create the GNDViewFile object")
        data_ref = self.save_gnd_view_file_to_workspace(workspace_name, 
                                                        gnd_view_file_path,
                                                        mapping["description"])[0]
        
        print("Creating the HTML report")
        # 
        report_data = {
            "nIDs": mapping["nIDs"],
            "gnd_view_file_name": "gnd_view_file"
        }
        # only one object created (the GNDViewFile) so list of len 1
        objects_created_list = [
            {
                "ref": data_ref, 
                "description": "Genome Neighborhood Diagram View File"
            }
        ]
        report_output = self.generate_report(workspace_name, 
                                             report_data, 
                                             objects_created_list)

        return {"gnd_ref": data_ref, 
                "report_ref": report_output["report_ref"], 
                "report_name": report_output["report_name"]}

    def _create_file_links(self, include_zip=True):
        """
        NOTE: replace hardcoded file paths/names to be dynamic or use a 
              stem that is defined in user-input
        """
        # hard coded for now since no stem variable is given
        output_file_names = [
            "test.sqlite"
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

        if include_zip:
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

    def generate_report(self, ws_name, template_var_dict, objects_created):
        """
        Take in the results dict from run_gnt_pipeline() method, write the 
        associated html report, link files, ...

        runs the _create_file_links() method
        :param ws_name: string, name for the active Workspace
        :param template_var_dict: dict, keys are variables in the 
                                  jinja2-readable template source file. Values
                                  are strings pasted in the template. 

        :param objects_created: list of dicts, the `gnd_ref` key maps to the 
                                GNDViewFile UPA string. 

        :returns: dict, filled with information about the report object but 
                        doesn"t return the actual dict report_info...
        """
        # get the workspace_id
        workspace_id = self.dfu.ws_name_to_id(ws_name)

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
                      "objects_created": objects_created,
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
                                        gnd_view_file_path,
                                        title):
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
                                "view_title": title,
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








