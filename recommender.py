"""Deterministic title-based course recommendations using the actual Kaggle CSV."""
from pathlib import Path
import json
import re
import unicodedata
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

ROOT = Path(__file__).resolve().parent
FIELDS = ['course_title', 'course_organization', 'course_Certificate_type',
          'course_rating', 'course_difficulty', 'course_students_enrolled']
SOURCE = 'https://www.kaggle.com/datasets/siddharthm1698/coursera-course-dataset/data'

def title_key(value):
    return unicodedata.normalize('NFKC', str(value)).strip().casefold()

# Small, explicit aliases only; no inference, stemming or external services.
SYNONYMS = {'math': 'mathematics', 'maths': 'mathematics',
            'ai': 'artificial intelligence', 'ml': 'machine learning',
            'stats': 'statistics'}
_ALIAS_PATTERN = re.compile(r'\b(?:' + '|'.join(map(re.escape, SYNONYMS)) + r')\b')

def normalize_learning_terms(value):
    text = unicodedata.normalize('NFKC', str(value)).casefold()
    text = re.sub(r'\s+', ' ', text).strip()
    return _ALIAS_PATTERN.sub(lambda match: SYNONYMS[match.group()], text)

def parse_enrollment(value):
    if pd.isna(value):
        return np.nan
    text = str(value).strip().lower().replace(',', '')
    match = re.fullmatch(r'(\d+(?:\.\d+)?)\s*([km]?)', text)
    if not match:
        return np.nan
    number, suffix = match.groups()
    result = float(number) * {'': 1, 'k': 1000, 'm': 1000000}[suffix]
    return int(result) if np.isfinite(result) else np.nan

def clean_courses(raw):
    missing = set(FIELDS) - set(raw.columns)
    if missing:
        raise ValueError(f'Missing required columns: {sorted(missing)}')
    df = raw[FIELDS].copy()
    stats = {'source': SOURCE, 'raw_rows': len(df),
             'missing_before': {k: int(v) for k, v in df.isna().sum().items()},
             'exact_duplicates': int(df.duplicated().sum())}
    for col in FIELDS:
        if col != 'course_rating':
            df[col] = df[col].astype('string').str.strip().str.replace(r'\s+', ' ', regex=True)
    blank_title = df.course_title.isna() | df.course_title.eq('')
    stats['empty_title_rows_removed'] = int(blank_title.sum())
    df = df.loc[~blank_title].copy()
    for col in ['course_organization', 'course_Certificate_type', 'course_difficulty']:
        df[col] = df[col].fillna('Unknown').replace('', 'Unknown')
    df.course_rating = pd.to_numeric(df.course_rating, errors='coerce')
    df.loc[~df.course_rating.between(0, 5), 'course_rating'] = np.nan
    df['enrolled_count'] = df.course_students_enrolled.map(parse_enrollment)
    stats['missing_or_invalid_ratings'] = int(df.course_rating.isna().sum())
    stats['missing_or_invalid_enrollment'] = int(df.enrolled_count.isna().sum())
    df['title_key'] = df.course_title.map(title_key)
    # Same title: prefer higher known enrollment, then rating; stable input order breaks ties.
    df = df.sort_values(['enrolled_count', 'course_rating'], ascending=False,
                        na_position='last', kind='stable')
    stats['duplicate_titles_removed'] = int(df.title_key.duplicated().sum())
    df = df.drop_duplicates('title_key').sort_values('title_key', kind='stable').reset_index(drop=True)
    stats['clean_rows'] = len(df)
    stats['difficulty_counts'] = {k: int(v) for k, v in df.course_difficulty.value_counts().items()}
    stats['organizations'] = int(df.loc[df.course_organization.ne('Unknown'), 'course_organization'].nunique())
    stats['average_known_rating'] = float(df.course_rating.mean()) if df.course_rating.notna().any() else None
    return df, stats

def prepare_data(root=ROOT):
    root = Path(root)
    candidates = sorted((root / 'data/raw').glob('*.csv'))
    if not candidates:
        raise FileNotFoundError('Download the specified Kaggle CSV into data/raw/; see README.md.')
    if len(candidates) != 1:
        raise ValueError('Keep exactly one source CSV in data/raw/ to avoid ambiguous input.')
    raw = pd.read_csv(candidates[0])
    df, stats = clean_courses(raw)
    if df.empty:
        raise ValueError('No valid course titles remain after cleaning.')
    stats['raw_file'] = candidates[0].name
    import hashlib
    stats['raw_sha256'] = hashlib.sha256(candidates[0].read_bytes()).hexdigest()
    (root / 'data/processed').mkdir(parents=True, exist_ok=True)
    (root / 'artifacts').mkdir(parents=True, exist_ok=True)
    df.to_csv(root / 'data/processed/courses_cleaned.csv', index=False)
    (root / 'artifacts/cleaning_summary.json').write_text(
        json.dumps(stats, indent=2, ensure_ascii=False), encoding='utf-8')
    return df, stats

class CourseRecommender:
    def __init__(self, courses, ngram_range=(1, 2), popularity_weight=0.15):
        if not 0 <= popularity_weight <= 1:
            raise ValueError('Popularity weight must be between 0 and 1.')
        self.courses = courses.copy().reset_index(drop=True)
        if self.courses.empty:
            raise ValueError('No courses available.')
        self.weight = popularity_weight
        log_enrolled = np.log1p(self.courses.enrolled_count.fillna(0).clip(lower=0))
        spread = log_enrolled.max() - log_enrolled.min()
        popularity = (log_enrolled - log_enrolled.min()) / spread if spread else log_enrolled * 0
        rating = self.courses.course_rating.fillna(0).clip(0, 5) / 5
        baseline = 0.7 * popularity + 0.3 * rating
        span = baseline.max() - baseline.min()
        self.courses['baseline_score'] = (baseline - baseline.min()) / span if span else baseline * 0
        self.vectorizer = TfidfVectorizer(stop_words='english', ngram_range=ngram_range,
                                          preprocessor=normalize_learning_terms)
        try:
            self.matrix = self.vectorizer.fit_transform(self.courses.course_title)
        except ValueError as exc:
            if 'empty vocabulary' not in str(exc):
                raise
            self.matrix = None
        self.terms = self.vectorizer.get_feature_names_out() if self.matrix is not None else np.array([])

    def eligible_courses(self, difficulty='All levels', completed=()):
        taken = {title_key(t) for t in completed}
        allowed = ~self.courses.title_key.isin(taken)
        if difficulty != 'All levels':
            allowed &= self.courses.course_difficulty.eq(difficulty)
        return self.courses.loc[allowed].copy()

    def recommend(self, interests='', difficulty='All levels', completed=(), mode='Personalized', k=5):
        if mode not in ['Personalized', 'Popular']:
            raise ValueError('Mode must be Personalized or Popular.')
        if k < 1:
            raise ValueError('k must be positive.')
        df = self.courses.copy()
        similarities = np.zeros(len(df))
        query = None
        if str(interests).strip() and self.matrix is not None:
            query = self.vectorizer.transform([str(interests)])
            if query.nnz:
                similarities = cosine_similarity(self.matrix, query).ravel()
        df['similarity'] = similarities
        df['match_score'] = (1 - self.weight) * df.similarity + self.weight * df.baseline_score
        eligible = df.loc[self.eligible_courses(difficulty, completed).index].copy()
        if mode == 'Popular':
            selected = eligible.sort_values(['baseline_score', 'title_key'], ascending=[False, True]).head(k).copy()
            selected['recommendation_type'] = 'Popular'
        else:
            topical = eligible.loc[eligible.similarity.gt(0)].sort_values(
                ['match_score', 'similarity', 'title_key'], ascending=[False, False, True]).head(k).copy()
            topical['recommendation_type'] = 'Title match'
            fallback = eligible.loc[eligible.similarity.le(0)].sort_values(
                ['baseline_score', 'title_key'], ascending=[False, True]).head(max(0, k - len(topical))).copy()
            fallback['recommendation_type'] = 'Popularity fallback'
            selected = pd.concat([topical, fallback])
        reasons = []
        for index, row in selected.iterrows():
            if row.recommendation_type == 'Title match' and query is not None:
                common = self.matrix[index].multiply(query)
                terms = self.terms[common.indices[np.argsort(-common.data)]][:4]
                reasons.append('Matched title terms: ' + ', '.join(terms))
            elif row.recommendation_type == 'Popularity fallback':
                reasons.append('No title-term match; added by enrollment and rating popularity.')
            else:
                reasons.append('Ranked by enrollment and rating across eligible courses.')
        selected['reason'] = reasons
        selected['rank'] = range(1, len(selected) + 1)
        return selected.reset_index(drop=True)

if __name__ == '__main__':
    _, summary = prepare_data()
    print(json.dumps(summary, ensure_ascii=True, indent=2))
