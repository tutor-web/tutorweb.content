from AccessControl import Unauthorized

from plone.app.testing import login, logout

from Products.CMFCore.utils import getToolByName

from .base import IntegrationTestCase
from .base import MANAGER_ID, USER_A_ID, USER_B_ID


class EnrolViewTest(IntegrationTestCase):
    def test_enrol(self):
        """Is the user part of a class?"""
        portal = self.layer['portal']

        # Add an empty class
        login(portal, MANAGER_ID)
        portal.invokeFactory(
            type_name="tw_class",
            id="classa",
            title="Unittest ClassA",
        )
        c = portal['classa']
        c.students = []

        # Enrol user A
        login(portal, USER_A_ID)
        c.restrictedTraverse('enrol')()
        c.students = [USER_A_ID]

        # Enrol user B
        login(portal, USER_B_ID)
        c.restrictedTraverse('enrol')()
        c.students = [USER_A_ID, USER_B_ID]

        # User B can't enrol twice
        c.restrictedTraverse('enrol')()
        c.students = [USER_A_ID, USER_B_ID]

        # Anonymous users can't enrol
        logout()
        with self.assertRaises(Unauthorized):
            c.restrictedTraverse('enrol')()


class BulkAddStudentViewTest(IntegrationTestCase):
    def setUp(self):
        """Create class"""
        portal = self.layer['portal']
        login(portal, MANAGER_ID)
        portal.invokeFactory(
            type_name="tw_class",
            id="classa",
            title="Unittest ClassA",
        )
        portal['classa'].students = []

    def test_uploadLog(self):
        view = self.getView()
        # Empty log at start
        self.assertEquals(
            view.uploadLog(),
            "",
        )

        # First line
        self.assertEquals(
            view.uploadLog("One line... a, a, aaaa."),
            "One line... a, a, aaaa.\n",
        )

        # Second line gets separator
        self.assertEquals(
            view.uploadLog("Two line... a, a, aaaa."),
            "One line... a, a, aaaa.\nTwo line... a, a, aaaa.\n",
        )

        # Return the same when no line is supplied
        self.assertEquals(
            view.uploadLog(),
            "One line... a, a, aaaa.\nTwo line... a, a, aaaa.\n",
        )

    def test_getAllMemberEmails(self):
        view = self.getView()
        self.assertEquals(view.getAllMemberEmails(), {
            '': 'test_user_1_',
            'arnold@example.com': 'Arnold',
            'betty@example.com': 'Betty',
            'caroline@example.com': 'Caroline',
            'daryl@example.com': 'Daryl',
        })

    def test_addUsersToClass(self):
        def doAddUsers(emails):
            """Call view, handing in email list"""
            self.layer['request'].form['userlist'] = emails
            view = self.getView()
            view()
            return view.uploadLog()
        c = self.layer['portal']['classa']
        rtool = getToolByName(self.layer['portal'], 'portal_registration')

        log = doAddUsers(USER_A_ID + """@example.com
badgercamelferret
moo@example.com
        """)
        self.assertTrue("Creating new user moo@example.com" in log)
        self.assertTrue('"badgercamelferret" not a valid email address, skipping' in log)
        self.assertTrue("Adding moo@example.com (moo@example.com) to course" in log)
        self.assertEquals(c.students, [
            "Arnold",
            "moo@example.com",
        ])
        self.assertEquals(self.getView().getAllMemberEmails(), {
            '': 'test_user_1_',
            'arnold@example.com': 'Arnold',
            'betty@example.com': 'Betty',
            'caroline@example.com': 'Caroline',
            'daryl@example.com': 'Daryl',
            'moo@example.com': 'moo@example.com',
        })

        log = doAddUsers("""
moo@example.com
oink@example.com
        """)
        self.assertEquals(c.students, [
            "Arnold",
            "moo@example.com",
            "oink@example.com",
        ])
        self.assertEquals(self.getView().getAllMemberEmails(), {
            '': 'test_user_1_',
            'arnold@example.com': 'Arnold',
            'betty@example.com': 'Betty',
            'caroline@example.com': 'Caroline',
            'daryl@example.com': 'Daryl',
            'moo@example.com': 'moo@example.com',
            'oink@example.com': 'oink@example.com',
        })

        # Create a user that already uses the email address as ID
        rtool.addMember('dave@example.com', rtool.generatePassword(), properties=dict(
            email='dave_01@example.com',
            username='dave@example.com',
            fullname='dave@example.com',
        ))
        log = doAddUsers("dave@example.com")
        self.assertEquals(c.students, [
            "Arnold",
            "moo@example.com",
            "oink@example.com",
            'dave@example.com',
        ])

    def getView(self):
        """Get an instance of the view for testing"""
        c = self.layer['portal']['classa']
        return c.restrictedTraverse('bulk-add-student')
