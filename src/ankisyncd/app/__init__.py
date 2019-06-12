import logging

from ankisyncd.app import sync
from ankisyncd.app.api import api
from ankisyncd.config import load
from ankisyncd.sync_app import SyncApp
from ankisyncd.thread import get_collection_manager
from ankisyncd.users import get_user_manager


def create_app(config=None, sync_app=None, user_manager=None, collection_manager=None):

    from flask import Flask

    logging.basicConfig(
        level=logging.DEBUG, format="[%(asctime)s]:%(levelname)s:%(name)s:%(message)s"
    )

    if config is None:
        config = load()

    app = Flask("ankisyncd")
    app.logger.setLevel(logging.DEBUG)

    if user_manager is None:
        user_manager = get_user_manager(config)

    if collection_manager is None:
        collection_manager = get_collection_manager(config)

    if sync_app is None:
        sync_app = SyncApp(
            config, user_manager=user_manager, collection_manager=collection_manager
        )

    app.register_blueprint(sync.create_blueprint(sync_app=sync_app))
    app.register_blueprint(
        api.create_blueprint(config, user_manager, collection_manager),
        url_prefix="/api",
    )

    return app
