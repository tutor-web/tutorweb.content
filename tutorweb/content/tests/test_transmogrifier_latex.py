# -*- coding: utf8 -*-
import unittest
import tempfile

from tutorweb.content.transmogrifier.latex import LatexSourceSection

from .base import testImage


class LatexSourceSectionTest(unittest.TestCase):
    maxDiff = None

    def tearDown(self):
        if hasattr(self, 'tf'):
            self.tf.close()

    def test_singleQn(self):
        qns = [x for x in self.createSource("""
%ID q03
%title Sum
Find the values of $x$ and $y$ such that the sum of the first  20

a) $x=20$ and $y=190$.
b) $x = 190$ and $y = 20$.

c)$x = 20$ and $y = 20$.

%Explanation
We use that $\log(a^x b^y) = x \log a + y \log b$. By rules for logarithm we get the sum
        """)]
        self.assertEqual(len(qns), 1)
        self.assertEqual(qns, [
            {
                '_type': 'tw_latexquestion',
                'id': 'q03',
                'title': 'Sum',
                'processLatex': True,
                'text': {
                    'contenttype': 'text/x-tex',
                    'data': 'Find the values of $x$ and $y$ such that the sum of the first  20',
                    'encoding': 'utf-8',
                },
                'choices': [
                    {'correct': True, 'text': '$x=20$ and $y=190$.'},
                    {'correct': False, 'text': '$x = 190$ and $y = 20$.'},
                    {'correct': False, 'text': '$x = 20$ and $y = 20$.'}
                ],
                'explanation': {
                    'contenttype': 'text/x-tex',
                    'data': 'We use that $\\log(a^x b^y) = x \\log a + y \\log b$. By rules for logarithm we get the sum',
                    'encoding': 'utf-8',
                },
            },
        ])

    def test_explicitTrueFalse(self):
        qns = [x for x in self.createSource("""
%ID q03
%title Sum
a.true)$x=20$
b.false) $x = 190$
b.true) $x = 191$
c.false)x = 21
        """)]
        self.assertEqual(len(qns), 1)
        self.assertTrue(qns[0], {
            '_type': 'tw_latexquestion',
            'id': u'q03',
            'title': u'Sum',
            'processLatex': True,
            'choices': [
                {'correct': True, 'text': u'$x=20$'},
                {'correct': False, 'text': u'$x = 190$'},
                {'correct': True, 'text': u'$x = 191$'},
                {'correct': False, 'text': u'x = 21'},
            ],
        })

    def test_trailingSpace(self):
        """Trailing space gets removed from fields"""
        qns = [x for x in self.createSource("%ID camel       \n%title I'm a camel\n%Explanation  I   \nGot 2 humps, see")]
        self.assertEqual(qns, [{
            '_type': 'tw_latexquestion',
            'id': 'camel',
            'title': "I'm a camel",
            'processLatex': True,
            'explanation': {'contenttype': 'text/x-tex', 'data': 'I\nGot 2 humps, see', 'encoding': 'utf-8'},
        }])

    def test_multipleQns(self):
        qns = [x for x in self.createSource("""
%ID q1
%title Sum
Find the values of $x$ and $y$ such that the sum of the first  20
a) $x=20$ and $y=190$.
b) $x = 190$ and $y = 20$.
c) $x = 20$ and $y = 20$.
%Explanation
Seems obvious now, doesn't it?
Well, duh.

%===
%ID q2
%title Sum
Find the values of $x$ and $y$ such that the sum of the first  20
a) $x=20$ and $y=190$.
b) $x = 190$ and $y = 20$.
c) $x = 20$ and $y = 20$.
%Explanation
You should have worked it out the first time.
%===
%ID q3
%title Sum
Find the values of $x$ and $y$ such that the sum of the first  20
a) $x=20$ and $y=190$.
b) $x = 190$ and $y = 20$.
c) $x = 20$ and $y = 20$.
%Explanation
Don't catch on quickly, do you?
        """)]
        self.assertEqual(len(qns), 3)
        self.assertTrue([q['id'] for q in qns], ['q1', 'q2', 'q3'])
        self.assertTrue([q['explanation'] for q in qns], [
            {'contenttype': 'text/x-tex', 'data': """Seems obvious now, doesn't it?\nWell, duh.""", 'encoding': 'utf-8'},
            {'contenttype': 'text/x-tex', 'data': """You should have worked it out the first time.""", 'encoding': 'utf-8'},
            {'contenttype': 'text/x-tex', 'data': """Don't catch on quickly, do you?""", 'encoding': 'utf-8'},
        ])

    def test_qnsWithTabs(self):
        qns = [x for x in self.createSource("""
%ID	question-053
%title	Question
%format	latex
%r  61
%n  133


Helmingunartími $C^{14}$ er 5730 ár.

a)  $N(2000)=20\cdot 2^{-\frac{200}{573}}$.
b)
$N(2000)=20\cdot (2 + e^{-\frac{200}{573}})$.
c)  $N(2000)=20\cdot (\frac12 + e^{\frac{200}{573}})$.
        """)]
        self.assertEqual(len(qns), 1)
        self.assertEqual(qns[0]['title'], u'Question')
        self.assertEqual(qns[0]['id'], u'question-053')
        self.assertEqual(qns[0]['text']['data'], u'Helmingunartími $C^{14}$ er 5730 ár.')
        self.assertEqual([x['text'] for x in qns[0]['choices']], [
            """$N(2000)=20\cdot 2^{-\frac{200}{573}}$.""",
            """$N(2000)=20\cdot (2 + e^{-\frac{200}{573}})$.""",
            """$N(2000)=20\cdot (\frac12 + e^{\frac{200}{573}})$.""",
        ])

    def test_plainText(self):
        qns = [x for x in self.createSource("""
%ID	question-053
%title	Question
%format	txt
%r  61
%n  133


Helmingunartími $C^{14}$ er 5730 ár.

a)  $N(2000)=20\cdot 2^{-\frac{200}{573}}$.
b)
$N(2000)=20\cdot (2 + e^{-\frac{200}{573}})$.
c)  $N(2000)=20\cdot (\frac12 + e^{\frac{200}{573}})$.

%Explanation
Don't catch on quickly, do you?
        """)]
        self.assertEqual(len(qns), 1)
        self.assertEqual(qns[0]['title'], u'Question')
        self.assertEqual(qns[0]['id'], u'question-053')
        self.assertEqual(qns[0]['text']['data'], u'Helmingunartími $C^{14}$ er 5730 ár.')
        self.assertEqual(qns[0]['text']['contenttype'], u'text/x-web-intelligent')
        self.assertEqual(qns[0]['explanation']['data'], u"Don't catch on quickly, do you?")
        self.assertEqual(qns[0]['explanation']['contenttype'], u'text/x-web-intelligent')

    def test_anyOfTheAbove(self):
        """A d.true|false) question is interpreted as non-random"""
        qns = [x for x in self.createSource("""
%ID	q1
%title	Question with no right answer
%format	latex

What is the winning move?

a) LEFT 5
b) FORWARD 10
c) Jump!
d.true) None of the above

%===

%ID	q2
%title	Question with lots of answers
%format	latex

What is my favourite colour?

a) Green
b) Orange
c) Pink
d) Blue
e) Mauve
        """)]
        self.assertEqual(len(qns), 2)
        # First question will have the last answer as fixed
        self.assertEqual(qns[0]['choices'], [
            dict(correct=False, text=u"LEFT 5"),
            dict(correct=False, text=u"FORWARD 10"),
            dict(correct=False, text=u"Jump!"),
        ])
        self.assertEqual(qns[0]['finalchoices'], [
            dict(correct=True, text=u"None of the above"),
        ])
        
        # Second question just has lots of answers
        self.assertEqual(qns[1]['choices'], [
            dict(correct=True, text=u"Green"),
            dict(correct=False, text=u"Orange"),
            dict(correct=False, text=u"Pink"),
            dict(correct=False, text=u"Blue"),
            dict(correct=False, text=u"Mauve"),
        ])
        self.assertTrue('finalchoices' not in qns[1])

    def test_image(self):
        imagetf = testImage()
        qns = [x for x in self.createSource("""
%%ID	question-053
%%title	Question with image
%%format	latex
%%image file://%s
        """ % imagetf.name)]
        self.assertEqual(len(qns), 1)
        self.assertEqual(qns[0]['title'], u'Question with image')
        self.assertEqual(qns[0]['id'], u'question-053')
        imagetf.seek(0)
        self.assertEqual(qns[0]['image'], dict(
            contenttype='image/png',
            data=imagetf.read(),
            filename=u'file://%s' % imagetf.name,
        ))
        imagetf.close()

    def createSource(self, tex):
        if hasattr(self, 'tf'):
            self.tf.close()
        self.tf = tempfile.NamedTemporaryFile()
        self.tf.write(tex)
        self.tf.flush()
        return LatexSourceSection({}, "latexsource", dict(
            blueprint="camel",
            filename=self.tf.name,
        ), None)

    def test_blankQuestion(self):
        """Separators without anything within are ignored"""
        qns = [x for x in self.createSource("""
%===
%ID	q1
%title	Question with no right answer
%format	latex

What is the winning move?

a) LEFT 5
b) FORWARD 10
c) Jump!
d.true) None of the above

%===


%===

%ID	q2
%title	Question with lots of answers
%format	latex

What is my favourite colour?

a) Green
b) Orange
c) Pink
d) Blue
e) Mauve
%===
        """)]
        self.assertEqual(len(qns), 2)
        self.assertEqual(qns[0]['id'], 'q1')
        self.assertEqual(qns[1]['id'], 'q2')


if __name__ == '__main__':
    unittest.main()
