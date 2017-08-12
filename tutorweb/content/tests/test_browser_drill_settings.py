from zope.component import queryUtility

from plone.registry.interfaces import IRegistry

from .base import IntegrationTestCase

class DrillSettingsViewTest(IntegrationTestCase):
    def get_settings(self, base_settings = None, tut_settings = None, lec_settings = None):
        portal = self.layer['portal']

        registry = queryUtility(IRegistry)
        registry.records['tutorweb.content.lectureSettings'].value = base_settings
        portal['dept1']['tut1'].settings = tut_settings
        portal['dept1']['tut1']['lec1'].settings = lec_settings

        return portal['dept1']['tut1']['lec1'].unrestrictedTraverse('@@drill-settings').asDict()

    def test_drillsettings(self):
        # lecture wins over tutorial, wins over registry
        self.assertEqual(self.get_settings(
            base_settings=dict(
                base_only = u'0.1',
                base_tut = u'0.01',
                base_tut_lec = u'0.001',
            ),
            tut_settings=[
                dict(key='base_tut', value=u'0.02'),
                dict(key='base_tut_lec', value=u'0.002'),
            ],
            lec_settings=[
                dict(key='base_tut_lec', value=u'0.003'),
            ],
        ), dict(
            base_only=dict(value=u'0.1'),
            base_tut=dict(value=u'0.02'),
            base_tut_lec=dict(value=u'0.003'),
        ))

        # min/max properties override existing static values
        self.assertEqual(self.get_settings(
            base_settings=dict(
                prop = u'0.5',
            ),
            tut_settings=[
                dict(key='prop:min', value=u'0.1'),
                dict(key='prop:max', value=u'1.0'),
            ],
            lec_settings=[
            ],
        ), dict(
            prop=dict(min=u'0.1', max=u'1.0'),
        ))
        self.assertEqual(self.get_settings(
            base_settings=dict(
                prop = u'0.5',
            ),
            tut_settings=[
                dict(key='prop:min', value=u'0.1'),
                dict(key='prop:max', value=u'1.0'),
            ],
            lec_settings=[
                dict(key='prop:max', value=u'2.0'),
            ],
        ), dict(
            prop=dict(max=u'2.0'),
        ))

        # can override back to static value again
        self.assertEqual(self.get_settings(
            base_settings=dict(
                prop = u'0.5',
            ),
            tut_settings=[
                dict(key='prop:min', value=u'0.1'),
                dict(key='prop:max', value=u'1.0'),
            ],
            lec_settings=[
                dict(key='prop', value=u'8.0'),
            ],
        ), dict(
            prop=dict(value=u'8.0'),
        ))

        # We munge :min == :max as a value
        self.assertEqual(self.get_settings(
            base_settings=dict(
                prop = u'0.5',
            ),
            tut_settings=[
                dict(key='prop:min', value=u'0.1'),
                dict(key='prop:max', value=u'1.0'),
            ],
            lec_settings=[
                dict(key='prop:min', value=u'0.4 '), # NB: Make sure we're stripping whitespace
                dict(key='prop:max', value=u'0.4'),
            ],
        ), dict(
            prop=dict(value=u'0.4'),
        ))
