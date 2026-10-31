"""Focused Streamlit smoke test for roadmap refinements and existing modes."""
import unittest
from html import escape
from recommender import ROOT
from streamlit.testing.v1 import AppTest

class RoadmapAppTests(unittest.TestCase):
    def test_planner_controls_and_discovery_modes(self):
        at = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=60).run()
        def check():
            self.assertFalse(at.exception, str(at.exception))
        def steps():
            return [m.value for m in at.markdown if '<article' in m.value and 'road-step' in m.value]
        check()
        self.assertIn('AI Learning Architect', [tab.label for tab in at.tabs])
        at.button(key='FormSubmitter:architect_form-Build my roadmap').click().run()
        check()
        self.assertEqual(len(steps()), 5)
        at.button(key='road_easier').click().run()
        check()
        self.assertTrue(at.session_state['architect_request']['easier'])
        self.assertTrue(all('Beginner' in card for card in steps()))
        known = at.selectbox(key='road_known_step').value
        at.button(key='road_known').click().run()
        check()
        self.assertIn(known, at.session_state['architect_request']['completed'])
        self.assertFalse(any(escape(known) in card for card in steps()))
        at.button(key='road_shorter').click().run()
        check()
        self.assertEqual(at.session_state['architect_request']['length'], 3)
        self.assertLessEqual(len(steps()), 3)
        at.text_input(key='road_focus_topic').set_value('python').run()
        at.button(key='road_focus').click().run()
        check()
        self.assertEqual(at.session_state['architect_request']['focus'], 'python')
        at.button(key='road_regenerate').click().run()
        check()
        self.assertEqual(at.session_state['architect_request']['variant'], 1)
        for mode in ['Personalized', 'Popular']:
            at.radio(key='recommendation_mode').set_value(mode).run()
            check()
            self.assertEqual(len([m for m in at.markdown if '<article' in m.value and 'road-step' not in m.value]), 5)
        at.text_area(key='architect_goal').set_value('I want a quantumdragonzzzx career')
        at.button(key='FormSubmitter:architect_form-Build my roadmap').click().run()
        check()
        self.assertFalse(steps())
        self.assertTrue(any('No curated progression' in item.value for item in at.info))
        self.assertEqual(len(at.warning), 5)
        at.text_area(key='architect_goal').set_value('')
        at.button(key='FormSubmitter:architect_form-Build my roadmap').click().run()
        check()
        self.assertFalse(steps())
        self.assertTrue(any('Enter a learning goal' in item.value for item in at.info))

if __name__ == '__main__':
    unittest.main()
