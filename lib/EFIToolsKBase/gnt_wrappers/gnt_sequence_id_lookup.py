import os
import re

from .gnt import EFIGNT
from ..const import *


class GNTSequenceIDLookup(EFIGNT):
    def do_analysis(self, params):
        """
        run the sequnce ID lookup input path to the GNT
        1) parse the input parameters, 
        2) write necessary parameters to file, 
        3) pass the input parameters to the `gather_sequence_data()` method
           - this method daisy chains into the `run_gnt_pipeline()` method
             which runs the GNT nextflow code and creates the output objects

        TODO: DESCRIBE THE NECESSARY KEY:VALUE PAIRS
        :params params: dict, 
        :params self: this object, important attributes used here and later on:
                      - 

        :return: results from the `gather_sequence_data()` method, which is 
                 actually the results from the `run_gnt_pipeline()` method, 
                 which is actually ... ...
        """
        print(params)
        accession_file = os.path.join(self.shared_folder, "pasted_accessions.txt")
        # regex substitute any non-alphanumeric character with an empty space
        # then split based on white space to get a list of IDs
        accessions = re.sub(r'[^0-9a-zA-Z]+',
                            r' ',
                            params["sequence_ids_input"]["sequence_ids"]).split()
        
        # currently unclear what format the GNT tool will expect, so write 
        # list out to file, one ID per line
        accessions_file_string = '\n'.join(accessions) + '\n'
        with open(accession_file, "w") as f:
            f.write(accessions_file_string)
        print(f"Wrote {len(accessions)} accession IDs to file")
        mapping = {
            "final_output_dir": self.shared_folder,
            "ids_file": accession_file,
            "sequence_database": params["sequence_database"],
            "gnt_input": 'SeqLookup'    # use a dict item to signify which input method was used
        }
        
        return self.gather_sequence_data(mapping, params["workspace_name"])
