import cgi
import os
import os.path
import re
import subprocess
import tempfile

from zope.interface import implements

from Products.PortalTransforms.interfaces import ITransform

R_BINARY = "/usr/bin/R"
FIG_BINARY = "/usr/bin/fig2dev"
TIMEOUT = "3m"
TIMEOUT_BINARY = "/usr/bin/timeout"


class ScriptToHtml(object):
    """
    Run script, generate SVG and wrap that as HTML
    """
    implements(ITransform)
    __name__ = "script_to_html"
    inputs = ('text/r', 'text/x-gnuplot', 'image/x-xfig',)
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

    def _rConvert(self, script):
        if not os.path.isfile(R_BINARY):
            raise ValueError("Binary %s not available" % R_BINARY)
        if not os.path.isfile(TIMEOUT_BINARY):
            raise ValueError("Binary %s not available" % TIMEOUT_BINARY)

        tmpSvg = tempfile.mktemp('.svg')
        p = subprocess.Popen(
            [TIMEOUT_BINARY, TIMEOUT, R_BINARY, '--vanilla', '--quiet'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        (out, err) = p.communicate(
            input='svg("%s", width= 4, height=4, onefile = TRUE, bg = "transparent")\n\n%s' % (
                tmpSvg,
                script,
            ),
        )
        if not os.path.exists(tmpSvg) and err:
            raise RuntimeError("No SVG generated:-\n" + err)
        if not os.path.exists(tmpSvg):
            return '<pre class="script output">%s</pre>' % cgi.escape(str(out))

        # Read SVG into string
        with open(tmpSvg, 'r') as f:
            out = f.read()
        os.remove(tmpSvg)

        # Remove XML declaration
        out = re.sub(r'<\?xml.*?\?>', '', out)

        # Glyph IDs should be unique
        out = re.sub(
            r'(glyph\d+-\d+)',
            re.sub(r'\W', '', tmpSvg) + r'-\1',
            out,
        )
        return out

    def convert(self, orig, data, **kwargs):
        # NB: This potentially hugely expensive, but portal_transforms has a
        # cache keyed on the content that lasts an hour.
        try:
            if orig.strip() == "":
                # Don't bother translating empty strings
                data.setData("")
            if kwargs['mimetype'] in ('text/r', 'text/R',):
                data.setData(self._rConvert(orig))
            else:
                raise ValueError("Unknown MIME type %s" % kwargs['mimetype'])
        except Exception as e:
            data.setData('<pre class="script error">%s</pre>' % (
                cgi.escape(str(e)),
            ))
        data.setData(data.getData() + '<pre class="code-block"><code>%s</code></pre>' % cgi.escape(orig))
        return data


def register():
    return ScriptToHtml()
