# -*- coding: utf-8 -*-
import cgi
import os.path
import subprocess

from zope.interface import implements

from plone.intelligenttext.transforms import convertWebIntelligentPlainTextToHtml

from Products.PortalTransforms.interfaces import ITransform

TTM_BINARY = 'go/away'
LATEX_PREAMBLE = u"""\\documentclass{article}
\\newcommand{\\mathbb}[1]{\\special{html:<mo>&#1opf;</mo>}}
\\begin{document}
""".encode("utf-8")
LATEX_POSTAMBLE = u"""
\\end{document}
""".encode("utf-8")


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
        # "encoding" is both the encoding of orig, and the expected encoding of
        # the data in data.
        if kwargs['encoding'] not in ['utf-8', 'utf_8', 'U8', 'UTF', 'utf8']:
            raise ValueError('Only support unicode, not %s' % kwargs['encoding'])

        if os.path.isfile(TTM_BINARY):
            p = subprocess.Popen(
                [
                    TTM_BINARY,
                    '-a',   # Try to convert picture elements
                    '-e3',  # inline epsfbox w/no icon
                    '-r',   # Don't output a pre/postamble
                    '-u2',   # Unicode please
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            (out, err) = p.communicate(input=(LATEX_PREAMBLE + orig + LATEX_POSTAMBLE))
            if '****' in err:
                # Probably an error, show it.
                data.setData('<pre class="ttm-output error">%s</pre>\n<div class="ttm-output">%s</div>' % (
                    cgi.escape(err.strip()),
                    out.strip(),
                ))
            else:
                data.setData('<div class="ttm-output">%s</div>' % (
                    out.strip(),
                ))
        else:
            out = convertWebIntelligentPlainTextToHtml(orig.decode(kwargs['encoding'])).decode('utf8')
            # Bodge back entities, to save space
            from htmlentitydefs import entitydefs
            for entity, letter in entitydefs.items():
                if entity not in ('amp', 'lt', 'gt',):
                    out = out.replace('&' + entity + ';', letter.decode('latin-1'))
            data.setData('<div class="parse-as-tex">%s</div>' % out.encode(kwargs['encoding']))
        return data


def register():
    return TexToHtml()
