# -*- coding: utf-8 -*-

import six
import unittest
from decimal import Decimal
import simplejson as json

from flask import Flask

from flask_rest_toolkit.api import Api
from flask_rest_toolkit.endpoint import ApiEndpoint
from flask_rest_toolkit import exceptions

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


class SerializerConfTestCase(unittest.TestCase):
    def test_unexisting_serializer_raises_proper_exception(self):
        app = Flask(__name__)
        app.config['TESTING'] = True

        api_v1 = Api(version="v1")
        api_v1.register_endpoint(ApiEndpoint(
            http_method="GET",
            endpoint="/test/",
            handler=lambda req: {},
            serializer='non-existent'
        ))

        app.register_blueprint(api_v1)
        client = app.test_client()

        with self.assertRaises(exceptions.InvalidSerializerException):
            resp = client.get('/v1/test/')
            self.assertEqual(resp.status_code, 500)


class TextAndJavascriptSerializerTestCase(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True

    def test_js_with_text_serializer(self):
        "Should return valid javascript using a text serializer"

        def js_endpoint_text_serializer(request):
            js_text = "window.ReallyImportantVariable = XXX-XXX-001;"
            return js_text, 200, {'Content-Type': 'application/javascript'}

        api_v1 = Api(version="v1")
        api_v1.register_endpoint(ApiEndpoint(
            http_method="GET",
            endpoint="/js-text-serializer/",
            handler=js_endpoint_text_serializer,
            serializer='text'
        ))
        self.app.register_blueprint(api_v1)

        client = self.app.test_client()
        resp = client.get('/v1/js-text-serializer/')
        self.assertEqual(resp.status_code, 200)

        self.assertEqual(
            resp.data.decode(resp.charset),
            "window.ReallyImportantVariable = XXX-XXX-001;"
        )
        self.assertEqual(
            resp.headers['Content-Type'], 'application/javascript')

    def test_js_with_javascript_serializer(self):
        "Should return valid javascript using the js serializer"
        api_v1 = Api(version="v1")

        def js_endpoint_javascript_serializer(request):
            js_text = "window.ReallyImportantVariable = XXX-XXX-002;"
            return js_text

        api_v1.register_endpoint(ApiEndpoint(
            http_method="GET",
            endpoint="/js-javascript-serializer/",
            handler=js_endpoint_javascript_serializer,
            serializer='javascript'
        ))
        self.app.register_blueprint(api_v1)

        client = self.app.test_client()
        resp = client.get('/v1/js-javascript-serializer/')
        self.assertEqual(resp.status_code, 200)

        self.assertEqual(
            resp.data.decode(resp.charset),
            "window.ReallyImportantVariable = XXX-XXX-002;"
        )
        self.assertEqual(
            resp.headers['Content-Type'], 'application/javascript')

    def test_byte_text_serializer(self):
        "Should return correct text response returning bytes"
        api_v1 = Api(version="v1")

        text = six.b("""
Plain text
In Multiple Lines""")

        def bytes_endpoint(request):
            return text

        api_v1.register_endpoint(ApiEndpoint(
            http_method="GET",
            endpoint="/bytes-endpoint/",
            handler=bytes_endpoint,
            serializer='text'
        ))
        self.app.register_blueprint(api_v1)

        client = self.app.test_client()
        resp = client.get('/v1/bytes-endpoint/')
        self.assertEqual(resp.status_code, 200)

        self.assertEqual(resp.data, text)
        self.assertEqual(
            resp.data.decode(resp.charset),
            text.decode('utf-8')
        )
        self.assertEqual(
            resp.headers['Content-Type'], 'text/plain')

    def test_string_unicode_text_serializer(self):
        "Should return correct text response encoding str/unicode"
        api_v1 = Api(version="v1")

        text = six.u("""
Plain text
ñÑüÜäÄÁáà
In Multiple Lines""")

        def unicode_endpoint(request):
            return text

        api_v1.register_endpoint(ApiEndpoint(
            http_method="GET",
            endpoint="/unicode-endpoint/",
            handler=unicode_endpoint,
            serializer='text'
        ))
        self.app.register_blueprint(api_v1)

        client = self.app.test_client()
        resp = client.get('/v1/unicode-endpoint/')
        self.assertEqual(resp.status_code, 200)

        self.assertEqual(resp.data, text.encode(resp.charset))
        self.assertEqual(
            resp.data.decode(resp.charset),
            text
        )
        self.assertEqual(
            resp.headers['Content-Type'], 'text/plain')
