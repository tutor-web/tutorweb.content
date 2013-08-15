from Products.CMFCore.utils import getToolByName

from plone.app.testing import setRoles, login

from .base import IntegrationTestCase
from .base import MANAGER_ID, USER_A_ID, USER_B_ID, USER_C_ID


class ContentTypeTest(IntegrationTestCase):

    def test_transformTeX(self):
        """tex_to_html should have been registered and should transform content
        """
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

    def doTransform(self, content):
        pt = getToolByName(self.layer['portal'], 'portal_transforms')
        return pt.convertTo('text/html', content, mimetype='text/x-tex').getData()
