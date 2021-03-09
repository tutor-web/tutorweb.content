import zope.event
from Products.Five.browser import BrowserView
from zope.lifecycleevent import ObjectModifiedEvent

from tutorweb.content.script import scriptInit, scriptCommit


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


def script():
    import argparse
    import transaction
    import logging

    parser = argparse.ArgumentParser(description='Sync Plone->MySQL')
    parser.add_argument(
        '--zope-conf',
        help='Zope configuration file',
    )
    parser.add_argument(
        '--debug',
        default=False,
        action='store_true',
        help='Output debug messages',
    )
    args = parser.parse_args()
    if args.debug:
        sqllog = logging.getLogger('sqlalchemy.engine')
        sqllog.addHandler(logging.StreamHandler())
        sqllog.setLevel(logging.INFO)

    app, site = scriptInit('tutor-web', configFile=args.zope_conf)
    site.unrestrictedTraverse('@@sync-all')()
    scriptCommit(app)
