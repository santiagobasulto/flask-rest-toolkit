from werkzeug.exceptions import Unauthorized


class AuthenticatedException(Exception):
    pass


class AuthenticationStrategy(object):
    """Base authentication class. Every subclass
    should implement both methods:

    * def authenticate(self, request)
    * def authorize(self, request)

    Every method receives the request and should either
    return None (if it was successful) or raise an Exception
    if it failed.
    """
    def authenticate(self, request):
        raise NotImplementedError()

    def authorize(self, request):
        return NotImplementedError()


class NoAuthenticationStrategy(object):
    def authenticate(self, request):
        return None


class NoAuthorizationStrategy(object):
    def authorize(self, request):
        return None


class BasicAuth(AuthenticationStrategy, NoAuthorizationStrategy):
    def __init__(self, is_valid_user):
        self.is_valid_user = is_valid_user

    def authenticate(self, request):
        valid_user = request.authorization and self.is_valid_user(
            request.authorization.get('username'),
            request.authorization.get('password'))
        if not valid_user:
            raise Unauthorized()


class And(AuthenticationStrategy):
    def __init__(self, *auth_strategies):
        self.auth_stratgies = auth_strategies

    def authenticate(self, request):
        [auth.authenticate(request) for auth in self.auth_stratgies]

    def authorize(self, request):
        [auth.authorize(request) for auth in self.auth_stratgies]
