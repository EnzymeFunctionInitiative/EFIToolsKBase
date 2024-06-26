
import os
import subprocess
import string


class NextflowRunner():
    def __init__(self, workflow_def, est_dir="/EST", config_name="kbase.config"):
        assert os.path.exists(est_dir)
        self.est_dir = est_dir
        self.workflow_def = os.path.join(est_dir, workflow_def)
        self.config_file = os.path.join(est_dir, "conf", config_name)
        self.params_file = ""
        self.run_command = ""
    
    def render_params_file(self, mapping, parameter_file):
        template_file = os.path.join(self.est_dir, "templates", parameter_file)
        os.makedirs(mapping["output_dir"], exist_ok=True)
        params_output = os.path.join(mapping["output_dir"], "params.yml")

        with open(template_file) as f:
            template = string.Template(f.read())
        with open(params_output, "w") as f:
            f.write(template.substitute(mapping))
        self.params_file = params_output

    def generate_run_command(self, stub=False):
        if self.params_file == "":
            raise ValueError("Must render params with `render_params_file()` before generating run command")
        cmd = [
                "nextflow",
                "-C",  f"{self.config_file}",
                "run", f"{self.workflow_def}",
                "-ansi-log", "false ",
                "-offline ",
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
        
