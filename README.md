**Work in progress. Everything is subject to changes**

# Flask Rest Toolkit

A set of tools to create simple Flask REST web services and APIs.

### Why not just Flask-RESTful

[Flask-restful](https://github.com/flask-restful/flask-restful) is great. I've used it and I definitively love it. But it's a full fledged framework to build APIs.
This toolkit is conceived just as a set of tools to ease development of a simple REST API. Plus, it's not tied to resources and it's really easy to extend.

### Basic usage

I recommend checking the `tests/` directory for every possible usage. But this would be the minimum required to build an API:

```python
app = Flask("TODO App")
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

api_v1 = Api(version="v1")
api_v1.register_endpoint(ApiEndpoint(
    http_method="GET",
    endpoint="/task/",
    handler=get_task
))

api_v1.register_endpoint(ApiEndpoint(
    http_method="POST",
    endpoint="/task/",
    handler=post_task
))

app.register_blueprint(api_v1)
```

Flask REST toolkit supports serialization. The default serialization method is JSON. We plan to add more serialization options and make them configurable in an API and EndPoint level.

### How it works

**1) Create an API**

```python
api = Api(version="v1")
```

**2) Write your function**

```python
def get_tasks(request):
   return [{'id': 1, 'task': 'Do the dishes'}]
```

Functions receive a _request_ as first parameter and must return `data[, status_code, additional_headers]`. Full example:

```python
def get_tasks(request):
   return [{'id': 1, 'task': 'Do the dishes'}], 201, {'X-API-version': 'v1'}
```

**3) Hook up an endpoint**

```python
api.register_endpoint(ApiEndpoint(
    http_method="GET",
    endpoint="/task/",
    handler=get_task
))
```

Every endpoint receives an _HTTP method_ for which it'll act, a _path_ and a _function_ (previous step) that will be executed.

**4) Hook up the API to the App. (this will probably change)**

```python
app.register_blueprint(api_v1)
```

### Authentication and Authorization

Flask REST toolkit support a simple Auth scheme along with several helpful classes to ease your development. To use it just indicate the authentication class in your endpoint:

```python
api_v1.register_endpoint(ApiEndpoint(
    http_method="GET",
    endpoint="/task/",
    handler=get_task,
    authentication=YourAuthenticationClass()
))
```

An authentication class can must implement two methods:

* `def authenticate(self, request)`
* `def authorize(self, request)`

If any method returns None the user is considered to pass your auth method. On the contrary, you can raise a Werkzeug exception to flag the user is not authorized to access a given resource. Example:

```python
from werkzeug.exceptions import Unauthorized, Forbidden

class YourAuthenticationClass(object):
    "Dummy example to show how auth works"
    ADMINS = [
        '10.160.156.24', '50.170.200.24'
    ]
    def authenticate(self, request):
        if request.remote_addr != 10.160.156.24:
            raise Unauthorized()

    def authorize(self, request):
        if request.path.startswith('/admin/') and request.remote_addr not in self.ADMINS:
            raise Forbidden()
```

There are a few classes to ease development. Currently the most interesting one is `flask_rest_toolkit.auth.BasicAuth`. Check out the source code for more details.

### Middleware

Each endpoint can define a list of middleware classes that **will be invoked in order before the request**. Each middleware must implement a `process_request` method that will take place before the actual endpoint handler is invoked.

Simple example:

```python
from werkzeug.exceptions import Forbidden

class UserMiddleware(object):
    def process_request(self, request):
        request.user = User(...)

class AdminMiddleware(object):
    def process_request(self, request):
        if request.user.role != 'admin':
            raise Forbidden()

api_v1.register_endpoint(ApiEndpoint(
    http_method="GET",
    endpoint="/admin/task/",
    handler=get_task_admin,
    middleware=[UserMiddleware, AdminMiddleware]
))

```

Check `tests/test_middleware.py` for more details.

### Expected exceptions

An endpoint could possibly raise an exception that is expected. You can specify a list of exceptions to expect and how to react to them. Example:

We have a simple method `register_user` tied to an endpoint. That method could raise a known and expected exception when the email used is already present in the database. You can specify how to react to that exception if it happens in your endpoint.

```python
def register_user(request):
    if email_exists(request.json['email']):
        raise UserEmailAlreadyExistsException()
    if len(request.json['password']) < 5:
        raise PasswordNotStrongEnoughException()

api_v1.register_endpoint(ApiEndpoint(
    http_method="POST",
    endpoint="/user/",
    handler=register_user,
    exceptions=[
        (UserEmailAlreadyExistsException, 409),  # Conflict
        (PasswordNotStrongEnoughException, 400)
    ]
))
```

In that case when a `UserEmailAlreadyExistsException` happens a 409 will be returned to the client.

**All the exceptions not specified there will be treated as errors and return a 500**

You can also work with hierarchies of exceptions. Please check tests for more details: `tests/errors.py`

# Run tests

    $ python setup.py test
