import json
import unittest

from flask import Flask

from flask_rest_toolkit.api import Api
from flask_rest_toolkit.endpoint import ApiEndpoint


def get_task_index_by_id(tasks, task_id):
    return ([t['id'] for t in tasks]).index(task_id)


def get_task_by_id(tasks, task_id):
    return tasks[get_task_index_by_id(tasks, task_id)]


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

        api_201409 = Api(version="v201409")
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
        resp = self.app.get('/v201409/task/', content_type='application/json')
        self.assertEqual(resp.status_code, 200)

        data = json.loads(resp.data.decode(resp.charset))
        self.assertEqual(len(data), 2)

        self.assertEqual(resp.headers['Content-Type'], 'application/json')

    def test_simple_POST(self):
        resp = self.app.post(
            '/v201409/task/',
            content_type='application/json',
            data=json.dumps({'task': 'New Task!'}))
        self.assertEqual(resp.status_code, 201)

        resp = self.app.get('/v201409/task/', content_type='application/json')
        self.assertEqual(resp.status_code, 200)

        data = json.loads(resp.data.decode(resp.charset))
        self.assertEqual(len(data), 3)

        self.assertEqual(resp.headers['Content-Type'], 'application/json')


class VersioningTestCase(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        tasks = [
            {'id': 1, 'task': 'Do the laundry'},
            {'id': 2, 'task': 'Do the dishes'},
        ]

        def get_task(request):
            return tasks

        api_201409 = Api(version="v201409")
        api_201507 = Api(version="v201507")
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

    def test_versions(self):
        resp = self.app.get('/v201409/task/', content_type='application/json')
        self.assertEqual(resp.status_code, 200)

        resp = self.app.get('/v201507/task/', content_type='application/json')
        self.assertEqual(resp.status_code, 200)


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

        api_201409 = Api(version="v201409")
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
        resp = self.app.get('/v201409/task/2/', content_type='application/json')
        self.assertEqual(resp.status_code, 200)

        data = json.loads(resp.data.decode(resp.charset))
        self.assertTrue('task' in data)
        self.assertTrue('id' in data)
        self.assertEqual(data['task'], 'Do the dishes')
        self.assertEqual(data['id'], 2)

    def test_get_all_tasks(self):
        resp = self.app.get('/v201409/task/', content_type='application/json')
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

        api_201409 = Api(version="v201409")
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
        resp = self.app.get('/v201409/task/', content_type='application/json')
        self.assertEqual(resp.status_code, 200)

        data = json.loads(resp.data.decode(resp.charset))
        self.assertEqual(data, self.tasks)

    def test_post(self):
        resp = self.app.post(
            '/v201409/task/',
            content_type='application/json',
            data=json.dumps({'task': 'New Task!'}))
        self.assertEqual(resp.status_code, 201)

        self.assertEqual(len(self.tasks), 3)

    def test_put(self):
        tasks = self.tasks.copy()

        resp = self.app.put(
            '/v201409/task/2/', content_type='application/json',
            data=json.dumps({'id': 99, 'task': 'Updated Task'}))
        self.assertEqual(resp.status_code, 204)

        tasks[1]['id'] = 99
        tasks[1]['task'] = 'Updated Task'
        self.assertEqual(self.tasks, tasks)

    def test_patch(self):
        tasks = self.tasks.copy()

        resp = self.app.patch(
            '/v201409/task/2/', content_type='application/json',
            data=json.dumps({'task': 'Updated Task'}))
        self.assertEqual(resp.status_code, 204)

        tasks[1]['task'] = 'Updated Task'
        self.assertEqual(self.tasks, tasks)

    def test_delete(self):
        tasks, deleted_task = self.tasks.copy()[:1], self.tasks.copy()[-1]

        resp = self.app.delete(
            '/v201409/task/2/', content_type='application/json')

        self.assertEqual(resp.status_code, 200)

        self.assertEqual(len(self.tasks), 1)
        self.assertEqual(self.tasks, tasks)

        data = json.loads(resp.data.decode(resp.charset))
        self.assertEqual(data, deleted_task)


class HTTPStatusCodeSTestCase(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)

        def success_handler(request):
            if request.method == 'GET':
                return {}, 200
            elif request.method == 'POST':
                return {}, 201

        def conflict_handler(request):
            return {'task': 'Conflicted Task'}, 409

        api_201409 = Api(version="v201409")
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
        resp = self.app.get('/v201409/', content_type='application/json')
        self.assertEqual(resp.status_code, 200)

        resp = self.app.post('/v201409/', content_type='application/json')
        self.assertEqual(resp.status_code, 201)

    def test_conflict_code(self):
        resp = self.app.get('/v201409/conflict', content_type='application/json')
        self.assertEqual(resp.status_code, 409)
        data = json.loads(resp.data.decode(resp.charset))
        self.assertEqual(data['task'], 'Conflicted Task')


class ExceptionsTestCase(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)

        def raises_dummy_exception(request):
            exc_type = request.args.get('exc_type')

            if exc_type == 'subclass':
                raise DummyExceptionSubclass()
            elif exc_type == 'other-subclass':
                raise DummyExceptionOtherSubclass()

            raise DummyException()

        api_201409 = Api(version="v201409")
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
            '/v201409/dummy-exception?exc_type=subclass',
            content_type='application/json')
        self.assertEqual(resp.status_code, 406)

        resp = self.app.get(
            '/v201409/dummy-exception?exc_type=other-subclass',
            content_type='application/json')
        self.assertEqual(resp.status_code, 409)

        resp = self.app.get(
            '/v201409/dummy-exception',
            content_type='application/json')
        self.assertEqual(resp.status_code, 400)


class ExtraHeadersTestCase(unittest.TestCase):
    pass
