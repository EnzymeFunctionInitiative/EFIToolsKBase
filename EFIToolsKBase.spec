/*
A KBase module: EFIToolsKBase
*/

module EFIToolsKBase {

    /* @id handle */
    typedef string handle;

    /* 
	data object types to be registered
	registration happens else where
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
	string sequence_database;	/* currently unused */
    } initial_blast_options;

    typedef structure {
	string taxonomic_level;		/* currently unused */
	string filter_string;		/* currently unused */
    } taxonomy_filter_options;

    typedef structure {
	string families_to_add;				/* currently unused */
	string families_addition_cluster_id_format;	/* currently unused */
	int fraction;					/* currently unused */
    } protein_family_addition_options;

    typedef structure {
	string domain;			/* currently unused */
	string family_domain_bound;	/* currently unused */
	int region;			/* currently unused */
    } family_domain_boundary_options;

    typedef structure {
	string accession_ids;
	string accession_id_format; 	/* currently unused */
    } accession_id_input;

    typedef structure {
	string filter_parameters;
	float filter_value;
    } ssn_filter_options;

    typedef structure {
	handle ssn_data_object;
	int nb_size;
	float cooc_threshold;
    } gnt_inputs;


    /* 
	App input data structures
    */
    typedef structure {
	handle workspace_name;
	string query_sequence;
	string ssn_e_value;
	initial_blast_options blast_options;
	int fragment_option; 						 /* currently unused */
	taxonomy_filter_options taxonomy_filter_options;		 /* currently unused */
	protein_family_addition_options protein_family_addition_options; /* currently unused */
    } run_EFI_EST_Sequence_BLAST_input;

    typedef structure {
	handle workspace_name;
	string fasta_sequences_file; 					 /* really maps to a KBaseSequences.ProteinSequenceSet */
	string header_format;						 /* currently unused */
	int fragment_option; 						 /* currently unused */
	string family_filter;						 /* currently unused */
	taxonomy_filter_options taxonomy_filter_options;		 /* currently unused */
	protein_family_addition_options protein_family_addition_options; /* currently unused */
	family_domain_boundary_options family_domain_boundary_options;	 /* currently unused */
	string ssn_e_value;
    } run_EFI_EST_FASTA_input;

    typedef structure {
	handle workspace_name;
	accession_id_input accession_id_input;
	int fragment_option; 						 /* currently unused */
	string family_filter;						 /* currently unused */
	taxonomy_filter_options taxonomy_filter_options;		 /* currently unused */
	protein_family_addition_options protein_family_addition_options; /* currently unused */
	family_domain_boundary_options family_domain_boundary_options;	 /* currently unused */
	string ssn_e_value;
    } run_EFI_EST_Accession_IDs_input;

    typedef structure {
	handle workspace_name;
	protein_family_addition_options protein_family_addition_options;
	int fragment_option; 						 /* currently unused */
	taxonomy_filter_options taxonomy_filter_options;		 /* currently unused */
	family_domain_boundary_options family_domain_boundary_options;	 /* currently unused */
	string ssn_e_value; 						 /* should map to an int or float */
    } run_EFI_EST_Families_input;

    typedef structure {
	handle workspace_name;
	handle blast_edge_file; 	/* actually maps to a EFIToolsKBase.BlastEdgeFile data object */
	ssn_filter_options filter_options;
	int min_length; 		/* should map to an int */
	int max_length; 		/* should map to an int */
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
