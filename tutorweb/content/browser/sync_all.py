import zope.event
from Products.Five.browser import BrowserView
from zope.lifecycleevent import ObjectModifiedEvent

class SyncAllView(BrowserView):
    def __call__(self):
        response = self.request.response
        portal = self.context

        listing = portal.portal_catalog.unrestrictedSearchResults(
            portal_type='tw_lecture'
        )

        response.setHeader("Content-type", "text/plain")
        for b in listing:
            lec = b.getObject()
            response.write('/'.join(lec.getPhysicalPath()))

            lec.reindexObject()
            response.write(" (reindexed)")

            zope.event.notify(ObjectModifiedEvent(lec))
            response.write(" (notified)\n")
