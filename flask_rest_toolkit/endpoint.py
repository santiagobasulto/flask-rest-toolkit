class ApiEndpoint(object):
    def __init__(self, http_method, endpoint, handler, exceptions=None):
        self.http_method = http_method
        self.endpoint = endpoint
        self.handler = handler
        self.exceptions = exceptions or []
