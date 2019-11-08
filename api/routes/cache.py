import helper

from flask import Blueprint, request, jsonify, make_response
from flask import current_app as app
from api import cache
from api.routes.login import token_required

cache_bp = Blueprint('cache_bp', __name__)


@cache_bp.route("/ping")
def ping():
    return make_response(jsonify(
        {
            'message': 'Success',
            'data': {'route': request.path}
        }), 200)


@cache_bp.route("/clear", methods=['POST'])
@token_required
def clear_cache():
    if helper.is_empty_content_length(request):
        app.logger.error(f'Exception: {request.content_type}')
        return make_response(jsonify(
            {
                'message': 'Payload can not be empty'
            }), 411)

    if not helper.is_json_content(request):
        app.logger.error(f'Exception: {request.content_type}')
        return make_response(jsonify(
            {
                'message': 'Unsupported Media Type'
            }), 415)

    if request.method == 'POST':
        try:
            cache_key = request.json['cache_key']
        except KeyError as err:
            app.logger.error(f'Exception: {err}')
            return make_response(jsonify(
                {
                    'message': 'Some parameter is missing on request'
                }), 400)

        if cache_key is None or not cache_key.strip():
            return make_response(jsonify(
                {
                    'message': 'You must send cache_key value on payload and it can not be empty'
                }), 400)

        cache_key = cache_key.strip()
        app.logger.info(f'cache_key: {cache_key}')

        try:
            if cache_key == 'all':
                cache.clear()
            else:
                cache.delete(cache_key)

            return make_response(jsonify(
                {
                    'message': 'Success!'
                }), 200)
        except Exception as err:
            app.logger.error(f'Exception: {err}')
            return make_response(jsonify(
                {
                    'message': 'Error while clearing cache'
                }), 500)
