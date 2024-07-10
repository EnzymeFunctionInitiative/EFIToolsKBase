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

    # def test_run_EFI_EST_AccessionIDs(self):
    #     ret = self.serviceImpl.run_EFI_EST_Accession_IDs(self.ctx, {
    #         "accession_id_input": {"accession_ids": "A0A010ZH43\nA0A017RWE5\nA0A017SQS5\nA0A063ZUG7\nA0A073ITR3\nA0A075KES1\nA0A077M284\nA0A078LBK1\nA0A084JAL8\nA0A088TMM5\nA0A090FUD8\nA0A090NBY8\nA0A090V3Y1\nA0A094IHS1\nA0A095ZGF5\nA0A097R141\nA0A098B3F3\nA0A099SB27\nA0A099SFX4\nA0A0A1A2Z3\nA0A0A2DQ68\nA0A0A2EEM4\nA0A0A2EMT4\nA0A0A2FQ19\nA0A0A2JHA1\nA0A0A2R940\nA0A0A6ZP69\nA0A0B3W871\nA0A0B5GQM8\nA0A0B7MAU0\nA0A0C1R2W2\nA0A0C6P9L1\nA0A0C6PC75\nA0A0D7LWZ5\nA0A0D8IBG0\nA0A0E1NIT1\nA0A0E2EIB4\nA0A0E2N462\nA0A0E2NZK5\nA0A0E3M9V7\nA0A0E7UUD8\nA0A0F0IK83\nA0A0F1BBX8\nA0A0F2JI16\nA0A0F2SEG8\nA0A0F6MQD1\nA0A0F6TU15\nA0A0F9RVE4\nA0A0H2R0M1\nA0A0H3HAS8\nA0A0H3LSV2\nA0A0H3LX20\nA0A0H3MEI1\nA0A0H3NZI0\nA0A0H3PR78\nA0A0J1DN26\nA0A0J1F8K5\nA0A0J1FLT2\nA0A0J1LJU5\nA0A0J1QVJ5\nA0A0J2DKC3\nA0A0J7JDM6\nA0A0J9AS39\nA0A0K1IYI9"},
    #         "workspace_name": self.wsName
    #     })
    #     print(ret)
    #     self.assertTrue(len(ret[0]["report_name"]))
    #     self.assertTrue(len(ret[0]["edge_ref"]))

    # def test_run_EFI_EST_FASTA(self):
    #     ret = self.serviceImpl.run_EFI_EST_FASTA(self.ctx, {
    #         "fasta_sequences_file": "73509/90/1",
    #         "workspace_name": self.wsName
    #     })
    #     print(ret)
    #     self.assertTrue(len(ret[0]["report_name"]))
    #     self.assertTrue(len(ret[0]["edge_ref"]))

    # def test_run_EFI_EST_Families(self):
    #     ret = self.serviceImpl.run_EFI_EST_Families(self.ctx, {
    #         "fragment_option": False,
    #         "protein_family_addition_options": {
    #             "families_addition_cluster_id_format": "UniProt",
    #             "families_to_add": "PF07476"
    #         },
    #         "workspace_name": self.wsName
    #     })
    #     print(ret)
    #     self.assertTrue(len(ret[0]["report_name"]))
    #     self.assertTrue(len(ret[0]["edge_ref"]))

    # def test_run_EFI_EST_SSN_Creation(self):
    #     ret = self.serviceImpl.run_EFI_EST_SSN_Creation(self.ctx, {
    #         "blast_edge_file": "73509/94/5",
    #         "alignment_score": 87,
    #         "min_length": 75,
    #         "max_length": 50000,
    #         "workspace_name": self.wsName
    #     })

    def test_run_EFI_EST_SSN_Creation(self):
        ret = self.serviceImpl.run_EFI_SSN_Utils_Color_SSN(self.ctx, {
            "ssn_file": "73509/108/3",
            "workspace_name": self.wsName
        })