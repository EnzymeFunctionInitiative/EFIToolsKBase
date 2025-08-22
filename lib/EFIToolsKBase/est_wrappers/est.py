
import os
import json
import logging
import uuid
import zipfile
from typing import List, Dict, Any

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
        self.wsClient = self.clients.Workspace
        self.flow = NextflowRunner("pipelines/est/est.nf", "est/kbase.config")

    ###########################################################################
    # interface method
    ###########################################################################
    def do_analysis(self, params: Dict[str,Any]):
        """
        child classes should use this method to wrap (a) rendering of the
        nextflow parameter file and (b) running the `run_est_pipeline()` method.
        """
        raise NotImplementedError("Please Implement this method")


    ###########################################################################
    # inherited methods, used in each subclass' `do_analysis()` call
    ###########################################################################
    def prepare_nf_parameters(
            self,
            parameter_dict: Dict[str, str],
            sequence_version: str
        ) -> Dict[str, Any]:
        """
        Prepare the nextflow parameter dict, filled with generic and/or 
        EST input branch-agnostic parameters.

        This should be called in do_analysis before running the est pipeline.

        ARGUMENTS
        ---------
            parameter_dict
                dict, parameters gathered from the App's user input.
            sequence_version
                str, either "UniProt", "UniRef90", or "UniRef50" (or any 
                capitalization therein). Accepted as an input argument because
                this info can be stashed in different UI subdicts that should 
                be handled in the App specific wrapper.

        RESULTS
        -------
            mapping
                dict, key:value pairs that have been mapped from the App's
                user-input to the nextflow parameter keys.
        """
        mapping = {}

        # fill in with the hardcoded parameters
        mapping.update(DEFAULT_NF_PARAMETERS)

        # get values 
        neg_log_e_value = -1*parameter_dict[blast_evalue_keys.dict_key][blast_evalue_keys.subdict_key]
        num_matches = parameter_dict[blast_nmatches_keys.dict_key][blast_nmatches_keys.subdict_key]
        
        # fill in with the user- and app-specific parameters
        mapping.update(
            {
                blast_evalue_keys.nf_parameter_name: 10**neg_log_e_value,
                blast_nmatches_keys.nf_parameter_name: num_matches,
                "final_output_dir": self.shared_folder,
                "sequence_version": sequence_version.lower(),
                "job_id": 131,  # NOTE: CHANGE THIS
            }
        )

        # handle nf's params.fasta_db
        blast_db_source = ("combined"
            if sequence_version.lower() == "uniprot"
            else sequence_version
        )
        
        print(parameter_dict)
        print(FRAGMENT_FILTER)
        dict_key = FRAGMENT_FILTER.dict_key
        subdict_key = FRAGMENT_FILTER.subdict_key
        fragment_filter_bool = bool(
            parameter_dict.get(dict_key) and parameter_dict[dict_key].get(subdict_key)
        )
        fasta_db = BlastDB.get_path(
            blast_db_source,
            fragment_filter_bool
        )
        # add it to the mapping dict
        mapping.update({"fasta_db": fasta_db})

        # add the taxonomy_filter() 
        taxonomy_filters = apply_taxonomy_filter(parameter_dict)
        # add the first entry to the "filter" keyword, whether the 
        # taxonomy_filters is an empty list
        mapping.update({"filter": taxonomy_filters})

        return mapping


    def run_est_pipeline(
            self,
            mapping: Dict[str, str],
            workspace_name: str,
            data_obj_name: str = "blast_edge_file", 
        ) -> Dict[str, str]:
        """
        This should be called in do_analysis after rendering parameters.

        ARGUMENTS
        ---------
            mapping
                dict, contains key:value pairs for all input parameters used
                within the est.nf pipeline code.
            workspace_name
                str, identifier string for the workspace within which the app
                is running.
            data_obj_name
                str, to be used as the name for the BlastEdgeFile data object
                created to contain the EST results.

        RESULTS
        -------
            output_dict
                dict, contains key:value pairs of object references and other
                metadata. Mostly, this dict goes unused.
        """
        # prepare the params file
        self.flow.write_params_file(mapping)
        # generate the `nextflow run` command
        self.flow.generate_run_command()
        # execute the command
        retcode, stdout, stderr = self.flow.execute()
        if retcode != 0:
            raise ValueError(f"Failed to execute Nextflow pipeline.")
        
        print(self.shared_folder, os.listdir(self.shared_folder))
        
        # make the images to be shown in the report
        pident_dataurl = png_to_base64(
            os.path.join(self.shared_folder, "pident_sm.png")
        )
        length_dataurl = png_to_base64(
            os.path.join(self.shared_folder, "length_sm.png")
        )
        edge_dataurl = png_to_base64(
            os.path.join(self.shared_folder, "edge_sm.png")
        )

        # gather stats output from the workflow
        with open(os.path.join(self.shared_folder, "stats.json")) as f:
            acc_data = json.load(f)

        # create the data object output from the EST Apps
        print("Create the BlastEdgeFile object")
        data_ref = self._save_edge_file_to_workspace(
            workspace_name,
            os.path.join(self.shared_folder, "1.out.parquet"),
            os.path.join(self.shared_folder, "all_sequences.fasta"),
            os.path.join(self.shared_folder, "evalue.tab"),
            os.path.join(self.shared_folder, "sequence_metadata.tab"),
            acc_data,
            data_obj_name
        )
        
        # prepare the data structures to be used in the report
        report_data = {
            "pident_img": pident_dataurl,
            "length_img": length_dataurl,
            "edge_img": edge_dataurl,
            "convergence_ratio": f"{acc_data['convergence_ratio']:.3e}",
            "edge_count": acc_data["num_blast_edges"],
            "unique_seqs": acc_data["num_unique_ids"]
        }
        # only one object created (the BlastEdgeFile) so list of len 1
        objects_created_list = [
            {
                "ref": data_ref,
                "description": "Edge file and other metadata"
            }
        ]
        
        print("Create the HTML report")
        output = self._generate_report(
            workspace_name,
            report_data,
            objects_created_list
        )
        
        output["edge_ref"] = data_ref

        # add cleaning code to remove unnecessary files that nextflow creates

        return output

    ###########################################################################
    # private methods, called within the `run_est_pipeline()` method
    ###########################################################################
    def _create_file_links(self, include_zip=True):
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

        if include_zip:
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

    def _generate_report(
            self,
            ws_name,
            template_var_dict,
            objects_created
        ) -> Dict[str,str]:
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

    def _save_edge_file_to_workspace(
            self,
            workspace_name: str,
            edge_filepath: str,
            fasta_filepath: str,
            evalue_filepath: str,
            seq_meta_filepath: str,
            acc_data: Dict[str, str],
            obj_name: str
        ) -> str:
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
                    'name': obj_name,
                    "data": {
                        "edgefile_handle": edge_file_shock_id,
                        "fasta_handle": fasta_handle_shock_id,
                        "evalue_handle": evalue_shock_id,
                        "seq_meta_handle": seq_meta_shock_id,
                        "edge_count": acc_data["num_blast_edges"],
                        "unique_seq": acc_data["num_unique_ids"],
                        "convergence_ratio": acc_data['convergence_ratio'],
                    }
                }
            ]
        }
        # since only one object is being created, just grab the zeroth element
        # and parse its tuple
        dfu_oi = self.dfu.save_objects(save_object_params)[0]
        object_reference = f"{dfu_oi[6]}/{dfu_oi[0]}/{dfu_oi[4]}"

        return object_reference


###############################################################################
# create dictionary key mapping objects from `..const.dict_keys()` namedtuple.
# only include the generic mappings here. 

FRAGMENT_FILTER = dict_keys(
    "fragment_option",
    "exclude_fragments",
    "fragments"
)

# NOTE: make the equivalent for taxonomy filtering

# used in option A, C, and D
ADD_FAMILIES = dict_keys(
    "protein_family_addition_options",
    "families_to_add",
    "families"
)
FRACTION_FILTER = dict_keys(
    "protein_family_addition_options",
    "fraction",
    "fraction"
)
#families_fmt_keys = dict_keys(
#    "protein_family_addition_options",
#    "families_addition_cluster_id_format"
#    "unknown",
#)

# EST specific dictionary mappings (via const.dict_keys namedtuples objects)
blast_evalue_keys = dict_keys("all_by_all_blast_options","blast_e_value","blast_evalue")
blast_nmatches_keys = dict_keys("all_by_all_blast_options","blast_num_matches","blast_num_matches")


###############################################################################
# parameter handling functions, shared across multiple Apps.

def apply_fragment_filter(parameter_dict: Dict[str, str]) -> str:
    """
    Given the appropriate input dictionary, map KBase App UI inputs to relevant
    nextflow est.nf input parameters. Specific for the fragment filter and
    called by A, B, and D input paths.
    """
    dict_key = FRAGMENT_FILTER.dict_key
    subdict_key = FRAGMENT_FILTER.subdict_key
    name = FRAGMENT_FILTER.nf_parameter_name
    if (
            parameter_dict.get(dict_key) and 
            parameter_dict[dict_key].get(subdict_key)
    ):
        val = parameter_dict[dict_key].get(subdict_key)
        return f"{name}={val}"

    return ""

# NOTE: incomplete
def apply_taxonomy_filter(parameter_dict: Dict[str, str]) -> List[str]:
    """
    Given the appropriate input dictionary, map KBase App UI inputs to relevant
    nextflow est.nf input parameters. Specific for the taxonomy filter(s) and
    called by all input paths.
    """
    # INCOMPLETE
    return []

def apply_family_addition(parameter_dict: Dict[str, str]) -> Dict[str,str]:
    """
    Given the appropriate input dictionary, map KBase App UI inputs to relevant
    nextflow est.nf input parameters. Specific for the Protein Family Addition
    and called by A, C, and D input paths.
    """
    # get the keys to the families subdictionary
    families_dict_key = ADD_FAMILIES.dict_key
    families_subdict_key = ADD_FAMILIES.subdict_key
    families_name = ADD_FAMILIES.nf_parameter_name
    # get the keys to the fraction subdictionary
    fraction_dict_key = FRACTION_FILTER.dict_key
    fraction_subdict_key = FRACTION_FILTER.subdict_key
    fraction_name = FRACTION_FILTER.nf_parameter_name

    # check that the (sub)dictionary and values exist and/or are true-ish
    if (
            parameter_dict.get(families_dict_key) and
            parameter_dict[families_dict_key].get(families_subdict_key) and
            parameter_dict[fraction_dict_key].get(fraction_subdict_key)
    ):
        return {
                families_name: params[families_dict_key][families_subdict_key],
                fraction_name: params[fraction_dict_key][fraction_subdict_key],
        }

    return {}

