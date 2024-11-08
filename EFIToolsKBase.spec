/*
A KBase module: EFIToolsKBase
*/

module EFIToolsKBase {

    /* @id handle */
    typedef string handle;

  
    typedef structure {
        handle edgefile_handle;
        handle fasta_handle;
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
        handle gnd_sql_handle;
    } GNDFile;
    
    typedef structure {
        string report_name;
        string report_ref;
    } ReportResults;

    typedef structure {
        string report_name;
        string report_ref;
        string edge_ref;
    } ESTReportResults;

    typedef structure {
        string report_name;
        string report_ref;
        string gnd_widget_ref; /* temp placeholder for some widget information */
    } GNDViewerResults;

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

    funcdef run_EFI_GNT_View_Saved_Diagrams(mapping<string, UnspecifiedObject> params) returns (GNDViewerResults output) authentication required;
};
