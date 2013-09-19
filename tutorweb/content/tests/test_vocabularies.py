from zope.schema.interfaces import IVocabularyFactory
from zope.component import queryUtility

from .base import IntegrationTestCase


class LectureSettingsVocabularyTest(IntegrationTestCase):
    def test_fetchValues(self):
        """Check we can fetch vocab and at least one value is inside"""
        vocab = self.getVocab('tutorweb.content.vocabularies.lectureSettings')
        values = [x.value for x in vocab]
        self.assertTrue(u'hist_sel' in values)

    def getVocab(self, name):
        """Fetch a named vocab"""
        util = queryUtility(IVocabularyFactory, name)
        return util(self.layer['portal'])
