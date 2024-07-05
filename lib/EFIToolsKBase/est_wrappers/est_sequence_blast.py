from .est import EFIEST

class EFISequenceBLAST(EFIEST):
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
            "efi_config": "/EST/efi.config",
            "fasta_db": "/data/blastdb/combined.fasta",
            "efi_db": "/data/efi_db.sqlite",
            "blast_evalue": 1e-5,
            "import_mode": "blast",
            # TODO fill in parameters for single sequence BLAST import
        }
        return self.run_est_pipeline(mapping, params["workspace_name"])