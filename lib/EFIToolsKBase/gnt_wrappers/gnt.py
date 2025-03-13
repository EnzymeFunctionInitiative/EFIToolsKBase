
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
        params 
            dict, keys from the UI input fields
                "ssn_data_object": str, data object reference string
                "nb_size": int, number of neighbors from up and down
                           stream to be gathered and analyzed.
                "cooc_threshold": float, lower limit for the co-occurrence of 
                                  Pfam families in the SSN clusters' 
                                  neighborhoods.
                "gnd_object_name": str, name to be used for the GNDViewFile 
                                   data object to be created from this App.
        

        workspace_name
            str, passed in from params dict in runner (params["workspace_name"])

        RETURNS
        -------
        output_dict 
            dict, keys are "gnd_ref", "gnd_sqlite_path", "report_ref", 
            "report_name". 


            keys as defined by the UI output mapping
                "gnd_ref" key maps to the object reference string created for
                the GNDViewFile object written to the workspace

        """
        # log the start of the app
        logging.info(f"Working in {workspace_name} Workspace.")
        logging.info(f"shared folder ({self.shared_folder}) contains:\n" 
            + f"{os.listdir(self.shared_folder)}")
        
        # adding hardcoded input parameters to the params dict
        params["final_output_dir"] = self.shared_folder
        params["efi_config"] = EFI_CONFIG_PATH
        params["efi_db"] = EFI_DB_PATH
        
        # NOTE: does this need to change; write code that detects which
        # sequence database to use?
        params["fasta_db"] = "/data/blastdb/combined.fasta" 

        # using the object reference, grab the input SequenceSimilarityNetwork
        # data object.
        ssn_file_obj = self.dfu.get_objects(
            {"object_refs": [params["ssn_data_object"]]}
        )["data"][0]
        # grab the "ssn_input" xgmml file from the input ssn data object, save
        # a copy of the file to the docker storage space as "full_ssn.xgmml" 
        ssn_file_path = os.path.join(self.shared_folder, "full_ssn.xgmml"),
        self.dfu.shock_to_file({
            "shock_id": ssn_file_obj["data"]["ssn_xgmml_handle"], 
            "file_path": ssn_file_path,
            "unpack": "unpack"}
        )
        params["ssn_input"] = ssn_file_path
        params.pop("ssn_data_object")

        # log the parameters used for this run of the App
        logging_str = "parameters for running the GNT:"
        for key, value in params.items():
            logging_str += f"\n\t{key}: {value}"
        logging.info(logging_str)

        # validate input params
        fail = False
        if params["nb_size"] < 1 or params["nb_size"] > 20:
            logging.info(f'Invalid value for --nb-size ({params["nb_size"]}).')
            fail = True
        if params["cooc_threshold"] < 0 or params["cooc_threshold"] > 1:
            logging.info(f'Invalid value for --cooc-threshold '
                         + f'({params["cooc_threshold"]}).')
            fail = True
        if fail:
            exit("Failed to render input params.")

        self.flow.write_params_file(params)
        self.flow.generate_run_command()
        retcode, stdout, stderr = self.flow.execute()
        #if retcode != 0:
        #   raise ValueError(f"Failed to execute Nextflow pipeline\n{stderr}")

        logging.info(f"shared folder ({self.shared_folder}) contains:\n" 
            + f"{os.listdir(self.shared_folder)}")
        
        ######################################################################
        # validate the gnd.sqlite file and create the associated GNDViewFile 
        # Object
        logging.info('Creating the GNDViewFile object, named ' 
                     + f'{params["gnd_object_name"]}.')
        gnd_view_file_path = os.path.join(self.shared_folder, "gnd.sqlite")
        # test the sqlite for readability
        try:
            with sqlite3.connect(gnd_view_file_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM attributes")
                results = cursor.fetchall()
        except Exception as e: 
            logging.info(f"Unexpected error: {e=}, {type(err)=}")
            raise

        # create the GNDViewFile data object containing the gnd.sqlite file 
        gnd_obj_ref = self.save_gnd_view_file_to_workspace(
            workspace_name,
            gnd_view_file_path,
            params["gnd_object_name"],
            "testing"
        )

        # create an objects_created list, filled with dicts, each with "ref"
        # and "description" keys associated for each data object created
        # only the GNDViewFile object is created
        objects_created = [
            {
                "ref": gnd_obj_ref,
                "description": "SQLite database file containing information"
                    + " needed to visualize the genome neighborhood diagrams"
                    + " of SSN clusters",
            }
        ]
        
        ######################################################################
        # prep the info to be fed into the generate_report() method
        # read and prep the color_and_retrieve() output files
        logging.info(f'Creating the HTML report.')
        stats = pd.read_csv(os.path.join(self.shared_folder, "stats.txt"), sep="\t", header=None).to_html(index=False)
        try:
            ### UPDATE PATH TO THIS FILE WHEN EST #148 ISSUE GETS FIXED
            cluster_sizes = pd.read_csv(os.path.join(self.shared_folder, "cluster-data/id_lists/cluster_sizes.txt"), sep="\t").to_html(index=False)
        except:
            cluster_sizes = "No data"
        
        try:
            conv_ratios = pd.read_csv(os.path.join(self.shared_folder, "conv_ratio.txt"), sep="\t").to_html(index=False)
        except:
            conv_ratios = "No data"

        # read and prep the create_gnns() output files
        hub = pd.read_csv(os.path.join(self.shared_folder, "hub_count.txt"), sep="\t", header=None).to_html(index=False)
        cooc = pd.read_csv(os.path.join(self.shared_folder, "cooc_table.txt"), sep="\t", header=None).to_html(index=False)

        # gather the html strings and link to the data objects
        report_data = {
            "stats_tab": stats,
            "cluster_sizes_tab": cluster_sizes,
            "conv_ratios_tab": conv_ratios,
            "hub_tab": hub,
            "cooc_tab": cooc,
            "gnd_view_file_name": params["gnd_object_name"],
        }

        # create the HTML report, including linking files
        report_output = self.generate_report(workspace_name, 
                                             report_data, 
                                             objects_created_list)

        # NOTE: NEED TO FIGURE OUT WHAT INFO NEEDS TO BE PASSED TO THE IMPL.PY CODE
        return {"gnd_ref": gnd_obj_ref,
                "gnd_sqlite_path": gnd_view_file_path,
                "report_ref": report_output["report_ref"], 
                "report_name": report_output["report_name"]}


    def _create_file_links(self, include_zip=True):
        """
        !!! NOTE: missing SwissProt annotations by singleton
        
        Find, validate, and link important files created from the GNT to enable
        users to download these files. 

        Parameters
        ----------
            include_zip
                bool, control for whether a zip file of all linked files is 
                also created and linked. Default: True. 

        Returns
        -------
            file_links
                list of dicts, one dict per linked file. Each dict contains the
                necessary information for the KBaseReport creater to find and
                link the file to the Report.
        """
        # hard coded local file paths
        file_links = [
                {
                    "path": os.path.join(self.shared_folder, 
                                         "ssn_colored.xgmml"),
                    "name": "ssn_colored.xgmml",
                    "label":"Colored Sequence Similarity Network (SSN)",
                    "description": 'Each cluster in the submitted SSN has been identified and assigned a unique number and color. Node attributes for "Neighbor Pfam Families" and "Neighbor InterPro Families" have been added.',
                },
                {
                    "path": os.path.join(self.shared_folder, 
                                         "cluster_gnn.xgmml"),
                    "name": "cluster_gnn.xgmml",
                    "label":"SSN Cluster Hub-Nodes: Genome Neighborhood Network (GNN)",
                    "description": " GNNs provide a representation of the neighboring Pfam families for each SSN cluster identified in the colored SSN. To be displayed, neighboring Pfams families must be detected in the specified window and at a co-occurrence frequency higher than the specified minimum.\n\nEach hub-node in the network represents a SSN cluster. The spoke nodes represent Pfam families that have been identified as neighbors of the sequences from the center hub.",
                },
                {
                    "path": os.path.join(self.shared_folder, 
                                         "pfam_gnn.xgmml"),
                    "name": "pfam_gnn.xgmml",
                    "label":"Pfam Family Hub-Nodes Genome Neighborhood Network (GNN)",
                    "description": " GNNs provide a representation of the neighboring Pfam families for each SSN cluster identified in the colored SSN. To be displayed, neighboring Pfams families must be detected in the specified window and at a co-occurrence frequency higher than the specified minimum.\n\n Each hub-node in the network represents a Pfam family identified as a neighbor. The spokes nodes represent SSN clusters that identified the Pfam family from the center hub.",
                },
                {
                    "path": os.path.join(self.shared_folder, 
                                         "gnd.sqlite"),
                    "name": "gnd.sqlite",
                    "label":"Genome Neighborhood Diagrams (GNDs)",
                    "description": "Diagrams representing genomic regions around the genes encoded for the sequences from the submitted SSN are generated. All genes present in the specified window can be visualized (no minimal co-occurrence frequency filter or neighborhood size threshold is applied). Diagram data can be downloaded in .sqlite file format for later review in the View Saved Diagrams tab.",
                },
                {
                    "path": os.path.join(self.shared_folder, 
                                         "nomatches_noneighbors.txt"),
                    "name": "nomatches_noneighbors.txt",
                    "label":"No matches/no neighbors file",
                    "description": "",
                },
                {
                    "path": os.path.join(self.shared_folder, 
                                         "cooc_table.txt"),
                    "name": "cooc_table.txt",
                    "label":"Pfam family/cluster co-occurrence table file",
                    "description": "",
                },
                {
                    "path": os.path.join(self.shared_folder, 
                                         "hub_count.txt"),
                    "name": "hub_count.txt",
                    "label":"GNN hub cluster sequence count file",
                    "description": "",
                },
                {
                    "path": os.path.join(self.shared_folder, 
                                         "cluster-data/id_lists/cluster_sizes.txt"),
                    "name": "cluster_sizes.txt",
                    "label":"Cluster size file",
                    "description": "",
                },
                {
                    "path": os.path.join(self.shared_folder, 
                                         "swissprot_clusters_desc.txt"),
                    "name": "swissprot_clusters_desc.txt",
                    "label":"SwissProt annotations per SSN cluster",
                    "description": "",
                },
                {
                    "path": os.path.join(self.shared_folder, 
                                         "mapping_table.txt"),
                    "name": "mapping_table.txt",
                    "label":"Sequence to colored SSN cluster mapping file",
                    "description": "",
                }
        ]

        # gotta zip up directories for Mapping Tables download options
        subdirs = [
            ("nb_pfam/pfam/", "pfam.zip", "Neighbor Pfam domain fusions at specified minimal co-occurrence frequency "),
            ("nb_pfam/pfam_split/", "pfam_split.zip", "Neighbor Pfam domains at specified minimal co-occurrence frequency "),
            ("nb_pfam/all_pfam/", "all_pfam.zip", "Neighbor Pfam domain fusions at 0% minimal co-occurrence frequency"),
            ("nb_pfam/all_pfam_split/", "all_pfam_split.zip", "Neighbor Pfam domains at 0% minimal co-occurrence frequency"),
            ("nb_pfam/no_fam", "no_fam.zip", "Neighbors without Pfam assigned")
        ]
        
        # loop over the subdirectories
        for subdir, zip_file_name, label in subdirs:
            # open a zip file to be written to.
            zip_file_path = os.path.join(self.shared_folder, zip_file_name)
            with zipfile.ZipFile(
                    zip_file_path, 
                    "w", 
                    zipfile.ZIP_DEFLATED, 
                    allowZip64=True) as zf:
                # loop over files in the subdirectory and write them to the zip
                for file in os.scandir(subdir):
                    zf.write(f"{subdir}/{file.name}", arcname = file.name)
            # append the zip file to the file_links list
            file_links.append(
                {
                    "path": zip_file_path,
                    "name": zip_file_name,
                    "label": label,
                    "description": "",
                }
            )

        # check the include_zip boolean
        if include_zip:
            zip_file_path = os.path.join(self.shared_folder, "all_files.zip")
            # open a zip file to be written to.
            with zipfile.ZipFile(
                    zip_file_path, 
                    "w", 
                    zipfile.ZIP_DEFLATED, 
                    allowZip64=True) as zf:
                # loop over subdicts in file_links to grab the paths
                for file_dict in file_links:
                    zf.write(file_dict["path"], file_dict["name"])
            # append the zip file to the file_links list
            file_links.append(
                {
                    "path": zip_file_path,
                    "name": "all_files.zip",
                    "label": "all_files.zip",
                    "description": "All files created by the analysis collected in a zip archive."
                }
            )

        return file_links


    def generate_report(self, ws_name, template_var_dict, objects_created):
        """
        Take in the results dict from run_gnt_pipeline() method, write the 
        associated html report, link files, ...

        runs the _create_file_links() method
        
        Parameters
        ----------
            ws_name
                str, name for the active Workspace.
            template_var_dict
                dict, keys are variables in the jinja2-readable template source
                file. Values are strings pasted in the template. 
            objects_created
                list of dicts, the `gnd_ref` key maps to the GNDViewFile UPA 
                string. 

        Returns
        -------
            dict, 
                keys are "report_name" and "report_ref" with associated values. 
        """
        # get the workspace_id
        workspace_id = self.dfu.ws_name_to_id(ws_name)

        # output_files is a list of dicts, each element mapping to a file
        # created by the app. subdict keys are "path", "name", "label", and
        # "description"
        output_files = self._create_file_links(include_zip=True)

        # hand make the reports_path and file io variables
        reports_path = os.path.join(self.shared_folder, "reports")
        os.makedirs(reports_path, exist_ok=True)
        report_uuid = str(uuid.uuid4())
        report_name = f"EFI_GNT_{report_uuid}"
        report_path = os.path.join(reports_path, f"{report_name}.html")

        # create report from the template
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

        # fill the KBaseReport configuration dictionary
        kbr_config = {
            "workspace_id": workspace_id,
            "file_links": output_files,
            "objects_created": objects_created,
            "direct_html_link_index": 0,
            "html_links": [
                {
                    "path": reports_path,
                    "name": f"{report_name}.html",
                    "description": "HTML report for GNT Submission App",
                }
            ],
            "html_window_height": 375,
            "report_object_name": report_name,
            "message": "A sample report." # printed in the summary tab
        }
        
        # run the KBaseReport method to create the report to be shown
        report_info = self.report.create_extended_report(kbr_config)
        print(report_info)
        
        # return the name and UPA for the report file
        return {
            "report_name": report_info["name"],
            "report_ref": report_info["ref"],
        }


    def save_gnd_view_file_to_workspace(
            self, 
            ws_name, 
            gnd_view_file_path,
            data_obj_name,
            title):
        """
        Save the GNDViewFile file to the workspace and return its object UPA.

        Parameters
        ----------
            ws_name
                str, name for the active Workspace.
            gnd_view_file_path
                str, file path where the "gnd.sqlite" file is stashed.
            data_obj_name
                str, name for the GNDViewFile data object to be used in the
                data tab.
            
            title
                str, ....

        Returns
        -------
            gnd_object_reference
                str, UPA of the GNDViewFile object that is created with the
                format f"{wsid}/{objid}/{version}"
        """
        # get the ID instead of the name. apparently there's some race 
        # conditions to be considered.
        workspace_id = self.dfu.ws_name_to_id(ws_name)
        # move file to the blobstore and get its ID
        gnd_view_file_shock_id = self.dfu.file_to_shock({"file_path": gnd_view_file_path})["shock_id"]
        # prep the save_objects() parameter dictionary
        save_object_params = {
            "id": workspace_id,
            # objects is a list of dicts, where each element contains info about
            # the object to be saved/created
            "objects": [
                {
                    "type": "EFIToolsKBase.GNDViewFile",
                    "data": {
                        "gnd_view_file_handle": gnd_view_file_shock_id,
                        "view_title": title,
                    },
                    "name": data_obj_name
                }
            ]
        }
        # save file(s) to the workspace, given the parameters defined above
        # dfu.save_objects returns a list of length 
        # len(save_object_params["objects"]), each element being a tuple of 
        # len 11. See DataFileUtil client for more information.
        
        # since only one object is being created, just grab the zeroth element
        # and parse its tuple
        dfu_oi = self.dfu.save_objects(save_object_params)[0]
        print(dfu_oi)
        # creates a str of f"{wsid}/{objid}/{version}" that is the object's UPA
        gnd_object_reference = f"{dfu_oi[6]}/{dfu_oi[0]}/{dfu_oi[4]}"
        return gnd_object_reference


