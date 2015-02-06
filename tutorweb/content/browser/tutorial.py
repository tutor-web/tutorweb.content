from Products.Five.browser import BrowserView
from plone.namedfile.file import NamedBlobFile

from ..tex_generator import TexGenerator, TexWriter

class TutorialUpdatePDFView(BrowserView):
    """Convert tutorials into PDF, update local copy"""

    def __call__(self):
        tw = TexWriter()
        try:
            self.request.response.setHeader("Content-type", "text/plain")
            tex = TexGenerator(self.context).tex()
            self.request.response.write(tw.createPDF(tex))
            self.request.response.write("\n\nFinished.\n")

            pdfOut = tw.outputPdf()
            if pdfOut is not None:
                with open(pdfOut, 'r') as f:
                    self.context.pdf = NamedBlobFile(
                        data=f.read(),
                        contentType='application/pdf',
                        filename=u'',
                    )
                self.request.response.write("Tutorial PDF updated with %s\n" % pdfOut)
            else:
                self.request.response.write("Tutorial PDF *NOT* updated\n")

        finally:
            if self.request.form.get('keep', False):
                self.request.response.write("Output saved in %s" % tw.dir)
            else:
                tw.close()


class TutorialTeXView(BrowserView):
    """Show tex for tutorial"""

    def __call__(self):
        self.request.response.setHeader("Content-type", "text/x-tex")
        tex = TexGenerator(self.context).tex()
        self.request.response.write(tex)
