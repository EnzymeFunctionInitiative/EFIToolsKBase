/*
A KBase module: EFIToolsKBase
*/

module EFIToolsKBase {

    /* @id handle */
    typedef string handle;

    /* 
    Data object type containing files and results from the EST apps
    */
    typedef structure {
        handle edgefile_handle;
        handle fasta_handle;
        int edge_count;
        int unique_seq;
        float convergence_ratio;
    } BlastEdgeFile;
    
    /* 
    Data object type containing SSN xgmml file and results from the SSN Utility apps
    */
    typedef structure {
        handle ssn_xgmml_handle;
        int node_count;
        int edge_count;
    } SequenceSimilarityNetwork;
    
    /*
    Results objects that map to the reports only? 
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
 
    /*
        This example function accepts any number of parameters and returns results in a KBaseReport
    */
    funcdef run_EFIToolsKBase(mapping<string,UnspecifiedObject> params) returns (ReportResults output) authentication required;

    funcdef run_EFI_EST_Sequence_BLAST(mapping<string,UnspecifiedObject> params) returns (ESTReportResults output) authentication required;
    
    funcdef run_EFI_EST_FASTA(mapping<string,UnspecifiedObject> params) returns (ESTReportResults output) authentication required;
    
    funcdef run_EFI_EST_Families(mapping<string,UnspecifiedObject> params) returns (ESTReportResults output) authentication required;
    
    funcdef run_EFI_EST_Accession_IDs(mapping<string,UnspecifiedObject> params) returns (ESTReportResults output) authentication required;

    funcdef run_EFI_EST_SSN_Creation(mapping<string, UnspecifiedObject> params) returns (ReportResults output) authentication required;

    funcdef run_EFI_SSN_Utils_Color_SSN(mapping<string, UnspecifiedObject> params) returns (ReportResults output) authentication required;

    /* 
    Data object type that contains the sqlite file to be viewed with the GND 
    Viewer 
    */
    typedef structure {
        handle gnd_view_file_handle;
    } GNDViewFile;
   
    /* 
    Strong typing control of input parameters for the 
    run_EFI_GNT_GND_Sequence_ID_Lookup code 
    */
    typedef structure {
        string sequence_ids;
        string sequence_database;
        string description;
        string workspace_name;
    } GNTSeqLookupParams;

    /* 
    declaring input and output objects for the run_EFI_GNT_GND_Sequence_ID_Lookup method
    */ 
    funcdef run_EFI_GNT_GND_Sequence_ID_Lookup(GNTSeqLookupParams params) 
	    returns (GNDViewFile output) authentication required;

};
