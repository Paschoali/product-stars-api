from flask import Blueprint, jsonify, make_response, request
from flask import current_app as app

errors_bp = Blueprint('errors_bp', __name__)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify(
        {
            'message': 'Path not found!',
            'data': {'path': request.path}
        }), 404)
