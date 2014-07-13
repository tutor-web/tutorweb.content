from Products.Five.browser import BrowserView

from collective.transmogrifier.interfaces import ITransmogrifier


class LectureSlideImportView(BrowserView):
    def __call__(self):
        url = 'http://www.tutor-web.net:8089/tutor-web/fish/fish5106stockrec'
        transmogrifier = ITransmogrifier(self.context)
        transmogrifier(
            'tutorweb.content.transmogrifier.oldtutorwebslideimport',
            definitions=dict(url=url, folder=''),
        )
