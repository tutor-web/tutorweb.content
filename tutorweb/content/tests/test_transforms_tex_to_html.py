# -*- coding: utf-8 -*-
import os.path
import unittest

from Products.CMFCore.utils import getToolByName

from plone.app.testing import setRoles, login

from .base import IntegrationTestCase
from .base import MANAGER_ID, USER_A_ID, USER_B_ID, USER_C_ID

import tutorweb.content.transforms.tex_to_html
TTM_BINARY = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..', 'parts', 'ttm', 'ttm')
tutorweb.content.transforms.tex_to_html.TTM_BINARY = TTM_BINARY


def expMathML(exp):
    return """
<math xmlns="http://www.w3.org/1998/Math/MathML">
<mrow>
<msup><mrow><mi>c</mi></mrow><mrow><mn>%s</mn></mrow>
</msup>
</mrow></math>""" % exp


class ContentTypeTest(IntegrationTestCase):

    def test_transformTeXNoTtM(self):
        """tex_to_html should have been registered and should transform content,
           even if TtM is missing
        """
        tutorweb.content.transforms.tex_to_html.TTM_BINARY = '/tmp/non-existant'
        # Basically we just get a div around content
        self.assertEquals(
            self.doTransform("camel $c^2$"),
            """<div class="parse-as-tex">camel $c^2$</div>""",
        )

        # But as we use intelligent text, line breaks are also converted
        self.assertEquals(
            self.doTransform("camel $c^2$\ndromedary $c^1$"),
            """<div class="parse-as-tex">camel $c^2$<br />dromedary $c^1$</div>""",
        )
        tutorweb.content.transforms.tex_to_html.TTM_BINARY = TTM_BINARY

    @unittest.skipUnless(os.path.isfile(TTM_BINARY), "Need TtM for this test")
    def test_transformTeXTtM(self):
        """tex_to_html should have been registered and should transform content
        """
        # We get a MathML version
        self.assertEquals(
            self.doTransform("camel $c^2$"),
            """<div class="ttm-output">camel %s</div>""" % expMathML(2),
        )

        # We understand fractions
        out = self.doTransform("camel $\\frac{1}{2}$")
        self.assertTrue('<mfrac>' in out)

        #TODO: What does TtM do with line breaks?
        self.assertEquals(
            self.doTransform("camel $c^2$\ndromedary $c^1$"),
            """<div class="ttm-output">camel %s\ndromedary %s</div>""" % (
                expMathML(2),
                expMathML(1),
            ),
        )

        # Can use unicode
        self.assertEquals(
            self.doTransform(u'Mengi n\xe1tt\xfarlegu talnanna'),
            u"""<div class="ttm-output">Mengi n\xe1tt\xfarlegu talnanna</div>""",
        )

        # \mathbb does something useful
        out = self.doTransform(u'Mengi $\mathbb{R} \mathbb{Z} \mathbb{N}$')
        # TODO: This is rubbish, but it'll do for now
        self.assertTrue('<mi fontweight="bold">R</mi>' in out)
        self.assertTrue('<mi fontweight="bold">Z</mi>' in out)
        self.assertTrue('<mi fontweight="bold">N</mi>' in out)

        # We notice errors
        self.assertEquals(
            self.doTransform(u"\\begin{oatemise}n\xe1tt\xfarlegu"),
            u"""<pre class="ttm-output error">HTML unicode style 2
Latex base filename blank. Auxiliary files will not be found.
**** Unknown or ignored environment: \\begin{oatemise} Line 4
Number of lines processed approximately 5</pre>
<div class="ttm-output">n\xe1tt\xfarlegu</div>""",
        )

        # We notice errors and unicode
        self.assertEquals(
            self.doTransform("\\begin{oatemise}And some other stuff"),
            """<pre class="ttm-output error">HTML unicode style 2
Latex base filename blank. Auxiliary files will not be found.
**** Unknown or ignored environment: \\begin{oatemise} Line 4
Number of lines processed approximately 5</pre>
<div class="ttm-output">And some other stuff</div>""",
        )

    def doTransform(self, content):
        pt = getToolByName(self.layer['portal'], 'portal_transforms')
        raw = pt.convertTo(
            'text/html',
            content.encode('utf-8'),
            mimetype='text/x-tex',
            encoding='utf-8',
        ).getData()
        return raw.decode('utf-8')
