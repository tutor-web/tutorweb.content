import re

from App.config import getConfiguration

from zope.interface import implements
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm

from plone.registry.interfaces import IRegistry

def getConfigKey(name, product_name='tutorweb.content'):
    """Fetch from product config"""
    product_config = getattr(getConfiguration(), 'product_config', {})
    if product_name not in product_config:
        raise RuntimeError("%s not in zope.conf. Edit buildout config" % product_name)
    try:
        return product_config[product_name].get(name)
    except:
        raise RuntimeError("%s was misconfigured, %s missing from zope.conf. Edit buildout config" % (
            product_name,
            name,
        ))


def parseSettingsFile(settingsDoc):
    out = []
    with open(settingsDoc, 'r') as f:
        for line in f:
            m = re.match(r'^\* ``(.*)``: (.*)Default (.*)', line)
            if not m:
                continue

            default = m.group(3)
            if default == "None":
                default = None
            elif default.startswith("'"):
                default = default[1:-1]
            else:
                try:
                    default = int(default)
                except ValueError:
                    try:
                        default = float(default)
                    except ValueError:
                        pass

            out.append(dict(name=m.group(1), desc=m.group(2).strip(), default=default))
    return out


class LectureSettingsVocabulary(object):
    """Turns tutorweb.content.lectureSettings registry entry into a vocab"""
    implements(IVocabularyFactory)

    def __call__(self, context):
        settingsDoc = getConfigKey('settings-documentation')
        terms = []
        for t in parseSettingsFile(settingsDoc):
            terms.append(SimpleVocabulary.createTerm(t['name'], t['name'], "%s: %s Default %s" % (
                t['name'],
                t['desc'],
                t['default'],
            )))
            if isinstance(t['default'], int) or isinstance(t['default'], float):
                terms.append(SimpleVocabulary.createTerm(t['name'] + ":min"))
                terms.append(SimpleVocabulary.createTerm(t['name'] + ":max"))
                terms.append(SimpleVocabulary.createTerm(t['name'] + ":shape"))
        return SimpleVocabulary(terms)

LectureSettingsVocabularyFactory = LectureSettingsVocabulary()


variantsVocab = SimpleVocabulary([
    SimpleTerm(value=u'', title=(u'default')),
    SimpleTerm(value=u'registered', title=(u'registered (student is subscribed to a course)')),
])
