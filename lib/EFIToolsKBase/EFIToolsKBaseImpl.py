# -*- coding: utf-8 -*-
#BEGIN_HEADER
import logging
import os

from installed_clients.KBaseReportClient import KBaseReport
from installed_clients.ReadsUtilsClient import ReadsUtils
from installed_clients.DataFileUtilClient import DataFileUtil
from installed_clients.AssemblyUtilClient import AssemblyUtil
from installed_clients.WorkspaceClient import Workspace

from .est_wrappers.est_sequence_blast import EFISequenceBLAST
from .est_wrappers.est_families import EFIFamilies
from .est_wrappers.est_fasta import EFIFasta
from .est_wrappers.est_accession_ids import EFIAccessionIDs
from .est_wrappers.ssn_creation import SSNCreation

from .ssnutil_wrappers.colorssn import ColorSSN

from base import Core

#END_HEADER


class EFIToolsKBase:
    '''
    Module Name:
    EFIToolsKBase

    Module Description:
    A KBase module: EFIToolsKBase
    '''

    ######## WARNING FOR GEVENT USERS ####### noqa
    # Since asynchronous IO can lead to methods - even the same method -
    # interrupting each other, you must be *very* careful when using global
    # state. A method could easily clobber the state set by another while
    # the latter method is running.
    ######################################### noqa
    VERSION = "0.0.1"
    GIT_URL = "git@github.com:EnzymeFunctionInitiative/EFIToolsKBase.git"
    GIT_COMMIT_HASH = "8de270df255ab86b92853ecab4a395278c054367"

    #BEGIN_CLASS_HEADER
    #END_CLASS_HEADER

    # config contains contents of config file in a hash or None if it couldn't
    # be found
    def __init__(self, config):
        #BEGIN_CONSTRUCTOR
        self.callback_url = os.environ['SDK_CALLBACK_URL']
        self.shared_folder = config['scratch']
        logging.basicConfig(format='%(created)s %(levelname)s: %(message)s',
                            level=logging.INFO)
        os.environ["JAVA_HOME"] = "/root/.sdkman/candidates/java/current"
        self.wsc = Workspace(self.callback_url)
        self.config = dict(
            callback_url=self.callback_url,
            shared_folder=self.shared_folder,
            clients=dict(
                KBaseReport=KBaseReport,
                ReadsUtils=ReadsUtils,
                DataFileUtil=DataFileUtil,
                AssemblyUtil=AssemblyUtil,
                Workspace=Workspace
            ),
        )
        #END_CONSTRUCTOR
        pass


    def run_EFIToolsKBase(self, ctx, params):
        """
        This example function accepts any number of parameters and returns results in a KBaseReport
        :param params: instance of mapping from String to unspecified object
        :returns: instance of type "ReportResults" -> structure: parameter
           "report_name" of String, parameter "report_ref" of String
        """
        # ctx is the context object
        # return variables are: output
        #BEGIN run_EFIToolsKBase
        #END run_EFIToolsKBase

        # At some point might do deeper type checking...
        if not isinstance(output, dict):
            raise ValueError('Method run_EFIToolsKBase return value ' +
                             'output is not type dict as required.')
        # return the results
        return [output]

    def run_EFI_EST_Sequence_BLAST(self, ctx, params):
        """
        :param params: instance of mapping from String to unspecified object
        :returns: instance of type "ESTReportResults" -> structure: parameter
           "report_name" of String, parameter "report_ref" of String,
           parameter "edge_ref" of String
        """
        # ctx is the context object
        # return variables are: output
        #BEGIN run_EFI_EST_Sequence_BLAST
        efi = EFISequenceBLAST(ctx, config=self.config)
        output = efi.do_analysis(params)

        #END run_EFI_EST_Sequence_BLAST

        # At some point might do deeper type checking...
        if not isinstance(output, dict):
            raise ValueError('Method run_EFI_EST_Sequence_BLAST return value ' +
                             'output is not type dict as required.')
        # return the results
        return [output]

    def run_EFI_EST_FASTA(self, ctx, params):
        """
        :param params: instance of mapping from String to unspecified object
        :returns: instance of type "ESTReportResults" -> structure: parameter
           "report_name" of String, parameter "report_ref" of String,
           parameter "edge_ref" of String
        """
        # ctx is the context object
        # return variables are: output
        #BEGIN run_EFI_EST_FASTA
        efi = EFIFasta(ctx, config=self.config)
        output = efi.do_analysis(params)
        
        #END run_EFI_EST_FASTA

        # At some point might do deeper type checking...
        if not isinstance(output, dict):
            raise ValueError('Method run_EFI_EST_FASTA return value ' +
                             'output is not type dict as required.')
        # return the results
        return [output]

    def run_EFI_EST_Families(self, ctx, params):
        """
        :param params: instance of mapping from String to unspecified object
        :returns: instance of type "ESTReportResults" -> structure: parameter
           "report_name" of String, parameter "report_ref" of String,
           parameter "edge_ref" of String
        """
        # ctx is the context object
        # return variables are: output
        #BEGIN run_EFI_EST_Families
        efi = EFIFamilies(ctx, config=self.config)
        logging.info(params)
        output = efi.do_analysis(params)
        #END run_EFI_EST_Families

        # At some point might do deeper type checking...
        if not isinstance(output, dict):
            raise ValueError('Method run_EFI_EST_Families return value ' +
                             'output is not type dict as required.')
        # return the results
        return [output]

    def run_EFI_EST_Accession_IDs(self, ctx, params):
        """
        :param params: instance of mapping from String to unspecified object
        :returns: instance of type "ESTReportResults" -> structure: parameter
           "report_name" of String, parameter "report_ref" of String,
           parameter "edge_ref" of String
        """
        # ctx is the context object
        # return variables are: output
        #BEGIN run_EFI_EST_Accession_IDs
        efi = EFIAccessionIDs(ctx, config=self.config)
        output = efi.do_analysis(params)

        #END run_EFI_EST_Accession_IDs

        # At some point might do deeper type checking...
        if not isinstance(output, dict):
            raise ValueError('Method run_EFI_EST_Accession_IDs return value ' +
                             'output is not type dict as required.')
        # return the results
        return [output]

    def run_EFI_EST_SSN_Creation(self, ctx, params):
        """
        :param params: instance of mapping from String to unspecified object
        :returns: instance of type "ReportResults" -> structure: parameter
           "report_name" of String, parameter "report_ref" of String
        """
        # ctx is the context object
        # return variables are: output
        #BEGIN run_EFI_EST_SSN_Creation
        config = dict(
            callback_url=self.callback_url,
            shared_folder=self.shared_folder,
            clients=dict(
                KBaseReport=KBaseReport,
                DataFileUtil=DataFileUtil
            ),
        )
        ssnc = SSNCreation(ctx, config=config)
        logging.info(params)
        output = ssnc.do_analysis(params)
        #END run_EFI_EST_SSN_Creation

        # At some point might do deeper type checking...
        if not isinstance(output, dict):
            raise ValueError('Method run_EFI_EST_SSN_Creation return value ' +
                             'output is not type dict as required.')
        # return the results
        return [output]

    def run_EFI_SSN_Utils_Color_SSN(self, ctx, params):
        """
        :param params: instance of mapping from String to unspecified object
        :returns: instance of type "ReportResults" -> structure: parameter
           "report_name" of String, parameter "report_ref" of String
        """
        # ctx is the context object
        # return variables are: output
        #BEGIN run_EFI_SSN_Utils_Color_SSN
        config = dict(
            callback_url=self.callback_url,
            shared_folder=self.shared_folder,
            clients=dict(
                KBaseReport=KBaseReport,
                DataFileUtil=DataFileUtil
            ),
        )
        cssn = ColorSSN(ctx, config=config)
        logging.info(params)
        output = cssn.do_analysis(params)
        #END run_EFI_SSN_Utils_Color_SSN

        # At some point might do deeper type checking...
        if not isinstance(output, dict):
            raise ValueError('Method run_EFI_SSN_Utils_Color_SSN return value ' +
                             'output is not type dict as required.')
        # return the results
        return [output]
    def status(self, ctx):
        #BEGIN_STATUS
        returnVal = {'state': "OK",
                     'message': "",
                     'version': self.VERSION,
                     'git_url': self.GIT_URL,
                     'git_commit_hash': self.GIT_COMMIT_HASH}
        #END_STATUS
        return [returnVal]
