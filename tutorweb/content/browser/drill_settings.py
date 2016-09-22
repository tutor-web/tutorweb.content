import itertools
import re

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

        def combine_settings(settings):
            """Take iterator of single values, combine everything into a dict"""
            out = dict()
            for (k, v) in settings:
                m = re.match("(.*):(min|max)$", k)

                if m:
                    # :min / :max property
                    if not isinstance(out.get(m.group(1), None), dict):
                        # Either property not set yet, or a non-dict value
                        out[m.group(1)] = dict()
                    out[m.group(1)][m.group(2)] = v
                else:
                    out[k] = v

            # Moosh dicts back to :min and :max
            for base_key in out.keys():
                if not isinstance(out[base_key], dict):
                    continue
                for (k, v) in out[base_key].items():
                    out['%s:%s' % (base_key, k)] = v
                del out[base_key]

            return out

        registry = queryUtility(IRegistry)
        if registry is None:
            raise ValueError("Cannot get Plone registry")

        # Combine, later items override previous ones
        return combine_settings(itertools.chain(
            registry.get('tutorweb.content.lectureSettings', ()).items(),
            tlate(aq_parent(self.context).settings),
            tlate(self.context.settings),
        ))
