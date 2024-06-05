import argparse
import string

def parse_args():
    parser = argparse.ArgumentParser(description="Render the DuckDB SQL template for alphabetizing IDs")
    parser.add_argument("--blast-output", type=str, required=True, help="Path to directory containing the BLAST output file")
    parser.add_argument(
        "--sql-template",
        type=str,
        default="../templates/allreduce-template.sql",
        help="Path to the template sql file for reduce operations",
    )
    parser.add_argument(
        "--sql-output-file",
        type=str,
        default="reduce.sql",
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
        help="The final output file the aggregated BLAST output should be written to. Will be Parquet.",
    )
    return parser.parse_args()

def render_sql_from_template(
    template_file: str,
    sql_output_file: str,
    mem_limit: str,
    duckdb_temp_dir: str,
    blast_output: str,
    prereduce_output_file: str,
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
        reduce_output_file
            Location to which the combined output (in Parquet format) should be written
    """
    mapping = {
        "mem_limit": mem_limit,
        "duckdb_temp_dir": duckdb_temp_dir,
        "transcoded_blast_output_glob": blast_output,
        "prereduce_output_file": prereduce_output_file,
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
            )