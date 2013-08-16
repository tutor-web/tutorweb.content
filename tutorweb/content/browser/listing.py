import urllib

from AccessControl import getSecurityManager
from zope.component import getMultiAdapter

from Products.CMFCore import permissions
from Products.Five.browser import BrowserView

from tutorweb.content.schema import IQuestion


class ListingView(BrowserView):
    """Class for all views that just list sub-content"""
    def questionListing(self):
        """Listing of all question items"""
        listing = self.context.restrictedTraverse('@@folderListing')(
            object_provides=IQuestion.__identifier__,
        )
        return listing

    def slideListing(self):
        """Listing of all slide items"""
        listing = self.context.restrictedTraverse('@@folderListing')(
            portal_type="Slide",
        )
        return listing

    def lectureListing(self):
        """Listing of all lecture items"""
        listing = self.context.restrictedTraverse('@@folderListing')(
            portal_type="tw_lecture",
        )
        return listing

    def quizUrl(self):
        """Return URL to the quiz for this lecture"""
        portal_state = getMultiAdapter(
            (self.context, self.request),
            name=u'plone_portal_state',
        )
        out = portal_state.portal_url()
        out += "/++resource++tutorweb.quiz/load.html?"
        out += urllib.urlencode(dict(
            tutUri=self.context.aq_parent.absolute_url() + '/quizdb-sync',
            lecUri=self.context.absolute_url() + '/quizdb-sync',
        ))
        return out

    def canEdit(self):
        """Return true iff user can edit context"""
        return getSecurityManager() \
            .checkPermission(permissions.ModifyPortalContent, self)
