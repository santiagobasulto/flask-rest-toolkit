from flask import Flask

from flask_rest_toolkit.api import Api
from flask_rest_toolkit.endpoint import ApiEndpoint

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
    print(tasks)
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


# from flask import Blueprint
# simple_page = Blueprint('simple_page', __name__)


# def hello_world():
#     return 'Hello World!'

# simple_page.add_url_rule('/v201409/task/', 'index', hello_world)
# app.register_blueprint(simple_page)

if __name__ == "__main__":
    app.run()
