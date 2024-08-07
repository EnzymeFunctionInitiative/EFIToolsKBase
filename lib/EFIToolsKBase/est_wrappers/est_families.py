from .est import EFIEST
from ..const import *


class EFIFamilies(EFIEST):
    def do_analysis(self, params):
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
            "exclude_fragments": True if params["fragment_option"] == 1 else False,
            "blast_evalue": f"1e-{params['ssn_e_value']}",
            "sequence_version": "uniprot",
            "import_mode": "family",
            "families": params["protein_family_addition_options"]["families_to_add"],
        }
        return self.run_est_pipeline(mapping, params["workspace_name"])