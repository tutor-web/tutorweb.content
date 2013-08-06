import unittest
import tempfile

from tutorweb.content.transmogrifier.latex import LatexSourceSection


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

c) $x = 20$ and $y = 20$.

%Explanation
We use that $\log(a^x b^y) = x \log a + y \log b$. By rules for logarithm we get the sum
        """)]
        self.assertEqual(len(qns), 1)
        self.assertEqual(qns, [
            {
                '_type': 'tw_question',
                'id': 'q03',
                'title': 'Sum',
                'processLatex': True,
                'text': {
                    'contenttype': 'text/plain',
                    'data': 'Find the values of $x$ and $y$ such that the sum of the first  20',
                    'encoding': 'utf-8',
                },
                'choices': [
                    {'correct': False, 'randomize': True, 'text': '$x=20$ and $y=190$.'},
                    {'correct': False, 'randomize': True, 'text': '$x = 190$ and $y = 20$.'},
                    {'correct': True, 'randomize': True, 'text': '$x = 20$ and $y = 20$.'}
                ],
                'explanation': {
                    'contenttype': 'text/plain',
                    'data': 'We use that $\\log(a^x b^y) = x \\log a + y \\log b$. By rules for logarithm we get the sum',
                    'encoding': 'utf-8',
                },
            },
        ])

    def test_trailingSpace(self):
        """Trailing space gets removed from fields"""
        qns = [x for x in self.createSource("%ID camel       \n%title I'm a camel\n%Explanation  I   \nGot 2 humps, see")]
        self.assertEqual(qns, [{
            '_type': 'tw_question',
            'id': 'camel',
            'title': "I'm a camel",
            'processLatex': True,
            'explanation': {'contenttype': 'text/plain', 'data': 'I\nGot 2 humps, see', 'encoding': 'utf-8'},
        }])

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

if __name__ == '__main__':
    unittest.main()
