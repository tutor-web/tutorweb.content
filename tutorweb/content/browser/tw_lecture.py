from ZPublisher.HTTPRequest import FileUpload

from collective.transmogrifier.interfaces import ITransmogrifier
from Products.Five.browser import BrowserView

from tutorweb.content.schema import IQuestion


class LectureTeXView(BrowserView):
    """Render all questions from lecture in TeX form"""
    def __call__(self):
        response = self.request.response

        listing = self.context.restrictedTraverse('@@folderListing')(
            object_provides=IQuestion.__identifier__,
        )
        response.setHeader('Content-Type', 'application/x-tex')
        response.setHeader(
            'Content-disposition',
            "attachment; filename=%s.tex" % self.context.id,
        )
        response.write("\n")  # To finalise the headers
        for (i, l) in enumerate(listing):
            if i > 0:
                response.write("\n%===\n")
            response.write(l.getObject()
                            .restrictedTraverse('tex')()
                            .encode('utf8'))


class LectureTeXImport(BrowserView):
    """Import questions from a TeX upload"""
    def __call__(self):
        upload = self.request.get('media', None)
        if not isinstance(upload, FileUpload):
            return ValueError("Missing upload")

        transmogrifier = ITransmogrifier(self.context)
        transmogrifier('tutorweb.content.latexquizimport', definitions=dict(
            input_file=upload.name,
            folder='',  # i.e. upload to current context
        ))
        self.request.response.redirect(self.context.absolute_url())
