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
                m = re.match("(.*):(min|max|shape)$", k)

                if m:
                    # :min / :max property
                    if m.group(1) not in out:
                        out[m.group(1)] = dict()
                    out[m.group(1)][m.group(2)] = v.strip()
                else:
                    if k not in out:
                        out[k] = dict()
                    out[k]['value'] = v.strip()

            # Someone seems to have been setting :min == :max, creating needless noise
            for (k, v) in out.iteritems():
                if 'min' in v and 'max' in v and v['min'] == v['max']:
                    out[k] = dict(value=v['max'])
            return out

        registry = queryUtility(IRegistry)
        if registry is None:
            raise ValueError("Cannot get Plone registry")

        # Combine, later items override previous ones
        out = {}
        for iter in (
                registry.get('tutorweb.content.lectureSettings', ()).items(),
                tlate(aq_parent(self.context).settings),
                tlate(self.context.settings)):
            out.update(combine_settings(iter))
        return out
