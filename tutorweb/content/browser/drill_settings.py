import itertools

from Acquisition import aq_parent
from zope.component import queryUtility

from plone.registry.interfaces import IRegistry

from .jsonbrowserview import JSONBrowserView


class DrillSettingsView(JSONBrowserView):
    def asDict(self, data={}):
        def tlate(settings):
            """Settings are stored as list of dicts, turn into list of tuples"""
            if not settings:
                return []
            return ((i['key'], i['value']) for i in settings)

        registry = queryUtility(IRegistry)
        if registry is None:
            raise ValueError("Cannot get Plone registry")

        # Combine, later items override previous ones
        return dict(itertools.chain(
            tlate(aq_parent(self.context).settings),
            tlate(self.context.settings),
        ))
