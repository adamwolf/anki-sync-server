import logging
import sys

from flask import Flask

from ankisyncd.sync_app import SyncApp


def create_app():
    logging.basicConfig(level=logging.DEBUG, format="[%(asctime)s]:%(levelname)s:%(name)s:%(message)s")
    import ankisyncd.config

    # if len(sys.argv) > 1: # backwards compat
    #    config = ankisyncd.config.load(sys.argv[1])
    # else:

    config = ankisyncd.config.load()

    ankiserver = SyncApp(config)

    app = Flask("ankisyncd")

    app.add_url_rule('/', 'sync', defaults={'path': ''}, view_func=ankiserver, methods=["GET", "POST"])
    app.add_url_rule('/<path:path>', 'sync', view_func=ankiserver, methods=["GET", "POST"])
    port = config['port']
    return app
