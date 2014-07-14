import logging
import pkgutil

from plone.app.dexterity.behaviors import constrains
from Products.CMFPlone.interfaces.constrains import IConstrainTypes

from Products.CMFCore.utils import getToolByName


def availableTransforms():
    try:
        import tutorweb.content.transforms
        return [x[1] for x in pkgutil.iter_modules(tutorweb.content.transforms.__path__)]
    except ImportError:
        return []


def installTransforms(context, logger=None):
    if logger is None:
        logger = logging.getLogger('tutorweb.content')
    if context.readDataFile('tutorweb.content.marker.txt') is None:
        return

    transforms = getToolByName(context, 'portal_transforms')
    for tform in availableTransforms():
        try:
            transforms.unregisterTransform(tform)
            logger.info('Unregistered %s' % tform)
        except AttributeError:
            pass  # Not there yet, doesn't matter
        transforms.manage_addTransform(tform, 'tutorweb.content.transforms.%s' % tform)
        logger.info('Registered %s' % tform)


def uninstallTransforms(context, logger=None):
    if logger is None:
        logger = logging.getLogger('tutorweb.content')
    if context.readDataFile('tutorweb.content.marker.txt') is None:
        return

    transforms = getToolByName(context, 'portal_transforms')
    for tform in availableTransforms():
        try:
            transforms.unregisterTransform(tform)
            logger.info('Unregistered %s' % tform)
        except AttributeError:
            logger.info('Could not unregister %s!' % tform)


def createSchoolsClassesFolder(context, logger=None):
    """Create schools & classes folder"""
    if logger is None:
        logger = logging.getLogger('tutorweb.content')
    if hasattr(context, 'readDataFile'):
        # Installing profile
        if context.readDataFile('tutorweb.content.marker.txt') is None:
            return
        portal = context.getSite()
    else:
        # Upgrade step
        portal = getToolByName(context, 'portal_url').getPortalObject()

    # Create folder if it doesn't already exist
    if 'schools-and-classes' not in portal:
        portal.invokeFactory(
            type_name='Folder',
            id='schools-and-classes',
            title=u'Schools and Classes',
        )

    # Restrict folder so we have a structure of classes
    types = IConstrainTypes(portal['schools-and-classes'])
    types.setConstrainTypesMode(constrains.ENABLED)
    types.setLocallyAllowedTypes(['Folder', 'tw_class'])
    types.setImmediatelyAddableTypes(['Folder', 'tw_class'])
