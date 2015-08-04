from werkzeug.wrappers import Response as ResponseBase

from flask import Blueprint, request, make_response
from flask import Response

from .serializers import JsonSerializer

from .utils import unpack

SERIALIZERS = {
    'json': JsonSerializer
}


class ViewHandler(object):
    def __init__(self, endpoint):
        self.endpoint = endpoint

    def __call__(self, *args, **kwargs):
        output = self.endpoint.handler(request, *args, **kwargs)

        if isinstance(output, ResponseBase):
            return output

        data, code, headers = unpack(output)
        serializer = JsonSerializer()

        response = make_response(
            serializer.serialize(data),
            code
        )
        response.headers.extend(headers or {})
        response.headers['Content-Type'] = JsonSerializer().get_content_type()
        return response


class Api(Blueprint):
    def __init__(self, version=None, serializer='json'):
        super(Api, self).__init__(version, __name__)
        self.version = version
        self.endpoints = []
        self.serializer = SERIALIZERS[serializer]()

    def register_endpoint(self, endpoint):
        self.endpoints.append(endpoint)

        url = '/{version}{endpoint}'.format(
            version=self.version,
            endpoint=endpoint.endpoint)

        methods = endpoint.http_method
        if not isinstance(endpoint.http_method, (list, tuple)):
            methods = [endpoint.http_method]

        self.add_url_rule(
            url,
            endpoint.handler.__name__,
            ViewHandler(endpoint=endpoint),
            methods=methods
        )
