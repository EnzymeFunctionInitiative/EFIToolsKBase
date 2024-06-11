/*
A KBase module: EFIToolsKBase
*/

module EFIToolsKBase {
    typedef structure {
        string report_name;
        string report_ref;
    } ReportResults;

    typedef structure {
        string report_name;
        string report_ref;
        string fasta_ref;
    } EFIFastaReportResults;

    /*
        This example function accepts any number of parameters and returns results in a KBaseReport
    */
    funcdef run_EFIToolsKBase(mapping<string,UnspecifiedObject> params) returns (ReportResults output) authentication required;

    funcdef run_EFI_EST_FASTA(mapping<string,UnspecifiedObject> params) returns (EFIFastaReportResults output) authentication required;


};
