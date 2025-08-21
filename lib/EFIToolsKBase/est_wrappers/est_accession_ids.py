import os
import re
import logging

from .est import EFIEST, fragment_filter, taxonomy_filter, family_filter, domain_filter, family_addition
from ..const import *

IMPORT_MODE = ("import_mode", "accessions")

# create the accession id dictionary mapping objects
accession_ids_keys = dict_keys(
    "accession_id_input",
    "accession_ids",
    ""
)
accession_fmt_keys = dict_keys(
    "accession_id_input",
    "accession_id_format",
    ""
)

# only used in Option D (AccessionIds)
FAMILY_FILTER = dict_keys("filter_by_family", "family_filter", "family")

# create the domain filtering/truncating dictionary mapping objects
DOMAIN_FILTER = dict_keys(
    "family_domain_boundary_options",
    "domain",
    ""  # does not get written in the param file
)
DOMAIN_FAMILY = dict_keys(
    "family_domain_boundary_options",
    "domain_family",
    "domain_family"
)
DOMAIN_REGION = dict_keys(
    "family_domain_boundary_options",
    "region",
    "domain"
)

class EFIAccessionIDs(EFIEST):
    def do_analysis(self, params):
        # log user input from the UI 
        logging.debug(f"User input parameters:\n{params}")
        
        # do validation

        # correctly map and gather all nextflow parameters
        nf_parameters = self.prepare_nf_parameters(params)

        # log the nextflow parameters
        logging.debug(f"Nextflow parameter file contains:\n{nf_parameters}")

        # run the parent class' run_est_pipeline method with nf-ready parameter
        # dictionary
        return self.run_est_pipeline(
            nf_parameters,
            params["workspace_name"], 
            params["est_object_name"]
        )

    def prepare_nf_parameters(
            self,
            parameter_dict: Dict[str, str],
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
        fmt_dict_key = accession_fmt_keys.dict_key
        fmt_subdict_key = accession_fmt_keys.subdict_key
        nf_parameters = super().prepare_nf_parameters(
            parameter_dict,
            parameter_dict[fmt_dict_key][fmt_subdict_key]
        )
        # at this point, the nf_parameters contain the generic parameters in
        # const.DEFAULT_NF_PARAMETERS, all_by_all_blast parameters, 
        # "final_output_dir", "sequence_version", "job_id", "fasta_db", and
        # "filter". The "filter" key maps to a list of strings or an empty list
        # if no taxonomy filters are being applied.

        # write the pasted accession ID list to a file; needed in a specific
        # file format for the EST backend code
        ids_dict_key = accession_ids_keys.dict_key
        ids_subdict_key = accession_ids_keys.subdict_key
        accessions_file = self._prepare_accessions_file(
            parameter_dict[ids_dict_key][ids_subdict_key]
        )
        
        # add the accession input parameters to the nf_parameters dict
        nf_parameters.update(
            {
                IMPORT_MODE[0]: IMPORT_MODE[1],
                "accessions_file": accessions_file
            }
        )
      
        # check for the fragment fitler boolean
        frag_filter_str = fragment_filter(parameter_dict)
        if frag_filter_str:
            nf_parameter["filter"].append(frag_filter_str)

        # check the family filter
        fam_filter_str = family_filter(parameter_dict)
        if fam_filter_str:
            nf_parameter["filter"].append(fam_filter_str)

        # check for domain truncation
        domain_params = domain_options(parameter_dict)
        if domain_params:
            nf_parameter.update(domain_params)

        # check for family additions
        family_addn_params = family_addition(parameter_dict)
        if family_addn_params:
            nf_parameter.update(family_addn_params)

        # remove the filter parameter if it is an empty list
        if not nf_parameter.get("filter"):
            nf_parameter.pop("filter", None)

        return nf_parameter


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
        accession_list = re.split("\n| |,|;|&|>|<|?", accession_string)
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

def family_filter(parameter_dict: Dict[str, str]) -> str:
    """
    Given the appropriate input dictionary, map KBase App UI inputs to relevant
    nextflow est.nf input parameters. Specific for the family filter and only
    called by D input path. 
    """
    dict_key = FAMILY_FILTER.dict_key
    subdict_key = FAMILY_FILTER.subdict_key
    name = FAMILY_FILTER.nf_parameter_name
    if (
            parameter_dict.get(dict_key) and 
            parameter_dict[dict_key].get(subdict_key)
    ):
        val = parameter_dict[dict_key].get(subdict_key)
        return f"{name}={val}"

    return ""

def domain_options(parameter_dict: Dict[str, str]) -> Dict[str,str]:
    """
    Given the appropriate input dictionary, map KBase App UI inputs to relevant
    nextflow est.nf input parameters. Specific for the domain filter/truncation
    and only called by D input path (in this fashion).
    """
    # get and check the domain boolean;
    dict_key = DOMAIN_FILTER.dict_key
    subdict_key = DOMAIN_FILTER.subdict_key
    if (
        parameter_dict.get(dict_key) and
        parameter_dict[dict_key].get(subdict_key)
    ):
        #  if both are true, then a domain has been specified
        fam_dict_key = DOMAIN_FAMILY.dict_key
        fam_subdict_key = DOMAIN_FAMILY.subdict_key
        fam_name = DOMAIN_FAMILY.nf_parameter_name
        fam_value = parameter_dict[fam_dict_key].get(fam_subdict_key)
        # validate that only a single family is entered by grabbing the first
        # word in the string.
        fam_value = re.split("\n| |,|;",fam_value.strip())[0]

        # region values are from a drop down menu
        region_dict_key = DOMAIN_REGION.dict_key
        region_subdict_key = DOMAIN_REGION.subdict_key
        region_name = DOMAIN_REGION.nf_parameter_name
        region_value = parameter_dict[region_dict_key].get(region_subdict_key)
        
        if fam_value and region_value: 
            return {fam_name: fam_value, region_name: region_value}
    
    return {}
    

