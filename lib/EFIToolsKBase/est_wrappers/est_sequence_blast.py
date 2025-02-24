import os

from .est import EFIEST
from ..const import *


class EFISequenceBLAST(EFIEST):
    def do_analysis(self, params):
        """
        """
        # handle user-input sequence
        query_sequence = params["query_sequence"]
        query_sequence_path = os.path.join(self.shared_folder, "query_sequence.fasta")
        with open(query_sequence_path, "w") as f:
            f.write(query_sequence)
        # handle user-input BLAST search DB choice; choose from a dropdown menu
        # containing only "UniProt", "UniRef90", and "UniRef50"
        if params["blast_options"]["sequence_database"] == "UniProt":
            search_sequence_database = FASTA_DB_PATH
        ######################################################################
        # NOTE: update this once EST app enables this
        elif params["blast_options"]["sequence_database"] == "UniRef90":
            print("UniRef90 sequence database not currently available."
                    + f" Using default: {EFI_DB_PATH}")
            search_sequence_database = FASTA_DB_PATH
        elif params["blast_options"]["sequence_database"] == "UniRef50":
            print("UniRef50 sequence database not currently available."
                    + f" Using default: {EFI_DB_PATH}")
            search_sequence_database = FASTA_DB_PATH
        ######################################################################

        # create parameter dictionary
        mapping = {
            "final_output_dir": self.shared_folder,
            "duckdb_memory_limit": "64GB",
            "num_fasta_shards": 64,
            "num_accession_shards": 16,
            "multiplex": False,
            "efi_config": EFI_CONFIG_PATH,
            "fasta_db": FASTA_DB_PATH,
            "efi_db": EFI_DB_PATH,
            "num_blast_matches": 250,   # this should not exist
            "blast_evalue": f"1e-{params['ssn_e_value']}",
            "sequence_version": "uniprot",
            # parameters specifically for the sequence blast search step
            "import_mode": "blast",
            "blast_query_file": query_sequence_path,
            "import_blast_fasta_db": search_sequence_database,
            "search_evalue": f"1e-{params['blast_options']['e_value']}",
            "search_num_blast_matches": params["blast_options"]["max_sequences_retrieved"],
            # unused keys
            "job_id": 131,
            "duckdb_threads": 1,
            "families": "",
            "accession_file": "",
        }
        return self.run_est_pipeline(mapping, params["workspace_name"])
