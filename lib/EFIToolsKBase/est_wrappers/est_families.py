import os
import re
import logging
from typing import Dict, Tuple, Any

from .est import EFIEST, apply_fragment_filter, ADD_FAMILIES
from ..const import *

IMPORT_MODE = ("import_mode", "family")

# ADD_FAMILIES KBaseMapping object is reusable here but need to include the
# FAMILIES_FMT object below and use a different apply_families_addition() func
# to correctly apply the given UI parameters.
FAMILIES_FMT = KBaseMapping(
    "protein_family_addition_options",
    "families_id_format",
    ""
)
FRACTION_FILTER = KBaseMapping(
    "protein_family_size_option",
    "fraction",
    "fraction"
)

# create the domain filtering/truncating dictionary mapping objects
DOMAIN_FILTER = KBaseMapping(
    "family_domain_boundary_options",
    "domain",
    ""  # does not get written in the param file
)
DOMAIN_REGION = KBaseMapping(
    "family_domain_boundary_options",
    "region",
    "domain"
)

class EFIFamilies(EFIEST):
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

        # log the number of family IDs used to get sequences
        logging.info(
            f"Using {len(nf_parameters[ADD_FAMILIES.nf_parameter_name])}"
            + " Family IDs for gathering sequences."
        )

        # do validation

        # log the nextflow parameters
        logging.info(f"Nextflow parameter file contains:\n{nf_parameters}")

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
            get_param_value(parameter_dict, FAMILIES_FMT)
        )
        # at this point, the nf_parameters contain the generic parameters in
        # const.DEFAULT_NF_PARAMETERS, all_by_all_blast parameters,
        # "final_output_dir", "sequence_version", "job_id", "fasta_db", and
        # "filter". The "filter" key maps to a list of strings or an empty list
        # if no taxonomy filters are being applied.

        nf_parameters.update({IMPORT_MODE[0]: IMPORT_MODE[1]})

        # check for the fragment fitler boolean
        frag_filter_str = apply_fragment_filter(parameter_dict)
        if frag_filter_str:
            nf_parameters["filter"].append(frag_filter_str)

        # check for domain truncation
        domain_params = apply_domain_options(parameter_dict)
        if domain_params:
            nf_parameters.update(domain_params)

        # check for family additions
        family_addn_params, frac_str = apply_family_addition(parameter_dict)
        nf_parameters.update(family_addn_params)
        if frac_str:
            nf_parameters["filter"].append(frac_str)

        # remove the filter parameter if it is an empty list
        if not nf_parameters.get("filter"):
            nf_parameters.pop("filter", None)

        return nf_parameters

################################################################################
# parameter handling functions

def apply_domain_options(parameter_dict: Dict[str, str]) -> Dict[str,str]:
    """
    Given the appropriate input dictionary, map KBase App UI inputs to relevant
    nextflow est.nf input parameters. Specific for the domain filter/truncation
    and only called by B input path (in this fashion).
    """
    # get and check the domain boolean;
    domain_val = get_param_value(parameter_dict, DOMAIN_FILTER)
    dict_key = DOMAIN_FILTER.dict_key
    subdict_key = DOMAIN_FILTER.subdict_key
    if domain_val:
        # region values are from a drop down menu; no handling of the value
        # is needed.
        return apply_mapping(parameter_dict, DOMAIN_REGION)
    return {}

def apply_family_addition(
        parameter_dict: Dict[str, str]
    ) -> Tuple[Dict[str,str], str]:
    """
    Given the appropriate input dictionary, map KBase App UI inputs to relevant
    nextflow est.nf input parameters. Specific for the Protein Family Addition
    and called by A, C, and D input paths.
    """
    # get the keys to the families subdictionary
    families_val = get_param_value(parameter_dict, ADD_FAMILIES)
    # remove any potential delimiters or malicious code
    families_list = re.split(r"\n| |,|;|&|>|<|\?",families_val)
    families_list = [family for family in families_list if family]
    # create the comma-separated (no spaces) string of the families
    families_str = ",".join(families_list)
    families_name = ADD_FAMILIES.nf_parameter_name
    
    # get the keys to the fraction subdictionary
    fraction_val = get_param_value(parameter_dict, FRACTION_FILTER)
    fraction_name = FRACTION_FILTER.nf_parameter_name

    # check that the values are both true-ish
    if fraction_val:
        return {families_name: families_str}, f"{fraction_name}={fraction_val}"
    
    return {families_name: families_str}, None


