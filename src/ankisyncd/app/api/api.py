import logging
import os

from anki.find import Finder
from flask import Blueprint, g, jsonify, render_template, request
from flask_httpauth import HTTPBasicAuth
from werkzeug.http import HTTP_STATUS_CODES

auth = HTTPBasicAuth()


def create_blueprint(config, user_manager, collection_manager):
    api = Blueprint("api", __name__, template_folder="templates")

    def wants_json_response():
        return (
            request.accept_mimetypes["application/json"]
            >= request.accept_mimetypes["text/html"]
        )

    def api_error_response(status_code, message=None):
        payload = {"error": HTTP_STATUS_CODES.get(status_code, "Unknown error")}
        if message:
            payload["message"] = message
        response = jsonify(payload)
        response.status_code = status_code
        return response

    @auth.error_handler
    def basic_auth_error():
        return api_error_response(401)

    @auth.verify_password
    def verify_password(username, password):
        if not user_manager.authenticate(username, password):
            return False
        g.authenticated_username = username
        return True

    def group_cards_for_deck(finder, deck=None):
        if deck is None:
            return {
                "due_count": len(finder.findCards("is:due")),
                "overdue_count": len(finder.findCards("prop:due=-1")),
                "new_count": len(finder.findCards("is:new")),
                "all_count": len(finder.findCards("")),
            }

        return {
            "due_count": len(finder.findCards('is:due deck:"{}"'.format(deck["name"]))),
            "overdue_count": len(
                finder.findCards('prop:due=-1 deck:"{}"'.format(deck["name"]))
            ),
            "new_count": len(finder.findCards('is:new deck:"{}"'.format(deck["name"]))),
            "all_count": len(finder.findCards('deck:"{}"'.format(deck["name"]))),
        }

    def get_resource(username):
        logging.debug("Getting resource.")
        collection_path = os.path.join(
            config["data_root"], username, "collection.anki2"
        )

        col = collection_manager.get_collection(collection_path, None)
        real_col = col.wrapper._get_collection()

        data_by_deck = {}
        finder = Finder(real_col)
        for deck in real_col.decks.all():
            data_by_deck[deck["name"]] = group_cards_for_deck(finder, deck)
        data_for_all = group_cards_for_deck(finder)
        finder = None
        real_col.close()

        data = {"all": data_for_all, "by_deck": data_by_deck}
        return data

    @api.route("/decks")
    @auth.login_required
    def show_resource():
        data = get_resource(g.authenticated_username)
        if wants_json_response():
            return jsonify(data)
        else:
            return render_template(
                "api.html.j2", username=g.authenticated_username, data=data
            )

    return api
