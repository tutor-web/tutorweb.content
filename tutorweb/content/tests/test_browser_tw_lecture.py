import cStringIO

from .base import FunctionalTestCase, MANAGER_ID, testImage


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
        self.assertEqual(qn.image.filename, u'file://%s' % imagetf.name)
        self.assertEqual(qn.image.contentType, 'image/png')
        imagetf.seek(0)
        self.assertEqual(qn.image.data, imagetf.read())
        imagetf.close()

    def uploadTeX(self, lecUrl, tex):
        browser = self.getBrowser(lecUrl, user=MANAGER_ID)
        ctrl = browser.getControl('Update questions from TeX file')
        ctrl.add_file(cStringIO.StringIO(tex), 'text/plain', 'test.tex')
        browser.getControl('Upload').click()
        return browser

    def getObject(self, path):
        return self.layer['portal'].unrestrictedTraverse(path)
