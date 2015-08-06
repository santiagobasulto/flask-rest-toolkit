import json
import unittest
import base64

from flask import Flask

from flask_rest_toolkit.api import Api
from flask_rest_toolkit.endpoint import ApiEndpoint
from flask_rest_toolkit.auth import BasicAuth


class BasicAuthTestCase(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        self.username = "testing@payability.com"
        self.password = "ShowMeTheMoney"

        def is_valid_user(username, password):
            return (username, password) == (self.username, self.password)

        self.tasks = [
            {'id': 1, 'task': 'Do the laundry'},
            {'id': 2, 'task': 'Do the dishes'},
        ]

        def get_tasks(request):
            return self.tasks

        api_201409 = Api(version="v201409")
        api_201409.register_endpoint(ApiEndpoint(
            http_method="GET",
            endpoint="/task/basic",
            handler=get_tasks,
            authentication=BasicAuth(is_valid_user=is_valid_user)
        ))

        app.register_blueprint(api_201409)

        app.config['TESTING'] = True
        self.app = app.test_client()

    def test_basic_auth_not_authenticated(self):
        resp = self.app.get(
            '/v201409/task/basic',
            content_type='application/json')
        self.assertEqual(resp.status_code, 401)

    def test_basic_auth_authenticated(self):
        auth_str = "{username}:{password}".format(
            username=self.username, password=self.password).encode('ascii')
        resp = self.app.get(
            '/v201409/task/basic',
            content_type='application/json',
            headers={
                'Authorization': b'Basic ' + base64.b64encode(auth_str)
            }
        )
        self.assertEqual(resp.status_code, 200)

        data = json.loads(resp.data.decode(resp.charset))
        self.assertEqual(data, self.tasks)

    def test_basic_auth_with_wrong_username_and_password(self):
        auth_str = "{username}:{password}".format(
            username="XXX", password="OOO").encode('ascii')
        resp = self.app.get(
            '/v201409/task/basic',
            content_type='application/json',
            headers={
                'Authorization': b'Basic ' + base64.b64encode(auth_str)
            }
        )
        self.assertEqual(resp.status_code, 401)
