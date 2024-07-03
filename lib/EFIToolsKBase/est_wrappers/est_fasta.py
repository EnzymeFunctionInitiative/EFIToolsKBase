from .est import EFIEST

class EFIFasta(EFIEST):
    def do_analysis(self, params):
        mapping = {
            "fasta_file": "/results/sequences.fasta",#params["fasta_sequences_file"],
            "output_dir": self.shared_folder,
            "duckdb_mem": "64GB",
            "duckdb_threads": 1,
            "fasta_shards": 1,
            "blast_matches": 250,
            "job_id": 0,
        }
        
        return self.run_est_pipeline(mapping, params["workspace_name"])