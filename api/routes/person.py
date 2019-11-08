import math
import helper
import requests

from flask import Blueprint, request, jsonify, make_response
from flask import current_app as app
from api import db, cache
from api.models import Person, PersonSchema, ProductList
from api.routes.login import token_required

person_bp = Blueprint('person_bp', __name__)


@person_bp.route("/ping")
def ping():
    return make_response(jsonify(
        {
            'message': 'Success',
            'data': {'route': request.path}
        }), 200)


@person_bp.route('/', methods=['GET', 'POST'])
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

        name = request.json['name']
        email = request.json['email']

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


@person_bp.route('/<uuid:person_id>', endpoint='getById', methods=['GET', 'PUT', 'PATCH', 'DELETE'])
@token_required
def person(person_id):
    _person = cache.get(f'person_{person_id}')

    if _person is None:
        _person = Person.query.get(person_id)

    if request.method == 'GET':
        schema = PersonSchema()
        result = schema.dump(_person)
        cache.set(f'person_{person_id}', result, helper.get_hours_in_seconds(1))
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
            _person.name = request.json['name']
            _person.email = request.json['email']
        except KeyError as err:
            app.logger.error(f'Exception: {err}')
            return make_response(jsonify(
                {
                    'message': 'Some parameter is missing on request'
                }), 400)

        try:
            db.session.commit()
            cache.delete(f'person_{person_id}')
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
        _person.name = request.json.get('name') or _person.name
        _person.email = request.json.get('email') or _person.email

        try:
            db.session.commit()
            cache.delete(f'person_{person_id}')
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
            cache.delete(f'person_{person_id}')
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


@person_bp.route('/<uuid:person_id>/product', methods=['GET', 'POST'])
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

        product_list = cache.get(f'products_person_{person_id}_page_{page}')

        if product_list is not None:
            return make_response(jsonify(
                {
                    'message': 'Success',
                    'data': {'person_id': person_id, 'product_list': product_list}
                }), 200)

        product_count = ProductList.query.filter(ProductList.person_id == person_id).count()

        if product_count <= 0:
            return make_response(jsonify(
                {
                    'message': 'This product list is empty',
                    'data': {'person_id': person_id}
                }), 200)

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
            cache.set(f'products_person_{person_id}_page_{page}', product_list, helper.get_hours_in_seconds(1))
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

        product_count = ProductList.query.filter(ProductList.person_id == person_id).count()
        items_per_page = int(app.config['ITEMS_PER_PAGE'])

        if items_per_page > 0:
            max_page = math.ceil(product_count / items_per_page)

            if max_page > 0:
                for page in range(1, max_page + 1):
                    app.logger.debug(f'Deleting cache key: products_person_{person_id}_page_{page}')
                    cache.delete(f'products_person_{person_id}_page_{page}')

        return make_response(jsonify(
            {
                'message': 'Product successfully added to list',
                'data': {'person_id': person_id, 'product_id': product_id}
            }), 200)

@person_bp.route('/<uuid:person_id>/product', methods=['DELETE'])
@token_required
def delete_product(person_id):
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

    try:
        product_id = request.json['product_id']
    except KeyError as err:
        app.logger.error(f'Exception: {err}')
        return make_response(jsonify(
            {
                'message': 'Some parameter is missing on payload'
            }), 400)

    _product = ProductList.query.filter(ProductList.person_id == person_id, ProductList.product_id == product_id).first()

    if _product:
        try:
            db.session.delete(_product)
            db.session.commit()

            product_count = ProductList.query.filter(ProductList.person_id == person_id).count()

            if product_count == 0:
                cache.delete(f'products_person_{person_id}_page_1')
            else:
                items_per_page = int(app.config['ITEMS_PER_PAGE'])

                if items_per_page > 0:
                    max_page = math.ceil(product_count / items_per_page)

                    if max_page > 0:
                        for page in range(1, max_page + 1):
                            app.logger.debug(f'Deleting cache key: products_person_{person_id}_page_{page}')
                            cache.delete(f'products_person_{person_id}_page_{page}')

            return make_response(jsonify(
                {
                    'message': 'Success',
                    'data': {'person_id': person_id, 'product_id': product_id}
                }), 200)
        except Exception as err:
            app.logger.error(f'Exception: {err}')
            return make_response(jsonify(
                {
                    'message': 'Error while deleting product from list',
                    'data': {'person_id': person_id, 'product_id': product_id}
                }), 500)