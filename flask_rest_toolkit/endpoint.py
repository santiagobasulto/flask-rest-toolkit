class ApiEndpoint(object):
    def __init__(self, http_method, endpoint, handler):
        self.http_method = http_method
        self.endpoint = endpoint
        self.handler = handler
