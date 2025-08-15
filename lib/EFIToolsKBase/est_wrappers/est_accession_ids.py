import os

from .est import EFIEST
from ..const import *


class EFIAccessionIDs(EFIEST):
    def do_analysis(self, params):
        print(params)
        accession_file = os.path.join(self.shared_folder, "pasted_accessions.txt")
        accessions = params["accession_id_input"]["accession_ids"].splitlines(keepends=True)
        with open(accession_file, "w") as f:
            f.writelines(accessions)
        print(f"Wrote {len(accessions)} accession IDs to file")
        mapping = {
            "final_output_dir": self.shared_folder,
            "duckdb_memory_limit": "64GB",
            "duckdb_threads": 1,
            "num_fasta_shards": 64,
            "num_accession_shards": 16,
            "num_blast_matches": 250,
            "multiplex": False,
            "job_id": 131,
            "efi_config": EFI_CONFIG_PATH,
            "fasta_db": "/data/blastdb/combined.fasta",
            "efi_db": EFI_DB_PATH,
            "blast_evalue": f"1e-{params['ssn_e_value']}",
            "sequence_version": "uniprot",
            "import_mode": "accessions",
            "accessions_file": accession_file
        }
        return self.run_est_pipeline(mapping, params["workspace_name"])