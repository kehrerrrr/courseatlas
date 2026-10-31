import unittest
import pandas as pd
from recommender import ROOT, CourseRecommender
from roadmap import plan_roadmap, refine_request, PROGRESSIONS

class RoadmapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = pd.read_csv(ROOT / 'data/processed/courses_cleaned.csv')
        cls.model = CourseRecommender(cls.df)

    def test_curated_sequence_unique_real_metadata(self):
        for goal in PROGRESSIONS:
            for length in [3, 5]:
                with self.subTest(goal=goal, length=length):
                    result = plan_roadmap(self.model, goal, length=length)
                    steps = result['steps']
                    self.assertEqual(result['goal_type'], goal)
                    self.assertEqual(len(steps), length)
                    self.assertEqual(len({s['course_title'] for s in steps}), length)
                    slots = [0, 3, 4] if length == 3 else list(range(5))
                    self.assertEqual([s['topic'] for s in steps], [PROGRESSIONS[goal][1][i] for i in slots])
                    self.assertEqual([s['stage'] for s in steps], [1, 2, 3] if length == 3 else [1, 1, 2, 2, 3])
                    for step in steps:
                        original = self.df.loc[self.df.course_title.eq(step['course_title'])].iloc[0]
                        for field in ['course_organization', 'course_difficulty', 'course_rating']:
                            self.assertEqual(step[field], original[field])
                        self.assertGreater(step['similarity'], 0)
                        self.assertIn('Planning heuristic', step['reason'])

    def test_exclusions_known_topics_and_empty_candidates(self):
        first = plan_roadmap(self.model, 'Data Analyst')
        completed = [s['course_title'] for s in first['steps']]
        next_plan = plan_roadmap(self.model, 'Data Analyst', completed=completed, known_topics='SQL, python')
        self.assertFalse(set(completed) & {s['course_title'] for s in next_plan['steps']})
        self.assertTrue(all('python' not in s['course_title'].lower() and 'sql' not in s['course_title'].lower() for s in next_plan['steps']))
        empty = plan_roadmap(self.model, 'Data Analyst', completed=self.df.course_title.tolist())
        self.assertFalse(empty['steps'])
        self.assertEqual(len(empty['gaps']), 5)

    def test_unknown_and_empty_goals(self):
        self.assertFalse(plan_roadmap(self.model, '  ')['steps'])
        missing = plan_roadmap(self.model, 'I want a quantumdragonzzzx career')
        self.assertIsNone(missing['goal_type'])
        self.assertEqual(missing['strategy'], 'Title-based exploration only')
        self.assertFalse(missing['steps'])
        contextual = plan_roadmap(self.model, 'I want a quantumdragonzzzx career, but I have no programming experience.')
        self.assertFalse(contextual['steps'])
        generic = plan_roadmap(self.model, 'I want to learn psychology', length=3)
        self.assertIsNone(generic['goal_type'])
        self.assertTrue(generic['steps'])
        self.assertTrue(all(s['similarity'] > 0 for s in generic['steps']))
        self.assertTrue(all('psychology' in s['course_title'].lower() for s in generic['steps']))

    def test_missing_stage_is_not_popularity_filled(self):
        # Real catalog subset with all SQL-related titles removed.
        reduced = self.df.loc[~self.df.course_title.str.contains(r'sql|database', case=False, regex=True)]
        result = plan_roadmap(CourseRecommender(reduced), 'Data Analyst')
        self.assertTrue(any(g['topic'] == 'SQL' and g['stage'] == 2 for g in result['gaps']))
        self.assertFalse(any(s['topic'] == 'SQL' for s in result['steps']))
        self.assertEqual(len(result['steps']), 4)

    def test_level_determinism_synonyms_and_context(self):
        a = plan_roadmap(self.model, 'ML', level='Intermediate')
        self.assertEqual(a, plan_roadmap(self.model, 'machine learning', level='Intermediate'))
        a = plan_roadmap(self.model, 'I want to become a data analyst, but I have no programming experience.', level='Advanced')
        self.assertEqual(a['goal_type'], 'Data Analyst')
        self.assertEqual(a['effective_level'], 'Beginner')
        self.assertTrue(all(s['course_difficulty'] == 'Beginner' for s in a['steps'] if s['stage'] == 1))
        easy = plan_roadmap(self.model, 'Data Analyst', easier=True)
        self.assertTrue(all(s['course_difficulty'] == 'Beginner' for s in easy['steps']))
        self.assertFalse(any(s['course_difficulty'] == 'Advanced' for s in a['steps']))

    def test_refinements_change_inputs_and_respect_exclusions(self):
        request = dict(goal='Python Programming', level='Intermediate', completed=[], known_topics='', length=5, focus='', easier=False, variant=0)
        self.assertEqual(refine_request(request, 'easier')['level'], 'Beginner')
        easy = refine_request({**request, 'level': 'Beginner'}, 'easier')
        self.assertTrue(easy['easier'])
        self.assertEqual(refine_request(request, 'shorten')['length'], 3)
        self.assertEqual(refine_request(request, 'focus', focus='statistics')['focus'], 'statistics')
        first = plan_roadmap(self.model, **request)
        selected = first['steps'][0]['course_title']
        known = refine_request(request, 'known', course=selected)
        self.assertIn(selected, known['completed'])
        self.assertNotIn(selected, [s['course_title'] for s in plan_roadmap(self.model, **known)['steps']])
        alternative = refine_request(request, 'regenerate')
        self.assertEqual(alternative['variant'], 1)
        self.assertNotEqual([s['course_title'] for s in first['steps']], [s['course_title'] for s in plan_roadmap(self.model, **alternative)['steps']])
        focused = plan_roadmap(self.model, 'Data Analyst', focus='statistics')
        unfocused = plan_roadmap(self.model, 'Data Analyst')
        self.assertNotEqual([s['course_title'] for s in focused['steps']], [s['course_title'] for s in unfocused['steps']])
        self.assertEqual(request['completed'], [])
        self.assertEqual(request['variant'], 0)

if __name__ == '__main__':
    unittest.main()
