from unittest import TestCase

from zope.app.intid.interfaces import IIntIds
from zope.component import getUtility
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent
from z3c.relationfield.relation import RelationValue

from plone.app.testing import PloneSandboxLayer
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import IntegrationTesting, FunctionalTesting
from plone.app.testing import applyProfile
from plone.app.testing import setRoles, login, logout
from zope.configuration import xmlconfig

from Products.CMFCore.utils import getToolByName

USER_A_ID = "Arnold"
USER_B_ID = "Betty"
USER_C_ID = "Caroline"
MANAGER_ID = "BigBoss"


class TestFixture(PloneSandboxLayer):
    default_bases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        import tutorweb.content
        xmlconfig.include(configurationContext, 'meta.zcml', tutorweb.content)
        xmlconfig.include(configurationContext, 'configure.zcml', tutorweb.content)
        xmlconfig.includeOverrides(configurationContext, 'overrides.zcml', tutorweb.content)
        configurationContext.execute_actions()

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'tutorweb.content:default')

        # Creates some users
        acl_users = getToolByName(portal, 'acl_users')
        for id in [USER_A_ID, USER_B_ID, USER_C_ID]:
            acl_users.userFolderAddUser(
                id, 'secret'+id[0],
                ['Member'],[]
            )
        acl_users.userFolderAddUser(
            MANAGER_ID, 'secretBB',
            ['Manager'],[]
        )

        # Create some content
        login(portal, MANAGER_ID)
        portal.invokeFactory(
            type_name="tw_department",
            id="dept1",
            title="Unittest D1",
        )
        portal.invokeFactory(
            type_name="tw_department",
            id="dept2",
            title="Unittest D2",
        )
        portal['dept1'].invokeFactory(
            type_name="tw_tutorial",
            id="tut1",
            title="Unittest D1 T1",
        )
        portal['dept1']['tut1'].invokeFactory(
            type_name="tw_lecture",
            id="lec1",
            title="Unittest D1 T1 L1",
        )
        portal['dept1']['tut1']['lec1'].invokeFactory(
            type_name="tw_latexquestion",
            id="qn1",
            title="Unittest D1 T1 L1 Q1",
        )
        portal['dept1'].invokeFactory(
            type_name="tw_course",
            id="course1",
            title="Unittest C1",
        )
        setRelations(portal['dept1']['course1'], 'tutorials', [
            portal['dept1']['tut1'],
        ])
        setRelations(
            portal['dept1']['tut1'],
            'primarycourse',
            portal['dept1']['course1'],
        )

    def tearDownPloneSite(self, portal):
        pass


FIXTURE = TestFixture()

TUTORWEB_CONTENT_INTEGRATION_TESTING = IntegrationTesting(
    bases=(FIXTURE,),
    name="tutorweb.content:Integration",
    )
TUTORWEB_CONTENT_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(FIXTURE,),
    name="tutorweb.content:Functional",
    )


class IntegrationTestCase(TestCase):
    layer = TUTORWEB_CONTENT_INTEGRATION_TESTING


class FunctionalTestCase(TestCase):
    layer = TUTORWEB_CONTENT_FUNCTIONAL_TESTING


def setRelations(target, field, objs):
    """Configure a relation field"""
    intids = getUtility(IIntIds)
    val = (
        [RelationValue(intids.getId(obj)) for obj in objs]
        if type(objs) is list
        else RelationValue(intids.getId(objs)))
    setattr(target, field, val)
    notify(ObjectModifiedEvent(target))
