import unittest
import tempfile

from zope.schema.interfaces import IVocabularyFactory
from zope.component import queryUtility

from tutorweb.content.vocabularies import parseSettingsFile, LectureSettingsVocabularyFactory

from .base import IntegrationTestCase


class ParseSettingsFileTest(unittest.TestCase):
     def psf(self, settingsDocString):
         with tempfile.NamedTemporaryFile() as tf:
             tf.write(settingsDocString)
             tf.flush()
             return parseSettingsFile(tf.name)

     def test_read(self):
         settings = self.psf("""
Coin awards for students:

* ``award_lecture_answered``: Milli-SMLY awarded for getting grade 5 in a lecture. Default 1000
* ``award_lecture_aced``: Milli-SMLY awarded for getting grade 10 in a lecture. Default 10000
* ``prob_template``: Probability that a student will get a question template instead of a regular question. Default 0.1
* ``grade_algorithm``: Grading algorithm to use. One of weighted, ratiocorrect. Default 'weighted'
* ``chat_competent_grade``: If a student gets a grade higher than this in a lecture, they can be a tutor. Default None
         """)
         self.assertEqual(settings, [
             dict(name='award_lecture_answered', desc='Milli-SMLY awarded for getting grade 5 in a lecture.', default=1000),
             dict(name='award_lecture_aced', desc='Milli-SMLY awarded for getting grade 10 in a lecture.', default=10000),
             dict(name='prob_template', desc='Probability that a student will get a question template instead of a regular question.', default=0.1),
             dict(name='grade_algorithm', desc='Grading algorithm to use. One of weighted, ratiocorrect.', default='weighted'),
             dict(name='chat_competent_grade', desc='If a student gets a grade higher than this in a lecture, they can be a tutor.', default=None),
         ])

class LectureSettingsVocabularyTest(IntegrationTestCase):
    def getVocab(self, name):
        """Fetch a named vocab"""
        util = queryUtility(IVocabularyFactory, name)
        return util(self.layer['portal'])

    def test_fetchValues(self):
        """Check we can fetch vocab and at least one value is inside"""
        vocab = self.getVocab('tutorweb.content.vocabularies.lectureSettings')
        values = [x.value for x in vocab]
        self.assertTrue(u'prob_template' in values)
