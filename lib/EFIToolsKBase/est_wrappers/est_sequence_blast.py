import os
import re
import logging
from typing import Dict, Any

from .est import EFIEST, apply_fragment_filter, apply_family_addition, FRAGMENT_FILTER
from ..const import *

IMPORT_MODE = ("import_mode", "blast")

IMPORT_SEQUENCE = KBaseMapping(
    "import_blast_sequence_options",
    "import_sequence",
    "blast_query_file"
)
IMPORT_BLAST_EVALUE = KBaseMapping(
    "import_blast_sequence_options",
    "import_blast_evalue",
    "import_blast_evalue"
)
IMPORT_BLAST_NMATCHES = KBaseMapping(
    "import_blast_sequence_options",
    "import_blast_num_matches",
    "import_blast_num_matches"
)
IMPORT_BLAST_DB_FMT = KBaseMapping(
    "import_blast_sequence_options",
    "sequence_database",
    ""
)

class EFISequenceBLAST(EFIEST):
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
        `parameter_dict`, specifically for an EST Sequence BLAST job.
        
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
            get_param_value(parameter_dict, IMPORT_BLAST_DB_FMT)
        )
        # at this point, the nf_parameters contain the generic parameters in
        # const.DEFAULT_NF_PARAMETERS, all_by_all_blast parameters,
        # "final_output_dir", "sequence_version", "job_id", "fasta_db", and
        # "filter". The "filter" key maps to a list of strings or an empty list
        # if no taxonomy filters are being applied.

        # handle user-input sequence
        query_sequence_file = self._prepare_query_file(
            get_param_value(parameter_dict, IMPORT_SEQUENCE)
        )

        # handle nf's params.import_blast_fasta_db
        sequence_version = nf_parameters["sequence_version"]
        import_blast_db_source = ("combined"
            if sequence_version.lower() == "uniprot"
            else sequence_version
        )
        fragment_filter_bool = bool(
            get_param_value(parameter_dict, FRAGMENT_FILTER)
        )
        import_blast_db = BlastDB.get_path(
            import_blast_db_source,
            fragment_filter_bool
        )
        
        # push the input blast parameters to the nf_parameters dict
        nf_parameters.update(
            {
                IMPORT_MODE[0]: IMPORT_MODE[1],
                IMPORT_SEQUENCE.nf_parameter_name: query_sequence_file,
                "import_blast_fasta_db": import_blast_db
            }
        )

        # handle Import Blast-all options
        nf_parameters.update(
            parse_import_blast_options(parameter_dict)
        )

        # check for the fragment fitler boolean
        frag_filter_str = apply_fragment_filter(parameter_dict)
        if frag_filter_str:
            nf_parameters["filter"].append(frag_filter_str)

        # check for family additions
        family_addn_params, frac_str = apply_family_addition(parameter_dict)
        if family_addn_params:
            nf_parameters.update(family_addn_params)
            nf_parameters["filter"].append(frac_str)

        # remove the filter parameter if it is an empty list
        if not nf_parameters.get("filter"):
            nf_parameters.pop("filter", None)

        return nf_parameters

    def _prepare_query_file(self, query_string: str) -> str:
        """
        Handle user-input text and write to the required file format.
        """
        # assume users did not input text in the desired format.
        query_lines_list = query_string.split("\n")
        # check if there is a header-line included
        if query_lines_list[0][0] == ">":
            header_line = query_lines_list[0]
            sequence_lines = "".join(query_lines_list[1:])
        else:
            header_line = ">INPUT SEQUENCE"
            sequence_lines = "".join(query_lines_list)

        # remove any non-sensical characters from the sequence
        sequence_lines_list = re.split(r",|;|&|>|<|\?", sequence_lines)
        sequence_str = "".join([line for line in sequence_lines_list if line])
        full_str = f"{header_line}\n{sequence_str}"
        
        # write the query sequence to file
        query_file = os.path.join(self.shared_folder, "query_sequence.fasta")
        with open(query_file,"w") as f:
            f.write(full_str)
        
        logging.info(
            f"Input sequence is\n{sequence_str}\nwith length ="
            + f" {len(sequence_str)}."
        )

        return query_file

def parse_import_blast_options(parameter_dict: Dict[str,str]) -> Dict[str,str]:
    """
    """
    # get the e-value value from the ui input
    import_blast_evalue_val = get_param_value(
        parameter_dict,
        IMPORT_BLAST_EVALUE
    )
    import_blast_evalue_name = IMPORT_BLAST_EVALUE.nf_parameter_name
    neg_log_e_value = 10**(-1*import_blast_evalue_val)

    # get the max number of hits value from the ui input
    import_blast_nhits_val = get_param_value(
        parameter_dict,
        IMPORT_BLAST_NMATCHES
    )
    # apply default value if user-provided value is either too high or less
    # than 0. 
    import_blast_nhits_val = 1000 if (
        import_blast_nhits_val > 10000 or import_blast_nhits_val < 1
    ) else import_blast_nhits_val
    import_blast_nhits_name = IMPORT_BLAST_NMATCHES.nf_parameter_name

    return {
        import_blast_evalue_name: neg_log_e_value,
        import_blast_nhits_name: import_blast_nhits_val
    }

