from zope.app.component.hooks import getSite


def loggedInHandler(event):
    """If a user has logged in without having a full name yet, prompt 'em"""
    portal = getSite()
    user = event.object
    request = getattr(portal, "REQUEST", None)
    if not request:
        # HTTP request is not present e.g.
        # when doing unit testing / calling scripts from command line
        return False

    # If user has a fullname, carry on
    if user.getProperty('fullname'):
        return False

    # Otherwise, redirect to personal information
    request['next'] = portal.absolute_url() + "/@@personal-information"
    return True
