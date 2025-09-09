
import os
import logging
import uuid
import zipfile
from typing import Iterator, List, Dict, Tuple, Any
import json

from jinja2 import DictLoader, Environment, select_autoescape

# This is the SFA base package which provides the Core app class.
from base import Core

from .est import apply_fragment_filter, apply_taxonomy_filter
from ..nextflow import NextflowRunner
from ..const import *

###############################################################################
# create dictionary key mapping objects from `..const.KBaseMapping()` namedtuple.
UNPACK_str = "unpack"
SHOCKID_str = "shock_id"
FILEPATH_str = "file_path"

BLAST_PARQUET = KBaseMapping(
    "data",
    "edgefile_handle",
    "blast_parquet"
)
BLAST_FASTA = KBaseMapping(
    "data",
    "fasta_handle",
    "fasta_file"
)
BLAST_META = KBaseMapping(
    "data",
    "seq_meta_handle",
    "seq_meta_file"
)

SSN_TITLE = KBaseMapping(
    "meta_options",
    "ssn_title",
    "ssn_title"
)

SEQ_LEN_MIN = KBaseMapping(
    "sequence_length_options",
    "min_length",
    "min_length"
)
SEQ_LEN_MAX = KBaseMapping(
    "sequence_length_options",
    "max_length",
    "max_length"
)

METRIC_STR = KBaseMapping(
    "metric_filter_options",
    "filter_parameter",
    "filter_parameter"
)
METRIC_VAL = KBaseMapping(
    "metric_filter_options",
    "filter_value",
    "filter_min_val"
)


###############################################################################
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
        self.wsClient = self.clients.Workspace
        self.flow = NextflowRunner(
            "pipelines/generatessn/generatessn.nf",
            "generatessn/kbase.config"
        )


    ###########################################################################
    # method called within the EFIToolsKBaseImpl.py run_EFI_EST_SSN_Creation
    ###########################################################################
    def do_analysis(self, params):
        """
        gather files from the BlastEdgeFile data object, create input json with
        parameters for the generatessn.nf script, execute the script, gather
        output files into the SequenceSimilarityNetwork data object, create
        linked files for user-download, create HTML report to summarize results

        Parameters
        ----------
            params
                dict of UI user input. Key:value pairs are:
                    "blast_edge_file_ref"
                        string, reference info to the selected BlastEdgeFile
                        data object
                    "filter_options"
                        dict, keys:value pairs are:
                            "filter_parameter"
                                string, which metric to filter BLAST results by
                            "filter_value"
                                float, value used as cutoff for the
                                "filter_parameter"
                    "min_length"
                        int, minimum sequence length to consider
                    "max_length"
                        int, maximum sequence length to consider
                    "workspace_name"
                        string, name of the narrative workspace
                    "ssn_object_name"
                        string, name to be used for the created
                        SequenceSimilarityNetwork data object output from the
                        app

        Returns
        -------
            output
                dict containing reference information for the report and data
                object created by the App.
        """
        # log user input from the UI
        logging.info(f"User input parameters:\n{params}")

        # clean the input params dict and subdict values
        # step 1. remove un-mapped keys in the outer dict; these are created
        # because parameter_groups are "optional" but are always included in
        # the params dict from the UI. If left un-enabled, the parameter
        # group's key maps to a NoneType object.
        params = clean_dict(params)
        # step 2. do the same for inner subdicts.
        for key in params.keys():
            params[key] = clean_dict(params[key])

        # correctly map and gather all nextflow parameters
        nf_parameters = self._prepare_nf_parameters(params)

        # do validation
        # - given a filter_parameter, make sure the given filter_value is 
        #   appropriate

        # log the nextflow parameters
        logging.info(f"Nextflow parameter file contains:\n{nf_parameters}")

        # prepare the nextflow json param file
        self.flow.write_params_file(nf_parameters)
        # generate the nextflow command to be subprocess run'd
        self.flow.generate_run_command()
        # run the command
        retcode, stdout, stderr = self.flow.execute()
        if retcode != 0:
             raise ValueError(f"Failed to execute Nextflow pipeline\n{stderr}")

        logging.info(
            f"Final output directory ({self.shared_folder}) contains:"
            + f" {os.listdir(self.shared_folder)}"
        )
        
        # gather stats output from the workflow
        with open(os.path.join(self.shared_folder, "stats.json")) as f:
            stats = json.load(f)
    
        stats_str = "\n".join(
            [f"{key}: {value}" for key, value in stats.items()]
        )
        logging.info(f"The full SSN has:\n{stats_str}")

        # create the data object output from the SSN_Creation App
        logging.info("Creating the SequenceSimilarityNetwork object")
        ssn_ref = self._save_ssn_file_to_workspace(
            params["workspace_name"],
            os.path.join(self.shared_folder, "full_ssn.xgmml"),
            int(stats["full_ssn.xgmml"]["num_nodes"]),
            int(stats["full_ssn.xgmml"]["num_edges"]),
            "A SSN XGMML file and metadata",
            params["ssn_object_name"]
        )

        # prepare the data structures to be used in the report
        report_data = {
            "num_nodes": stats["full_ssn.xgmml"]["num_nodes"],
            "num_edges": stats["full_ssn.xgmml"]["num_edges"],
            "size": f'{stats["full_ssn.xgmml"]["size"] * 10**-9}:.3f',
            "workspace_name": params["workspace_name"]
        }
        # only one object created (the SequenceSimilarityNetwork) so list of
        # len 1
        objects_created_list = [
            {
                "ref": ssn_ref,
                "description": "A SSN XGMML file and metadata"
            }
        ]

        output = self._generate_report(
            params["workspace_name"],
            report_data,
            objects_created_list
        )
       
        output["ssn_ref"] = ssn_ref

        # add cleaning code to remove unnecessary files that nextflow creates

        return output


    ###########################################################################
    # private methods, called within the `do_analysis()` method
    ###########################################################################
    def _prepare_nf_parameters(
            self, 
            parameter_dict: Dict[str,str],
        ) -> Dict[str, Any]:
        """
        Prepare the nextflow parameter dict, filled with generic and/or
        GenerateSSN workflow parameters.
        
        Parameters
        ----------
            parameter_dict
                dict, parameters gathered from the App's user input.

        Returns
        -------
            mapping
                dict, key:value pairs that have been mapped from the App's
                user-input to the nextflow parameter keys.
        """
        mapping = {}

        # fill in with the generic parameters
        mapping.update(DEFAULT_NF_PARAMETERS)
        mapping.update(
            {
                "db_version": EFI_DB_VERSION,
                "final_output_dir": self.shared_folder
            }
        )

        # prep the iterator to gather specific files from the user-specified
        # data object.
        file_iterator = zip(
            [BLAST_PARQUET, BLAST_FASTA, BLAST_META],
            ["1.out.parquet","sequences.fa","sequence_metadata.tab"]
        )
        # prep a similar list of metadata KBaseMapping objects if metadata 
        # needs to be grabbed.
        meta_list = []

        # get those files
        mapping.update(
            self._access_data_obj(
                parameter_dict["blast_edge_file_ref"],
                file_iterator,
                meta_list
            )
        )

        # handle the ssn_title meta-info, sequence length min and max values,
        # and metric filter options.
        mapping.update(
            {
                SSN_TITLE.nf_parameter_name: get_param_value(
                    parameter_dict,
                    SSN_TITLE
                ),
                SEQ_LEN_MIN.nf_parameter_name: get_param_value(
                    parameter_dict,
                    SEQ_LEN_MIN
                ),
                SEQ_LEN_MAX.nf_parameter_name: get_param_value(
                    parameter_dict,
                    SEQ_LEN_MAX
                ),
                METRIC_STR.nf_parameter_name: get_param_value(
                    parameter_dict,
                    METRIC_STR
                ),
                METRIC_VAL.nf_parameter_name: get_param_value(
                    parameter_dict,
                    METRIC_VAL
                )
            }
        )

        # NOTE: these filters have not been implemented on the backend
        # add the taxonomy_filter()
        taxonomy_filters = apply_taxonomy_filter(parameter_dict)
        # add the first entry to the "filter" keyword, whether the
        # taxonomy_filters is an empty list
        mapping.update({"filter": taxonomy_filters})

        # check for the fragment fitler boolean
        frag_filter_str = apply_fragment_filter(parameter_dict)
        if frag_filter_str:
            mapping["filter"].append(frag_filter_str)

        # remove the filter parameter if it is an empty list
        if not mapping.get("filter"):
            mapping.pop("filter", None)

        return mapping

    def _access_data_obj(
            self,
            dfu_ref_str: str,
            file_iterator: Iterator[tuple] = [],
            meta_iterator: List = []
        ) -> Dict[str, Any]:
        """
        Handle a single reference string for a data object, access the data
        object and gather relevant files/metadata from the data object. Then,
        given an iterator of files, gather the associated files to the current
        working directory. Return a dictionary of parameter names that map to
        the accessed file paths.

        Arguments
        ---------
            dfu_ref_str
                string, the reference string used to access a given data object.
            file_iterator
                iterator of tuples, each tuple contains the information needed
                to access the file in the current App. Default is an empty list.
                If not default, organization is:
                    [0] - KBaseMapping object containing keys to access the data
                          object's "data" dict and associated file's subdict
                          key's value. Also includes the parameter name to be
                          used in the returned dictionary.
                    [1] - string, a file name to be used for transferring the
                          file from the data object to the current App's working
                          directory.
            meta_iterator
                A list of KBaseMapping objects, each containing the information
                needed to access the data object's "data" dict and associated
                metadata's subdict. Also includes the parameter name to be used
                in the returned dictionary. Default is an empty list.
        """
        # grab the data object via the Data File Utility (dfu) via the object
        # ref string.
        data_obj_dict = self.dfu.get_objects(
            {
                "object_refs": [dfu_ref_str]
            }
        )["data"][0]
        
        logging.info(
            f"The BlastEdgeFile {dfu_ref_str} data object contains:"
            + f"\n{data_obj_dict}"
        )
      
        parameter_dict = {}
        # grab files
        for file_mapping, file_name in file_iterator:
            # prep the necessary values for a call to the DFU `shock_to_file()`
            # method.
            file_handle = get_param_value(data_obj_dict, file_mapping)
            file_path = os.path.join(self.shared_folder, file_name)
            # run the DFU `shock_to_file` method to "download" the specified
            # file to the current App's working directory.
            self.dfu.shock_to_file(
                {
                    SHOCKID_str: file_handle,
                    FILEPATH_str: file_path,
                    UNPACK_str: UNPACK_str
                }
            )
            # update the output dict to map the new file_path to the nextflow
            # parameter.
            parameter_dict.update({file_mapping.nf_parameter_name: file_path})

        # grab metadata values
        for meta_mapping in meta_iterator:
            parameter_dict.update(
                {
                    meta_mapping.nf_parameter_name: get_param_value(
                        data_obj_dict,
                        meta_mapping
                    )
                }
            )

        return parameter_dict

    def _save_ssn_file_to_workspace(
            self,
            workspace_name: str,
            filepath: str,
            nodes: int,
            edges: int,
            description: str = "SSN XGMML file and metadata",
            obj_name: str = "ssn_file"
        ) -> str:
        """Create the SequenceSimilarityNetwork data object"""
        workspace_id = self.dfu.ws_name_to_id(workspace_name)
        output_file_shock_id = self.dfu.file_to_shock(
            {"file_path": filepath}
        )["shock_id"]
        # prep the save_objects() parameter_dictionary
        save_object_params = {
            "id": workspace_id,
            # objects is a list of dicts, where each element dict contains info
            # about the object to be saved/created
            "objects": [
                {
                    "type": "EFIToolsKBase.SequenceSimilarityNetwork",
                    "name": obj_name,
                    "data": {
                        "ssn_xgmml_handle": output_file_shock_id,
                        "node_count": nodes,
                        "edge_count": edges,
                    }
                }
            ]
        }
        # since only one object is being created, just grab the zeroth element
        # and parse its tuple
        dfu_oi = self.dfu.save_objects(save_object_params)[0]
        object_reference = f"{dfu_oi[6]}/{dfu_oi[0]}/{dfu_oi[4]}"
        return object_reference


    def _create_file_links(self, include_zip=True):
        """link named files to the App's output report"""
        output_file_names = [
            "2.out",
            "filtered_sequences.fasta",
            "full_ssn.xgmml",
            "ssn_metadata.tab"
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
                "description": "Filtered FASTA file containing sequences"
                                + " present in the network"
            },
            {
                "path": os.path.join(self.shared_folder, output_file_names[2]),
                "name": output_file_names[2],
                "label": output_file_names[2],
                "description": "Sequence similarity network file (format:"
                                + " xgmml)"
            },
            {
                "path": os.path.join(self.shared_folder, output_file_names[3]),
                "name": output_file_names[3],
                "label": output_file_names[3],
                "description": "Taxonomy and other metadata about each"
                                + " sequence in filtered_sequences.fasta"
            }
        ]

        if include_zip:
            zip_path = os.path.join(self.shared_folder, "all_files.zip")
            with zipfile.ZipFile(
                    zip_path, "w", zipfile.ZIP_DEFLATED, allowZip64=True
            ) as zf:
                for file in file_links:
                    zf.write(file["path"], file["name"])

            zip_file_link = {
                "path": zip_path,
                "name": "all_files.zip",
                "label": "all_files.zip",
                "description": "All files created by the analysis collected"
                                + " in a zip archive"
            }
            file_links = [zip_file_link] + file_links

        return file_links


    def _generate_report(
            self,
            ws_name: str,
            template_var_dict: Dict[str, Any],
            objects_created: Dict[str, Any]
        ) -> Dict[str,str]:
        """
        Generate the HTML report file associated with the App

        Parameters
        ----------
            ws_name
                string, workspace name used to map to the workspace ID

            template_var_dict
                Dictionary. Key:value pairs:
                    "stats": html string representing the tabulated SSN results
                    "filter_options": dict,

            objects_created
                list of dicts, each dict containing the shock_id reference and
                description for the Data Objects created by the App. Only
                contains info about the SequenceSimilarityNetwork object.

        Returns
        -------
            output
                Dictionary of reference information for the report file.

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
        report_name = f"SSN_Creation_{report_uuid}"
        report_path = os.path.join(reports_path, f"{report_name}.html")
        
        # fill the KBaseReport configuration dictionary
        kbr_config = dict(
            workspace_id= workspace_id,
            file_links = output_files,
            objects_created = objects_created,
            direct_html_link_index = 0,
            html_links = [
                {
                    "description": "HTML report for the SSN Creation App",
                    "name": f"{report_name}.html",
                    "path": reports_path,
                }
            ],
            html_window_height = 375,
            report_object_name = report_name,
            message = "A sample report."            # update!
        )

        # Create report from template
        logging.info("Creating the HTML report")
        template_path = os.path.join(TEMPLATES_DIR, "ssn_creation_report.html")
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
        
        # Create report object including report
        with open(report_path, "w") as report_file:
            report_file.write(report)

        # run the KBaseReport method to create the report to be shown
        report_info = self.report.create_extended_report(kbr_config)

        return {
            "report_name": report_info["name"],
            "report_ref": report_info["ref"],
        }

