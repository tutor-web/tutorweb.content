import tempfile

from ZPublisher.HTTPRequest import FileUpload

from collective.transmogrifier.interfaces import ITransmogrifier
from Products.Five.browser import BrowserView

from tutorweb.content.schema import IQuestion

from tutorweb.content.transmogrifier.latex import objectsToTex


class LaTeXQuestionTeXView(BrowserView):
    """Render question in TeX form"""
    def __call__(self):
        context = self.context
        self.request.response.setHeader('Content-Type', 'application/x-tex')
        self.request.response.setHeader(
            'Content-disposition',
            "attachment; filename=%s.tex" % context.id,
        )
        return objectsToTex([context])


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
        return objectsToTex(l.getObject() for l in listing)


class LectureTeXImport(BrowserView):
    """Import questions from a TeX upload"""
    def __call__(self):
        upload = self.request.get('media', None)
        if not isinstance(upload, FileUpload):
            return ValueError("Missing upload")

        if hasattr(upload, 'name'):
            # Upload has already been buffered
            filename = upload.name
        else:
            # Zope just slurped it, so we have to put it back
            tf = tempfile.NamedTemporaryFile(suffix='.' + upload.filename)
            tf.file.write(upload.read())
            tf.file.flush()
            filename = tf.name

        transmogrifier = ITransmogrifier(self.context)
        transmogrifier('tutorweb.content.latexquizimport', definitions=dict(
            input_file=filename,
            folder='',  # i.e. upload to current context
        ))
        self.request.response.redirect(self.context.absolute_url())
