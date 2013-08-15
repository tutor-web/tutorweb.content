from AccessControl import Unauthorized

from Products.CMFCore.utils import getToolByName

from plone.app.testing import setRoles, login

from .base import IntegrationTestCase
from .base import MANAGER_ID, USER_A_ID, USER_B_ID, USER_C_ID


class LectureViewTest(IntegrationTestCase):

    def test_questionListing(self):
        """questions will not be listed unless you are an editor"""
        portal = self.layer['portal']

        # User A is just a member, can't see questions
        login(portal, USER_A_ID);
        self.assertEquals([q.getPath() for q in self.getView().questionListing()], [
        ])

        # Manager however, can.
        login(portal, MANAGER_ID);
        self.assertEquals([q.getPath() for q in self.getView().questionListing()], [
            '/plone/dept1/tut1/lec1/qn1',
        ])

    def test_quizUrl(self):
        """Should formulate a quiz URL"""
        self.assertEquals(
            self.getView().quizUrl(),
            """http://nohost/plone/++resource++tutorweb.quiz/load.html?lecUri=http%3A%2F%2Fnohost%2Fplone%2Fdept1%2Ftut1%2Flec1%2Fquizdb-sync&tutUri=http%3A%2F%2Fnohost%2Fplone%2Fdept1%2Ftut1%2Fquizdb-sync""",
        )

    def test_canEdit(self):
        """Make sure regular users can't edit"""
        portal = self.layer['portal']

        # User A is just a member, can't edit
        login(portal, USER_A_ID);
        self.assertFalse(self.getView().canEdit())

        # Manager however, can.
        login(portal, MANAGER_ID);
        self.assertTrue(self.getView().canEdit())

    def getView(self, path='dept1/tut1/lec1'):
        """Get the view for a lecture path"""
        return self.layer['portal'].restrictedTraverse(path + '/view')
