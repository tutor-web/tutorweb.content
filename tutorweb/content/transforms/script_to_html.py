import cgi
import os
import os.path
import re
import subprocess
import tempfile
import urllib2

from zope.interface import implements

from Products.PortalTransforms.interfaces import ITransform

R_BINARY = "/usr/bin/R"
FIG_BINARY = "/usr/bin/fig2dev"
GNU_BINARY = "/usr/bin/gnuplot"
TIMEOUT = "3m"
TIMEOUT_BINARY = "/usr/bin/timeout"


class ScriptToMarkup(object):
    implements(ITransform)
    inputs = ('text/r', 'text/x-uri', 'text/x-gnuplot', 'image/x-xfig',)

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
        tmpFile = tempfile.mktemp()
        preamble = {
            'text/x-tex': 'postscript(file="%s", paper="special", width=10, height=10, horizontal=FALSE)\n' % tmpFile,
            'text/html': 'svg("%s", width= 4, height=4, onefile = TRUE, bg = "transparent")\n' % tmpFile,
        }

        return self._formatOutput(self._runProgram(
            [R_BINARY, '--vanilla', '--quiet'],
            "%s\n%s" % (preamble[self.output], script),
            readFile=tmpFile,
        ))

    def _figConvert(self, script):
        preamble = {'text/x-tex': 'eps', 'text/html': 'svg'}

        return self._formatOutput(self._runProgram(
            [FIG_BINARY, '-L', preamble[self.output]],
            script,
        ))

    def _gnuConvert(self, script):
        tmpFile = tempfile.mktemp()
        preamble = {
            'text/x-tex': """
set terminal epslatex color""",
            'text/html': """
set terminal svg \
    size 410,250 \
    fname 'Helvetica Neue, Helvetica, Arial, sans-serif' \
    fsize '9' rounded dashed""",
        }

        return self._formatOutput(self._runProgram(
            [GNU_BINARY, '--vanilla', '--quiet'],
            "%s\nset output '%s'\n%s" % (preamble[self.output], tmpFile, script),
            readFile=tmpFile,
        ))

    def _urlConvert(self, script):
        # Fetch a URL, turn it into an <img>, not quite a script but meh
        #TODO: What about relative URLs? What are they relative to?
        if self.output == 'text/html':
            # Short-cut: just link to source of image
            return '<img src="%s" />' % script
        else:
            # Fetch image, and format it as a data URL
            resp = urllib2.urlopen(urllib2.Request(script))
            return self._formatOutput(":".join([
                "data",
                resp.info().type,
                "base64,%s" % resp.read().encode("base64").replace("\n", ""),
            ]))

    def _runProgram(self, command, input, readFile=None):
        for b in [TIMEOUT_BINARY, command[0]]:
            if not os.path.isfile(b):
                raise ValueError("Binary %s not available" % b)

        p = subprocess.Popen(
            [TIMEOUT_BINARY, TIMEOUT] + command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        (out, err) = p.communicate(input)
        exit_code = p.wait()

        if exit_code == 124:
            raise RuntimeError("Script took too long")
        elif exit_code != 0:
            raise RuntimeError("Script produced error:-\n%s" % (err))

        if readFile and os.path.exists(readFile):
            # Read in output file if it exists
            with open(readFile, 'r') as f:
                out = f.read()
            os.remove(readFile)

        return out

    def _formatOutput(self, content, isError=False):
        if isError:
            if self.output == "text/html":
                content = '<pre class="script error">%s</pre>' % cgi.escape(str(content))
            elif self.output == "text/x-tex":
                content = "\\begin{verbatim}ERROR: %s\\end{verbatim}" % content  #TODO: Escaping

        elif content.strip().endswith("</svg>"):
            if self.output == "text/html":
                # Remove XML declaration
                content = re.sub(r'^.*?(<svg)', r'\1', content, flags=re.DOTALL + re.MULTILINE)

                # Glyph IDs should be unique
                tmp = tempfile.mktemp()
                content = re.sub(
                    r'(glyph\d+-\d+)',
                    re.sub(r'\W', '', tmp) + r'-\1',
                    content,
                )
            elif self.output == "text/x-tex":
                raise NotImplemented

        elif content.startswith("data:"):
            if self.output == "text/html":
                content = '<img src="%s" />' % content
            elif self.output == "text/x-tex":
                content = "\\includegraphicsdata{%s}" % content

        elif content.strip().endswith("%EOF") and "%!PS-Adobe" in content:
            if self.output == "text/html":
                raise NotImplmented
            elif self.output == "text/x-tex":
                content = "\\includegraphicsdata{%s}" % ":".join([
                    "data",
                    "application/postscript",
                    "base64,%s" % content.encode("base64").replace("\n", ""),
                ])

        else:
            if self.output == "text/html":
                content = '<pre class="script output">%s</pre>' % cgi.escape(str(content))
            elif self.output == "text/x-tex":
                content = "\\begin{verbatim}%s\\end{verbatim}" % content  #TODO: Escaping

        return content

    def convert(self, orig, data, **kwargs):
        # NB: This potentially hugely expensive, but portal_transforms has a
        # cache keyed on the content that lasts an hour.
        try:
            if orig.strip() == "":
                # Don't bother translating empty strings
                data.setData("")
            elif kwargs['mimetype'] in ('text/r', 'text/R',):
                data.setData(self._rConvert(orig))
            elif kwargs['mimetype'] in ('text/x-uri'):
                data.setData(self._urlConvert(orig))
            elif kwargs['mimetype'] in ('image/x-xfig'):
                data.setData(self._figConvert(orig))
            elif kwargs['mimetype'] in ('text/x-gnuplot'):
                data.setData(self._gnuConvert(orig))
            else:
                raise ValueError("Unknown script MIME type %s" % kwargs['mimetype'])
        except Exception as e:
            import traceback
            data.setData(self._formatOutput(
                str(e) + "\n" + traceback.format_exc(),
                isError=True,
            ))
        if self.output == "text/html":
            data.setData(data.getData() + '<pre class="code-block"><code>%s</code></pre>' % cgi.escape(orig))
        return data


class ScriptToTeX(ScriptToMarkup):
    """
    Run script, generate EPS and wrap that into (admittedly invalid) TeX
    """
    __name__ = "script_to_tex"
    output = "text/x-tex"


class ScriptToHtml(ScriptToMarkup):
    """
    Run script, generate SVG and wrap that as HTML
    """
    __name__ = "script_to_html"
    output = "text/html"


def register():
    return ScriptToHtml()
