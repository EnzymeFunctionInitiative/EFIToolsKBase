# -*- coding: utf-8 -*-
#BEGIN_HEADER
import logging
import os

from installed_clients.KBaseReportClient import KBaseReport
from installed_clients.ReadsUtilsClient import ReadsUtils
from installed_clients.DataFileUtilClient import DataFileUtil
from installed_clients.AssemblyUtilClient import AssemblyUtil
from .est_wrappers.est_fasta import EFIFasta
from .est_wrappers.ssn_creation import SSNCreation
from base import Core

from .nextflow import NextflowRunner

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
    GIT_COMMIT_HASH = "aee730d7642ccba17d6937ea24194ab7832f822c"

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

    def run_EFI_EST_FASTA(self, ctx, params):
        """
        :param params: instance of mapping from String to unspecified object
        :returns: instance of type "EFIFastaReportResults" -> structure:
           parameter "report_name" of String, parameter "report_ref" of
           String, parameter "fasta_ref" of String, parameter "edge_ref" of
           String
        """
        # ctx is the context object
        # return variables are: output
        #BEGIN run_EFI_EST_FASTA
        config = dict(
            callback_url=self.callback_url,
            shared_folder=self.shared_folder,
            clients=dict(
                KBaseReport=KBaseReport,
                ReadsUtils=ReadsUtils,
                DataFileUtil=DataFileUtil,
                AssemblyUtil=AssemblyUtil
            ),
        )
        efi = EFIFasta(ctx, config=config)
        logging.info(params)
        if params["fasta_sequences_file"] is None:
           params["fasta_sequences_file"] = "/results/sequences.fasta"
        output = efi.do_analysis(params)
        
        #END run_EFI_EST_FASTA

        # At some point might do deeper type checking...
        if not isinstance(output, dict):
            raise ValueError('Method run_EFI_EST_FASTA return value ' +
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
    def status(self, ctx):
        #BEGIN_STATUS
        returnVal = {'state': "OK",
                     'message': "",
                     'version': self.VERSION,
                     'git_url': self.GIT_URL,
                     'git_commit_hash': self.GIT_COMMIT_HASH}
        #END_STATUS
        return [returnVal]
