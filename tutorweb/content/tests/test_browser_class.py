from AccessControl import Unauthorized

from plone.app.testing import login, logout

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

        # Anonymous users can't enrol
        logout()
        with self.assertRaises(Unauthorized):
            c.restrictedTraverse('enrol')()
