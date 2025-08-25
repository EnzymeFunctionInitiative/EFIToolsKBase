import os
import re
import logging
from typing import Dict, Any

from .est import EFIEST, apply_fragment_filter, apply_family_addition
from ..const import *

IMPORT_MODE = ("import_mode", "accessions")

# create the accession id dictionary mapping objects
ACCESSION_IDS = KBaseMapping(
    "accession_id_input",
    "accession_ids",
    ""
)
ACCESSION_FMT = KBaseMapping(
    "accession_id_input",
    "accession_id_format",
    ""
)

# only used in Option D (AccessionIds)
FAMILY_FILTER = KBaseMapping("filter_by_family", "family_filter", "family")

# create the domain filtering/truncating dictionary mapping objects
DOMAIN_FILTER = KBaseMapping(
    "family_domain_boundary_options",
    "domain",
    ""  # does not get written in the param file
)
DOMAIN_FAMILY = KBaseMapping(
    "family_domain_boundary_options",
    "domain_family",
    "domain_family"
)
DOMAIN_REGION = KBaseMapping(
    "family_domain_boundary_options",
    "region",
    "domain"
)

class EFIAccessionIDs(EFIEST):
    def do_analysis(self, params):
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
        nf_parameters = self.prepare_nf_parameters(params)

        # do validation

        # log the nextflow parameters
        logging.info(f"Nextflow parameter file contains:\n{nf_parameters}")

        # run the parent class' run_est_pipeline method with nf-ready parameter
        # dictionary
        return self.run_est_pipeline(
            nf_parameters,
            params["workspace_name"],
            params["est_object_name"]
        )

    def prepare_nf_parameters(
            self,
            parameter_dict: Dict[str, Any],
        ) -> Dict[str, Any]:
        """
        Prepare the nextflow parameter dict from the user input in
        `parameter_dict`, specifically for an EST Accession Ids job.
        
        ARGUMENTS
        ---------
            parameter_dict
                dict, parameters gathered from the App's user input.

        RESULTS
        -------
            nf_parameters
                dict, contains parameters' key:value pairs ready for use in the
                EFI nextflow pipeline.
        """
        # gather generic parameters by calling the parent class'
        # `prepare_nf_parameters()` method.
        nf_parameters = super().prepare_nf_parameters(
            parameter_dict,
            get_param_value(parameter_dict, ACCESSION_FMT)
        )
        # at this point, the nf_parameters contain the generic parameters in
        # const.DEFAULT_NF_PARAMETERS, all_by_all_blast parameters,
        # "final_output_dir", "sequence_version", "job_id", "fasta_db", and
        # "filter". The "filter" key maps to a list of strings or an empty list
        # if no taxonomy filters are being applied.

        # write the pasted accession ID list to a file; needed in a specific
        # file format for the EST backend code
        accessions_file = self._prepare_accessions_file(
            get_param_value(parameter_dict, ACCESSION_IDS)
        )
        
        # add the accession input parameters to the nf_parameters dict
        nf_parameters.update(
            {
                IMPORT_MODE[0]: IMPORT_MODE[1],
                "accessions_file": accessions_file
            }
        )
      
        # check for the fragment fitler boolean
        frag_filter_str = apply_fragment_filter(parameter_dict)
        if frag_filter_str:
            nf_parameters["filter"].append(frag_filter_str)

        # check the family filter
        fam_filter_str = apply_family_filter(parameter_dict)
        if fam_filter_str:
            nf_parameters["filter"].append(fam_filter_str)

        # check for domain truncation
        domain_params = apply_domain_options(parameter_dict)
        if domain_params:
            nf_parameters.update(domain_params)

        # check for family additions
        family_addn_params = apply_family_addition(parameter_dict)
        if family_addn_params:
            nf_parameters.update(family_addn_params)

        # remove the filter parameter if it is an empty list
        if not nf_parameters.get("filter"):
            nf_parameters.pop("filter", None)

        return nf_parameters


    def _prepare_accessions_file(self, accession_string: str) -> str:
        """
        Handle user-input text and write to the required file format.
        
        EST/pipelines/est/import/get_sequence_ids.pl docs say that the file
        must have sequence IDs on a separate line; no additional delimiters
        are expected. This code assumes that the user does not follow the
        suggested format.
        """
        # assume users did not input text in the desired format. Also add
        # malicious-looking characters for security.
        accession_list = re.split(r"\n| |,|;|&|>|<|\?", accession_string)
        # remove empty strings if present
        accession_list = [
            accession for accession in accession_list if accession
        ]
        # write cleaned and formatted accession_list to file
        accession_str = "\n".join(accession_list)
        accessions_file = os.path.join(self.shared_folder, "pasted_accessions.txt")
        with open(accessions_file, "w") as f:
            f.write(accession_str)
        logging.info(f"Wrote {len(accession_list)} accession IDs to file.")
        
        return accessions_file

################################################################################
# parameter handling functions

def apply_family_filter(parameter_dict: Dict[str, str]) -> str:
    """
    Given the appropriate input dictionary, map KBase App UI inputs to relevant
    nextflow est.nf input parameters. Specific for the family filter and only
    called by D input path.
    """
    val = get_param_value(parameter_dict, FAMILY_FILTER)
    name = FAMILY_FILTER.nf_parameter_name
    if val:
        return f"{name}={val}"
    return ""

def apply_domain_options(parameter_dict: Dict[str, str]) -> Dict[str,str]:
    """
    Given the appropriate input dictionary, map KBase App UI inputs to relevant
    nextflow est.nf input parameters. Specific for the domain filter/truncation
    and only called by D input path (in this fashion).
    """
    # get and check the domain boolean;
    domain_val = get_param_value(parameter_dict, DOMAIN_FILTER)
    dict_key = DOMAIN_FILTER.dict_key
    subdict_key = DOMAIN_FILTER.subdict_key
    if domain_val:
        # region values are from a drop down menu; no handling of the value
        # is needed.
        result = apply_mapping(parameter_dict, DOMAIN_REGION)

        # gather the domain family string, validate it, and add to the result
        # dict
        fam_val = get_param_value(parameter_dict, DOMAIN_FAMILY)
        fam_name = DOMAIN_FAMILY.nf_parameter_name
        # validate that only a single family is entered by grabbing the first
        # word in the string.
        fam_val = re.split("\n| |,|;",fam_val.strip())[0]
        result.update({fam_name: fam_val})
        return result
    return {}
    

