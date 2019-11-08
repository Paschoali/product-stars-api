import base64
import json
import unittest

from api import create_app, db
from api.routes.login import login_bp
from api.routes.person import person_bp

app = create_app()
app.app_context().push()
TEST_DB = 'test.db'


class BasicTests(unittest.TestCase):
    def login(self):
        response = self.app.get('/login/', headers={'Authorization': 'Basic ' + self.valid_credentials})
        return response.json['data']['token']

    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['DEBUG'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'

        app.register_blueprint(login_bp, url_prefix='/login')
        app.register_blueprint(person_bp, url_prefix='/person')

        self.app = app.test_client()
        self.valid_credentials = base64.b64encode(b'user:d48c55d159fcc95789b5243948d64cb3').decode('utf-8')
        self.api_token = self.login()
        db.drop_all()
        db.create_all()

    def test_login(self):
        response = self.app.get('/login/', headers={'Authorization': 'Basic ' + self.valid_credentials})
        app.logger.info("token: " + response.json['data']['token'])
        self.api_token = response.json['data']['token']
        self.assertEqual(response.status_code, 200)

    def test_get_person_list(self):
        response = self.app.get('/person/?token=' + self.api_token)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Success', response.json['message'])

    def test_add_person(self):
        response = self.app.post(
            '/person/?token=' + self.api_token,
            data=json.dumps(dict(name='Bruno 01', email='bruno01@teste.com')),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

    def test_get_person_list_not_empty(self):
        self.app.post(
            '/person/?token=' + self.api_token,
            data=json.dumps(dict(name='Bruno 01', email='bruno01@teste.com')),
            content_type='application/json'
        )
        response = self.app.get('/person/?token=' + self.api_token)
        self.assertEqual(response.status_code, 200)
        app.logger.info(response.json['data']['person_list'])
        person_list = response.json['data']['person_list']
        assert len(person_list) != 0, "Empty list"


if __name__ == "__main__":
    unittest.main()
