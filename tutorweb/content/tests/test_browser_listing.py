from zope.annotation.interfaces import IAnnotations

from plone.app.testing import login, logout

from .base import IntegrationTestCase, setRelations
from .base import MANAGER_ID, USER_A_ID, USER_B_ID, USER_C_ID


class ListingViewTest(IntegrationTestCase):

    def test_questionListing(self):
        """questions will not be listed unless you are an editor"""
        portal = self.layer['portal']
        self.path = 'dept1/tut1/lec1'

        # User A is just a member, can't see questions
        login(portal, USER_A_ID)
        self.assertEquals([q['url'] for q in self.getView().questionListing()], [
        ])

        # Manager however, can.
        login(portal, MANAGER_ID)
        self.assertEquals([q['url'] for q in self.getView().questionListing()], [
            'http://nohost/plone/dept1/tut1/lec1/qn1',
            'http://nohost/plone/dept1/tut1/lec1/qn2',
        ])

    def test_lectureListing(self):
        """Get counts of questions within lectures"""
        portal = self.layer['portal']
        self.path = 'dept1/tut1'
        login(portal, MANAGER_ID)

        # Each has 2 questions out of the box
        self.assertEquals(self.getView().lectureListing(), [
            {'id': 'lec1', 'title': 'Unittest D1 T1 L1',
             'url': 'http://nohost/plone/dept1/tut1/lec1',
             'pdf': None, 'questions': 2, 'slides': 0},
            {'id': 'lec2', 'title': 'Unittest D1 T1 L2',
             'url': 'http://nohost/plone/dept1/tut1/lec2',
             'pdf': None, 'questions': 2, 'slides': 0},
        ])

    def test_lectureListingMultiple(self):
        """Get counts of questions within lectures"""
        portal = self.layer['portal']
        self.path = 'dept1/tut1'
        login(portal, MANAGER_ID)

        # Add some more lectures, we see them in the view too
        # NB: This is a separate test since otherwise we trip over memoize
        portal['dept1']['tut1']['lec1'].invokeFactory(
            type_name="tw_latexquestion",
            id="qn3",
            title="Unittest D1 T1 L1 Q3",
        )
        portal['dept1']['tut1']['lec1'].invokeFactory(
            type_name="tw_latexquestion",
            id="qn4",
            title="Unittest D1 T1 L1 Q4",
        )
        self.assertEquals(self.getView().lectureListing(), [
            {'id': 'lec1', 'title': 'Unittest D1 T1 L1',
             'url': 'http://nohost/plone/dept1/tut1/lec1',
             'pdf': None, 'questions': 4, 'slides': 0},
            {'id': 'lec2', 'title': 'Unittest D1 T1 L2',
             'url': 'http://nohost/plone/dept1/tut1/lec2',
             'pdf': None, 'questions': 2, 'slides': 0},
        ])

    def test_lectureListingOrdering(self):
        """Lectures should appear in right order, even if added after"""
        portal = self.layer['portal']
        self.path = 'dept1/tut1'
        login(portal, MANAGER_ID)

        # NB: This is a separate test since otherwise we trip over memoize
        portal['dept1']['tut1'].invokeFactory(
            type_name="tw_lecture",
            id="lec0",
            title="ZZUnittest D1 T1 L0",
        )

        self.assertEquals(self.getView().lectureListing(), [
            {'id': 'lec0', 'title': 'ZZUnittest D1 T1 L0',
             'url': 'http://nohost/plone/dept1/tut1/lec0',
             'pdf': None, 'questions': 0, 'slides': 0},
            {'id': 'lec1', 'title': 'Unittest D1 T1 L1',
             'url': 'http://nohost/plone/dept1/tut1/lec1',
             'pdf': None, 'questions': 2, 'slides': 0},
            {'id': 'lec2', 'title': 'Unittest D1 T1 L2',
             'url': 'http://nohost/plone/dept1/tut1/lec2',
             'pdf': None, 'questions': 2, 'slides': 0},
        ])

    def test_fileListing(self):
        """Can get listings for any files within current node"""
        portal = self.layer['portal']
        self.path = 'dept1/tut1'

        # Create some files first
        login(portal, MANAGER_ID)
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
            {'title': 'File A',
             'id': 'filea.pdf',
             'url': 'http://nohost/plone/dept1/tut1/filea.pdf/view'},
            {'title': 'File B',
             'id': 'fileb.pdf',
             'url': 'http://nohost/plone/dept1/tut1/fileb.pdf/view'},
        ])

    def test_courseListing(self):
        """Can get listings for any courses within current node"""
        portal = self.layer['portal']
        login(portal, MANAGER_ID)
        self.path = 'dept1'

        # Here's one we made earlier
        self.assertEquals(self.getView().courseListing(), [
            {'files': 0, 'id': 'course1', 'title': 'Unittest C1',
             'tutorials': 1, 'url': 'http://nohost/plone/dept1/course1'},
        ])

        # Add another tutorial, doesn't automatically appear in course1
        portal['dept1'].invokeFactory(
            type_name="tw_tutorial",
            id="tut2",
            title="Unittest D1 T2",
        )
        self.assertEquals(self.getView().courseListing(), [
            {'files': 0, 'id': 'course1', 'title': 'Unittest C1',
             'tutorials': 1, 'url': 'http://nohost/plone/dept1/course1'},
        ])

        # Add to course1's list
        setRelations(portal['dept1']['course1'], 'tutorials', [
            portal['dept1']['tut1'],
            portal['dept1']['tut2'],
        ])
        self.assertEquals(self.getView().courseListing(), [
            {'files': 0, 'id': 'course1', 'title': 'Unittest C1',
             'tutorials': 2, 'url': 'http://nohost/plone/dept1/course1'},
        ])

    def test_relatedCourses(self):
        """Tutorials should know what courses they are related to"""
        portal = self.layer['portal']
        login(portal, MANAGER_ID)
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
        self.path = 'dept1/tut1/lec2'
        self.assertEquals(
            self.getView().quizUrl(),
            "http://nohost/plone/++resource++tutorweb.quiz/load.html" + 
            "?lecUri=http%3A%2F%2Fnohost%2Fplone%2Fdept1%2Ftut1%2Flec2%2Fquizdb-sync" +
            "&tutUri=http%3A%2F%2Fnohost%2Fplone%2Fdept1%2Ftut1%2Fquizdb-sync",
        )
        # For the tutorial above it formulates a link to the first lecture
        self.path = 'dept1/tut1'
        self.assertEquals(
            self.getView().quizUrl(),
            "http://nohost/plone/++resource++tutorweb.quiz/load.html" +
            "?lecUri=http%3A%2F%2Fnohost%2Fplone%2Fdept1%2Ftut1%2Flec1%2Fquizdb-sync" +
            "&tutUri=http%3A%2F%2Fnohost%2Fplone%2Fdept1%2Ftut1%2Fquizdb-sync",
        )

        # Create a new tutorial with no lectures, not going to be very
        # interesting
        portal = self.layer['portal']
        login(portal, MANAGER_ID)
        portal['dept1'].invokeFactory(
            type_name="tw_tutorial",
            id="tut2",
            title="Unittest D1 T2",
        )
        self.path = 'dept1/tut2'
        self.assertEquals(self.getView().quizUrl(), '#')

        # Can specify which object we want the quiz URL for
        # NB: tut2 isn't used as tutorial, is irrelevant
        self.path = 'dept1/tut2'
        self.assertEquals(
            self.getView().quizUrl(portal['dept1']['tut1']['lec2']),
            "http://nohost/plone/++resource++tutorweb.quiz/load.html" +
            "?lecUri=http%3A%2F%2Fnohost%2Fplone%2Fdept1%2Ftut1%2Flec2%2Fquizdb-sync" +
            "&tutUri=http%3A%2F%2Fnohost%2Fplone%2Fdept1%2Ftut1%2Fquizdb-sync"
        )

    def test_partOfClass(self):
        """Is the user part of a class?"""
        def isInClass(user):
            # Clear out plone.memoize cache
            anno = IAnnotations(self.layer['request'])
            if 'plone.memoize' in anno:
                del anno['plone.memoize']
            # Login as appropriate user
            if user:
                login(portal, user)
            else:
                logout()
            self.path='classa'
            return self.getView().partOfClass()
        portal = self.layer['portal']

        # Nobody is part of empty class
        login(portal, MANAGER_ID)
        portal.invokeFactory(
            type_name="tw_class",
            id="classa",
            title="Unittest ClassA",
        )
        self.assertFalse(isInClass(USER_A_ID))
        self.assertFalse(isInClass(USER_B_ID))
        self.assertFalse(isInClass(USER_C_ID))
        self.assertFalse(isInClass(None))

        # Add users A and C
        login(portal, MANAGER_ID)
        portal['classa'].students = [USER_A_ID, USER_C_ID]
        self.assertTrue(isInClass(USER_A_ID))
        self.assertFalse(isInClass(USER_B_ID))
        self.assertTrue(isInClass(USER_C_ID))
        self.assertFalse(isInClass(None))

    def test_canEdit(self):
        """Make sure regular users can't edit"""
        portal = self.layer['portal']
        self.path = 'dept1/tut1/lec1'

        # User A is just a member, can't edit
        login(portal, USER_A_ID)
        self.assertFalse(self.getView().canEdit())

        # Manager however, can.
        login(portal, MANAGER_ID)
        self.assertTrue(self.getView().canEdit())

    def getView(self):
        """Get the view for a lecture path"""
        return self.layer['portal'].restrictedTraverse(self.path + '/view')
