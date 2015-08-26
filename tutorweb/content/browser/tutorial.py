from Products.Five.browser import BrowserView
from plone.namedfile.file import NamedBlobFile

from ..tex_generator import TexGenerator, TexSlideGenerator, TexWriter

class TutorialUpdatePDFView(BrowserView):
    """Convert tutorials into PDF, update local copy"""
    def updateObj(self, context, generator):
        tw = TexWriter()
        try:
            self.request.response.write("Generating PDF for %s...\n" % context.id)
            tex = generator(context).tex()
            self.request.response.write(tw.createPDF(tex))
            self.request.response.write("\n\nFinished.\n")

            pdfOut = tw.outputPdf()
            if pdfOut:
                with open(pdfOut, 'r') as f:
                    context.pdf = NamedBlobFile(
                        data=f.read(),
                        contentType='application/pdf',
                        filename=u'',
                    )
                    self.request.response.write("PDF for %s updated with %s\n" % (context.id, pdfOut))
            else:
                self.request.response.write("PDF for %s *NOT* updated\n" % context.id)
                return
        finally:
            if self.request.form.get('keep', False):
                self.request.response.write("Output saved in %s" % tw.dir)
                tw.close(True)
            else:
                tw.close(False)

    def children(self, obj):
        # TODO: Should filter by workflow state
        return (
            l.getObject()
            for l
            in obj.restrictedTraverse('@@folderListing')(
                Type=dict(
                    Tutorial='Lecture',
                    Lecture='Slide',
                )[obj.Type()],
                sort_on="id",
            )
        )

    def __call__(self):
        self.request.response.setHeader("Content-type", "text/plain")
        self.updateObj(self.context, TexGenerator)
        for lec in self.children(self.context):
            self.request.response.write("\n")
            self.updateObj(lec, TexSlideGenerator)


class TutorialTeXView(BrowserView):
    """Show tex for tutorial"""

    def __call__(self):
        self.request.response.setHeader("Content-type", "text/x-tex")
        tex = TexGenerator(self.context).tex()
        self.request.response.write(tex)
