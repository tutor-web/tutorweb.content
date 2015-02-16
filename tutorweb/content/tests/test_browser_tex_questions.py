import cStringIO
import urllib

from plone.app.testing import login
from plone.namedfile.file import NamedBlobImage

from .base import IntegrationTestCase, FunctionalTestCase, MANAGER_ID, testImage


class LaTeXQuestionTeXViewTest(IntegrationTestCase):
    """Convert individual question"""
    def test_question(self):
        imagetf = testImage()
        imagetf.seek(0)
        imageContents = imagetf.read()
        self.assertEqual(self.questionToTeX(dict(
            title="qtd image question",
            text=self.rtv("Here is some text with an image below"),
            image=NamedBlobImage(
                data=imageContents,
                contentType='image/png'
            ),
            choices=[
                dict(text='woo', correct=False),
                dict(text='yay', correct=False),
            ],
            finalchoices=[
                dict(text='lastone', correct=True),
            ],
            explanation=self.rtv("Apparently you are"),
            timesanswered=980,
            timescorrect=640,
        )).strip(),"""
%ID qtd0
%title qtd image question
%format latex
%image http://nohost/plone/dept1/tut1/lec1/qtd0/@@download-image
Here is some text with an image below

a) woo
b) yay
xa.true) lastone

%Explanation
Apparently you are
%r 640
%n 980
        """.strip())

        self.assertEqual(self.questionToTeX(dict(
            title="qtd text question",
            text=self.rtv("Here is some text"),
            choices=[
                dict(text='woo', correct=False),
                dict(text='yay', correct=True),
            ],
            finalchoices=[
                dict(text='lastone', correct=False),
                dict(text='reallylastone', correct=False),
            ],
        )).strip(),"""
%ID qtd1
%title qtd text question
%format latex
Here is some text

a) woo
b.true) yay
xa) lastone
xb) reallylastone
        """.strip())

    def questionToTeX(self, qnData):
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
        return lecture[qnId].restrictedTraverse('@@tex')()

class LectureTeXViewTest(FunctionalTestCase):
    """Convert an entire lecture in one go"""
    def test_questions(self):
        self.assertEqual(
            self.getBrowser('http://nohost/plone/dept1/tut1/lec2/@@tex', user=MANAGER_ID).contents.strip(),
            """
%ID qn1
%title Unittest D1 T1 L2 Q1
%format latex
a) pink
b.true) purple

%===
%ID qn2
%title Unittest D1 T1 L2 Q2
%format latex
a) pink
b.true) purple
            """.strip(),
        )

class LectureTeXImportTest(FunctionalTestCase):
    def test_shortFile(self):
        """Short files get buffered by Zope"""
        browser = self.uploadTeX('http://nohost/plone/dept1/tut1/lec2', """
%ID     q54
%title  Imported question
%format latex
A man walks into a bar
a)      $T_h = a$
b)      $T_h = b$
c)      ouch, it was an iron bar.
        """)
        # Browser returned to lecture page
        self.assertEqual(browser.url, 'http://nohost/plone/dept1/tut1/lec2')
        # The question got created
        qn = self.getObject('dept1/tut1/lec2/q54')
        self.assertEqual(qn.title, u'Imported question')

    def test_longFile(self):
        """Long files will get written to disk by Zope"""
        questions = ""
        for i in range(100):
            if i > 0:
                questions += "\n%===\n"
            questions += """
%%ID     q%d
%%title  Imported question #%d
%%format latex
A man walks into a bar
a)      $T_h = a$
b)      $T_h = b$
c)      ouch, it was an iron bar.
            """ % (i, i)
        # Browser returned to lecture page
        browser = self.uploadTeX('http://nohost/plone/dept1/tut1/lec2', questions)
        # All the questions were created
        self.assertEqual(browser.url, 'http://nohost/plone/dept1/tut1/lec2')
        self.assertEqual(
            [x.id for x in self.getObject('dept1/tut1/lec2').getChildNodes()],
            ['qn1', 'qn2'] + ['q%d' % i for i in range(100)],
        )

    def test_imageTeX(self):
        imagetf = testImage()
        browser = self.uploadTeX('http://nohost/plone/dept1/tut1/lec2', """
%%ID	q92
%%title	Question with image
%%format	latex
%%image file://%s
        """ % imagetf.name)
        # Browser returned to lecture page
        self.assertEqual(browser.url, 'http://nohost/plone/dept1/tut1/lec2')
        # The question got created
        qn = self.getObject('dept1/tut1/lec2/q92')
        self.assertEqual(qn.title, u'Question with image')
        self.assertEqual(qn.image.filename, u'file%%3A%%2F%%2F%s' % urllib.quote_plus(imagetf.name))
        self.assertEqual(qn.image.contentType, 'image/png')
        imagetf.seek(0)
        self.assertEqual(qn.image.data, imagetf.read())
        imagetf.close()

    def test_leaveValuesAlone(self):
        browser = self.uploadTeX('http://nohost/plone/dept1/tut1/lec2', """
%ID     q88
%title  Imported question
%format latex
A man walks into a bar
a)      $T_h = a$
b)      $T_h = b$
c)      ouch, it was an iron bar.
%r 22
%n 19
        """)
        # Browser returned to lecture page
        self.assertEqual(browser.url, 'http://nohost/plone/dept1/tut1/lec2')
        # Question had it's answered / correct values updated
        qn = self.getObject('dept1/tut1/lec2/q88')
        self.assertEqual(qn.text.raw, u'A man walks into a bar')
        self.assertEqual(qn.timesanswered, 19)
        self.assertEqual(qn.timescorrect, 22)

        # Updating question again, not updating values
        browser = self.uploadTeX('http://nohost/plone/dept1/tut1/lec2', """
%ID     q88
%title  Imported question
%format latex
A man walks into a lamp post
        """)
        # Browser returned to lecture page
        self.assertEqual(browser.url, 'http://nohost/plone/dept1/tut1/lec2')
        # Question still has answered / correct values
        qn = self.getObject('dept1/tut1/lec2/q88')
        self.assertEqual(qn.title, u'Imported question')
        self.assertEqual(qn.text.raw, u'A man walks into a lamp post')
        self.assertEqual(qn.timesanswered, 19)
        self.assertEqual(qn.timescorrect, 22)

        # Updating question again, updating %r %n
        # NB: MySQL will overwrite these values once a student uploads answers
        browser = self.uploadTeX('http://nohost/plone/dept1/tut1/lec2', """
%ID     q88
%format latex
A man walks into a tree
%r 990
%n 999
        """)
        # Browser returned to lecture page
        self.assertEqual(browser.url, 'http://nohost/plone/dept1/tut1/lec2')
        # Question still has answered / correct values
        qn = self.getObject('dept1/tut1/lec2/q88')
        self.assertEqual(qn.title, u'Imported question')
        self.assertEqual(qn.text.raw, u'A man walks into a tree')
        self.assertEqual(qn.timesanswered, 999)
        self.assertEqual(qn.timescorrect, 990)

    def uploadTeX(self, lecUrl, tex):
        browser = self.getBrowser(lecUrl, user=MANAGER_ID)
        ctrl = browser.getControl('Update questions from TeX file')
        ctrl.add_file(cStringIO.StringIO(tex), 'text/plain', 'test.tex')
        browser.getControl('Upload').click()
        return browser

    def getObject(self, path):
        return self.layer['portal'].unrestrictedTraverse(path)
