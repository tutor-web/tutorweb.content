from .base import FunctionalTestCase, MANAGER_ID

class SyncAllViewTest(FunctionalTestCase):
    def test_call(self):
        portal = self.layer['portal']
        browser = self.getBrowser(portal.absolute_url() + '/@@sync-all', user=MANAGER_ID, streaming=True)
        self.assertEquals(browser.headers['content-type'], 'text/plain')
        self.assertEquals(browser.contents.strip(), """
/plone/dept1/tut1/lec1 (reindexed) (notified)
/plone/dept1/tut1/lec2 (reindexed) (notified)
        """.strip())
