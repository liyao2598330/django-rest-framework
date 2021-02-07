"""
The Response class in REST framework is similar to HTTPResponse, except that
it is initialized with unrendered data, instead of a pre-rendered string.

The appropriate renderer is called during Django's template response rendering.
"""
from http.client import responses

from django.template.response import SimpleTemplateResponse

from rest_framework.serializers import Serializer


class Response(SimpleTemplateResponse):
    """
    An HttpResponse that allows its data to be rendered into
    arbitrary media types.
    """

    def __init__(self, data=None, status=None,
                 template_name=None, headers=None,
                 exception=False, content_type=None):
        """
        Alters the init arguments slightly.
        For example, drop 'template_name', and instead use 'data'.

        Setting 'renderer' and 'media_type' will typically be deferred,
        For example being set automatically by the `APIView`.
        """
        super().__init__(None, status=status)

        if isinstance(data, Serializer):
            msg = (
                'You passed a Serializer instance as data, but '
                'probably meant to pass serialized `.data` or '
                '`.error`. representation.'
            )
            raise AssertionError(msg)

        self.data = data
        self.template_name = template_name
        self.exception = exception
        self.content_type = content_type

        if headers:
            for name, value in headers.items():
                self[name] = value

    @property
    def rendered_content(self):
        renderer = getattr(self, 'accepted_renderer', None)
        accepted_media_type = getattr(self, 'accepted_media_type', None)
        context = getattr(self, 'renderer_context', None)

        assert renderer, ".accepted_renderer not set on Response"
        assert accepted_media_type, ".accepted_media_type not set on Response"
        assert context is not None, ".renderer_context not set on Response"
        context['response'] = self

        media_type = renderer.media_type
        charset = renderer.charset
        content_type = self.content_type

        if content_type is None and charset is not None:
            content_type = "{}; charset={}".format(media_type, charset)
        elif content_type is None:
            content_type = media_type
        self['Content-Type'] = content_type

        ret = renderer.render(self.data, accepted_media_type, context)
        if isinstance(ret, str):
            assert charset, (
                'renderer returned unicode, and did not specify '
                'a charset value.'
            )
            return ret.encode(charset)

        if not ret:
            del self['Content-Type']

        return ret

    @property
    def status_text(self):
        """
        Returns reason text corresponding to our HTTP response status code.
        Provided for convenience.
        """
        return responses.get(self.status_code, '')

    def __getstate__(self):
        """
        Remove attributes from the response that shouldn't be cached.
        """
        state = super().__getstate__()
        for key in (
            'accepted_renderer', 'renderer_context', 'resolver_match',
            'client', 'request', 'json', 'wsgi_request'
        ):
            if key in state:
                del state[key]
        state['_closable_objects'] = []
        return state


class HttpResponseMessage:
    """
        根据不同的http状态码，设置统一的默认返回信息
        https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status
    """

    http_default = '服务可能发生了一点点小问题，程序员哥哥正在加班处理..'

    http_200 = 'success'
    http_201 = '资源创建成功'

    http_400 = '无法执行您的操作，可能是参数等必要条件不足，请按流程重新执行'
    http_401 = '糟糕，您的登陆信息失效或异常，可重新登陆后在尝试'
    http_403 = '糟糕，您没有权限访问此资源'
    http_404 = '您请求的资源不存在'
    http_405 = '不支持此方式请求，请以正确的姿势进入'
    http_429 = '请求过快，请降低访问频率'

    http_500 = '处理异常，服务器可能抽风了'

    def __call__(self, code: int, *args, **kwargs) -> dict:
        """
            根据http状态码返回默认信息和表情
        :param code: http_status_code
        :return: eg. {'msg': 'ok', 'mood': '(ノ￣ω￣)ノ'}
        """
        return self.get_message(code)

    @classmethod
    def get_message(cls, code: int) -> str:
        """
            根据http状态码返回默认信息和表情
        :param code: http_status_code
        :return: eg. {'msg': 'ok', 'mood': '(ノ￣ω￣)ノ'}
        """
        assert isinstance(code, int) and 200 <= code < 600, 'code Must be a standard HTTP status code'
        message = getattr(cls, 'http_%s' % code) if hasattr(cls, 'http_%s' % code) else cls.http_default
        return message
