# -*- coding: utf-8 -*-
import os
import time
import unittest
from configparser import ConfigParser

from installed_clients.DataFileUtilClient import DataFileUtil

from EFIToolsKBase.EFIToolsKBaseImpl import EFIToolsKBase
from EFIToolsKBase.EFIToolsKBaseServer import MethodContext
from EFIToolsKBase.authclient import KBaseAuth as _KBaseAuth

from installed_clients.WorkspaceClient import Workspace


class EFIToolsKBaseTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        token = os.environ.get("KB_AUTH_TOKEN", None)
        config_file = os.environ.get("KB_DEPLOYMENT_CONFIG", None)
        cls.cfg = {}
        config = ConfigParser()
        config.read(config_file)
        for nameval in config.items("EFIToolsKBase"):
            cls.cfg[nameval[0]] = nameval[1]
        # Getting username from Auth profile for token
        authServiceUrl = cls.cfg["auth-service-url"]
        auth_client = _KBaseAuth(authServiceUrl)
        user_id = auth_client.get_user(token)
        # WARNING: don't call any logging methods on the context object,
        # it'll result in a NoneType error
        cls.ctx = MethodContext(None)
        cls.ctx.update(
            {
                "token": token,
                "user_id": user_id,
                "provenance": [
                    {
                        "service": "EFIToolsKBase",
                        "method": "please_never_use_it_in_production",
                        "method_params": [],
                    }
                ],
                "authenticated": 1,
            }
        )
        cls.wsURL = cls.cfg["workspace-url"]
        cls.wsClient = Workspace(cls.wsURL)
        cls.serviceImpl = EFIToolsKBase(cls.cfg)
        cls.scratch = cls.cfg["scratch"]
        cls.callback_url = os.environ["SDK_CALLBACK_URL"]
        suffix = int(time.time() * 1000)
        cls.wsName = "test_ContigFilter_" + str(suffix)
        ret = cls.wsClient.create_workspace({"workspace": cls.wsName})  # noqa

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "wsName"):
            cls.wsClient.delete_workspace({"workspace": cls.wsName})
            print("Test workspace was deleted")

    # NOTE: According to Python unittest naming rules test method names should start from 'test'. # noqa
    # @unittest.skip("Skip test for debugging")
    # def test_your_method(self):
        # Prepare test objects in workspace if needed using
        # self.getWsClient().save_objects({'workspace': self.getWsName(),
        #                                  'objects': []})
        #
        # Run your method by
        # ret = self.getImpl().your_method(self.getContext(), parameters...)
        #
        # Check returned data with
        # self.assertEqual(ret[...], ...) or other unittest methods
        # ret = self.serviceImpl.run_(
        #     self.ctx,
        #     {
        #         "workspace_name": self.wsName,
        #         "reads_ref": "70257/2/1",
        #         "output_name": "ReadsOutputName",
        #     },
        # )
        # next steps:
        # - download report
        # - assert that the report has expected contents

    def test_run_EFI_EST_FASTA(self):
        ret = self.serviceImpl.run_EFI_EST_FASTA(self.ctx, {
            "fasta_sequences_file": "73509/88/1",
            "fragment_option": 0,
            "workspace_name": self.wsName
        })
        print(ret)
        self.assertTrue(len(ret[0]["report_name"]))
        self.assertTrue(len(ret[0]["edge_ref"]))

    def test_run_EFI_EST_Families(self):
        ret = self.serviceImpl.run_EFI_EST_Families(self.ctx, {
            "fragment_option": False,
            "protein_family_addition_options": {
                "families_addition_cluster_id_format": "UniProt",
                "families_to_add": "PF07476"
            },
            "workspace_name": self.wsName
        })
        print(ret)
        self.assertTrue(len(ret[0]["report_name"]))
        self.assertTrue(len(ret[0]["edge_ref"]))

    def test_run_EFI_EST_SSN_Creation(self):
        ret = self.serviceImpl.run_EFI_EST_SSN_Creation(self.ctx, {
            "blast_edge_file": "73509/84/1",
            "alignment_score": 87,
            "workspace_name": self.wsName
        })