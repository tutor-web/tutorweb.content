from plone.app.textfield.value import RichTextValue
from plone.app.testing import login
from plone.namedfile.file import NamedBlobImage
from Products.CMFCore.utils import getToolByName

from .base import IntegrationTestCase, MANAGER_ID, testImage


class LaTeXQuestionStructTest(IntegrationTestCase):
    def doTransform(self, content):
        pt = getToolByName(self.layer['portal'], 'portal_transforms')
        return pt.convertTo('text/html', content, mimetype='text/x-tex').getData()

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
            text=self.doTransform('Are you exicted?'),
            choices=[self.doTransform(x) for x in ['woo', 'yay', 'lastone']],
            shuffle=[0, 1],
            answer=dict(
                correct=[2],
                explanation=self.doTransform('Apparently you are'),
            )
        ))

        # Images get data uri'ed
        imagetf = testImage()
        imagetf.seek(0)
        imageContents = imagetf.read()
        self.assertEqual(self.questionToDict(dict(
            title="qtd image question",
            text=self.rtv("Here is some text with an image below"),
            image=NamedBlobImage(
                data=imageContents,
                contentType='image/png'
            ),
        )), dict(
            title=u'qtd image question',
            text=self.doTransform('Here is some text with an image below')
                +'<img src="data:image/png;base64,%s" width="1" height="1" />' % imageContents.encode("base64").replace("\n", ""),
            choices=[],
            shuffle=[],
            answer=dict(
                correct=[],
                explanation='',
            )
        ))

    def test_updateStats(self):
        portal = self.layer['portal']
        login(portal, MANAGER_ID)
        qn = portal.restrictedTraverse('dept1/tut1/lec1/qn1')
        qnView = qn.restrictedTraverse('@@data')

        qn.timesanswered = 5
        qn.timescorrect = 6
        qnView.updateStats(8,9)
        self.assertEqual(qn.timesanswered, 8)
        self.assertEqual(qn.timescorrect, 9)

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
