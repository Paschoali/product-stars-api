import datetime
import jwt

from flask import Blueprint, request, jsonify, make_response
from flask import current_app as app
from functools import wraps

login_bp = Blueprint('login_bp', __name__)


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.args.get('token')

        if not token:
            return make_response(jsonify(
                {
                    'message': 'Token is missing!'
                }), 403)

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
        except Exception as err:
            app.logger.error(f'Exception: {err}')
            return make_response(jsonify(
                {
                    'message': 'Token is invalid!'
                }), 403)

        return f(*args, **kwargs)

    return decorated


@login_bp.route("/ping")
def ping():
    return make_response(jsonify(
        {
            'message': 'Success',
            'data': {'route': request.path}
        }), 200)


@login_bp.route("/")
def login():
    auth = request.authorization

    if auth and auth.password == app.config['PASSWORD']:
        token = jwt.encode({'user': auth.username, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])
        return make_response(jsonify(
            {
                'message': 'Success',
                'data': {'token': token.decode('UTF-8')}
            }), 200)

    return make_response(jsonify(
        {
            'message': 'Invalid credentials'
        }), 401, {'WWW-Authenticate': 'Basic realm="Login required"'})
