from plone.app.textfield.value import RichTextValue
from plone.app.testing import login

from .base import IntegrationTestCase, MANAGER_ID


class LaTeXQuestionStructTest(IntegrationTestCase):
    def test_asDict(self):
        # Test ~empty question to make sure we don't fall over
        self.assertEqual(self.questionToDict(dict(
            title="qtd empty question",
        )), dict(
            title=u'qtd empty question',
            text=u'',
            choices=[],
            shuffle=[],
            answer=dict(
                correct=[],
                explanation='',
            )
        ))

        # Answers appear in the correct place
        self.assertEqual(self.questionToDict(dict(
            title="qtd empty question",
            text=self.rtv("Are you exicted?"),
            choices=[
                dict(text='woo', correct=False),
                dict(text='yay', correct=False),
            ],
            finalchoices=[
                dict(text='lastone', correct=True),
            ],
            explanation=self.rtv("Apparently you are"),
        )), dict(
            title=u'qtd empty question',
            text='<div class="parse-as-tex">Are you exicted?</div>',
            choices=[
                '<div class="parse-as-tex">woo</div>',
                '<div class="parse-as-tex">yay</div>',
                '<div class="parse-as-tex">lastone</div>',
            ],
            shuffle=[0, 1],
            answer=dict(
                correct=[2],
                explanation='<div class="parse-as-tex">Apparently you are</div>',
            )
        ))

    def rtv(self, string, mimeType="application/x-tex"):
        return RichTextValue(
            string,
            mimeType="text/x-tex",
            outputMimeType='text/html',
        )

    def questionToDict(self, qnData):
        if not hasattr(self, 'qnCounter'):
            self.qnCounter = 0
        else:
            self.qnCounter += 1
        qnId = "qtd%d" % self.qnCounter

        portal = self.layer['portal']
        login(portal, MANAGER_ID)
        lecture = portal['dept1']['tut1']['lec1']
        lecture.invokeFactory(
            type_name="tw_latexquestion",
            id=qnId,
            **qnData)
        return lecture[qnId].restrictedTraverse('@@data').asDict()
