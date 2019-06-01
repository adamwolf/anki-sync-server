# -*- coding: utf-8 -*-
import tempfile
import filecmp
import sqlite3
import os
import shutil

import helpers.file_utils
import helpers.server_utils
import helpers.db_utils
from anki.sync import MediaSyncer
from helpers.mock_servers import MockRemoteMediaServer
from helpers.monkey_patches import monkeypatch_mediamanager, unpatch_mediamanager
from sync_app_functional_test_base import SyncAppFunctionalTestBase


class SyncAppFunctionalMediaTest(SyncAppFunctionalTestBase):
    def setUp(self):
        SyncAppFunctionalTestBase.setUp(self)

        monkeypatch_mediamanager()
        self.tempdir = tempfile.mkdtemp(prefix=self.__class__.__name__)
        self.hkey = self.mock_remote_server.hostKey("testuser", "testpassword")
        client_collection = self.colutils.create_empty_col()
        self.client_syncer = self.create_client_syncer(client_collection,
                                                       self.hkey,
                                                       self.server_test_app)

    def tearDown(self):
        self.hkey = None
        self.client_syncer = None
        unpatch_mediamanager()
        SyncAppFunctionalTestBase.tearDown(self)

    @staticmethod
    def create_client_syncer(collection, hkey, server_test_app):
        mock_remote_server = MockRemoteMediaServer(col=collection,
                                                   hkey=hkey,
                                                   server_test_app=server_test_app)
        media_syncer = MediaSyncer(col=collection,
                                   server=mock_remote_server)
        return media_syncer

    def media_dbs_differ(self, left_db_path, right_db_path, compare_timestamps=False):
        """
        Compares two media sqlite database files for equality. mtime and dirMod
        timestamps are not considered when comparing.

        :param left_db_path: path to the left db file
        :param right_db_path: path to the right db file
        :param compare_timestamps: flag determining if timestamp values
                                   (media.mtime and meta.dirMod) are included
                                   in the comparison
        :return: True if the specified databases differ, False else
        """

        if not os.path.isfile(right_db_path):
            raise IOError("file '" + left_db_path + "' does not exist")
        elif not os.path.isfile(right_db_path):
            raise IOError("file '" + right_db_path + "' does not exist")

        # Create temporary copies of the files to act on.
        newleft = os.path.join(self.tempdir, left_db_path) + ".tmp"
        shutil.copyfile(left_db_path, newleft)
        left_db_path = newleft

        newright = os.path.join(self.tempdir, left_db_path) + ".tmp"
        shutil.copyfile(right_db_path, newright)
        right_db_path = newright

        if not compare_timestamps:
            # Set all timestamps that are not NULL to 0.
            for dbPath in [left_db_path, right_db_path]:
                connection = sqlite3.connect(dbPath)

                connection.execute("""UPDATE media SET mtime=0
                                      WHERE mtime IS NOT NULL""")

                connection.execute("""UPDATE meta SET dirMod=0
                                      WHERE rowid=1""")
                connection.commit()
                connection.close()

        return helpers.db_utils.diff(left_db_path, right_db_path)

    def test_sync_empty_media_dbs(self):
        # With both the client and the server having no media to sync,
        # syncing should change nothing.
        self.assertEqual('noChanges', self.client_syncer.sync())
        self.assertEqual('noChanges', self.client_syncer.sync())

    def test_sync_file_from_server(self):
        """
        Adds a file on the server. After syncing, client and server should have
        the identical file in their media directories and media databases.
        """
        client = self.client_syncer
        server = helpers.server_utils.get_syncer_for_hkey(self.server_app,
                                                          self.hkey,
                                                          'media')

        # Create a test file.
        temp_file_path = helpers.file_utils.create_named_file("foo.jpg", "hello")

        # Add the test file to the server's collection.
        helpers.server_utils.add_files_to_mediasyncer(server,
                                                      [temp_file_path],
                                                      update_db=True,
                                                      bump_last_usn=True)

        # Syncing should work.
        self.assertEqual(client.sync(), 'OK')

        # The test file should be present in the server's and in the client's
        # media directory.
        self.assertTrue(
            filecmp.cmp(os.path.join(client.col.media.dir(), "foo.jpg"),
                        os.path.join(server.col.media.dir(), "foo.jpg")))

        # Further syncing should do nothing.
        self.assertEqual(client.sync(), 'noChanges')

    def test_sync_file_from_client(self):
        """
        Adds a file on the client. After syncing, client and server should have
        the identical file in their media directories and media databases.
        """
        join = os.path.join
        client = self.client_syncer
        server = helpers.server_utils.get_syncer_for_hkey(self.server_app,
                                                          self.hkey,
                                                          'media')

        # Create a test file.
        temp_file_path = helpers.file_utils.create_named_file("foo.jpg", "hello")

        # Add the test file to the client's media collection.
        helpers.server_utils.add_files_to_mediasyncer(client,
                                                      [temp_file_path],
                                                      update_db=True,
                                                      bump_last_usn=False)

        # Syncing should work.
        self.assertEqual(client.sync(), 'OK')

        # The same file should be present in both the client's and the server's
        # media directory.
        self.assertTrue(filecmp.cmp(join(client.col.media.dir(), "foo.jpg"),
                                    join(server.col.media.dir(), "foo.jpg")))

        # Further syncing should do nothing.
        self.assertEqual(client.sync(), 'noChanges')

        # Except for timestamps, the media databases of client and server
        # should be identical.
        self.assertFalse(
            self.media_dbs_differ(client.col.media.db._path, server.col.media.db._path)
        )

    def test_sync_different_files(self):
        """
        Adds a file on the client and a file with different name and content on
        the server. After syncing, both client and server should have both
        files in their media directories and databases.
        """
        join = os.path.join
        isfile = os.path.isfile
        client = self.client_syncer
        server = helpers.server_utils.get_syncer_for_hkey(self.server_app,
                                                          self.hkey,
                                                          'media')

        # Create two files and add one to the server and one to the client.
        file_for_client = helpers.file_utils.create_named_file("foo.jpg", "hello")
        file_for_server = helpers.file_utils.create_named_file("bar.jpg", "goodbye")

        helpers.server_utils.add_files_to_mediasyncer(client,
                                                      [file_for_client],
                                                      update_db=True)
        helpers.server_utils.add_files_to_mediasyncer(server,
                                                      [file_for_server],
                                                      update_db=True,
                                                      bump_last_usn=True)

        # Syncing should work.
        self.assertEqual(client.sync(), 'OK')

        # Both files should be present in the client's and in the server's
        # media directories.
        self.assertTrue(isfile(join(client.col.media.dir(), "foo.jpg")))
        self.assertTrue(isfile(join(server.col.media.dir(), "foo.jpg")))
        self.assertTrue(filecmp.cmp(
            join(client.col.media.dir(), "foo.jpg"),
            join(server.col.media.dir(), "foo.jpg"))
        )
        self.assertTrue(isfile(join(client.col.media.dir(), "bar.jpg")))
        self.assertTrue(isfile(join(server.col.media.dir(), "bar.jpg")))
        self.assertTrue(filecmp.cmp(
            join(client.col.media.dir(), "bar.jpg"),
            join(server.col.media.dir(), "bar.jpg"))
        )

        # Further syncing should change nothing.
        self.assertEqual(client.sync(), 'noChanges')

    def test_sync_different_contents(self):
        """
        Adds a file to the client and a file with identical name but different
        contents to the server. After syncing, both client and server should
        have the server's version of the file in their media directories and
        databases.
        """
        join = os.path.join
        isfile = os.path.isfile
        client = self.client_syncer
        server = helpers.server_utils.get_syncer_for_hkey(self.server_app,
                                                          self.hkey,
                                                          'media')

        # Create two files with identical names but different contents and
        # checksums. Add one to the server and one to the client.
        file_for_client = helpers.file_utils.create_named_file("foo.jpg", "hello")
        file_for_server = helpers.file_utils.create_named_file("foo.jpg", "goodbye")

        helpers.server_utils.add_files_to_mediasyncer(client,
                                                      [file_for_client],
                                                      update_db=True)
        helpers.server_utils.add_files_to_mediasyncer(server,
                                                      [file_for_server],
                                                      update_db=True,
                                                      bump_last_usn=True)

        # Syncing should work.
        self.assertEqual(client.sync(), 'OK')

        # A version of the file should be present in both the client's and the
        # server's media directory.
        self.assertTrue(isfile(join(client.col.media.dir(), "foo.jpg")))
        self.assertEqual(os.listdir(client.col.media.dir()), ['foo.jpg'])
        self.assertTrue(isfile(join(server.col.media.dir(), "foo.jpg")))
        self.assertEqual(os.listdir(server.col.media.dir()), ['foo.jpg'])
        self.assertEqual(client.sync(), 'noChanges')

        # Both files should have the contents of the server's version.
        _checksum = client.col.media._checksum
        self.assertEqual(_checksum(join(client.col.media.dir(), "foo.jpg")),
                         _checksum(file_for_server))
        self.assertEqual(_checksum(join(server.col.media.dir(), "foo.jpg")),
                         _checksum(file_for_server))

    def test_sync_add_and_delete_on_client(self):
        """
        Adds a file on the client. After syncing, the client and server should
        both have the file. Then removes the file from the client's directory
        and marks it as deleted in its database. After syncing again, the
        server should have removed its version of the file from its media dir
        and marked it as deleted in its db.
        """
        join = os.path.join
        isfile = os.path.isfile
        client = self.client_syncer
        server = helpers.server_utils.get_syncer_for_hkey(self.server_app,
                                                          self.hkey,
                                                          'media')

        # Create a test file.
        temp_file_path = helpers.file_utils.create_named_file("foo.jpg", "hello")

        # Add the test file to client's media collection.
        helpers.server_utils.add_files_to_mediasyncer(client,
                                                      [temp_file_path],
                                                      update_db=True,
                                                      bump_last_usn=False)

        # Syncing client should work.
        self.assertEqual(client.sync(), 'OK')

        # The same file should be present in both client's and the server's
        # media directory.
        self.assertTrue(filecmp.cmp(join(client.col.media.dir(), "foo.jpg"),
                                    join(server.col.media.dir(), "foo.jpg")))

        # Syncing client again should do nothing.
        self.assertEqual(client.sync(), 'noChanges')

        # Remove files from client's media dir and write changes to its db.
        os.remove(join(client.col.media.dir(), "foo.jpg"))

        # TODO: client.col.media.findChanges() doesn't work here - why?
        client.col.media._logChanges()
        self.assertEqual(client.col.media.syncInfo("foo.jpg"), (None, 1))
        self.assertFalse(isfile(join(client.col.media.dir(), "foo.jpg")))

        # Syncing client again should work.
        self.assertEqual(client.sync(), 'OK')

        # server should have picked up the removal from client.
        self.assertEqual(server.col.media.syncInfo("foo.jpg"), (None, 0))
        self.assertFalse(isfile(join(server.col.media.dir(), "foo.jpg")))

        # Syncing client again should do nothing.
        self.assertEqual(client.sync(), 'noChanges')

    def test_sync_compare_database_to_expected(self):
        """
        Adds a test image file to the client's media directory. After syncing,
        the server's database should, except for timestamps, be identical to a
        database containing the expected data.
        """
        client = self.client_syncer

        # Add a test image file to the client's media collection but don't
        # update its media db since the desktop client updates that, using
        # findChanges(), only during syncs.
        support_file = helpers.file_utils.get_asset_path('blue.jpg')
        self.assertTrue(os.path.isfile(support_file))
        helpers.server_utils.add_files_to_mediasyncer(client,
                                                      [support_file],
                                                      update_db=False)

        # Syncing should work.
        self.assertEqual(client.sync(), "OK")

        # Create temporary db file with expected results.
        chksum = client.col.media._checksum(support_file)
        sql = ("""
            CREATE TABLE meta (dirMod int, lastUsn int);

            INSERT INTO `meta` (dirMod, lastUsn) VALUES (123456789,1);

            CREATE TABLE media (
              fname text not null primary key,
              csum text,
              mtime int not null,
               dirty int not null
            );

            INSERT INTO `media` (fname, csum, mtime, dirty) VALUES (
               'blue.jpg',
               '%s',
               1441483037,
               0
            );

            CREATE INDEX idx_media_dirty on media (dirty);
        """ % chksum)

        _, dbpath = tempfile.mkstemp(suffix=".anki2")
        helpers.db_utils.from_sql(dbpath, sql)

        # Except for timestamps, the client's db after sync should be identical
        # to the expected data.
        self.assertFalse(self.media_dbs_differ(
            client.col.media.db._path,
            dbpath
        ))
        os.unlink(dbpath)
