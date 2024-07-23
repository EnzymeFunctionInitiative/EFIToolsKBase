import os

from .est import EFIEST
from ..const import *


class EFISequenceBLAST(EFIEST):
    def do_analysis(self, params):
        query_sequence = params["query_sequence"]
        query_sequence_path = os.path.join(self.shared_folder, "query_sequence.fasta")
        with open(query_sequence_path, "w") as f:
            f.write(query_sequence)
        mapping = {
            "final_output_dir": self.shared_folder,
            "duckdb_memory_limit": "64GB",
            "duckdb_threads": 1,
            "num_fasta_shards": 64,
            "num_accession_shards": 16,
            "num_blast_matches": params["blast_options"]["max_sequences_retrieved"],
            "multiplex": False,
            "job_id": 131,
            "efi_config": EFI_CONFIG_PATH,
            "fasta_db": "/data/blastdb/combined.fasta",
            "efi_db": EFI_DB_PATH,
            "blast_evalue": params["blast_options"]["e_value"],
            "sequence_version": "uniprot",
            "import_mode": "blast",
            "blast_query_file": query_sequence_path
        }
        return self.run_est_pipeline(mapping, params["workspace_name"])