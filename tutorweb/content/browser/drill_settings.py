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
            return ((i['key'], i.get('variant', ''), i['value']) for i in settings)

        def tlate_registry(settings):
            for (k, v) in settings.items():
                if k.endswith(':registered'):
                    k = k[:k.rindex(':registered')]
                    variant = "registered"
                else:
                    variant = ''
                yield (k, variant, v)

        def combine_settings(settings):
            """Take iterator of single values, combine everything into a dict"""
            out = dict()
            for (k, variant, v) in settings:
                # Bodge award_registered_* -> award_*:registered
                if k.startswith("award_registered"):
                    k = re.sub("^award_registered_", "award_", k)
                    variant = "registered"

                m = re.match("(.*):(min|max|shape)$", k)
                if m:
                    k = m.group(1)
                    prop = m.group(2) # :min / :max property
                else:
                    prop = 'value'
                if variant:
                    k = "%s:%s" % (k, variant)

                if k not in out:
                    out[k] = dict()
                out[k][prop] = str(v).strip()

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
                tlate_registry(registry.get('tutorweb.content.lectureSettings', ())),
                tlate(aq_parent(self.context).settings),
                tlate(self.context.settings)):
            out.update(combine_settings(iter))
        return out
