import transaction

from Products.CMFCore.utils import getToolByName

from .base import FunctionalTestCase


class LoggedInHandlerTest(FunctionalTestCase):
    def test_redirectLogin(self):
        portal = self.layer['portal']
        acl_users = getToolByName(portal, 'acl_users')
        mtool = getToolByName(portal, 'portal_membership')

        # Create test user
        user_id = 'redirectloginuser'
        user_pass = 'secretrlu'
        acl_users.userFolderAddUser(
            user_id, user_pass,
            ['Member'], []
        )
        transaction.commit()

        # Try logging in, should be prompted for more details
        browser = self.doLogin(user_id, user_pass)
        self.assertTrue(
            browser.url,
            'http://nohost/plone/@@personal-information',
        )

        # Set full name, no longer prompted
        mtool.getMemberById(user_id).setMemberProperties(dict(
            fullname=u'Edwina Curry',
        ))
        browser = self.doLogin(user_id, user_pass)
        self.assertTrue(
            browser.url,
            'http://nohost/plone/came_from',
        )

    def doLogin(self, u, p):
        """Use the login form to log in, return browser"""
        browser = self.getBrowser('http://nohost/plone/login?'
                                  'came_from=http%3A//nohost/plone/came_from')
        browser.getControl('Login Name').value = u
        browser.getControl('Password').value = p
        browser.getControl('Log in').click()
        browser.getControl('Continue').click()
        return browser
