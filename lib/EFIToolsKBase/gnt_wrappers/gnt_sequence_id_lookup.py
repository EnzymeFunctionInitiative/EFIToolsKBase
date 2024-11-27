import os
import re

from .gnt import EFIGNT
from ..const import *


class EFISequenceIDs(EFIGNT):
    def do_analysis(self, params):
        print(params)
        accession_file = os.path.join(self.shared_folder, "pasted_accessions.txt")
        # regex substitute any non-alphanumeric character with an empty space
        # then split based on white space to get a list of IDs
        accessions = re.sub(r'[^0-9a-zA-Z]+',
                            r' ',
                            params["sequence_ids_input"]["sequence_ids"]).split()
        accessions_file_string = '\n'.join(accessions) + '\n'
        # currently unclear what format the GNT tool will expect, so 
        with open(accession_file, "w") as f:
            f.write(accessions_file_string)
        print(f"Wrote {len(accessions)} accession IDs to file")
        mapping = {
            "final_output_dir": self.shared_folder,
            "ids_file": accession_file
        }
        
        return self.run_gnt_pipeline(mapping, params["workspace_name"])
