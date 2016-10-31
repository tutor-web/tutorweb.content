import cStringIO
import os.path
import urllib

from plone.app.testing import login
from plone.namedfile.file import NamedBlobImage

from ..datauri import encodeDataUri

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
%image data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAQMAAAAl21bKAAAAA1BMVEX///+nxBvIAAAACklEQVQI12NgAAAAAgAB4iG8MwAAAABJRU5ErkJggg==
Here is some text with an image below

a) woo
b) yay
xa.true) lastone

%Explanation
Apparently you are
%r 640
%n 980
        """.strip())

        # Make sure image filename gets encoded too
        self.assertEqual(self.questionToTeX(dict(
            title="qtd image question",
            text=self.rtv("Here is some text with an image below"),
            image=NamedBlobImage(
                data=imageContents,
                contentType='image/png',
                filename=u"moo.png",
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
%ID qtd1
%title qtd image question
%format latex
%image data:image/png;filename=moo.png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAQMAAAAl21bKAAAAA1BMVEX///+nxBvIAAAACklEQVQI12NgAAAAAgAB4iG8MwAAAABJRU5ErkJggg==
Here is some text with an image below

a) woo
b) yay
xa.true) lastone

%Explanation
Apparently you are
%r 3
%n 99
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
%ID qtd2
%title qtd text question
%format latex
Here is some text

a) woo
b.true) yay
xa) lastone
xb) reallylastone
        """.strip())

        # We can serialise question templates
        self.assertEqual(self.questionToTeX(dict(
            type_name='tw_questiontemplate',
            title='Question Template',
            hints=self.rtv('Here is a hint\nIt\'s a multiline string'),
            example_text=self.rtv('Here is some example text\nIt\'s a multiline string too'),
            example_choices=[
                dict(text='woo', correct=False),
                dict(text='yay', correct=True),
            ],
            example_explanation=self.rtv('Here is some example explanation\nIt\'s a multiline string too'),
        )).strip(),"""
%ID qtd3
%title Question Template
%format tw_questiontemplate

%hints
Here is a hint
It's a multiline string

%example_text
Here is some example text
It's a multiline string too
a) woo
b.true) yay

%example_explanation
Here is some example explanation
It's a multiline string too
        """.strip())

    def questionToTeX(self, qnData):
        if not hasattr(self, 'qnCounter'):
            self.qnCounter = 0
        else:
            self.qnCounter += 1
        qnData['id'] = "qtd%d" % self.qnCounter

        if 'type_name' not in qnData:
            qnData['type_name'] = "tw_latexquestion"

        portal = self.layer['portal']
        login(portal, MANAGER_ID)
        lecture = portal['dept1']['tut1']['lec1']
        return lecture[lecture.invokeFactory(**qnData)].restrictedTraverse('@@tex')()

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
%r 4
%n 44
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
        imagetf.seek(0)
        browser = self.uploadTeX('http://nohost/plone/dept1/tut1/lec2', """
%%ID	q92
%%title	Question with image
%%format	latex
%%image %s
        """ % encodeDataUri(imagetf.read(), mimeType="image/png", extra = dict(filename=os.path.basename(imagetf.name))))
        # Browser returned to lecture page
        self.assertEqual(browser.url, 'http://nohost/plone/dept1/tut1/lec2')
        # The question got created
        qn = self.getObject('dept1/tut1/lec2/q92')
        self.assertEqual(qn.title, u'Question with image')
        self.assertEqual(qn.image.filename, os.path.basename(imagetf.name))
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
        self.assertEqual(qn.text.raw, u'A man walks into a lamp post\n')
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
        # Question still has answered / correct values, title removed
        qn = self.getObject('dept1/tut1/lec2/q88')
        self.assertEqual(qn.title, None)
        self.assertEqual(qn.text.raw, u'A man walks into a tree\n')
        self.assertEqual(qn.timesanswered, 999)
        self.assertEqual(qn.timescorrect, 990)

    def test_replaceAllValues(self):
        browser = self.uploadTeX('http://nohost/plone/dept1/tut1/lec2', """
%ID     q88
%title  Imported question
%format latex
A man walks into a bar
a)      $T_h = a$
b)      $T_h = b$
xa.true)      ouch, it was an iron bar.
%r 22
%n 19
        """)
        qn = self.getObject('dept1/tut1/lec2/q88')
        self.assertEqual(qn.choices, [
            {'text': u'$T_h = a$', 'correct': False},
            {'text': u'$T_h = b$', 'correct': False},
        ])
        self.assertEqual(qn.finalchoices, [
            {'text': u'ouch, it was an iron bar.', 'correct': True},
        ])

        # Upload a new version, without finalchoices and less questions
        browser = self.uploadTeX('http://nohost/plone/dept1/tut1/lec2', """
%ID     q88
%title  Imported question
%format latex
A man walks into a bar
a.true)      $T_h = x$
%r 22
%n 19
        """)
        qn = self.getObject('dept1/tut1/lec2/q88')
        self.assertEqual(qn.choices, [
            {'text': u'$T_h = x$', 'correct': True},
        ])
        self.assertEqual(qn.finalchoices, [])

    def uploadTeX(self, lecUrl, tex):
        import mechanize
        browser = self.getBrowser(lecUrl, user=MANAGER_ID)
        browser.mech_browser.open(mechanize.Request(
            lecUrl + '/@@tex-import',
            data="\r\n".join([
                "",
                "--AaB03x",
                'Content-Disposition: form-data; name="media"; filename="file1.txt"',
                'Content-Type: text/x-tex',
                '',
            ] + tex.split("\n") + [
                "--AaB03x--",
            ]),
            headers={
                "Content-Type": "multipart/form-data; boundary=AaB03x",
            },
        ))
        return browser

    def getObject(self, path):
        return self.layer['portal'].unrestrictedTraverse(path)
