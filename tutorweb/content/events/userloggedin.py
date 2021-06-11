from zope.component.hooks import getSite
from zope.globalrequest import getRequest


def loggedInHandler(event):
    """If a user has logged in without having a full name yet, prompt 'em"""
    portal = getSite()
    user = event.object

    # If user has a fullname and has accepted terms, carry on
    mb = portal.portal_membership.getAuthenticatedMember()
    if mb.getProperty('fullname') and mb.getProperty('accept', False):
        return

    # Otherwise, redirect to personal information
    request = getRequest()
    if request is None:
        return
    request['next'] = portal.absolute_url() + "/@@personal-information"
