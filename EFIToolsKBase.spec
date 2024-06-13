/*
A KBase module: EFIToolsKBase
*/

module EFIToolsKBase {

    typedef structure {
        /*
            these are parallel arrays storing data about the number of sequences
            at each alignment score
        */
        list<int> alignment_scores; 
        list<int> alsc_count; 
        list<int> alsc_count_cumsum;
    } evaluetab;

    typedef structure {
        string shock_id;
        int edge_count;
        int unique_seq;
        float convergence_ratio;
        evaluetab evalues;
    } EdgeFileBLAST;


    typedef structure {
        string report_name;
        string report_ref;
    } ReportResults;

    typedef structure {
        string report_name;
        string report_ref;
        string fasta_ref;
        string edge_ref;
    } EFIFastaReportResults;

    /*
        This example function accepts any number of parameters and returns results in a KBaseReport
    */
    funcdef run_EFIToolsKBase(mapping<string,UnspecifiedObject> params) returns (ReportResults output) authentication required;

    funcdef run_EFI_EST_FASTA(mapping<string,UnspecifiedObject> params) returns (EFIFastaReportResults output) authentication required;


};
