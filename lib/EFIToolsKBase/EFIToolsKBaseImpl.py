# -*- coding: utf-8 -*-
#BEGIN_HEADER
import logging
import os

from installed_clients.KBaseReportClient import KBaseReport
from installed_clients.ReadsUtilsClient import ReadsUtils
from .utils import ExampleReadsApp
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
    GIT_COMMIT_HASH = "9df52a8cc63f42b1b488bb7bbb1868e8feefb3bf"

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
        #END_CONSTRUCTOR
        pass

    def run_EFI_EST_Sequence_BLAST(self, ctx, params):
        """
        This example function accepts any number of parameters and returns results in a KBaseReport
        :param params: instance of mapping from String to unspecified object
        :returns: instance of type "ReportResults" -> structure: parameter
           "report_name" of String, parameter "report_ref" of String
        """
        # ctx is the context object
        # return variables are: output
        #BEGIN run_EFI_EST_Sequence_BLAST

        config = dict(
            callback_url=self.callback_url,
            shared_folder=self.shared_folder,
            clients=dict(
                KBaseReport=KBaseReport,
                ReadsUtils=ReadsUtils
            ),
        )
        # Download Reads

        era = ExampleReadsApp(ctx, config=config)
        output = era.do_analysis(params)

        #END run_EFI_EST_Sequence_BLAST

        # At some point might do deeper type checking...
        if not isinstance(output, dict):
            raise ValueError('Method run_EFI_EST_Sequence_BLAST return value ' +
                             'output is not type dict as required.')
        # return the results
        return [output]

    def run_EFI_EST_Families(self, ctx, params):
        #BEGIN run_EFI_EST_Families
        pass
        #END run_EFI_EST_Families

    def run_EFI_EST_FASTA(self, ctx, params):
        #BEGIN run_EFI_EST_FASTA
        pass
        #END run_EFI_EST_FASTA

    def run_EFI_EST_Accession_IDs(self, ctx, params):
        #BEGIN run_EFI_EST_Accession_IDs
        pass
        #END run_EFI_EST_accession_IDs

    def run_EFI_GNT_GND_Single_Sequence_BLAST(self, ctx, params):
        #BEGIN run_EFI_GNT_GND_Single_Sequence_BLAST
        pass
        #END run_EFI_GNT_GND_Single_Sequence_BLAST

    def status(self, ctx):
        #BEGIN_STATUS
        returnVal = {'state': "OK",
                     'message': "",
                     'version': self.VERSION,
                     'git_url': self.GIT_URL,
                     'git_commit_hash': self.GIT_COMMIT_HASH}
        #END_STATUS
        return [returnVal]
