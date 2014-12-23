from zope.interface import implements

from Products.PortalTransforms.interfaces import ITransform


class TextToTex(object):
    """
    text/plain to tex is a ~noop
    """
    implements(ITransform)
    __name__ = "text_to_tex"
    inputs = ('text/plain',)
    output = "text/x-tex"

    def __init__(self, name=None):
        if name:
            self.__name__ = name

    def name(self):
        return self.__name__

    def __getattr__(self, attr):
        if attr in self.config:
            return self.config[attr]
        raise AttributeError(attr)

    def convert(self, orig, data, **kwargs):
        # "encoding" is both the encoding of orig, and the expected encoding of
        # the data in data.
        if kwargs['encoding'] not in ['utf-8', 'utf_8', 'U8', 'UTF', 'utf8']:
            raise ValueError('Only support unicode, not %s' % kwargs['encoding'])

        # Escape special characters
        out = orig
        out = out.replace('\\', '\\textbackslash')
        out = out.replace('&', '\\&')
        out = out.replace('%', '\\%')
        out = out.replace('$', '\\$')
        out = out.replace('#', '\\#')
        out = out.replace('_', '\\_')
        out = out.replace('{', '\\{')
        out = out.replace('}', '\\}')
        out = out.replace('~', '\\textasciitilde')
        out = out.replace('^', '\\textasciicircum')
        data.setData(out)
        return data


def register():
    return TextToTex()
