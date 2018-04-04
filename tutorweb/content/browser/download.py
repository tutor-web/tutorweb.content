import mimetypes

from zope.interface import implements
from zope.publisher.interfaces import IPublishTraverse, NotFound

from plone.namedfile.utils import set_headers, stream_data

from Products.Five.browser import BrowserView


class DownloadView(BrowserView):
    """Stream back the contents of a NamedBlobFile field"""
    implements(IPublishTraverse)

    def __init__(self, context, request):
        super(DownloadView, self).__init__(context, request)
        self.forceDownload = True

    def publishTraverse(self, request, id):
        # NB: We don't care what the filename is, just one is provided
        # for the browser when saving
        if self.forceDownload:
            self.forceDownload = False
        else:
            # Only one level of traversal allowed
            raise NotFound(self, id, request)
        return self

    def __call__(self):
        raise NotImplemented

    def downloadField(self, fieldName):
        file = getattr(self.context, fieldName, None)
        if file is None:
            raise NotFound(self.context, fieldName, self.request)

        if getattr(file, 'filename', False):
            fileName = file.filename
        else:
            fileName = ''.join([
                self.context.id, '-', fieldName,
                mimetypes.guess_extension(file.contentType) or '.dat',
            ])

        set_headers(file, self.request.response, filename=fileName if self.forceDownload else None)
        return stream_data(file)


class DownloadPdfView(DownloadView):
    """Stream back the contents of the PDF field"""
    def __call__(self):
        return self.downloadField('pdf')


class DownloadImageView(DownloadView):
    """Stream back the contents of the Image field"""
    def __call__(self):
        return self.downloadField('image')
