import os

from .est import EFIEST

class EFIFasta(EFIEST):
    def do_analysis(self, params):
        seq_obj = self.dfu.get_objects({"object_refs": [params["fasta_sequences_file"]]})["data"][0]
        sequences = seq_obj["sequences"]
        uploaded_fasta_file = os.path.join(self.shared_folder, "input_sequences.fasta")
        with open(uploaded_fasta_file, "w") as f:
            for record in sequences:
                id = record["id"]
                sequence = record["sequence"]
                f.writelines([f"{id}\n", f"{sequence}\n"])
        mapping = {
            "final_output_dir": self.shared_folder,
            "duckdb_memory_limit": "64GB",
            "duckdb_threads": 1,
            "num_fasta_shards": 64,
            "num_accession_shards": 16,
            "num_blast_matches": 250,
            "muliplex": False,
            "efi_config": "/EST/efi.config",
            "fasta_db": "/data/blastdb/combined.fasta",
            "efi_db": "/data/efi_db.sqlite",
            "import_mode": "FASTA",
            "exclude_fragments": True if params["fragment_option"] == 1 else False,
            "multiplex": False,
            "job_id": 131,

            "fasta_file": uploaded_fasta_file
        }
        return self.run_est_pipeline(mapping, params["workspace_name"])