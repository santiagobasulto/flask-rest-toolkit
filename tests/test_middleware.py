import mock
import json
import unittest

from flask import Flask, make_response
from werkzeug.exceptions import Forbidden

from flask_rest_toolkit.api import Api
from flask_rest_toolkit.endpoint import ApiEndpoint


class DummyMiddleware(object):
    def process_request(self, request):
        raise NotImplementedError()


class ForbiddenMiddleware(object):
    def process_request(self, request):
        raise Forbidden()


class CustomException(Exception):
    pass


class FullCustomExceptionMiddleware(object):
    EXCEPTIONS = [
        (CustomException, 400)
    ]

    def process_request(self, request):
        raise CustomException()


class CustomExceptionMiddleware(object):
    def process_request(self, request):
        raise CustomException()


class RedirectResponseMiddleware(object):
    def process_request(self, request):
        return make_response("Redirecting...", 302)


class RedirectDataMiddleware(object):
    def process_request(self, request):
        return {}, 302


class EndpointMiddlewareTestCase(unittest.TestCase):
    def setUp(self):
        self.tasks = [
            {'id': 1, 'task': 'Do the laundry'},
            {'id': 2, 'task': 'Do the dishes'},
            {'id': 3, 'task': 'Take the dog out'},
        ]

    def test_process_request_with_one_middleware_that_doesnt_return(self):
        app = Flask(__name__)

        def get_tasks(request):
            return self.tasks

        api_201409 = Api(version="v1")
        with mock.patch.object(DummyMiddleware, 'process_request',
                               return_value=None) as mock_method:
            api_201409.register_endpoint(ApiEndpoint(
                http_method="GET",
                endpoint="/task/",
                handler=get_tasks,
                middleware=[
                    DummyMiddleware
                ]
            ))
            app.register_blueprint(api_201409)

            app.config['TESTING'] = True
            self.app = app.test_client()

            resp = self.app.get('/v1/task/', content_type='application/json')
            self.assertEqual(resp.status_code, 200)

            data = json.loads(resp.data.decode(resp.charset))
            self.assertEqual(data, self.tasks)

        self.assertEqual(mock_method.call_count, 1)

    def test_process_request_with_one_middleware_that_raises_exception(self):
        app = Flask(__name__)

        def get_tasks(request):
            return self.tasks

        api_201409 = Api(version="v1")
        api_201409.register_endpoint(ApiEndpoint(
            http_method="GET",
            endpoint="/task/",
            handler=get_tasks,
            middleware=[
                ForbiddenMiddleware
            ]
        ))
        app.register_blueprint(api_201409)

        app.config['TESTING'] = True
        self.app = app.test_client()

        resp = self.app.get('/v1/task/', content_type='application/json')
        self.assertEqual(resp.status_code, 403)

    def test_process_request_with_one_middleware_that_returns_response(self):
        app = Flask(__name__)

        def get_tasks(request):
            return self.tasks

        api_201409 = Api(version="v1")
        api_201409.register_endpoint(ApiEndpoint(
            http_method="GET",
            endpoint="/task/",
            handler=get_tasks,
            middleware=[
                RedirectResponseMiddleware
            ]
        ))
        app.register_blueprint(api_201409)

        app.config['TESTING'] = True
        self.app = app.test_client()

        resp = self.app.get('/v1/task/', content_type='application/json')
        self.assertEqual(resp.status_code, 302)

        self.assertEqual(resp.data.decode(resp.charset), "Redirecting...")

    def test_process_request_with_one_middleware_that_returns_data(self):
        app = Flask(__name__)

        def get_tasks(request):
            return self.tasks

        api_201409 = Api(version="v1")
        api_201409.register_endpoint(ApiEndpoint(
            http_method="GET",
            endpoint="/task/",
            handler=get_tasks,
            middleware=[
                RedirectDataMiddleware
            ]
        ))
        app.register_blueprint(api_201409)

        app.config['TESTING'] = True
        self.app = app.test_client()

        resp = self.app.get('/v1/task/', content_type='application/json')
        self.assertEqual(resp.status_code, 302)

        self.assertEqual(json.loads(resp.data.decode(resp.charset)), {})

    def test_process_request_with_multiple_middlewares_order_1(self):
        app = Flask(__name__)

        def get_tasks(request):
            return self.tasks

        api_201409 = Api(version="v1")
        api_201409.register_endpoint(ApiEndpoint(
            http_method="GET",
            endpoint="/task/",
            handler=get_tasks,
            middleware=[
                RedirectDataMiddleware,
                ForbiddenMiddleware
            ]
        ))
        app.register_blueprint(api_201409)

        app.config['TESTING'] = True
        self.app = app.test_client()

        resp = self.app.get('/v1/task/', content_type='application/json')
        self.assertEqual(resp.status_code, 302)

        self.assertEqual(json.loads(resp.data.decode(resp.charset)), {})

    def test_process_request_with_multiple_middlewares_order_2(self):
        app = Flask(__name__)

        def get_tasks(request):
            return self.tasks

        api_201409 = Api(version="v1")
        api_201409.register_endpoint(ApiEndpoint(
            http_method="GET",
            endpoint="/task/",
            handler=get_tasks,
            middleware=[
                ForbiddenMiddleware,
                RedirectDataMiddleware
            ]
        ))
        app.register_blueprint(api_201409)

        app.config['TESTING'] = True
        self.app = app.test_client()

        resp = self.app.get('/v1/task/', content_type='application/json')
        self.assertEqual(resp.status_code, 403)


class ExceptionMiddlewareTestCase(unittest.TestCase):
    def setUp(self):
        self.tasks = [
            {'id': 1, 'task': 'Do the laundry'},
            {'id': 2, 'task': 'Do the dishes'},
            {'id': 3, 'task': 'Take the dog out'},
        ]

    def test_exception_is_not_defined_and_propagated(self):
        "Should propagate the exception if it's not defined"
        app = Flask(__name__)

        def get_tasks(request):
            return self.tasks

        api_201409 = Api(version="v1")
        api_201409.register_endpoint(ApiEndpoint(
            http_method="GET",
            endpoint="/task/",
            handler=get_tasks,
            middleware=[
                CustomExceptionMiddleware
            ]
        ))
        app.register_blueprint(api_201409)

        app.config['TESTING'] = True
        self.app = app.test_client()

        with self.assertRaises(CustomException):
            self.app.get('/v1/task/', content_type='application/json')

    def test_exception_is_defined_by_endpoint(self):
        "Should get the exception defined by the endpoint"
        app = Flask(__name__)

        def get_tasks(request):
            return self.tasks

        api_201409 = Api(version="v1")
        api_201409.register_endpoint(ApiEndpoint(
            http_method="GET",
            endpoint="/task/",
            handler=get_tasks,
            middleware=[
                CustomExceptionMiddleware
            ],
            exceptions=[
                (CustomException, 409),
            ]
        ))
        app.register_blueprint(api_201409)

        app.config['TESTING'] = True
        self.app = app.test_client()

        resp = self.app.get('/v1/task/', content_type='application/json')
        self.assertEqual(resp.status_code, 409)

    def test_exception_is_defined_by_middleware(self):
        "Should get the exception defined in the middleware"
        app = Flask(__name__)

        def get_tasks(request):
            return self.tasks

        api_201409 = Api(version="v1")
        api_201409.register_endpoint(ApiEndpoint(
            http_method="GET",
            endpoint="/task/",
            handler=get_tasks,
            middleware=[
                FullCustomExceptionMiddleware
            ]
        ))
        app.register_blueprint(api_201409)

        app.config['TESTING'] = True
        self.app = app.test_client()

        resp = self.app.get('/v1/task/', content_type='application/json')
        self.assertEqual(resp.status_code, 400)

    def test_exception_is_overwritten_by_endpoint(self):
        "The endpoint exception should take precedence"
        app = Flask(__name__)

        def get_tasks(request):
            return self.tasks

        api_201409 = Api(version="v1")
        api_201409.register_endpoint(ApiEndpoint(
            http_method="GET",
            endpoint="/task/",
            handler=get_tasks,
            middleware=[
                FullCustomExceptionMiddleware
            ],
            exceptions=[
                (CustomException, 409),
            ]
        ))
        app.register_blueprint(api_201409)

        app.config['TESTING'] = True
        self.app = app.test_client()

        resp = self.app.get('/v1/task/', content_type='application/json')
        self.assertEqual(resp.status_code, 409)
