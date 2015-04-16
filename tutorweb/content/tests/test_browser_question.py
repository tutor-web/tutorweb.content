# -*- coding: utf8 -*-
from zope.publisher.interfaces import NotFound

from plone.app.testing import login
from plone.namedfile.file import NamedBlobImage
from Products.CMFCore.utils import getToolByName

from ..datauri import encodeDataUri
from .base import IntegrationTestCase, MANAGER_ID, testImage


class LaTeXQuestionStructTest(IntegrationTestCase):
    def doTransform(self, content):
        pt = getToolByName(self.layer['portal'], 'portal_transforms')
        return pt.convertTo(
            'text/html',
            content.encode('utf-8'),
            mimetype='text/x-tex',
            encoding='utf-8',
        ).getData().decode('utf-8')

    def test_asDict(self):
        # Test ~empty question to make sure we don't fall over
        self.assertEqual(self.questionToDict(dict(
            title="qtd empty question",
        )), dict(
            _type='multichoice',
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
            _type='multichoice',
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
            _type='multichoice',
            title=u'qtd image question',
            text=self.doTransform('Here is some text with an image below')
                + '<img src="%s" width="1" height="1" />' % encodeDataUri(imageContents, "image/png"),
            choices=[],
            shuffle=[],
            answer=dict(
                correct=[],
                explanation='',
            )
        ))

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

class QuestionPackStructTest(IntegrationTestCase):
    maxDiff = None

    def test_asDict(self):
        from plone.namedfile.file import NamedBlobFile

        portal = self.layer['portal']
        login(portal, MANAGER_ID)
        lecture = portal['dept1']['tut1']['lec1']
        qn = lecture[lecture.invokeFactory(
            type_name="tw_questionpack",
            id='qnpack01',
            questionfile=NamedBlobFile(
                data="""
%ID umGen1-0
%title Einföld Umröðun
%format latex
Einangrið og finnið þannig gildi $x$ í eftirfarandi jöfnu. Merkið við þann möguleika sem best á við.
$$\frac{7}{4x-8}-8=3$$

a.true) $\frac{95}{44}$
b) $-\frac{95}{44}$
c) $-\frac{19}{4}$
d) $\frac{19}{4}$

%Explanation
Við leggjum 8 við báðum megin við jafnaðarmerkið, og fáum þá $\frac{7}{4x-8}=11$
%===
%ID Ag10q16
%title Táknmál mengjafræðinnar - mengi
%format latex
%image data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==
Hvert af eftirtöldu er rétt fyrir öll mengi $A,B,C$?

a.true) $\left((A \cup B) \cap C \right) \backslash B \subset A \cap C$
b) $\left((A \cup B) \cap C \right) \backslash B =  \emptyset $
c) $\left((A \cup B) \cap C \right) \backslash B \supset  A \cap C$

%Explanation
Stak sem er í annaðhvort $A$ eða $B$ og er í $C$ en
                """,
                contentType='text/x-tex',
                filename=u'qnpackcontent.tex',
            ),
        )]
        view = qn.restrictedTraverse('@@data')

        # Test 404's
        with self.assertRaisesRegexp(NotFound, 'question_id'):
            view.asDict() # No question_id
        with self.assertRaisesRegexp(NotFound, 'notarealquestion'):
            view.asDict(data=dict(question_id='notarealquestion')) # Invalid question_id

        # Can get questions by setting data
        self.assertEqual(view.asDict(data=dict(question_id='umGen1-0')), {
            '_type': 'multichoice',
            'answer': {'correct': [0],
            'explanation': u'<div class="parse-as-tex">Vi\xf0 leggjum 8 vi\xf0 b\xe1\xf0um megin vi\xf0 jafna\xf0armerki\xf0, og f\xe1um \xfe\xe1 $\x0crac{7}{4x-8}=11$</div>'},
            'choices': [u'<div class="parse-as-tex">$\x0crac{95}{44}$</div>',
                        u'<div class="parse-as-tex">$-\x0crac{95}{44}$</div>',
                        u'<div class="parse-as-tex">$-\x0crac{19}{4}$</div>',
                        u'<div class="parse-as-tex">$\x0crac{19}{4}$</div>'],
            'shuffle': [0, 1, 2, 3],
            'text': u'<div class="parse-as-tex">Einangri\xf0 og finni\xf0 \xfeannig gildi $x$ \xed eftirfarandi j\xf6fnu. Merki\xf0 vi\xf0 \xfeann m\xf6guleika sem best \xe1 vi\xf0.<br />$$\x0crac{7}{4x-8}-8=3$$</div>',
            'title': u'Einf\xf6ld Umr\xf6\xf0un',
        })
        self.assertEqual(view.asDict(data=dict(question_id=['Ag10q16'])), {
            '_type': 'multichoice',
            'answer': {'correct': [0],
                       'explanation': u'<div class="parse-as-tex">Stak sem er \xed anna\xf0hvort $A$ e\xf0a $B$ og er \xed $C$ en</div>'},
            'choices': [u'<div class="parse-as-tex">$\\left((A \\cup B) \\cap C \right) \x08ackslash B \\subset A \\cap C$</div>',
                        u'<div class="parse-as-tex">$\\left((A \\cup B) \\cap C \right) \x08ackslash B =  \\emptyset $</div>',
                        u'<div class="parse-as-tex">$\\left((A \\cup B) \\cap C \right) \x08ackslash B \\supset  A \\cap C$</div>'],
            'shuffle': [0, 1, 2],
            'text': u'<div class="parse-as-tex">Hvert af eftirt\xf6ldu er r\xe9tt fyrir \xf6ll mengi $A,B,C$?</div>' +
                    u'<img src="data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==" />',
            'title': u'T\xe1knm\xe1l mengjafr\xe6\xf0innar - mengi',
        })
