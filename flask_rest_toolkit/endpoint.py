class ApiEndpoint(object):
    def __init__(self, http_method, endpoint,
                 handler, exceptions=None, authentication=None,
                 middleware=None):
        self.http_method = http_method
        self.endpoint = endpoint
        self.handler = handler
        self.authentication = authentication

        self.exceptions = exceptions or []
        self.middleware = middleware or []
