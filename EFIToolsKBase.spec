/*
A KBase module: EFIToolsKBase
*/

module EFIToolsKBase {

    /* @id handle */
    typedef string handle;

    /* 
	data object types to be registered 
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
	data objects to guide development only 
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

    /* missing filter by taxonomy options */
    typedef structure {
	string query_sequence;
	string e_value; 		/* should map to an int or float */
	string max_sequences_retrieved; /* should map to an int */
	string sequence_database; 	/* currently unused */
	int fragment_option; 		/* currently unused */
	string families_to_add; 	/* currently unused */
	string families_addition_cluster_id_format;	/* currently unused */
	int fraction;			/* currently unused */
	string ssn_e_value; 		/* should map to an int or float */
    } run_EFI_EST_Sequence_BLAST_input;

    typedef structure {
	string fasta_sequence_file; 	/* really maps to a KBaseSequences.ProteinSequenceSet */
	string header_format;		/* currently unused */
	int fragment_option; 		/* currently unused */
	string family_filter; 		/* currently unused */
	string taxonomic_level; 	/* currently unused */
	string filter_string; 		/* currently unused */
	string families_to_add; 	/* currently unused */
	string families_addition_cluster_id_format;	/* currently unused */
	int fraction;			/* currently unused */
	int domain;			/* currently unused */
	string family_domain_bound; 	/* currently unused, should map to a bool? */
	string region; 			/* currently unused */
	string ssn_e_value; 		/* should map to an int or float */
    } run_EFI_EST_FASTA_input;

    typedef structure {
	string accession_ids;
	string accession_id_format; 	/* currently unused */
	int fragment_option; 		/* currently unused */
	string family_filter; 		/* currently unused */
	string taxonomic_level; 	/* currently unused */
	string filter_string; 		/* currently unused */
	string families_to_add; 	/* currently unused */
	string families_addition_cluster_id_format;	/* currently unused */
	int fraction;			/* currently unused */
	int domain;			/* currently unused */
	string family_domain_bound; 	/* currently unused, should map to a bool? */
	string region; 			/* currently unused */
	string ssn_e_value; 		/* should map to an int or float */
    } run_EFI_EST_Accession_IDs_input;

    typedef structure {
	string families_to_add;
	families_addition_cluster_id_format; /* currently unused */
	int fragment_option; 		/* currently unused */
	string taxonomic_level; 	/* currently unused */
	string filter_string; 		/* currently unused */
	int fraction;			/* currently unused */
	int domain;			/* currently unused */
	string region; 			/* currently unused */
	string ssn_e_value; 		/* should map to an int or float */
    } run_EFI_EST_Families_input;

    typedef structure {
	string blast_edge_file; 	/* actually maps to a EFIToolsKBase.BlastEdgeFile data object */
	string filter_parameter;
	string filter_value; 		/* should map to an int or float */
	string min_length; 		/* should map to an int */
	string max_length; 		/* should map to an int */
    } run_EFI_EST_SSN_Creation_input;

    typedef structure {
	string ssn_file;		/* actually maps to a EFIToolsKBase.SequenceSimilarityNetwork data object */
    } run_EFI_SSN_Utils_Color_SSN_input;

    typedef structure {
	string ssn_data_object;
	string neighborhood_size;	/* not actually used? */
	string percentage_lower_limit;	/* not actually used? */
    } run_EFI_GNT_GNT_Submission_input;

    /* temp object design */
    typedef structure {
	string gnd_obj_ref;
	string gnd_title;
    } GNDViewFile_mapping;


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
