from AccessControl import Unauthorized

from Products.CMFCore.utils import getToolByName

from plone.app.testing import setRoles, login

from .base import IntegrationTestCase, setRelations
from .base import MANAGER_ID, USER_A_ID, USER_B_ID, USER_C_ID


class ListingViewTest(IntegrationTestCase):

    def test_questionListing(self):
        """questions will not be listed unless you are an editor"""
        portal = self.layer['portal']
        self.path = 'dept1/tut1/lec1'

        # User A is just a member, can't see questions
        login(portal, USER_A_ID);
        self.assertEquals([q.getPath() for q in self.getView().questionListing()], [
        ])

        # Manager however, can.
        login(portal, MANAGER_ID);
        self.assertEquals([q.getPath() for q in self.getView().questionListing()], [
            '/plone/dept1/tut1/lec1/qn1',
        ])

    def test_lectureListing(self):
        """Get counts of questions within lectures"""
        portal = self.layer['portal']
        self.path = 'dept1/tut1'
        login(portal, MANAGER_ID);

        # Has one question out of the box
        self.assertEquals(self.getView().lectureListing(), [
            {'id': 'lec1', 'title': 'Unittest D1 T1 L1', 'url': 'http://nohost/plone/dept1/tut1/lec1',
             'pdf': None, 'questions': 1, 'slides': 0},
        ])

        # Can add some more
        portal['dept1']['tut1']['lec1'].invokeFactory(
            type_name="tw_latexquestion",
            id="qn2",
            title="Unittest D1 T1 L1 Q2",
        )
        portal['dept1']['tut1']['lec1'].invokeFactory(
            type_name="tw_latexquestion",
            id="qn3",
            title="Unittest D1 T1 L1 Q3",
        )
        self.assertEquals(self.getView().lectureListing(), [
            {'id': 'lec1', 'title': 'Unittest D1 T1 L1', 'url': 'http://nohost/plone/dept1/tut1/lec1',
             'pdf': None, 'questions': 3, 'slides': 0},
        ])

    def test_fileListing(self):
        """Can get listings for any files within current node"""
        portal = self.layer['portal']
        self.path = 'dept1/tut1'

        # Create some files first
        login(portal, MANAGER_ID);
        portal['dept1']['tut1'].invokeFactory(
            type_name="File",
            id="filea.pdf",
            title="File A",
        )
        portal['dept1']['tut1'].invokeFactory(
            type_name="File",
            id="fileb.pdf",
            title="File B",
        )
        self.assertEquals(self.getView().fileListing(), [
            {'title': 'File A', 'url': 'http://nohost/plone/dept1/tut1/filea.pdf'},
            {'title': 'File B', 'url': 'http://nohost/plone/dept1/tut1/fileb.pdf'},
        ])

    def test_courseListing(self):
        """Can get listings for any courses within current node"""
        portal = self.layer['portal']
        login(portal, MANAGER_ID);
        self.path = 'dept1'

        # Here's one we made earlier
        self.assertEquals(self.getView().courseListing(), [
            {'code': None, 'files': 0, 'id': 'course1', 'title': 'Unittest C1',
             'tutorials': 1, 'url': 'http://nohost/plone/dept1/course1'},
        ])

        # Add another tutorial, doesn't automatically appear in course1
        portal['dept1'].invokeFactory(
            type_name="tw_tutorial",
            id="tut2",
            title="Unittest D1 T2",
        )
        self.assertEquals(self.getView().courseListing(), [
            {'code': None, 'files': 0, 'id': 'course1', 'title': 'Unittest C1',
             'tutorials': 1, 'url': 'http://nohost/plone/dept1/course1'},
        ])

        # Add to course1's list
        setRelations(portal['dept1']['course1'], 'tutorials', [
            portal['dept1']['tut1'],
            portal['dept1']['tut2'],
        ])
        self.assertEquals(self.getView().courseListing(), [
            {'code': None, 'files': 0, 'id': 'course1', 'title': 'Unittest C1',
             'tutorials': 2, 'url': 'http://nohost/plone/dept1/course1'},
        ])

    def test_relatedCourses(self):
        """Tutorials should know what courses they are related to"""
        portal = self.layer['portal']
        login(portal, MANAGER_ID);
        self.path = 'dept1/tut1'

        self.assertEquals(self.getView().relatedCourses(), [
            dict(url='http://nohost/plone/dept1/course1', title='Unittest C1'),
        ])

        # Add another course that also has tut1.
        portal['dept1'].invokeFactory(
            type_name="tw_course",
            id="course2",
            title="Unittest C2",
        )
        setRelations(portal['dept1']['course2'], 'tutorials', [
            portal['dept1']['tut1'],
        ])
        self.assertEquals(self.getView().relatedCourses(), [
            dict(url='http://nohost/plone/dept1/course1', title='Unittest C1'),
            dict(url='http://nohost/plone/dept1/course2', title='Unittest C2'),
        ])

    def test_quizUrl(self):
        """Should formulate a quiz URL"""
        self.path = 'dept1/tut1/lec1'

        self.assertEquals(
            self.getView().quizUrl(),
            """http://nohost/plone/++resource++tutorweb.quiz/load.html?lecUri=http%3A%2F%2Fnohost%2Fplone%2Fdept1%2Ftut1%2Flec1%2Fquizdb-sync&tutUri=http%3A%2F%2Fnohost%2Fplone%2Fdept1%2Ftut1%2Fquizdb-sync""",
        )

    def test_canEdit(self):
        """Make sure regular users can't edit"""
        portal = self.layer['portal']
        self.path = 'dept1/tut1/lec1'

        # User A is just a member, can't edit
        login(portal, USER_A_ID);
        self.assertFalse(self.getView().canEdit())

        # Manager however, can.
        login(portal, MANAGER_ID);
        self.assertTrue(self.getView().canEdit())

    def getView(self):
        """Get the view for a lecture path"""
        return self.layer['portal'].restrictedTraverse(self.path + '/view')