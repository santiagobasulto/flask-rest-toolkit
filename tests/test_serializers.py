import simplejson as json
import unittest
from decimal import Decimal

from flask import Flask

from flask_rest_toolkit.api import Api
from flask_rest_toolkit.endpoint import ApiEndpoint

from utils import get_task_by_id


class BasicSerializerTestCase(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        self.tasks = [
            {'id': 1, 'task': 'Decimal task', 'price': Decimal(22.755)},
            {'id': 2, 'task': 'Float task', 'price': 88.322},
            {'id': 3, 'task': 'Integer task', 'price': 882},
        ]

        def get_tasks(request):
            return self.tasks

        def get_task(request, task_id):
            return get_task_by_id(self.tasks, task_id)

        def post_task(request):
            data = request.json
            self.tasks.append({'task': data['task'], 'price': data['price']})
            return {}, 201

        api_201409 = Api(version="v1")
        task_endpoint = ApiEndpoint(
            http_method="GET",
            endpoint="/task/",
            handler=get_tasks
        )
        api_201409.register_endpoint(task_endpoint)
        task_endpoint = ApiEndpoint(
            http_method="GET",
            endpoint="/task/<int:task_id>/",
            handler=get_task
        )
        api_201409.register_endpoint(task_endpoint)

        task_endpoint = ApiEndpoint(
            http_method="POST",
            endpoint="/task/",
            handler=post_task
        )
        api_201409.register_endpoint(task_endpoint)

        app.register_blueprint(api_201409)

        app.config['TESTING'] = True
        self.app = app.test_client()


class JsonSerializerTestCase(BasicSerializerTestCase):
    def test_get_different_number_types(self):
        "Should GET all the tasks that have different numbers"
        resp = self.app.get('/v1/task/', content_type='application/json')
        self.assertEqual(resp.status_code, 200)

        data = json.loads(resp.data.decode(resp.charset))
        self.assertEqual(len(data), 3)

        self.assertEqual(resp.headers['Content-Type'], 'application/json')

    def test_get_a_decimal_type(self):
        "Should GET an object with a decimal type"
        resp = self.app.get('/v1/task/1/', content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers['Content-Type'], 'application/json')

        data = json.loads(resp.data.decode(resp.charset))
        self.assertEqual(data['id'], 1)
        self.assertEqual(data['task'], 'Decimal task')
        self.assertEqual(data['price'], 22.755)

    def test_get_a_float_type(self):
        "Should GET an object with a float type"
        resp = self.app.get('/v1/task/2/', content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers['Content-Type'], 'application/json')

        data = json.loads(resp.data.decode(resp.charset))
        self.assertEqual(data['id'], 2)
        self.assertEqual(data['task'], 'Float task')
        self.assertEqual(data['price'], 88.322)

    def test_get_an_int_type(self):
        "Should GET an object with an int type"
        resp = self.app.get('/v1/task/3/', content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers['Content-Type'], 'application/json')

        data = json.loads(resp.data.decode(resp.charset))
        self.assertEqual(data['id'], 3)
        self.assertEqual(data['task'], 'Integer task')
        self.assertEqual(data['price'], 882)

    def test_post_a_decimal_type(self):
        resp = self.app.post(
            '/v1/task/',
            content_type='application/json',
            data=json.dumps({'task': 'New Decimal Task',
                             'price': Decimal('0.222')}))
        self.assertEqual(resp.status_code, 201)

        resp = self.app.get('/v1/task/', content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers['Content-Type'], 'application/json')

        data = json.loads(resp.data.decode(resp.charset))
        self.assertEqual(len(data), 4)

        task = self.tasks[-1]
        self.assertEqual(task['task'], 'New Decimal Task')
        self.assertEqual(task['price'], 0.222)
