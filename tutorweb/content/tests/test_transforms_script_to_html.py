from lxml import etree

from Products.CMFCore.utils import getToolByName

from .base import IntegrationTestCase

import tutorweb.content.transforms.script_to_html
from tutorweb.content.transforms.script_to_html import R_BINARY, TIMEOUT


class ContentTypeTest(IntegrationTestCase):

    def test_transformRMissingBinary(self):
        """If R isn't available, return error message"""
        tutorweb.content.transforms.script_to_html.R_BINARY = '/tmp/no-exist'
        self.assertTrue('/tmp/no-exist' in self.doTransform("cat('moo')"))
        tutorweb.content.transforms.script_to_html.R_BINARY = R_BINARY

    def test_transformR(self):
        # Script might not execute
        xml = self.doTransform("""
        stop('Oh <noes>')
        """)
        self.assertTrue('Error: Oh &lt;noes&gt;' in xml)

        # Script might not generate any plots
        xml = self.doTransform("""cat('poot')""")
        self.assertTrue(xml.startswith('<pre class="script output">'))
        self.assertTrue('poot' in xml)

        # Working script should though
        xml = self.doTransform("""
        plot(0:100, (0:100)^2, 'l')
        """)
        self.assertTrue('<svg' in xml)

        # Will timeout and not generate plot
        tutorweb.content.transforms.script_to_html.TIMEOUT = '1s'
        xml = self.doTransform("""
        Sys.sleep(5)
        plot(0:100, (0:100)^2, 'l')
        """)
        # NB: Timeout isn't an error...yet.
        self.assertTrue(xml.startswith('<pre class="script output">'))
        self.assertTrue('Sys.sleep(5)' in xml)
        tutorweb.content.transforms.script_to_html.TIMEOUT = TIMEOUT

        # Can use a different MIME type
        xml = self.doTransform("""
        plot(0:100, (0:100)^2, 'l')
        """, inputMime='text/R')
        self.assertTrue('<svg' in xml)

    def doTransform(self, content, inputMime='text/r'):
        pt = getToolByName(self.layer['portal'], 'portal_transforms')
        str = pt.convertTo('text/html', content, mimetype=inputMime).getData()
        doc = etree.fromstring(str)
        return str
