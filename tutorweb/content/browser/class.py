from AccessControl import Unauthorized

from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView


class EnrolView(BrowserView):
    def __call__(self):
        mt = getToolByName(self.context, 'portal_membership')
        if mt.isAnonymousUser():
            raise Unauthorized
        mb = mt.getAuthenticatedMember()

        if not getattr(self.context, 'students', None):
            self.context.students = []
        self.context.students.append(mb.getUserName())

        self.request.response.redirect(self.context.absolute_url())
