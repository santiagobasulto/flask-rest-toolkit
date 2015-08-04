def unpack(value):
    """
    Return a three tuple of data, code, and headers.
    Credits Flask-restful
    https://github.com/flask-restful/flask-restful/blob/master/flask_restful/__init__.py
    """
    if not isinstance(value, tuple):
        return value, 200, {}

    try:
        data, code, headers = value
        return data, code, headers
    except ValueError:
        pass

    try:
        data, code = value
        return data, code, {}
    except ValueError:
        pass

    return value, 200, {}
