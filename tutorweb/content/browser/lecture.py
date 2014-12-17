from Products.Five.browser import BrowserView

from collective.transmogrifier.interfaces import ITransmogrifier


class LectureSlideImportView(BrowserView):
    def __call__(self):
        if 'src' not in self.request.form:
            raise ValueError("Must provide a URL to a lecture in src")
        transmogrifier = ITransmogrifier(self.context)
        transmogrifier(
            'tutorweb.content.transmogrifier.oldtutorwebslideimport',
            definitions=dict(
                url=self.request.form['src'],
                folder='',
                desturl=self.context.absolute_url(),
            ),
        )
        return "success"
