import os
import re
import logging
from typing import Dict, Any

from .est import EFIEST, apply_family_addition
from ..const import *

IMPORT_MODE = ("import_mode", "fasta")

IMPORT_FASTA = KBaseMapping(
    "import_fasta_options",
    "protein_sequence_set_data_obj",
    "uploaded_fasta_file"
)
IMPORT_FASTA_DB_FMT = KBaseMapping(
    "import_fasta_options",
    "header_format",
    ""
)

class EFIFasta(EFIEST):
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
            get_param_value(parameter_dict, IMPORT_FASTA_DB_FMT)
        )
        # at this point, the nf_parameters contain the generic parameters in
        # const.DEFAULT_NF_PARAMETERS, all_by_all_blast parameters,
        # "final_output_dir", "sequence_version", "job_id", "fasta_db", and
        # "filter". The "filter" key maps to a list of strings or an empty list
        # if no taxonomy filters are being applied.

        # gather the Input ProteinSequenceSet data object's reference id from
        # ui input. Pass that reference id to the _prepare_query_file() method.
        fasta_file = self._prepare_query_file(
            get_param_value(parameter_dict, IMPORT_FASTA)
        )
        
        # push the input fasta parameters to the nf_parameters dict
        nf_parameters.update(
            {
                IMPORT_MODE[0]: IMPORT_MODE[1],
                IMPORT_FASTA.nf_parameter_name: fasta_file
            }
        )

        # check for family additions
        family_addn_params, frac_str = apply_family_addition(parameter_dict)
        if family_addn_params:
            nf_parameters.update(family_addn_params)
            nf_parameters["filter"].append(frac_str)

        # remove the filter parameter if it is an empty list
        if not nf_parameters.get("filter"):
            nf_parameters.pop("filter", None)

        return nf_parameters

    def _prepare_query_file(self, pss_data_obj_ref: str) -> str:
        """
        Handle user-input text and write to the required file format.

        This App requires handling of the ProteinSequenceSet data object, which
        is documented at https://appdev.kbase.us/legacy/spec/type/KBaseSequences.ProteinSequenceSet-2.0
        """
        # users upload or create a ProteinSequenceSet data object; that object
        # has a reference id that KBase Data File Utility uses to grab the
        # "data". Call dfu.get_objects() with the below dict returns a dict
        # with a "data" key that maps to a list. The zeroth element of that
        # list is the contents of the protein sequence set, itself stashed as a
        # dictionary.
        seq_obj = self.dfu.get_objects(
            {"object_refs": [pss_data_obj_ref]}
        )["data"][0]
        # get the sequences, which is a list of ProteinSequence dictionaries.
        # See documentation linked above.
        sequences = seq_obj["data"]["sequences"]
        # loop over the list of ProteinSequence dicts and write sequences to a
        # file.
        fasta_file = os.path.join(self.shared_folder, "input_sequences.fasta")
        seqs_written = 0
        with open(fasta_file, "w") as f:
            for record in sequences:
                f.write(f">{record['id']}\n{record['sequence']}\n")
                seqs_written += 1

        logging.info(f"Wrote {seqs_written} sequences")
        return fasta_file

