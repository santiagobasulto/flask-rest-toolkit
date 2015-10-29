import simplejson as json


class Serializer(object):
    def get_content_type(self):
        raise NotImplementedError()

    def serialize(self, content):
        raise NotImplementedError()

    def deserialize(self, content):
        raise NotImplementedError()


class JsonSerializer(Serializer):
    def get_content_type(self):
        return "application/json"

    def serialize(self, content):
        return json.dumps(content)


class TextSerializer(Serializer):
    def get_content_type(self):
        return "text/plain"

    def serialize(self, content):
        return content


class JavascriptSerializer(TextSerializer):
    def get_content_type(self):
        return "application/javascript"
