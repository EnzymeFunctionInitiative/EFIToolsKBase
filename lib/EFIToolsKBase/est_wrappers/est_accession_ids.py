import os
import re
import logging

from .est import EFIEST
from ..const import *


class EFIAccessionIDs(EFIEST):
    def do_analysis(self, params):
        # write the pasted accession ID list to a file; needed in a specific
        # file format for the EST backend code
        accession_file = self._prepare_accession_file(
            params["accession_id_input"]["accession_ids"]
        )
        
        # gather parameters
        logging.debug(f"User input parameters:\n{params}")
        nf_parameters = self.prepare_nf_parameters(params)

        # add the accession input parameters to the nf_parameters dict
        nf_parameters.update(
            {
                "import_mode": "accessions",
                "accessions_file": accession_file
            }
        )
        logging.debug(f"Nextflow parameter file contains:\n{nf_parameters}")

        # run the parent class' run_est_pipeline method with nf-ready parameter
        # dictionary
        return self.run_est_pipeline(nf_parameters, params["workspace_name"])

    def _prepare_accession_file(self, accession_string: str) -> str:
        """
        Handle user-input text and write to the required file format.
        
        EST/pipelines/est/import/get_sequence_ids.pl docs say that the file
        must have sequence IDs on a separate line; no additional delimiters
        are expected. This code assumes that the user does not follow the 
        suggested format.
        """
        # assume users did not input text in the desired format.
        accession_list = re.split("\n|\*|,|;", accession_string)
        # remove empty strings if present
        accession_list = [
            accession for accession in accession_list if accession
        ]
        # write cleaned and formatted accession_list to file
        accession_str = "\n".join(accession_list)
        accession_file = os.path.join(self.shared_folder, "pasted_accessions.txt")
        with open(accession_file, "w") as f:
            f.write(accession_str)
        logging.info(f"Wrote {len(accession_list)} accession IDs to file.")
        
        return accession_file

