import argparse
import string
import os

def parse_args():
    parser = argparse.ArgumentParser(description="Filter reduced BLAST output on specified parameter")
    parser.add_argument("--blast-output", type=str, required=True, help="Path to directory containing the reduced BLAST output file")
    parser.add_argument(
        "--sql-template",
        type=str,
        default="../templates/allreduce-template.sql",
        help="Path to the template sql file for reduce operations",
    )
    parser.add_argument(
        "--sql-output-file",
        type=str,
        default="filterblast.sql",
        help="Location to write the reduce SQL commands to",
    )
    parser.add_argument("--duckdb-memory-limit", type=str, default="4GB", help="Soft limit on DuckDB memory usage")
    parser.add_argument(
        "--duckdb-temp-dir",
        type=str,
        default="./duckdb",
        help="Location DuckDB should use for temporary files",
    )
    parser.add_argument(
        "--output-file",
        type=str,
        required=True,
        help="The final output file the filtered BLAST output should be written to. Will be tab-separated",
    )
    parser.add_argument(
        "--filter-parameter",
        type=str,
        required=True,
        choices=["pident", "bitscore", "alignment_score"],
        help="The parameter to filter on"
    )
    parser.add_argument(
        "--filter-min-val",
        type=float,
        required=True,
        help="The minimum value for the selected filter. Values below are not kept"
    )
    parser.add_argument(
        "--min-length",
        type=int,
        default=0,
        help="Minimum sequence length required to retain row"
    )
    parser.add_argument(
        "--max-length",
        type=int,
        default=0,
        help="Maximum sequence length allowed in retained rows"
    )

    args = parser.parse_args()

    fail = False
    if not os.path.exists(args.blast_output):
        print(f"BLAST output '{args.blast_output}' does not exist")
        fail = True
    if fail:
        exit(1)
    else:
        return args

def render_sql_from_template(
    template_file: str,
    sql_output_file: str,
    mem_limit: str,
    duckdb_temp_dir: str,
    blast_output: str,
    filtered_blast_output: str,
    filter_parameter: str,
    filter_min_val: float,
    min_seq_length: int,
    max_seq_length: int
):
    """
    Creates a .sql file for deduplication and merging using newly created
    parquet files

    This function uses the python stdlib
    :external+python:py:class:`string.Template` to fill in file paths and other
    options in a SQL file. The SQL file is executed with `DuckDB
    <https://duckdb.org/>`_.

    Parameters
    ----------
        template_file
            Path to the template sql file for reduce operations
        mem_limit
            Soft limit for DuckDB memory usage. In bytes by default but can use common suffixes such as `MB and `GB`
        duckdb_temp_dir
            Location where duckdb should place its on-disk cache. Folder will be created if it does not exist
        blast_output
            path to Parquet-encoded BLAST output file to combine (from :func:`csvs_to_parquets`)
    """
    mapping = {
        "mem_limit": mem_limit,
        "duckdb_temp_dir": duckdb_temp_dir,
        "blast_output": blast_output,
        "filter_parameter": filter_parameter,
        "min_val": filter_min_val,
        "min_length": min_seq_length,
        "max_length": max_seq_length,
        "filtered_blast_output": filtered_blast_output,
        "compression": "zstd",
    }
    with open(template_file) as f:
        template = string.Template(f.read())
        with open(sql_output_file, "w") as g:
            print(f"Saving template to '{sql_output_file}'")
            g.write(template.substitute(mapping))

if __name__ == "__main__":
    args = parse_args()
    render_sql_from_template(
                args.sql_template,
                args.sql_output_file,
                args.duckdb_memory_limit,
                args.duckdb_temp_dir,
                args.blast_output,
                args.output_file,
                args.filter_parameter,
                args.filter_min_val,
                args.min_length,
                args.max_length
            )