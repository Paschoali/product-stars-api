from flask import Blueprint, request, jsonify, make_response
from flask import current_app as app
from api.models import Person, ProductList, PersonSchema
from functools import wraps
from api import db, cache
import datetime
import helper
import jwt
import requests
import math

api_bp = Blueprint('api_bp', __name__)


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


@api_bp.route("/*")
def catch_all_routes():
    app.logger.info('Route catch')


@api_bp.errorhandler(404)
def not_found(error):
    return make_response(jsonify(
        {
            'message': 'Not found!'
        }), 404)


@api_bp.route("/clear_cache", methods=['POST'])
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


@api_bp.route("/login")
def login():
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

    auth = request.authorization

    if auth and auth.password == 'senha':
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


@api_bp.route("/ping")
def ping():
    return make_response(jsonify(
        {
            'message': 'Success'
        }), 200)


@api_bp.route('/person', methods=['GET', 'POST'])
@token_required
def person():
    if request.method == 'GET':
        person_list = cache.get('person_list')

        if person_list is not None:
            return make_response(jsonify(
                {
                    'message': 'Success',
                    'data': {'person_list': person_list}
                }), 200)

        person_list = Person.query.order_by(Person.create_date).all()
        schema = PersonSchema(many=True)
        result = schema.dump(person_list)
        cache.set('person_list', result, helper.get_hours_in_seconds(1))
        return make_response(jsonify(
            {
                'message': 'Success',
                'data': {'person_list': result}
            }), 200)

    if request.method == 'POST':
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

        name = request.form['name']
        email = request.form['email']

        if name or email:
            _person = Person(name=name, email=email)

            try:
                db.session.add(_person)
                db.session.commit()
            except Exception as err:
                app.logger.error(f'Exception: {err}')
                return make_response(jsonify(
                    {
                        'message': 'Error while creating person! That email address is already in use.'
                    }), 500)
        else:
            return make_response(jsonify(
                {
                    'message': 'Name or email is missing.'
                }), 200)

        cache.delete('person_list')

        return make_response(jsonify(
            {
                'message': 'Success!',
                'data': {'person_id': _person.id}
            }), 200)


@api_bp.route('/person/<uuid:person_id>', endpoint='getById', methods=['GET', 'PUT', 'PATCH', 'DELETE'])
@token_required
def person(person_id):
    _person = Person.query.get(person_id)

    if request.method == 'GET':
        schema = PersonSchema()
        result = schema.dump(_person)
        return make_response(jsonify(
            {
                'message': 'Success',
                'data': {'person': result}
            }), 200)

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

    if request.method == 'PUT':
        try:
            _person.name = request.form['name']
            _person.email = request.form['email']
        except KeyError as err:
            app.logger.error(f'Exception: {err}')
            return make_response(jsonify(
                {
                    'message': 'Some parameter is missing on request'
                }), 400)

        try:
            db.session.commit()
            cache.delete('person_list')
            return make_response(jsonify(
                {
                    'message': 'Success',
                    'data': {'person_id': person_id}
                }), 200)
        except Exception as err:
            app.logger.error(f'Exception: {err}')
            return make_response(jsonify(
                {
                    'message': 'Error while updating person information',
                    'data': {'person_id': person_id}
                }), 500),

    if request.method == 'PATCH':
        _person.name = request.form.get('name') or _person.name
        _person.email = request.form.get('email') or _person.email

        try:
            db.session.commit()
            cache.delete('person_list')
            return make_response(jsonify(
                {
                    'message': 'Success',
                    'data': {'person_id', person_id}
                }), 200)
        except Exception as err:
            app.logger.error(f'Exception: {err}')
            return make_response(jsonify(
                {
                    'message': 'Error while updating person information',
                    'data': {'person_id': person_id}
                }), 500)

    if request.method == 'DELETE':
        if _person is None:
            return make_response(jsonify(
                {
                    'message': 'Person not found',
                    'data': {'person_id': person_id}
                }), 200)

        try:
            db.session.delete(_person)
            db.session.commit()
            cache.delete('person_list')
            return make_response(jsonify(
                {
                    'message': 'Success',
                    'data': {'person_id': person_id}
                }), 200)
        except Exception as err:
            app.logger.error(f'Exception: {err}')
            return make_response(jsonify(
                {
                    'message': 'Error while deleting person',
                    'data': {'person_id': person_id}
                }), 500)


@api_bp.route('/person/<uuid:person_id>/product', methods=['GET', 'POST'])
@token_required
def get_person_product_list(person_id):
    if request.method == 'GET':
        try:
            page = int(request.args.get('page')) or 1
        except ValueError as err:
            app.logger.error(f'Exception: {err}')
            return make_response(jsonify(
                {
                    'message': 'Some parameter is on incorrect format',
                    'data': {'person_id': person_id}
                }), 500)
        except Exception as err:
            app.logger.error(f'Exception: {err}')
            return make_response(jsonify(
                {
                    'message': 'Some parameter is missing on request',
                    'data': {'person_id': person_id}
                }), 400)

        app.logger.debug(f'page: {page}')
        product_count = ProductList.query.filter(ProductList.person_id == person_id).count()
        items_per_page = int(app.config['ITEMS_PER_PAGE'])
        max_page = math.ceil(product_count / items_per_page)

        if page > max_page:
            return make_response(jsonify(
                {
                    'message': f'Page number must be less than or equal to {max_page}',
                    'data': {'product_count': product_count}
                }), 404)

        products = ProductList.query.filter(ProductList.person_id == person_id).group_by(ProductList.insert_date).paginate(page, items_per_page, True).items

        if products:
            product_list = []
            product_api_endpoint = app.config['EXTERNAL_API']

            for product in products:
                response = requests.get(product_api_endpoint.replace('|PRODUCT_ID|', str(product.product_id)))

                if response.status_code == 200:
                    p = response.json()
                    title = p['title']
                    image = p['image']
                    price = p['price']
                    review_score = p['reviewScore'] if 'reviewScore' in p else None

                    product_list.append(
                        {
                            'id': product.product_id,
                            'title': title,
                            'image': image,
                            'price': price,
                            'review_score': review_score
                        }
                    )
                else:
                    app.logger.info(f'Product ({product.product_id}) not found')

            app.logger.debug(f'{len(product_list)} products on list')
            return make_response(jsonify(
                {
                    'message': 'Success',
                    'data': {'person_id': person_id, 'product_list': product_list}
                }), 200)

        return make_response(jsonify(
            {
                'message': 'This product list is empty',
                'data': {'person_id': person_id}
            }), 200)

    if request.method == 'POST':
        product_id = request.json['product_id']
        app.logger.info(f'product_id: {product_id}')
        product_api_endpoint = app.config['EXTERNAL_API']
        response = requests.get(product_api_endpoint.replace('|PRODUCT_ID|', str(product_id)))

        if not response.status_code == 200:
            return make_response(jsonify(
                {
                    'message': 'This product does not exists',
                    'data': {'product_id': product_id}
                }), 404)

        _product = ProductList.query.filter(ProductList.person_id == person_id, ProductList.product_id == product_id).count()

        if _product:
            return make_response(jsonify(
                {
                    'message': 'Product already is this list',
                    'data': {'product_id': product_id}
                }), 200)

        _product = ProductList(person_id=person_id, product_id=product_id)

        try:
            db.session.add(_product)
            db.session.commit()
        except Exception as err:
            app.logger.error(f'Exception: {err}')
            return make_response(jsonify(
                {
                    'message': f'Error while adding product (\'{product_id}\') to person (\'{person_id}\'',
                    'data': {'person_id': person_id, 'product_id': product_id}
                }), 500)

        return make_response(jsonify(
            {
                'message': 'Product successfully added to list',
                'data': {'person_id': person_id, 'product_id': product_id}
            }), 200)
