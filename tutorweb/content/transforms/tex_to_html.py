from zope.interface import implements

from plone.intelligenttext.transforms import convertWebIntelligentPlainTextToHtml

from Products.PortalTransforms.interfaces import ITransform

class TexToHtml(object):
    """
    Treat TeX as intelligent text, wrap in a div to point
    mathJax at. Not strictly a transform, but good enough.
    """
    implements(ITransform)
    __name__ = "tex_to_html"
    inputs = ('text/x-tex',)
    output = "text/html"

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
        data.setData('<div class="parse-as-tex">' +
            convertWebIntelligentPlainTextToHtml(orig) +
            '</div>')
        return data

def register():
    return TexToHtml()
