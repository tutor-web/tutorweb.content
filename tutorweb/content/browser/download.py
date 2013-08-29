from zope.publisher.interfaces import NotFound

from plone.namedfile.utils import set_headers, stream_data

from Products.Five.browser import BrowserView


class DownloadView(BrowserView):
    """Stream back the contents of a NamedBlobFile field"""
    def __call__(self):
        raise NotImplemented

    def downloadField(self, fieldName):
        file = getattr(self.context, fieldName, None)
        if file is None:
            raise NotFound(self.context, fieldName, self.request)

        set_headers(file, self.request.response, filename=file.filename)
        return stream_data(file)


class DownloadPdfView(DownloadView):
    """Stream back the contents of the PDF field"""
    def __call__(self):
        return self.downloadField('pdf')


class DownloadImageView(DownloadView):
    """Stream back the contents of the Image field"""
    def __call__(self):
        return self.downloadField('image')
