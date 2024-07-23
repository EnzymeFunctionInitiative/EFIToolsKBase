import os

from .est import EFIEST
from ..const import *


class EFIFasta(EFIEST):
    def do_analysis(self, params):
        seq_obj = self.dfu.get_objects({"object_refs": [params["fasta_sequences_file"]]})["data"][0]
        sequences = seq_obj["data"]["sequences"]
        uploaded_fasta_file = os.path.join(self.shared_folder, "input_sequences.fasta")
        seqs_written = 0
        with open(uploaded_fasta_file, "w") as f:
            for record in sequences:
                id = record["id"]
                sequence = record["sequence"]
                f.write(f">{id}")
                f.write("\n")
                f.write(sequence)
                f.write("\n")
                seqs_written += 1
        print(f"Wrote {seqs_written} sequences")
        # with open(uploaded_fasta_file) as f:
        #     print(f.readlines())
        mapping = {
            "final_output_dir": self.shared_folder,
            "duckdb_memory_limit": "64GB",
            "duckdb_threads": 1,
            "num_fasta_shards": 64,
            "num_accession_shards": 16,
            "num_blast_matches": 250,
            "muliplex": False,
            "efi_config": EFI_CONFIG_PATH,
            "fasta_db": "/data/blastdb/combined.fasta",
            "efi_db": EFI_DB_PATH,
            "import_mode": "fasta",
            "multiplex": False,
            "job_id": 131,
            "blast_evalue": f"1e-{params['ssn_e_value']}",
            "sequence_version": "uniprot",
            "uploaded_fasta_file": uploaded_fasta_file
        }
        return self.run_est_pipeline(mapping, params["workspace_name"])