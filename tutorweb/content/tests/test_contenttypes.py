from AccessControl import Unauthorized

from Products.CMFCore.utils import getToolByName

from plone.app.testing import setRoles, login

from .base import IntegrationTestCase
from .base import MANAGER_ID, USER_A_ID, USER_B_ID, USER_C_ID


class ContentTypeTest(IntegrationTestCase):

    def test_createcontent(self):
        """Content types can be created and nested appropriately
        """
        portal = self.layer['portal']
        login(portal, MANAGER_ID)

        #NB: Happy path has already been done by setup, so just test failures
        for obj in [
            portal['dept1'],
            portal['dept1']['tut1'],
            portal['dept1']['tut1']['lec1'],
            portal['dept1']['tut1']['lec1']['qn1'],
        ]:
            with self.assertRaisesRegexp(ValueError, 'tw_department'):
                obj.invokeFactory(type_name="tw_department", id="dept")
        for obj in [
            portal['dept1']['tut1'],
            portal['dept1']['tut1']['lec1'],
            portal['dept1']['tut1']['lec1']['qn1'],
        ]:
            with self.assertRaisesRegexp(ValueError, 'tw_tutorial'):
                obj.invokeFactory(type_name="tw_tutorial", id="tut")
        for obj in [
            portal['dept1'],
            portal['dept1']['tut1']['lec1'],
            portal['dept1']['tut1']['lec1']['qn1'],
        ]:
            with self.assertRaisesRegexp(ValueError, 'tw_lecture'):
                obj.invokeFactory(type_name="tw_lecture", id="lec")
        for obj in [
            portal['dept1'],
            portal['dept1']['tut1'],
            portal['dept1']['tut1']['lec1']['qn1'],
        ]:
            with self.assertRaisesRegexp(ValueError, 'tw_latexquestion'):
                obj.invokeFactory(type_name="tw_latexquestion", id="dept")

    def test_question_permissions(self):
        """questions cannot be viewed unless you are an editor"""
        portal = self.layer['portal']

        # User A is just a member, can't see questions
        login(portal, USER_A_ID);
        with self.assertRaises(Unauthorized):
            portal.restrictedTraverse('dept1/tut1/lec1/qn1/@@view');

        # Manager however, can.
        login(portal, MANAGER_ID);
        portal.restrictedTraverse('dept1/tut1/lec1/qn1/@@view');

    def test_schoolsClasses(self):
        """Schools and classes folder should be already created"""
        portal = self.layer['portal']
        login(portal, MANAGER_ID)

        self.assertTrue('schools-and-classes' in portal)
        sac = portal['schools-and-classes']

        # Can't add a lecture
        with self.assertRaisesRegexp(ValueError, 'tw_lecture'):
            sac.invokeFactory(type_name="tw_lecture", id="lec")

        # Can add a class
        sac.invokeFactory(
            type_name="tw_class",
            id="class1",
            title="My nice class",
        )
