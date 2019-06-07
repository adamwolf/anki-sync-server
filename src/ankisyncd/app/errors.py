from flask import current_app


class BadRequest(Exception):
    status_code = 500

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload


@current_app.errorhandler(BadRequest)
def handle_bad_request(error):
    response = error.message
    response.status_code = error.status_code
    return response
