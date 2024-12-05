import os
import re

from .gnt import EFIGNT
from ..const import *


class GNTSequenceIDLookup(EFIGNT):
    def do_analysis(self, params):
        """
        run the sequnce ID lookup "input-path" to the GNT
        1) parse the input parameters, 
        2) write necessary parameters to file, 
        3) pass the input parameters to the `gather_sequence_data()` method
           - this method daisy chains into the `run_gnt_pipeline()` method
             which runs the GNT nextflow code and creates the output objects
             # LIKELY TO CHANGE DEPENDENT ON GNT TOOL NF CODE

        :params params: input from the App's fields, stored as a dict. 
                        - "sequence_ids_input", string, any-seperator formatted
                          list of IDs to be gathered
                        - "sequence_database", string, control which database 
                          is used to gather gene neighborhood info. 
                        - "description", string, used to title the GND view
                        - "workspace_name", string, unique(?) name for the WS

        :return: results from the `gather_sequence_data()` method, which is 
                 actually the results from the `run_gnt_pipeline()` method, 
                 which is a dict filled with the GNDViewFile object's
                 reference information. Current form: 
                 - {'gnd_ref': '{GNDViewFile_UPA_string}', 'other_results':  []}
        """
        accession_file = os.path.join(self.shared_folder, 
                                      "pasted_accessions.txt")
        # regex substitute any non-alphanumeric character with an empty space
        # then split based on white space to get a list of IDs
        # ASSUMES: all sources of IDs follow an expected alphanumeric-only 
        # format
        accessions = re.sub(r'[^0-9a-zA-Z]+',
                            r' ',
                            params['sequence_ids']).split()
        # if the accessions list is empty, raise an error
        if not accessions:
            raise TypeError(f"User input for Sequence IDs is empty.")

        # currently unclear what format the GNT tool will expect, so write 
        # list out to file, one ID per line
        accessions_file_string = '\n'.join(accessions) + '\n'
        with open(accession_file, "w") as f:
            f.write(accessions_file_string)
        print(f"Wrote {len(accessions)} accession IDs to file")
        mapping = {
            "final_output_dir": self.shared_folder,
            "ids_file": accession_file,
            "nIDs": len(accessions),
            "sequence_database": params['sequence_database'],
            "description": params['description'],
            "gnt_input": 'SeqLookup'
        }
        
        return self.gather_sequence_data(mapping, params['workspace_name'])
