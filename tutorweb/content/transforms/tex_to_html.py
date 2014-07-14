import cgi
import os.path
import subprocess

from zope.interface import implements

from plone.intelligenttext.transforms import convertWebIntelligentPlainTextToHtml

from Products.PortalTransforms.interfaces import ITransform

TTM_BINARY = '/usr/bin/ttm'


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
        if os.path.isfile(TTM_BINARY):
            p = subprocess.Popen(
                [
                    TTM_BINARY,
                    '-a',   # Try to convert picture elements
                    '-e3',  # inline epsfbox w/no icon
                    '-r',   # Don't output a pre/postamble
                    '-u',   # Unicode please
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            (out, err) = p.communicate(input=orig)
            if '****' in err:
                # Probably an error, show it.
                data.setData('<pre class="ttm-output error">%s</pre>\n<div class="ttm-output">%s</div>' % (
                    cgi.escape(err.strip()),
                    out.strip(),
                ))
            else:
                data.setData('<div class="ttm-output">%s</div>' % out.strip())
        else:
            data.setData('<div class="parse-as-tex">' +
                         convertWebIntelligentPlainTextToHtml(orig) +
                         '</div>')
        return data


def register():
    return TexToHtml()
