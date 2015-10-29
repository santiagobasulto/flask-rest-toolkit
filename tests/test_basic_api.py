import json
import unittest
try:
    from unittest import mock
except ImportError:
    import mock

from flask import Flask

from flask_rest_toolkit.api import Api
from flask_rest_toolkit.endpoint import ApiEndpoint

from utils import get_task_by_id, get_task_index_by_id


class DummyException(Exception):
    pass


class DummyExceptionSubclass(DummyException):
    pass


class DummyExceptionOtherSubclass(DummyException):
    pass


class ApiTestCase(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        tasks = [
            {'id': 1, 'task': 'Do the laundry'},
            {'id': 2, 'task': 'Do the dishes'},
        ]

        def get_task(request):
            return tasks

        def post_task(request):
            data = request.json
            tasks.append({'task': data['task']})
            return {}, 201

        api_201409 = Api(version="v1")
        task_endpoint = ApiEndpoint(
            http_method="GET",
            endpoint="/task/",
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

    def test_simple_versioning_and_GET(self):
        resp = self.app.get('/v1/task/', content_type='application/json')
        self.assertEqual(resp.status_code, 200)

        data = json.loads(resp.data.decode(resp.charset))
        self.assertEqual(len(data), 2)

        self.assertEqual(resp.headers['Content-Type'], 'application/json')

    def test_simple_POST(self):
        resp = self.app.post(
            '/v1/task/',
            content_type='application/json',
            data=json.dumps({'task': 'New Task!'}))
        self.assertEqual(resp.status_code, 201)

        resp = self.app.get('/v1/task/', content_type='application/json')
        self.assertEqual(resp.status_code, 200)

        data = json.loads(resp.data.decode(resp.charset))
        self.assertEqual(len(data), 3)

        self.assertEqual(resp.headers['Content-Type'], 'application/json')


class QueryParamsTestCase(unittest.TestCase):
    def test_query_params_are_accesible(self):
        app = Flask(__name__)

        def multiplier(request, value):
            return {'result': value * int(request.args.get('multiplier', 1))}

        api_v1 = Api(version="v1")
        multiplier_endpoint = ApiEndpoint(
            http_method="GET",
            endpoint="/multiply/<int:value>/",
            handler=multiplier
        )
        api_v1.register_endpoint(multiplier_endpoint)

        app.register_blueprint(api_v1)

        app.config['TESTING'] = True
        self.app = app.test_client()

        resp = self.app.get('/v1/multiply/3/', content_type='application/json')
        self.assertEqual(resp.status_code, 200)

        data = json.loads(resp.data.decode(resp.charset))
        self.assertEqual(data, {
            'result': 3
        })

        resp = self.app.get('/v1/multiply/3/?multiplier=5', content_type='application/json')
        self.assertEqual(resp.status_code, 200)

        data = json.loads(resp.data.decode(resp.charset))
        self.assertEqual(data, {
            'result': 15
        })


class VersioningTestCase(unittest.TestCase):
    def setUp(self):
        self.tasks = [
            {'id': 1, 'task': 'Do the laundry'},
            {'id': 2, 'task': 'Do the dishes'},
        ]

    def test_versions_with_same_endpoints(self):
        app = Flask(__name__)

        def get_task(request):
            return self.tasks

        api_201409 = Api(version="v1")
        api_201507 = Api(version="v2")
        task_endpoint = ApiEndpoint(
            http_method="GET",
            endpoint="/task/",
            handler=get_task
        )
        api_201409.register_endpoint(task_endpoint)
        api_201507.register_endpoint(task_endpoint)

        app.register_blueprint(api_201409)
        app.register_blueprint(api_201507)

        app.config['TESTING'] = True
        self.app = app.test_client()

        resp = self.app.get('/v1/task/', content_type='application/json')
        self.assertEqual(resp.status_code, 200)

        resp = self.app.get('/v2/task/', content_type='application/json')
        self.assertEqual(resp.status_code, 200)

    def test_version_accesible_from_handler(self):
        app = Flask(__name__)

        def get_task(request):
            return {'version': request.api.version}

        api_201409 = Api(version="v1")
        api_201507 = Api(version="v2")
        task_endpoint = ApiEndpoint(
            http_method="GET",
            endpoint="/task/",
            handler=get_task
        )
        api_201409.register_endpoint(task_endpoint)
        api_201507.register_endpoint(task_endpoint)

        app.register_blueprint(api_201409)
        app.register_blueprint(api_201507)

        app.config['TESTING'] = True
        self.app = app.test_client()

        resp = self.app.get('/v1/task/', content_type='application/json')
        self.assertEqual(resp.status_code, 200)

        data = json.loads(resp.data.decode(resp.charset))
        self.assertEqual(data, {
            'version': 'v1'
        })

        resp = self.app.get('/v2/task/', content_type='application/json')
        self.assertEqual(resp.status_code, 200)

        data = json.loads(resp.data.decode(resp.charset))
        self.assertEqual(data, {
            'version': 'v2'
        })

    def test_versions_with_different_endpoints_same_url(self):
        app = Flask(__name__)

        get_tasks_v1 = mock.MagicMock(return_value={
            'id': 1, 'task': 'Do dishes'
        })
        get_tasks_v1.__name__ = 'get_tasks_v1'
        get_tasks_v2 = mock.MagicMock(return_value={
            'id': 2, 'task': 'Do laundry'
        })
        get_tasks_v2.__name__ = 'get_tasks_v2'

        api_201409 = Api(version="v1")
        api_201507 = Api(version="v2")
        api_201409.register_endpoint(ApiEndpoint(
            http_method="GET",
            endpoint="/task/",
            handler=get_tasks_v1
        ))
        api_201507.register_endpoint(ApiEndpoint(
            http_method="GET",
            endpoint="/task/",
            handler=get_tasks_v2
        ))

        app.register_blueprint(api_201409)
        app.register_blueprint(api_201507)

        app.config['TESTING'] = True
        self.app = app.test_client()

        resp = self.app.get('/v1/task/', content_type='application/json')
        self.assertEqual(resp.status_code, 200)

        data = json.loads(resp.data.decode(resp.charset))
        self.assertEqual(data, {
            'id': 1, 'task': 'Do dishes'
        })

        self.assertEqual(get_tasks_v1.call_count, 1)
        self.assertEqual(get_tasks_v2.call_count, 0)

        resp = self.app.get('/v2/task/', content_type='application/json')
        self.assertEqual(resp.status_code, 200)

        data = json.loads(resp.data.decode(resp.charset))
        self.assertEqual(data, {
            'id': 2, 'task': 'Do laundry'
        })

        self.assertEqual(get_tasks_v1.call_count, 1)
        self.assertEqual(get_tasks_v2.call_count, 1)

    def test_versions_with_different_endpoints_different_url(self):
        app = Flask(__name__)

        get_tasks = mock.MagicMock(return_value={
            'id': 1, 'task': 'Do dishes'
        })
        get_tasks.__name__ = 'get_tasks'
        get_users = mock.MagicMock(return_value={
            'id': 2, 'username': 'johndoe'
        })
        get_users.__name__ = 'get_users'

        api_201409 = Api(version="v1")
        api_201507 = Api(version="v2")
        api_201409.register_endpoint(ApiEndpoint(
            http_method="GET",
            endpoint="/task/",
            handler=get_tasks
        ))
        api_201507.register_endpoint(ApiEndpoint(
            http_method="GET",
            endpoint="/users/",
            handler=get_users
        ))

        app.register_blueprint(api_201409)
        app.register_blueprint(api_201507)

        app.config['TESTING'] = True
        self.app = app.test_client()

        resp = self.app.get('/v1/users/', content_type='application/json')
        self.assertEqual(resp.status_code, 404)

        resp = self.app.get('/v1/task/', content_type='application/json')
        self.assertEqual(resp.status_code, 200)

        data = json.loads(resp.data.decode(resp.charset))
        self.assertEqual(data, {
            'id': 1, 'task': 'Do dishes'
        })

        self.assertEqual(get_tasks.call_count, 1)
        self.assertEqual(get_users.call_count, 0)

        resp = self.app.get('/v2/task/', content_type='application/json')
        self.assertEqual(resp.status_code, 404)

        resp = self.app.get('/v2/users/', content_type='application/json')
        self.assertEqual(resp.status_code, 200)

        data = json.loads(resp.data.decode(resp.charset))
        self.assertEqual(data, {
            'id': 2, 'username': 'johndoe'
        })

        self.assertEqual(get_tasks.call_count, 1)
        self.assertEqual(get_users.call_count, 1)


class URLTestCase(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        self.tasks = [
            {'id': 1, 'task': 'Do the laundry'},
            {'id': 2, 'task': 'Do the dishes'},
            {'id': 3, 'task': 'Take the dog out'},
        ]

        def get_tasks(request):
            return self.tasks

        def get_task(request, task_id):
            return get_task_by_id(self.tasks, task_id)

        api_201409 = Api(version="v1")
        all_task_endpoint = ApiEndpoint(
            http_method="GET",
            endpoint="/task/",
            handler=get_tasks
        )
        task_endpoint = ApiEndpoint(
            http_method="GET",
            endpoint="/task/<int:task_id>/",
            handler=get_task
        )
        api_201409.register_endpoint(task_endpoint)
        api_201409.register_endpoint(all_task_endpoint)

        app.register_blueprint(api_201409)

        app.config['TESTING'] = True
        self.app = app.test_client()

    def test_get_task_by_id(self):
        resp = self.app.get('/v1/task/2/', content_type='application/json')
        self.assertEqual(resp.status_code, 200)

        data = json.loads(resp.data.decode(resp.charset))
        self.assertTrue('task' in data)
        self.assertTrue('id' in data)
        self.assertEqual(data['task'], 'Do the dishes')
        self.assertEqual(data['id'], 2)

    def test_get_all_tasks(self):
        resp = self.app.get('/v1/task/', content_type='application/json')
        self.assertEqual(resp.status_code, 200)

        data = json.loads(resp.data.decode(resp.charset))
        self.assertEqual(data, self.tasks)


class HTTPMethodsTestCase(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        self.tasks = [
            {'id': 1, 'task': 'Do the laundry'},
            {'id': 2, 'task': 'Do the dishes'}
        ]

        def get_tasks(request):
            return self.tasks

        def post_task(request):
            data = request.json
            self.tasks.append({'task': data['task']})
            return {}, 201

        def put_task(request, task_id):
            task = get_task_by_id(self.tasks, task_id)
            data = request.json
            task['task'] = data['task']
            task['id'] = data['id']
            return {}, 204

        def patch_task(request, task_id):
            task = get_task_by_id(self.tasks, task_id)
            data = request.json
            task['task'] = data['task']
            return {}, 204

        def delete_task(request, task_id):
            index = get_task_index_by_id(self.tasks, task_id)
            task = self.tasks.pop(index)
            return task

        api_201409 = Api(version="v1")
        api_201409.register_endpoint(ApiEndpoint(
            http_method="GET",
            endpoint="/task/",
            handler=get_tasks
        ))
        api_201409.register_endpoint(ApiEndpoint(
            http_method="POST",
            endpoint="/task/",
            handler=post_task
        ))
        api_201409.register_endpoint(ApiEndpoint(
            http_method="PUT",
            endpoint="/task/<int:task_id>/",
            handler=put_task
        ))
        api_201409.register_endpoint(ApiEndpoint(
            http_method="PATCH",
            endpoint="/task/<int:task_id>/",
            handler=patch_task
        ))
        api_201409.register_endpoint(ApiEndpoint(
            http_method="DELETE",
            endpoint="/task/<int:task_id>/",
            handler=delete_task
        ))

        app.register_blueprint(api_201409)

        app.config['TESTING'] = True
        self.app = app.test_client()

    def test_get(self):
        resp = self.app.get('/v1/task/', content_type='application/json')
        self.assertEqual(resp.status_code, 200)

        data = json.loads(resp.data.decode(resp.charset))
        self.assertEqual(data, self.tasks)

    def test_post(self):
        resp = self.app.post(
            '/v1/task/',
            content_type='application/json',
            data=json.dumps({'task': 'New Task!'}))
        self.assertEqual(resp.status_code, 201)

        self.assertEqual(len(self.tasks), 3)

    def test_put(self):
        tasks = self.tasks[:]

        resp = self.app.put(
            '/v1/task/2/', content_type='application/json',
            data=json.dumps({'id': 99, 'task': 'Updated Task'}))
        self.assertEqual(resp.status_code, 204)

        tasks[1]['id'] = 99
        tasks[1]['task'] = 'Updated Task'
        self.assertEqual(self.tasks, tasks)

    def test_patch(self):
        tasks = self.tasks[:]

        resp = self.app.patch(
            '/v1/task/2/', content_type='application/json',
            data=json.dumps({'task': 'Updated Task'}))
        self.assertEqual(resp.status_code, 204)

        tasks[1]['task'] = 'Updated Task'
        self.assertEqual(self.tasks, tasks)

    def test_delete(self):
        tasks, deleted_task = self.tasks[:][:1], self.tasks[:][-1]

        resp = self.app.delete(
            '/v1/task/2/', content_type='application/json')

        self.assertEqual(resp.status_code, 200)

        self.assertEqual(len(self.tasks), 1)
        self.assertEqual(self.tasks, tasks)

        data = json.loads(resp.data.decode(resp.charset))
        self.assertEqual(data, deleted_task)


class HTTPStatusCodesTestCase(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)

        def success_handler(request):
            if request.method == 'GET':
                return {}, 200
            elif request.method == 'POST':
                return {}, 201

        def conflict_handler(request):
            return {'task': 'Conflicted Task'}, 409

        api_201409 = Api(version="v1")
        api_201409.register_endpoint(ApiEndpoint(
            http_method=["GET", "POST"],
            endpoint="/",
            handler=success_handler
        ))
        api_201409.register_endpoint(ApiEndpoint(
            http_method="GET",
            endpoint="/conflict",
            handler=conflict_handler
        ))

        app.register_blueprint(api_201409)

        app.config['TESTING'] = True
        self.app = app.test_client()

    def test_different_success_codes(self):
        resp = self.app.get('/v1/', content_type='application/json')
        self.assertEqual(resp.status_code, 200)

        resp = self.app.post('/v1/', content_type='application/json')
        self.assertEqual(resp.status_code, 201)

    def test_conflict_code(self):
        resp = self.app.get('/v1/conflict', content_type='application/json')
        self.assertEqual(resp.status_code, 409)
        data = json.loads(resp.data.decode(resp.charset))
        self.assertEqual(data['task'], 'Conflicted Task')


class ExtraHeadersTestCase(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        self.tasks = [
            {'id': 1, 'task': 'Do the laundry'},
            {'id': 2, 'task': 'Do the dishes'},
        ]

        def get_tasks(request):
            return self.tasks, 200, {'Access-Control-Allow-Origin': '*'}

        def post_task(request):
            data = request.json
            self.tasks.append({'task': data['task']})
            return {}, 201, {
                'X-Special-Header': 'XXX',
                'Access-Control-Allow-Origin': '*'}

        api_201409 = Api(version="v1")
        task_endpoint = ApiEndpoint(
            http_method="GET",
            endpoint="/task/",
            handler=get_tasks
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

    def test_spec_headers_returned_by_request(self):
        "Should return spec headers if specified by the handler"
        resp = self.app.get('/v1/task/', content_type='application/json')
        self.assertEqual(
            resp.headers['Content-Type'], 'application/json')
        self.assertEqual(
            resp.headers.get('Access-Control-Allow-Origin'), '*')
        self.assertEqual(resp.status_code, 200)

        data = json.loads(resp.data.decode(resp.charset))
        self.assertEqual(len(data), 2)

    def test_custom_headers_are_returned_by_request(self):
        "Should return custom headers if specified by the handler"
        resp = self.app.post(
            '/v1/task/',
            content_type='application/json',
            data=json.dumps({'task': 'New Task!'}))
        self.assertEqual(resp.status_code, 201)

        self.assertEqual(
            resp.headers['Content-Type'], 'application/json')
        self.assertEqual(
            resp.headers.get('Access-Control-Allow-Origin'), '*')
        self.assertEqual(
            resp.headers.get('X-Special-Header'), 'XXX')

        self.assertEqual(len(self.tasks), 3)


class LogicalAPINamingTestCase(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.tasks = [
            {'id': 1, 'task': 'Do the laundry'},
            {'id': 2, 'task': 'Do the dishes'},
        ]

        def get_tasks(request):
            return self.tasks

        def post_task(request):
            data = request.json
            self.tasks.append({'task': data['task']})
            return {}, 201

        self.get_tasks = get_tasks
        self.post_task = post_task

    def test_naming_a_single_api(self):
        api_1 = Api(version="v1", name="read-only-methods")
        api_1.register_endpoint(ApiEndpoint(
            http_method="GET",
            endpoint="/task/",
            handler=self.get_tasks
        ))

        self.app.register_blueprint(api_1)
        self.app.config['TESTING'] = True

        client = self.app.test_client()
        resp = client.get('/v1/task/', content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers['Content-Type'], 'application/json')

        data = json.loads(resp.data.decode(resp.charset))
        self.assertEqual(len(data), 2)

    def test_naming_multiple_logic_apis(self):
        api_1 = Api(version="v1", name="read-only-methods")
        api_1.register_endpoint(ApiEndpoint(
            http_method="GET",
            endpoint="/task/",
            handler=self.get_tasks
        ))

        self.app.register_blueprint(api_1)

        api_2 = Api(version="v1", name="write-methods")
        api_2.register_endpoint(ApiEndpoint(
            http_method="POST",
            endpoint="/task/",
            handler=self.post_task
        ))
        self.app.register_blueprint(api_2)
        self.app.config['TESTING'] = True

        client = self.app.test_client()

        # Testing GET
        resp = client.get('/v1/task/', content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers['Content-Type'], 'application/json')

        data = json.loads(resp.data.decode(resp.charset))
        self.assertEqual(len(data), 2)

        # Testing POST
        resp = client.post(
            '/v1/task/',
            content_type='application/json',
            data=json.dumps({'task': 'New Task!'}))

        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.headers['Content-Type'], 'application/json')
        self.assertEqual(len(self.tasks), 3)
