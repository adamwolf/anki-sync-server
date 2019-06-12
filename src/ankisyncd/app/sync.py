from flask import Blueprint

from ankisyncd.app.errors import BadRequest


def create_blueprint(sync_app):
    ankiserver = sync_app

    sync_blueprint = Blueprint("sync", __name__)

    sync_blueprint.add_url_rule(
        "/",
        "sync",
        defaults={"path": ""},
        view_func=ankiserver,
        methods=["GET", "POST"],
    )

    sync_blueprint.add_url_rule(
        "/<path:path>", "sync", view_func=ankiserver, methods=["GET", "POST"]
    )

    @sync_blueprint.errorhandler(BadRequest)
    def handle_bad_request(error):
        response = error.message
        response.status_code = error.status_code
        return response

    return sync_blueprint
