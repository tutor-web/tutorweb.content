from Products.CMFCore.utils import getToolByName

from .base import IntegrationTestCase


class UpgradesTest(IntegrationTestCase):
    profile = 'tutorweb.content:default'

    def test_updateLectureSettings(self):
        """hist_sel should get moved into settings hash"""
        portal = self.layer['portal']
        portal['dept1']['tut1'].histsel=0.8
        portal['dept1']['tut1']['lec1'].histsel=0.5
        portal['dept1']['tut1']['lec2'].histsel=-1.0
        self.runStep(u'Upgrade 1 -> 2.0')
        self.assertEqual(
            portal['dept1']['tut1'].settings,
            [dict(key='hist_sel', value='0.8')],
        )
        self.assertEqual(
            portal['dept1']['tut1']['lec1'].settings,
            [dict(key='hist_sel', value='0.5')],
        )
        self.assertEqual(
            portal['dept1']['tut1']['lec2'].settings,
            None,
        )

        # Rerunning won't blat values
        portal['dept1']['tut1']['lec1'].histsel=0.4
        portal['dept1']['tut1']['lec2'].histsel=0.3
        self.runStep(u'Upgrade 1 -> 2.0')
        self.assertEqual(
            portal['dept1']['tut1']['lec1'].settings,
            [dict(key='hist_sel', value='0.5')],
        )
        self.assertEqual(
            portal['dept1']['tut1']['lec2'].settings,
            [dict(key='hist_sel', value='0.3')],
        )

    def runStep(self, name):
        """Run a step by name"""
        portal = self.layer['portal']
        request = self.layer['request']
        setup = getToolByName(portal, "portal_setup")
        steps = setup.listUpgrades(
            self.profile,
            setup.getLastVersionForProfile(self.profile),
        )
        for s in steps:
            if s['title'] != name:
                continue
            request.form['profile_id'] = self.profile
            request.form['upgrades'] = [s['id']]
            setup.manage_doUpgrades(request=request)
            return
        raise KeyError(name)
