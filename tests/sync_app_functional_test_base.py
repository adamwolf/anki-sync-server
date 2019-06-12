# -*- coding: utf-8 -*-
import os
import unittest

from tests import helpers
from tests.helpers import server_utils
from tests.helpers.collection_utils import CollectionUtils
from tests.helpers.mock_servers import MockRemoteServer
from tests.helpers.monkey_patches import monkeypatch_db, unpatch_db
from webtest import TestApp

from ankisyncd.app import create_app
from ankisyncd.sync_app import SyncApp
from ankisyncd.users import SqliteUserManager


class SyncAppFunctionalTestBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.colutils = CollectionUtils()

    @classmethod
    def tearDownClass(cls):
        cls.colutils.clean_up()
        cls.colutils = None

    def setUp(self):
        monkeypatch_db()

        # Create temporary files and dirs the server will use.
        self.server_paths = server_utils.create_server_paths()

        # Add a test user to the temp auth db the server will use.
        self.user_manager = SqliteUserManager(
            self.server_paths["auth_db_path"], self.server_paths["data_root"]
        )
        self.user_manager.add_user("testuser", "testpassword")

        # Get absolute path to development ini file.
        script_dir = os.path.dirname(os.path.realpath(__file__))
        ini_file_path = os.path.join(script_dir, "assets", "test.conf")

        # Create SyncApp instance using the dev ini file and the temporary
        # paths.
        self.config = helpers.server_utils.create_config(
            self.server_paths, ini_file_path
        )
        self.sync_app = SyncApp(self.config["sync_app"])

        self.flask_app = create_app(sync_app=self.sync_app, config=self.config)
        self.flask_app.config["TESTING"] = True

        # Wrap the SyncApp object in TestApp instance for testing.
        self.server_test_app = TestApp(self.flask_app)

        # MockRemoteServer instance needed for testing normal collection
        # syncing and for retrieving hkey for other tests.
        self.mock_remote_server = MockRemoteServer(
            hkey=None, server_test_app=self.server_test_app
        )

    def tearDown(self):
        self.server_paths = {}
        self.user_manager = None

        # Shut down server.
        self.sync_app.collection_manager.shutdown()
        self.flask_app = None
        self.sync_app = None

        self.client_server_connection = None

        unpatch_db()
