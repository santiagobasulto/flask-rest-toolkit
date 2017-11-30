from werkzeug.wrappers import Response as ResponseBase

from flask import Blueprint, request, make_response

from . import serializers
from . import exceptions

from .utils import unpack

SERIALIZERS = {
    'json': serializers.JsonSerializer,
    'text': serializers.TextSerializer,
    'javascript': serializers.JavascriptSerializer,
}


class ViewHandler(object):
    def __init__(self, endpoint, api):
        self.endpoint = endpoint
        self.api = api

    def process_request(self, request, *args, **kwargs):
        try:
            for middleware_class in self.endpoint.middleware:
                middleware = middleware_class()
                method = getattr(middleware, 'process_request')
                result = method(request, *args, **kwargs)
                if result:
                    return result
        except Exception as exc:
            return self._handle_exception(
                exc,
                self.endpoint.exceptions + (getattr(
                    middleware_class, 'EXCEPTIONS', [])))

    def _get_serializer(self):
        serializer = self.endpoint.serializer or self.api.serializer
        if serializer not in SERIALIZERS:
            raise exceptions.InvalidSerializerException(
                "{} is an invalid serializer".format(
                    serializer))
        return SERIALIZERS[serializer]()

    def build_response(self, output):
        data, code, headers = unpack(output)

        if isinstance(data, ResponseBase):
            return data

        serializer = self._get_serializer()

        response = make_response(
            serializer.serialize(data),
            code
        )

        response.headers['Content-Type'] = headers.pop(
            'Content-Type', serializer.get_content_type())
        response.headers.extend(headers or {})

        return response

    def _handle_exception(self, exc, exception_list):
        for exc_class, status_code in exception_list:
            if exc_class == exc.__class__:
                if hasattr(exc, 'data'):
                    return self.build_response((exc.data, status_code))
                return make_response("", status_code)
        raise exc

    def __call__(self, *args, **kwargs):
        if self.endpoint.authentication:
            self.endpoint.authentication.authenticate(request)

        output = self.process_request(request, *args, **kwargs)

        if not output:
            request.api = self.api
            try:
                output = self.endpoint.handler(request, *args, **kwargs)
            except Exception as exc:
                return self._handle_exception(exc, self.endpoint.exceptions)

        return self.build_response(output)


class Api(Blueprint):
    def __init__(self, version=None, name=None, serializer='json'):
        super(Api, self).__init__((version or '') + (name or ''), __name__)
        self.version = version
        self.endpoints = []
        self.serializer = serializer

    def register_endpoint(self, endpoint):
        self.endpoints.append(endpoint)
        if self.version:
            url = '/{version}{endpoint}'.format(
                version=self.version,
                endpoint=endpoint.endpoint)
        else:
            url = '{endpoint}'.format(
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
