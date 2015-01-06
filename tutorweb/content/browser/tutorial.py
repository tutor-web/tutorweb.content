from Products.Five.browser import BrowserView
from plone.namedfile.file import NamedBlobFile

from ..tex_generator import TexGenerator

class TutorialUpdatePDFView(BrowserView):
    """Convert tutorials into PDF, update local copy"""

    def __call__(self):
        try:
            tg = TexGenerator(self.context)
            self.request.response.write(tg.createPDF())
            self.request.response.write("\n\nFinished\n")
            lastOut = tg.outputFiles()[-1]
            if lastOut.endswith('.pdf'):
                with open(lastOut, 'r') as f:
                    self.context.pdf = NamedBlobFile(
                        data=f.read(),
                        contentType=u'application/pdf',
                        filename=u'',
                    )
                self.request.response.write("Tutorial PDF updated with %s\n" % lastOut)
            else:
                self.request.response.write("Tutorial PDF *NOT* updated\n")
        finally:
            tg.close()
