from Products.Five.browser import BrowserView

from tutorweb.content.schema import IQuestion

class TutorialView(BrowserView):
    def lectureListing(self):
        listing = self.context.restrictedTraverse('@@folderListing')(
            portal_type="tw_lecture",
        )
        return listing
