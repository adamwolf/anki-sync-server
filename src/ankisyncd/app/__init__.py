import logging


def create_app(syncapp=None):
    from ankisyncd.sync_app import SyncApp
    from flask import Flask

    logging.basicConfig(
        level=logging.DEBUG, format="[%(asctime)s]:%(levelname)s:%(name)s:%(message)s"
    )
    import ankisyncd.config

    # if len(sys.argv) > 1: # backwards compat
    #    config = ankisyncd.config.load(sys.argv[1])
    # else:

    if syncapp is None:
        config = ankisyncd.config.load()
        ankiserver = SyncApp(config)
    else:
        ankiserver = syncapp

    app = Flask("ankisyncd")
    app.logger.setLevel(logging.DEBUG)

    app.add_url_rule(
        "/",
        "sync",
        defaults={"path": ""},
        view_func=ankiserver,
        methods=["GET", "POST"],
    )
    app.add_url_rule(
        "/<path:path>", "sync", view_func=ankiserver, methods=["GET", "POST"]
    )
    return app
