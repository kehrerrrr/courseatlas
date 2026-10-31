import unittest
import pandas as pd
from recommender import ROOT, CourseRecommender, parse_enrollment, clean_courses, normalize_learning_terms
from analysis import evaluate_precision_at_5

class RecommenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = pd.read_csv(ROOT / 'data/processed/courses_cleaned.csv')
        cls.model = CourseRecommender(cls.df)

    def test_enrollment_parsing(self):
        for text, expected in [('14k', 14000), ('1.3m', 1300000), ('32,000', 32000), (' 2 K ', 2000), ('0', 0)]:
            self.assertEqual(parse_enrollment(text), expected)
        for value in [None, '', 'unknown', '-3', 'nan']:
            self.assertTrue(pd.isna(parse_enrollment(value)))

    def test_top_five_unique_actual_values(self):
        result = self.model.recommend('python data science')
        self.assertEqual(len(result), 5)
        self.assertEqual(result.course_title.nunique(), 5)
        for row in result.itertuples():
            source = self.df.loc[self.df.course_title.eq(row.course_title)].iloc[0]
            for field in ['course_organization', 'course_difficulty', 'course_rating', 'enrolled_count']:
                self.assertEqual(getattr(row, field), source[field])

    def test_exclusions_both_modes(self):
        taken = self.model.recommend('data').course_title.tolist()
        for mode in ['Personalized', 'Popular']:
            result = self.model.recommend('data', completed=taken, mode=mode)
            self.assertFalse(set(result.course_title) & set(taken))
            self.assertEqual(len(result), 5)

    def test_difficulty_and_no_eligible(self):
        for difficulty in self.df.course_difficulty.unique():
            result = self.model.recommend('business', difficulty=difficulty)
            self.assertTrue(result.course_difficulty.eq(difficulty).all())
            self.assertEqual(len(result), min(5, int(self.df.course_difficulty.eq(difficulty).sum())))
        self.assertTrue(self.model.recommend('data', difficulty='not a level').empty)
        self.assertTrue(self.model.recommend('data', completed=self.df.course_title).empty)
        remaining = self.df.course_title.iloc[:2].tolist()
        result = self.model.recommend('data', completed=self.df.course_title.iloc[2:])
        self.assertEqual(set(result.course_title), set(remaining))

    def test_blank_oov_fallback_and_baseline_invariance(self):
        popular = self.model.recommend(mode='Popular').course_title.tolist()
        for query in ['', '   ', 'zzqxxyyvv112233', 'the and or']:
            result = self.model.recommend(query)
            self.assertEqual(result.course_title.tolist(), popular)
            self.assertTrue(result.recommendation_type.eq('Popularity fallback').all())
            self.assertTrue(result.similarity.eq(0).all())
        self.assertEqual(popular, self.model.recommend('psychology', mode='Popular').course_title.tolist())

    def test_partial_matches_and_formula(self):
        result = self.model.recommend('causality')
        matches = result.recommendation_type.eq('Title match')
        self.assertGreater(matches.sum(), 0)
        self.assertLess(matches.sum(), 5)
        self.assertTrue(result.loc[matches, 'similarity'].gt(0).all())
        self.assertTrue(result.loc[~matches, 'recommendation_type'].eq('Popularity fallback').all())
        for row in result.loc[matches].itertuples():
            self.assertAlmostEqual(row.match_score, .85 * row.similarity + .15 * row.baseline_score)
            self.assertTrue(row.reason.startswith('Matched title terms:'))

    def test_deterministic_cleaning_with_missing_and_duplicates(self):
        raw = pd.DataFrame({'course_title': [' A  course ', 'a course', None, 'Other'],
                            'course_organization': ['Org', 'Org', None, None],
                            'course_Certificate_type': ['COURSE'] * 4,
                            'course_rating': ['bad', '4.5', None, '7'],
                            'course_difficulty': ['Beginner', 'Beginner', None, None],
                            'course_students_enrolled': ['14k', '32,000', None, 'unknown']})
        cleaned, summary = clean_courses(raw)
        self.assertEqual(len(cleaned), 2)
        self.assertEqual(summary['duplicate_titles_removed'], 1)
        self.assertEqual(summary['empty_title_rows_removed'], 1)
        self.assertEqual(cleaned.loc[cleaned.title_key.eq('a course'), 'enrolled_count'].iloc[0], 32000)
        self.assertTrue(pd.isna(cleaned.loc[cleaned.course_title.eq('Other'), 'course_rating'].iloc[0]))
        small = CourseRecommender(cleaned).recommend('unknown')
        self.assertEqual(len(small), 2)

    def test_synonyms_equivalent_without_changing_display_titles(self):
        for alias, canonical in [('math', 'mathematics'), ('maths', 'mathematics'),
                                 ('AI', 'artificial intelligence'), ('ML', 'machine learning'),
                                 ('stats', 'statistics')]:
            pd.testing.assert_frame_equal(self.model.recommend(alias), self.model.recommend(canonical))
            self.assertTrue(self.model.recommend(alias).similarity.gt(0).any())
        self.assertEqual(normalize_learning_terms('  AI and MATH!  '), 'artificial intelligence and mathematics!')
        self.assertEqual(normalize_learning_terms('email mathematical aim'), 'email mathematical aim')
        self.assertEqual(normalize_learning_terms(normalize_learning_terms('AI maths')), 'artificial intelligence mathematics')
        pd.testing.assert_series_equal(self.model.courses.course_title, self.df.course_title)
        # Reverse direction: alias-bearing real titles are indexed as canonical terms.
        self.assertTrue(self.model.vectorizer.build_preprocessor()('AI math') == 'artificial intelligence mathematics')

    def test_eligible_count_shared_with_ranking(self):
        taken = self.df.loc[self.df.course_difficulty.eq('Beginner'), 'course_title'].head(3).tolist()
        eligible = self.model.eligible_courses('Beginner', taken)
        self.assertEqual(len(eligible), int(self.df.course_difficulty.eq('Beginner').sum()) - 3)
        for mode in ['Personalized', 'Popular']:
            result = self.model.recommend('AI', 'Beginner', taken, mode)
            self.assertTrue(set(result.course_title).issubset(set(eligible.course_title)))
        self.assertTrue(self.model.eligible_courses(completed=self.df.course_title).empty)

    def test_precision_requires_five_valid_labels(self):
        labels = pd.DataFrame({'persona': ['synthetic'] * 5, 'model': ['test'] * 5,
                               'rank': range(1, 6), 'course_title': list('abcde'),
                               'human_relevance_0_1': [None] * 5})
        self.assertTrue(pd.isna(evaluate_precision_at_5(labels).precision_at_5.iloc[0]))
        labels['human_relevance_0_1'] = [1, 1, 0, 1, None]
        self.assertTrue(pd.isna(evaluate_precision_at_5(labels).precision_at_5.iloc[0]))
        labels['human_relevance_0_1'] = [1, 1, 0, 1, 0]
        self.assertEqual(evaluate_precision_at_5(labels).precision_at_5.iloc[0], .6)
        self.assertTrue(pd.isna(evaluate_precision_at_5(labels.iloc[:4]).precision_at_5.iloc[0]))
        labels.loc[0, 'human_relevance_0_1'] = 2
        self.assertTrue(pd.isna(evaluate_precision_at_5(labels).precision_at_5.iloc[0]))

if __name__ == '__main__':
    unittest.main()
