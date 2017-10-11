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

        # Floats are fine too
        self.assertEqual(self.get_settings(
            base_settings=dict(
                prop = u'0.5',
            ),
            tut_settings=[
                dict(key='prop', value=0.2),
            ],
            lec_settings=[
                dict(key='plop:max', value=0.8),
            ],
        ), dict(
            prop=dict(value=u'0.2'),
            plop=dict(max=u'0.8'),
        ))

        # We convert award_registered into :registered
        self.assertEqual(self.get_settings(base_settings=dict(), tut_settings=[], lec_settings=[
            dict(key='award_rogistered_argle', value=u'0.7'),
            dict(key='award_registered_argle', value=u'0.8'),
            dict(key='award_registered_argle:max', value=u'0.9'),
            dict(key='award_registered_bargle', value=u'1.0'),
            dict(key='award_registered_cargle:shape', value=u'1.1'),
        ]), {
            "award_rogistered_argle": dict(value=u'0.7'),
            "award_argle:registered": dict(value=u'0.8', max=u'0.9'),
            "award_bargle:registered": dict(value=u'1.0'),
            "award_cargle:registered": dict(shape=u'1.1'),
        })

        # We add :registered to arbitary properties with variant set
        self.assertEqual(self.get_settings(base_settings={
            "global:min:registered": u"2",
            "global:max": u"5",
        }, tut_settings=[], lec_settings=[
            dict(key='prop', value=u'0.7'),
            dict(key='prop:max', variant=u'registered', value=u'0.8'),
            dict(key='plop', variant=u'registered', value=u'0.9'),
        ]), {
            'global:registered': {'min': '2'},
            'global': {'max': '5'},
            "prop": dict(value='0.7'),
            "prop:registered": dict(max='0.8'),
            "plop:registered": dict(value='0.9'),
        })
