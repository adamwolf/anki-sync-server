import base64
import json
import os

from tests.helpers.collection_utils import CollectionUtils
from tests.helpers.monkey_patches import monkeypatch_db, unpatch_db
from tests.helpers.server_utils import create_config, create_server_paths

from ankisyncd.app import create_app
from ankisyncd.sync_app import SyncApp
from ankisyncd.users import SqliteUserManager


class TestAPI:
    @classmethod
    def setup_class(cls):
        cls.colutils = CollectionUtils()

    @classmethod
    def teardown_class(cls):
        cls.colutils.clean_up()
        cls.colutils = None

    def setup_method(self, method):
        monkeypatch_db()

        # Create temporary files and dirs the server will use.
        self.server_paths = create_server_paths()

        # Add a test user to the temp auth db the server will use.
        self.user_manager = SqliteUserManager(
            self.server_paths["auth_db_path"], self.server_paths["data_root"]
        )
        self.user_manager.add_user("testuser", "testpassword")

        # Get absolute path to development ini file.
        script_dir = os.path.dirname(os.path.realpath(__file__))
        ini_file_path = os.path.join(script_dir, "assets", "test.conf")

        self.config = create_config(self.server_paths, ini_file_path)

        self.sync_app = SyncApp(self.config["sync_app"])
        self.flask_app = create_app(
            self.config, self.sync_app, user_manager=self.user_manager
        )
        self.flask_app.config["TESTING"] = True

        self.client = self.flask_app.test_client()

    def teardown_method(self):
        self.server_paths = {}
        self.user_manager = None

        # Shut down server.
        self.sync_app.collection_manager.shutdown()
        self.flask_app = None
        self.sync_app = None

        self.client_server_connection = None

        unpatch_db()

    def test_no_login(self):
        rv = self.client.get("/api/decks")
        assert rv.status_code == 401
        assert json.loads(rv.data)["error"] == "Unauthorized"

    def test_good_login(self):
        header_value = "Basic %s" % base64.b64encode(
            b"testusername" + b":" + b"testpassword"
        )

        rv = self.client.open(
            "/api/decks", method="GET", headers={"Authorization": header_value}
        )
        assert rv.status_code == 401
        assert json.loads(rv.data)["error"] == "Unauthorized"

    def test_bad_password(self):
        header_value = "Basic %s" % base64.b64encode(
            b"testusername" + b":" + b"badpassword"
        )

        rv = self.client.open(
            "/api/decks", method="GET", headers={"Authorization": header_value}
        )
        assert rv.status_code == 401
        assert json.loads(rv.data)["error"] == "Unauthorized"
