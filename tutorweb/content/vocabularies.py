from zope.component import queryUtility
from zope.interface import implements
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary

from plone.registry.interfaces import IRegistry


class LectureSettingsVocabulary(object):
    """Turns tutorweb.content.lectureSettings registry entry into a vocab"""
    implements(IVocabularyFactory)

    def __call__(self, context):
        registry = queryUtility(IRegistry)
        if registry is None:
            return []

        terms = []
        for v in registry.get('tutorweb.content.lectureSettings', ()):
            terms.append(SimpleVocabulary.createTerm(v))
        return SimpleVocabulary(terms)

LectureSettingsVocabularyFactory = LectureSettingsVocabulary()
