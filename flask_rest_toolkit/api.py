from werkzeug.wrappers import Response as ResponseBase

from flask import Blueprint, request, make_response

from .serializers import JsonSerializer

from .utils import unpack

SERIALIZERS = {
    'json': JsonSerializer
}


class ViewHandler(object):
    def __init__(self, endpoint, api):
        self.endpoint = endpoint
        self.api = api

    def process_request(self, request):
        for middleware_class in self.endpoint.middleware:
            middleware = middleware_class()
            method = getattr(middleware, 'process_request')
            result = method(request)
            if result:
                return result

    def build_response(self, output):
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

    def __call__(self, *args, **kwargs):
        if self.endpoint.authentication:
            self.endpoint.authentication.authenticate(request)

        try:
            output = self.process_request(request)

            if not output:
                request.api = self.api
                output = self.endpoint.handler(request, *args, **kwargs)

        except Exception as exc:
            for exc_class, status_code in self.endpoint.exceptions:
                if exc_class == exc.__class__:
                    if hasattr(exc, 'data'):
                        return self.build_response((exc.data, status_code))
                    return make_response("", status_code)
            raise exc

        return self.build_response(output)


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

        view_name = "{method}-{path}-{view}".format(
            method=str(methods), path=url, view=endpoint.handler.__name__
        )

        self.add_url_rule(
            url,
            view_name,
            ViewHandler(endpoint=endpoint, api=self),
            methods=methods
        )
