import os
import json
from ..nextflow import NextflowRunner
from ..utils import png_to_base64

def run_est_pipeline(pipeline, mapping, workspace_name, shared_folder, generate_report, wsClient):
    """
    pipeline: string
        filename of pipeline to run. ex: "est.nf", "ssn.nf"
    mapping: dict
        used to do string substitution on the yml parameter template
    workspace_name: string
        passed in from params dict in runner (params["workspace_name"])
    shared_folder: string
        passed in from params dict in runner (self.shared_folder)
    generate_report: function
        passed in from params dict in runner (self.generate_report)
    """
    flow = NextflowRunner(pipeline)
    flow.render_params_file(mapping, "est-params-template.yml")
    flow.generate_run_command()
    retcode, stdout, stderr = flow.execute()
    # if retcode != 0:
    #     raise ValueError(f"Failed to execute Nextflow pipeline\n{stderr}")
    print(shared_folder, os.listdir(shared_folder))
    pident_dataurl = png_to_base64(os.path.join(shared_folder, "pident_sm.png"))
    length_dataurl = png_to_base64(os.path.join(shared_folder, "length_sm.png"))
    edge_dataurl = png_to_base64(os.path.join(shared_folder, "edge_sm.png"))
    # edge_ref = save_file_to_workspace(params["workspace_name"], os.path.join(shared_folder, "1.out.parquet"), "All edges found by BLAST")
    # fasta_ref = save_sequences_to_workspace(os.path.join(shared_folder, "sequences.fasta"), params["workspace_name"])
    with open(os.path.join(shared_folder, "acc_counts.json")) as f:
        acc_data = json.load(f)
    report_data = {
        "pident_img": pident_dataurl, 
        "length_img": length_dataurl, 
        "edge_img": edge_dataurl, 
        "convergence_ratio": f"{acc_data['ConvergenceRatio']:.3f}",
        "edge_count": acc_data["EdgeCount"],
        "unique_seqs": acc_data["UniqueSeq"],
        "workspace_name": workspace_name
    }
    output = generate_report(report_data, ["edge_ref", "fasta_ref"])
    output["edge_ref"] = "edge_ref"#edge_ref["shock_id"]
    output["fasta_ref"] = "fasta_ref"#fasta_ref

    evalue_tab = {
        "alignment_scores": [],
        "alsc_count": [],
        "alsc_count_cumsum": []
    }

    edge_file_data = {
        "blobstore_id": "",
        "edge_count": 0,
        "unique_seq": 0,
        "convergence_ratio": 0.0,
        "evalues": evalue_tab
    }

    new_obj_info = wsClient.save_objects({'workspace': workspace_name,
                                                       'objects': [{'type': 'EFIToolsKBase.BlastEdgeFile',
                                                                    'data': edge_file_data,
                                                                    'name': "blast_edge_file",
                                                                    'meta': {}}]})[0]

    return output