from unittest import TestCase
import tempfile

import transaction

from zope.app.intid.interfaces import IIntIds
from zope.component import getUtility
from zope.event import notify
from zope.component import getSiteManager
from zope.lifecycleevent import ObjectModifiedEvent
from z3c.relationfield.relation import RelationValue

from plone.app.testing import PloneSandboxLayer
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import IntegrationTesting, FunctionalTesting
from plone.app.testing import applyProfile
from plone.app.testing import setRoles, login, logout
from plone.app.textfield.value import RichTextValue
from plone.testing.z2 import Browser, installProduct
from zope.configuration import xmlconfig

from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.tests.utils import MockMailHost
from Products.MailHost.interfaces import IMailHost

USER_A_ID = "Arnold"
USER_B_ID = "Betty"
USER_C_ID = "Caroline"
USER_D_ID = "Daryl"
MANAGER_ID = "BigBoss"


class TestFixture(PloneSandboxLayer):
    default_bases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        import tutorweb.content
        import tutorweb.content.tests.mockviews
        import collective.alias
        xmlconfig.include(configurationContext, 'meta.zcml', tutorweb.content)
        xmlconfig.include(configurationContext, 'configure.zcml', tutorweb.content)
        xmlconfig.include(configurationContext, 'configure.zcml', tutorweb.content.tests.mockviews)
        xmlconfig.includeOverrides(configurationContext, 'overrides.zcml', tutorweb.content)
        xmlconfig.include(configurationContext, 'configure.zcml', collective.alias)
        configurationContext.execute_actions()

        # https://github.com/plone/plone.app.event/issues/81#issuecomment-23930996
        installProduct(app, 'Products.DateRecurringIndex')

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'tutorweb.content:default')

        # Import just collective.alias types, since we don't have Collections installed
        setup = getToolByName(portal, 'portal_setup')
        setup.runImportStepFromProfile('profile-collective.alias:default', 'typeinfo')

        # Configure default chain, so tutorweb.quizdb can publish content
        workflowTool = getToolByName(portal, 'portal_workflow')
        workflowTool.setDefaultChain("simple_publication_workflow")

        # Creates some users
        acl_users = getToolByName(portal, 'acl_users')
        mtool = getToolByName(portal, 'portal_membership')
        for id in [USER_A_ID, USER_B_ID, USER_C_ID, USER_D_ID]:
            acl_users.userFolderAddUser(
                id, 'secret'+id[0],
                ['Member'],[]
            )
            mtool.getMemberById(id).setMemberProperties(dict(
                email=id + '@example.com',
                accept=True,
            ))
        acl_users.userFolderAddUser(
            MANAGER_ID, 'secret' + MANAGER_ID[0],
            ['Manager'],[]
        )

        # Set-up fake mailer
        portal.MailHost = mailhost = MockMailHost('MailHost')
        sm = getSiteManager(context=portal)
        sm.unregisterUtility(provided=IMailHost)
        sm.registerUtility(mailhost, provided=IMailHost)
        portal.email_from_address = 'tutorweb-ut@example.com'
        transaction.commit()

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
            choices=[dict(text="orange", correct=False), dict(text="green", correct=True)],
            finalchoices=[],
        )
        portal['dept1']['tut1']['lec1'].invokeFactory(
            type_name="tw_latexquestion",
            id="qn2",
            title="Unittest D1 T1 L1 Q2",
            choices=[dict(text="orange", correct=False), dict(text="blue", correct=False)],
            finalchoices=[dict(text="green", correct=True)],
        )
        portal['dept1']['tut1'].invokeFactory(
            type_name="tw_lecture",
            id="lec2",
            title="Unittest D1 T1 L2",
        )
        portal['dept1']['tut1']['lec2'].invokeFactory(
            type_name="tw_latexquestion",
            id="qn1",
            title="Unittest D1 T1 L2 Q1",
            choices=[dict(text="pink", correct=False), dict(text="purple", correct=True)],
            finalchoices=[],
        )
        portal['dept1']['tut1']['lec2'].invokeFactory(
            type_name="tw_latexquestion",
            id="qn2",
            title="Unittest D1 T1 L2 Q2",
            choices=[dict(text="pink", correct=False), dict(text="purple", correct=True)],
            finalchoices=[],
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
        transaction.commit()

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

    def rtv(self, string, mimeType="text/x-tex", outputMimeType='text/html'):
        return RichTextValue(
            string,
            mimeType=mimeType,
            outputMimeType=outputMimeType,
        )


class FunctionalTestCase(IntegrationTestCase):
    layer = TUTORWEB_CONTENT_FUNCTIONAL_TESTING

    def getBrowser(self, url, user=USER_A_ID):
        """Create a browser, optionally with auth details in headers"""
        browser = Browser(self.layer['app'])
        if user:
            browser.addHeader('Authorization', 'Basic %s:%s' % (
                user,
                'secret' + user[0],
            ))
        if url:
            browser.open(url)
        return browser

def setRelations(target, field, objs):
    """Configure a relation field"""
    intids = getUtility(IIntIds)
    val = (
        [RelationValue(intids.getId(obj)) for obj in objs]
        if type(objs) is list
        else RelationValue(intids.getId(objs)))
    setattr(target, field, val)
    notify(ObjectModifiedEvent(target))

def testImage():
    """Returns a NamedTemporaryFile with an image in it"""
    imagetf = tempfile.NamedTemporaryFile(suffix='.png')
    imagetf.write(
        '\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00'
        '\x01\x01\x03\x00\x00\x00%\xdbV\xca\x00\x00\x00\x03PLTE\xff\xff'
        '\xff\xa7\xc4\x1b\xc8\x00\x00\x00\nIDAT\x08\xd7c`\x00\x00\x00\x02'
        '\x00\x01\xe2!\xbc3\x00\x00\x00\x00IEND\xaeB`\x82')
    imagetf.flush()
    return imagetf
