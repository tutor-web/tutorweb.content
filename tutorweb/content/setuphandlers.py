import logging

from plone.app.dexterity.behaviors import constrains
from Products.CMFPlone.interfaces.constrains import IConstrainTypes

from Products.CMFCore.utils import getToolByName


def installTransforms(context, logger=None):
    if logger is None:
        logger = logging.getLogger('tutorweb.content')
    if context.readDataFile('tutorweb.content.marker.txt') is None:
        return

    transforms = getToolByName(context, 'portal_transforms')
    try:
        transforms.unregisterTransform('tex_to_html')
        logger.info('Unregistered tex_to_html')
    except AttributeError:
        pass  # Not there yet, doesn't matter
    transforms.manage_addTransform('tex_to_html', 'tutorweb.content.transforms.tex_to_html')
    logger.info('Registered tex_to_html')


def uninstallTransforms(context, logger=None):
    if logger is None:
        logger = logging.getLogger('tutorweb.content')
    if context.readDataFile('tutorweb.content.marker.txt') is None:
        return

    transforms = getToolByName(context, 'portal_transforms')
    try:
        transforms.unregisterTransform('tex_to_html')
        logger.info('Unregistered tex_to_html')
    except AttributeError:
        logger.info('Could not unregister tex_to_html!')


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
