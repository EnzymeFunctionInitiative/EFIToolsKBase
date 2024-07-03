
import os
import json
import subprocess

class NextflowRunner():
    def __init__(self, workflow_def, est_dir="/EST", config_name="kbase.config"):
        assert os.path.exists(est_dir)
        self.est_dir = est_dir
        self.workflow_def = os.path.join(est_dir, workflow_def)
        self.config_file = os.path.join(est_dir, "conf", config_name)
        self.params_file = ""
        self.run_command = ""
    
    def write_params_file(self, mapping):
        os.makedirs(mapping["final_output_dir"], exist_ok=True)
        params_output = os.path.join(mapping["final_output_dir"], "params.yml")

        with open(params_output, "w") as f:
            json.dump(mapping, f, indent=4)
        self.params_file = params_output

    def generate_run_command(self, stub=False):
        if self.params_file == "":
            raise ValueError("Must render params with `write_params_file()` before generating run command")
        cmd = [
                "nextflow",
                "-C",  f"{self.config_file}",
                "run", f"{self.workflow_def}",
                "-ansi-log", "false",
                "-offline",
                "-params-file", f"{self.params_file}"
        ]
        if stub:
            cmd.append("-stub")
        self.run_command = cmd

    def execute(self):
        if self.run_command == "":
            raise ValueError("Must call `generate_run_command()` before executing")
        nf_env = os.environ.copy()
        ran = subprocess.run(self.run_command, text=True, env=nf_env)
        return ran.returncode, ran.stdout, ran.stderr
        
