# -*- coding: utf-8 -*-
from Products.CMFCore.utils import getToolByName

from .base import IntegrationTestCase

class TextToTeXTest(IntegrationTestCase):

    def test_transformText(self):
        """Should get escaped LaTeX output
        """

        # Can transform
        self.assertEquals(
            self.doTransform("camel camel camel"),
            """camel camel camel""",
        )

        # Special characters are escaped, don't double-escape slashes
        self.assertEquals(
            self.doTransform("camel $camel$ \\$camel"),
            'camel \\$camel\\$ \\textbackslash\\$camel',
        )

        # Other special characters
        self.assertEquals(
            self.doTransform("& % # _ { } ~ ^"),
            '\\& \\% \\# \\_ \\{ \\} \\textasciitilde \\textasciicircum',
        )

        # Can go directly from html, but strips markup for now
        self.assertEquals(
            self.doTransform("<p>Hello <i>mum</i>!</p>", mimetype="text/html").strip(),
            'Hello mum!',
        )

    def doTransform(self, content, mimetype='text/plain'):
        pt = getToolByName(self.layer['portal'], 'portal_transforms')
        raw = pt.convertTo(
            'text/x-tex',
            content.encode('utf-8'),
            mimetype=mimetype,
            encoding='utf-8',
        ).getData()
        return raw.decode('utf-8')
