import json
import unittest

from flask import Flask

from flask_rest_toolkit.api import Api
from flask_rest_toolkit.endpoint import ApiEndpoint


class DummyException(Exception):
    pass


class DummyExceptionSubclass(DummyException):
    pass


class DummyExceptionOtherSubclass(DummyException):
    pass


class DummyDataException(Exception):
    def __init__(self, data=None):
        self.data = data


class ExceptionsHierarchyTestCase(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)

        def raises_dummy_exception(request):
            exc_type = request.args.get('exc_type')

            if exc_type == 'subclass':
                raise DummyExceptionSubclass()
            elif exc_type == 'other-subclass':
                raise DummyExceptionOtherSubclass()

            raise DummyException()

        api_201409 = Api(version="v1")
        api_201409.register_endpoint(ApiEndpoint(
            http_method="GET",
            endpoint="/dummy-exception",
            handler=raises_dummy_exception,
            exceptions=[
                (DummyExceptionOtherSubclass, 409),
                (DummyExceptionSubclass, 406),
                (DummyException, 400)
            ]
        ))

        app.register_blueprint(api_201409)

        app.config['TESTING'] = True
        self.app = app.test_client()

    def test_different_exceptions_with_different_codes(self):
        resp = self.app.get(
            '/v1/dummy-exception?exc_type=subclass',
            content_type='application/json')
        self.assertEqual(resp.status_code, 406)

        resp = self.app.get(
            '/v1/dummy-exception?exc_type=other-subclass',
            content_type='application/json')
        self.assertEqual(resp.status_code, 409)

        resp = self.app.get(
            '/v1/dummy-exception',
            content_type='application/json')
        self.assertEqual(resp.status_code, 400)


class ExceptionDataTestCase(unittest.TestCase):
    def test_data_returned_with_correct_status_code(self):
        app = Flask(__name__)
        self.conflicted_user = {
            'username': 'johndoe',
        }

        def raises_exception(request):
            raise DummyDataException(data=self.conflicted_user)

        api_201409 = Api(version="v1")
        api_201409.register_endpoint(ApiEndpoint(
            http_method="GET",
            endpoint="/dummy-exception",
            handler=raises_exception,
            exceptions=[
                (DummyDataException, 409),
            ]
        ))

        app.register_blueprint(api_201409)

        app.config['TESTING'] = True
        self.app = app.test_client()

        resp = self.app.get(
            '/v1/dummy-exception',
            content_type='application/json')
        self.assertEqual(resp.status_code, 409)

        data = json.loads(resp.data.decode(resp.charset))
        self.assertEqual(data, self.conflicted_user)
