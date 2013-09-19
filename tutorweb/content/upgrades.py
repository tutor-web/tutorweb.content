import logging

from Products.CMFCore.utils import getToolByName

def updateLectureSettings(context, logger=None):
    """Update lecture settings dict"""
    if logger is None:
        logger = logging.getLogger('aibel.content')
    portal = getToolByName(context, 'portal_url').getPortalObject()
    portal_catalog = portal.portal_catalog

    # Import registry step so we have the vocab
    context.runImportStepFromProfile(
        'profile-tutorweb.content:default',
        'plone.app.registry',
    )

    # Copy histsel into settings hash if the value is big enough
    brains = portal_catalog(
        Type=dict(
            query=['Lecture', 'Tutorial'],
        ),
    )
    for obj in [b.getObject() for b in brains]:
        if getattr(obj, 'histsel', -1.0) < 0:
            continue
        if not getattr(obj, 'settings', None):
            obj.settings = {}
        if 'hist_sel' in obj.settings:
            continue
        obj.settings['hist_sel'] = obj.histsel
        del obj.histsel
