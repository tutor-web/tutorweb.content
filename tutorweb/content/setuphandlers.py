import logging

from Products.CMFCore.utils import getToolByName


def installTransforms(context, logger=None):
    if logger is None:
        logger = logging.getLogger('tutorweb.content')
    if context.readDataFile('tutorweb.content.marker.txt') is None:
        return

    transforms = getToolByName(context, 'portal_transforms')
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
