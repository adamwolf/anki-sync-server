# -*- coding: utf-8 -*-

import os
from sqlite3 import dbapi2 as sqlite

import anki.db


class FullSyncManager:
    def upload(self, col, data, session):
        from ankisyncd.app.errors import BadRequest  # TODO MOVE TO TOP

        # Verify integrity of the received database file before replacing our
        # existing db.
        temp_db_path = session.get_collection_path() + ".tmp"
        with open(temp_db_path, "wb") as f:
            f.write(data)

        try:
            with anki.db.DB(temp_db_path) as test_db:
                if test_db.scalar("pragma integrity_check") != "ok":
                    raise BadRequest(
                        "Integrity check failed for uploaded "
                        "collection database file.",
                        status_code=500,
                    )
        except sqlite.Error:
            raise BadRequest(
                "Uploaded collection database file is corrupt.", status_code=500
            )
        # Overwrite existing db.
        col.close()
        try:
            os.replace(temp_db_path, session.get_collection_path())
        finally:
            col.reopen()
            col.load()

        return "OK"

    def download(self, col, session):
        col.close()
        try:
            data = open(session.get_collection_path(), "rb").read()
        finally:
            col.reopen()
            col.load()
        return data


def get_full_sync_manager(config):
    if (
        "full_sync_manager" in config and config["full_sync_manager"]
    ):  # load from config
        import importlib
        import inspect

        module_name, class_name = config["full_sync_manager"].rsplit(".", 1)
        module = importlib.import_module(module_name.strip())
        class_ = getattr(module, class_name.strip())

        if FullSyncManager not in inspect.getmro(class_):
            raise TypeError(
                """"full_sync_manager" found in the conf file but it doesn''t
                            inherit from FullSyncManager"""
            )
        return class_(config)
    else:
        return FullSyncManager()
