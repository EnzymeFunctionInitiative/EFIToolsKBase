/*
A KBase module: EFIToolsKBase
*/

module EFIToolsKBase {

    /* @id handle */
    typedef string handle;

    /* 
	data object types to be registered
	registration happens elsewhere
    */
    typedef structure {
        handle edgefile_handle;
        handle fasta_handle;
        handle evalue_handle;
	handle seq_meta_handle;
        int edge_count;
        int unique_seq;
        float convergence_ratio;
    } BlastEdgeFile;

    typedef structure {
        handle ssn_xgmml_handle;
        int node_count;
        int edge_count;
    } SequenceSimilarityNetwork;
   
    typedef structure {
        handle ssn_xgmml_handle;
        handle structfile_handle;
    } SSNCreationResult;           
    
    typedef structure {
        handle gnd_view_file_handle;
        string view_title;
    } GNDViewFile;

    /* 
	App output data structures
    */
    typedef structure {
        string report_name;
        string report_ref;
    } ReportResults;

    typedef structure {
        string report_name;
        string report_ref;
        string edge_ref;
    } ESTReportResults;

    /* temp output design */
    typedef structure {
	string gnd_ref;
	string report_name;
	handle report_ref;
    } GNDViewFile_mapping;


    /* 
	data structure for the parameter groups defined in the Apps' UI spec files 
    */
    typedef structure {
	string e_value;
	string max_sequences_retrieved;
	string sequence_database;	/* unused */
    } initial_blast_options;

    typedef structure {
	string taxonomic_level;		/* unused */
	string taxon_filter_string;	/* unused */
    } taxonomy_filter_options;

    typedef structure {
	string families;
	string families_id_format;
    } families_input_options;

    typedef structure {
        int fraction;
    } protein_family_size_option;

    typedef structure {
	string families;
	int fraction;
    } protein_family_addition_options;

    typedef structure {
	string domain;
	string domain_family;
	int region;
    } family_domain_boundary_options;

    typedef structure {
	string domain;
	int region;
    } domain_boundary_options;

    typedef structure {
	string accession_ids;
	string accession_id_format;
    } accession_id_input;

    typedef structure {
	string family_filter;
    } filter_by_family_option;

    typedef structure {
	int exclude_fragments;
    } fragment_option;

    typedef structure {
	string filter_parameter;
	float filter_value;
    } ssn_filter_options;

    typedef structure {
	handle ssn_data_object;
	int nb_size;
	float cooc_threshold;
    } gnt_inputs;

    typedef structure {
	int blast_e_value;
	int blast_num_matches;
    } all_by_all_blast_options;

    typedef structure {
	string import_sequence;
	int import_blast_evalue;
	int import_blast_num_matches;
	string sequence_database;
    } import_blast_sequence_options;

    typedef structure {
	string protein_sequence_set_data_obj;
	string header_format;
    } import_fasta_options;

    /* 
	App input data structures
    */
    typedef structure {
	handle workspace_name;
	string est_object_name;
	import_blast_sequence_options import_blast_sequence_options;
	fragment_option fragment_option;
	protein_family_addition_options protein_family_addition_options;
	all_by_all_blast_options all_by_all_blast_options;
	taxonomy_filter_options taxonomy_filter_options;		 /* unused */
    } run_EFI_EST_Sequence_BLAST_input;

    typedef structure {
	handle workspace_name;
	string est_object_name;
	import_fasta_options import_fasta_options;
	protein_family_addition_options protein_family_addition_options;
	all_by_all_blast_options all_by_all_blast_options;
	taxonomy_filter_options taxonomy_filter_options;		 /* unused */
    } run_EFI_EST_FASTA_input;

    typedef structure {
	handle workspace_name;
	string est_object_name;
	accession_id_input accession_id_input;
	family_domain_boundary_options family_domain_boundary_options;
	fragment_option fragment_option;
	filter_by_family_option filter_by_family;
	protein_family_addition_options protein_family_addition_options;
	all_by_all_blast_options all_by_all_blast_options;
	taxonomy_filter_options taxonomy_filter_options;	/* unused */
    } run_EFI_EST_Accession_IDs_input;

    typedef structure {
	handle workspace_name;
	string est_object_name;
	families_input_options protein_family_addition_options;
	fragment_option fragment_option;
	protein_family_size_option protein_family_size_option;
	domain_boundary_options family_domain_boundary_options;
	all_by_all_blast_options all_by_all_blast_options;
	taxonomy_filter_options taxonomy_filter_options;	/* unused */
    } run_EFI_EST_Families_input;

    typedef structure {
	handle workspace_name;
	handle blast_edge_file_ref;
	ssn_filter_options filter_options;
	int min_length;
	int max_length;
	str ssn_object_name;
    } run_EFI_EST_SSN_Creation_input;

    typedef structure {
	handle workspace_name;
	string ssn_file;		/* actually maps to a EFIToolsKBase.SequenceSimilarityNetwork data object */
    } run_EFI_SSN_Utils_Color_SSN_input;

    typedef structure {
	handle workspace_name;
	gnt_inputs gnt_submission;
	string gnd_object_name;
    } run_EFI_GNT_GNT_Submission_input;


    /*
        This example function accepts any number of parameters and returns results associated with the KBaseReport object
    */
    funcdef run_EFIToolsKBase(mapping<string,UnspecifiedObject> params) returns (ReportResults output) authentication required;

    
    /*
        Actual funcdef lines calling their designed input and output objects
    */
    funcdef run_EFI_EST_Sequence_BLAST(run_EFI_EST_Sequence_BLAST_input params) returns (ESTReportResults output) authentication required;
    
    funcdef run_EFI_EST_FASTA(run_EFI_EST_FASTA_input params) returns (ESTReportResults output) authentication required;
    
    funcdef run_EFI_EST_Families(run_EFI_EST_Families_input params) returns (ESTReportResults output) authentication required;
    
    funcdef run_EFI_EST_Accession_IDs(run_EFI_EST_Accession_IDs_input params) returns (ESTReportResults output) authentication required;

    funcdef run_EFI_EST_SSN_Creation(run_EFI_EST_SSN_Creation_input params) returns (ReportResults output) authentication required;

    funcdef run_EFI_SSN_Utils_Color_SSN(run_EFI_SSN_Utils_Color_SSN_input params) returns (ReportResults output) authentication required;

    funcdef run_EFI_GNT_GNT_Submission(run_EFI_GNT_GNT_Submission_input params) returns (GNDViewFile_mapping output) authentication required;
};
