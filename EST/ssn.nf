process import_data {
    input:
        val existing_blast_output
        val existing_fasta_file
    output:
        path '1.out.parquet', emit: blast_output
        path 'sequences.fa', emit: fasta
        path 'structfile', emit: struct_file
    """
    cp $existing_blast_output 1.out.parquet
    cp $existing_fasta_file sequences.fa
    """
}

process filter_blast {
    input:
        path blast_parquet
    output:
        path "2.out"
    """
    module load efidb/ip98
    module load efiest/devlocal
    module load DuckDB
    python ${params.est_dir}/ssn_prefilter/render_filter_blast_sql_template.py --blast-output $blast_parquet --filter-parameter ${params.filter_parameter} --filter-min-val ${params.filter_min_val} --min-length ${params.min_length} --max-length ${params.max_length} --sql-template ${params.est_dir}/templates/filterblast-template.sql --output-file 2.out --sql-output-file filterblast.sql
    duckdb < filterblast.sql
    """
}

process filter_fasta {
    input:
        path fasta
    output:
        path "filtered_sequences.fa"
    """

    """
}

process create_xgmml_100 {
    input:
        path filtered_blast
        path filtered_fasta
        path struct_file
    output:
        path "full_ssn.xgmml"
    """
    module load Perl
    perl ${params.est_dir}/xgmml_100_create.pl -blast=$filtered_blast -fasta $filtered_fasta -struct $struct_file -output full_ssn.xgmml  -title ${params.title} -maxfull ${params.maxfull}
    """
}

process create_xgmml_al {

}

process compute_stats {

}

workflow {
    // import data from EST run
    input_data = import_data(params.blast_parquet)

    // filter BLAST and fasta file
    filtered_blast = filter_blast(input_data.blast_output)
    filtered_fasta = filter_fasta(input_data.fasta)

    // create networks
    create_xgmml_100(filtered_blast, filtered_fasta, input_data.struct_file)
    create_xgmml_al()

    // compute stats
    compute_stats()
}