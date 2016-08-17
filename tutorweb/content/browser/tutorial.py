from Products.Five.browser import BrowserView
from plone.namedfile.file import NamedBlobFile

from plone.namedfile.utils import stream_data

from ..tex_generator import TexGenerator, TexSlideGenerator, TexWriter

class TutorialUpdatePDFView(BrowserView):
    """Convert tutorials into PDF, update local copy"""
    def updateObj(self, context, generator):
        tw = TexWriter()

        # NB: Using self.context since that's always the tutorial
        for l in self.context.restrictedTraverse('@@folderListing')(Type="File", sort_on="id"):
            df = l.getObject().file
            if getattr(df, 'filename', False):
                next
            filename = df.filename.encode('utf8')
            self.request.response.write("Adding data file %s\n" % filename)
            tw.addDataFile(filename, stream_data(df), overwrite_existing=False)

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
