import os.path

import transaction
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManager import setSecurityPolicy
from Testing.makerequest import makerequest
from Products.CMFCore.tests.base.security import PermissiveSecurityPolicy, OmnipotentUser
from zope.component.hooks import setSite


def getApplication(configFile):
    """Start Zope/Plone based on a config, return root app"""
    from Zope2.Startup.run import configure
    configure(configFile)
    import Zope2
    return Zope2.app()


def guessConfigFile():
    """Guess location of Zope config"""
    for f in ['instance', 'instance-debug', 'instance1']:
        config_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'parts', f, 'etc', 'zope.conf')
        if os.path.exists(config_path):
            return config_path
    raise ValueError("Cannot find zope.conf!")


def scriptInit(sitename, configFile=None):
    """
    Wire up security, fake request and site

    https://docs.plone.org/develop/plone/misc/commandline.html
    """
    app = getApplication(configFile or guessConfigFile())

    # Use Zope application server user database (not plone site)
    admin = app.acl_users.getUserById("admin")
    newSecurityManager(None, admin)

    _policy=PermissiveSecurityPolicy()
    _oldpolicy=setSecurityPolicy(_policy)
    newSecurityManager(None, OmnipotentUser().__of__(app.acl_users))
    app = makerequest(app)

    # Get Plone site object from Zope application server root
    site = app.unrestrictedTraverse(sitename)
    site.setupCurrentSkin(app.REQUEST)
    setSite(site)
    return app, site


def scriptCommit(app):
    """Commit any changes the script made"""
    transaction.commit()
    app._p_jar.sync()
