from AccessControl import Unauthorized

from plone.app.testing import login, logout

from Products.CMFCore.utils import getToolByName

from .base import IntegrationTestCase
from .base import MANAGER_ID, USER_A_ID, USER_B_ID


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

    def getAllMemberEmails(self):
        """Make lookup of member email addresses to ids"""
        mtool = getToolByName(self.layer['portal'], 'portal_membership')
        return [(
            m.getProperty('email'),
            m.id,
        ) for m in sorted(mtool.listMembers())]

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

    def test_addUsersToClass(self):
        def doAddUsers(emails):
            """Call view, handing in email list"""
            self.layer['request'].form['userlist'] = emails
            view = self.getView()
            view()
            return view.uploadLog()
        c = self.layer['portal']['classa']
        rtool = getToolByName(self.layer['portal'], 'portal_registration')

        log = doAddUsers("""
badgercamelferret
moo@example.com
        """)
        self.assertTrue("Creating new user moo@example.com" in log)
        self.assertTrue('"badgercamelferret" not a valid email address, skipping' in log)
        self.assertTrue("Adding moo@example.com (moo@example.com) to course" in log)
        self.assertEquals(c.students, [
            "moo@example.com",
        ])
        self.assertEquals(self.getAllMemberEmails(), [
            ('Arnold@example.com', 'Arnold'),
            ('Betty@example.com', 'Betty'),
            ('', 'BigBoss'),
            ('Caroline@example.com', 'Caroline'),
            ('Daryl@example.com', 'Daryl'),
            ('moo@example.com', 'moo@example.com'),
            ('', 'test_user_1_'),
        ])

        log = doAddUsers("""
moo@example.com
oink@example.com
        """)
        self.assertEquals(c.students, [
            "moo@example.com",
            "oink@example.com",
        ])
        self.assertEquals(self.getAllMemberEmails(), [
            ('Arnold@example.com', 'Arnold'),
            ('Betty@example.com', 'Betty'),
            ('', 'BigBoss'),
            ('Caroline@example.com', 'Caroline'),
            ('Daryl@example.com', 'Daryl'),
            ('moo@example.com', 'moo@example.com'),
            ('oink@example.com', 'oink@example.com'),
            ('', 'test_user_1_'),
        ])

        # Create a user that already uses the email address as ID
        rtool.addMember('dave@example.com', rtool.generatePassword(), properties=dict(
            email='dave_01@example.com',
            username='dave@example.com',
            fullname='dave@example.com',
        ))
        log = doAddUsers("dave@example.com")
        self.assertEquals(c.students, [
            "moo@example.com",
            "oink@example.com",
            'dave@example.com',
        ])

    def getView(self):
        """Get an instance of the view for testing"""
        c = self.layer['portal']['classa']
        return c.restrictedTraverse('bulk-add-student')
