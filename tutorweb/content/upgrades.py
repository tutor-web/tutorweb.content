import logging

from Products.CMFCore.utils import getToolByName


def reimportTypes(context, logger=None):
    """"Re-run the types step, to add new types"""
    if logger is None:
        logger = logging.getLogger('tutorweb.content')

    context.runImportStepFromProfile(
        'profile-tutorweb.content:default',
        'typeinfo',
    )


def reimportRegistry(context, logger=None):
    """"Re-run the plone.app.registry step to update registry keys"""
    if logger is None:
        logger = logging.getLogger('tutorweb.content')

    context.runImportStepFromProfile(
        'profile-tutorweb.content:default',
        'plone.app.registry',
    )


def updateLectureSettings(context, logger=None):
    """Update lecture settings dict"""
    def inSettings(settings, key):
        for s in settings:
            if s['key'] == key:
                return True
        return False

    if logger is None:
        logger = logging.getLogger('tutorweb.content')
    portal = getToolByName(context, 'portal_url').getPortalObject()
    portal_catalog = portal.portal_catalog

    # Import registry step so we have the vocab
    context.runImportStepFromProfile(
        'profile-tutorweb.content:default',
        'plone.app.registry',
    )

    # Copy histsel into settings hash if the value is big enough
    brains = portal_catalog(Type=['Lecture', 'Tutorial'])
    for obj in [b.getObject() for b in brains]:
        if getattr(obj, 'histsel', -1.0) < 0:
            continue
        if not getattr(obj, 'settings', None):
            obj.settings = []
        if inSettings(obj.settings, 'hist_sel'):
            continue

        obj.settings.append(dict(
            key='hist_sel',
            value=str(obj.histsel),
        ))
        try:
            del obj.histsel
        except AttributeError:
            pass
