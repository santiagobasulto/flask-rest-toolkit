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
        try:
            output = self.endpoint.handler(request, *args, **kwargs)
        except Exception as exc:
            for exc_class, status_code in self.endpoint.exceptions:
                if exc_class == exc.__class__:
                    return make_response("", status_code)
            raise exc

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

        view_name = "{path}-{view}".format(
            path=url, view=endpoint.handler.__name__
        )

        self.add_url_rule(
            url,
            view_name,
            ViewHandler(endpoint=endpoint),
            methods=methods
        )
