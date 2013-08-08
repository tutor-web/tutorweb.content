from Products.Five.browser import BrowserView

from tutorweb.content.schema import IQuestion

class LectureView(BrowserView):
    def questionListing(self):
        listing = self.context.restrictedTraverse('@@folderListing')(
            object_provides=IQuestion.__identifier__,
        )
        return listing

    def slideListing(self):
        listing = self.context.restrictedTraverse('@@folderListing')(
            portal_type="Slide",
        )
        return listing
