"""Generate real-data artifacts and optional human-label Precision@5."""
import json
import platform
import importlib.metadata
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from recommender import ROOT, prepare_data, CourseRecommender

PROFILES = {
    'Synthetic: data learner': 'python data science machine learning',
    'Synthetic: business learner': 'business finance marketing',
    'Synthetic: wellbeing learner': 'psychology happiness wellbeing',
}
CONFIGS = {
    'unigram_w15': ((1, 1), .15), 'unigram_w30': ((1, 1), .30),
    'bigram_w15': ((1, 2), .15), 'bigram_w30': ((1, 2), .30),
}

def evaluate_precision_at_5(labels):
    required = {'persona', 'model', 'rank', 'course_title', 'human_relevance_0_1'}
    if not required.issubset(labels.columns):
        raise ValueError('Evaluation CSV is missing required columns.')
    rows = []
    for (persona, model), group in labels.groupby(['persona', 'model'], sort=True):
        values = pd.to_numeric(group.human_relevance_0_1, errors='coerce')
        complete = (len(group) == 5 and set(group['rank']) == set(range(1, 6))
                    and group.course_title.nunique() == 5 and values.isin([0, 1]).all())
        rows.append({'persona': persona, 'model': model,
                     'precision_at_5': float(values.mean()) if complete else None,
                     'status': 'Evaluated from human labels' if complete else 'Not evaluated: human labels required.'})
    return pd.DataFrame(rows)

def make_charts(df, output):
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11,
                         'axes.spines.top': False, 'axes.spines.right': False,
                         'axes.titleweight': 'bold', 'figure.facecolor': '#F7F8FC'})
    counts = df.course_difficulty.value_counts()
    fig, ax = plt.subplots(figsize=(8, 4.2), layout='constrained')
    bars = ax.bar(counts.index, counts.values, color=['#6658E8', '#8D82ED', '#B5ACF5', '#CFEADF'][:len(counts)])
    ax.bar_label(bars, padding=4)
    ax.set(title='Courses by difficulty', ylabel='Number of unique course titles')
    ax.set_ylim(0, counts.max() * 1.15)
    fig.savefig(output / 'difficulty_distribution.png', dpi=160)
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), layout='constrained')
    axes[0].hist(df.course_rating.dropna(), bins=16, color='#6658E8', edgecolor='white')
    axes[0].set(title='Course rating distribution', xlabel='Rating (out of 5)', ylabel='Courses')
    axes[1].hist(np.log10(df.enrolled_count.dropna().clip(lower=1)), bins=18, color='#62B69B', edgecolor='white')
    axes[1].set(title='Enrollment distribution', xlabel='log10(enrolled learners)', ylabel='Courses')
    fig.savefig(output / 'rating_enrollment_distribution.png', dpi=160)
    plt.close(fig)

def main():
    df, stats = prepare_data()
    out = ROOT / 'artifacts'
    make_charts(df, out)
    models = {name: CourseRecommender(df, ngrams, weight) for name, (ngrams, weight) in CONFIGS.items()}
    rows, diagnostics = [], []
    for persona, interests in PROFILES.items():
        for name, model in [('Popular', models['bigram_w15'])] + list(models.items()):
            mode = 'Popular' if name == 'Popular' else 'Personalized'
            results = model.recommend(interests, mode=mode)
            for row in results.to_dict('records'):
                rows.append({'persona': persona, 'interests': interests, 'model': name,
                             **{key: row[key] for key in ['rank', 'course_title', 'course_organization',
                                'course_difficulty', 'course_rating', 'enrolled_count', 'similarity',
                                'baseline_score', 'match_score', 'recommendation_type', 'reason']}})
            diagnostics.append({'persona': persona, 'model': name, 'returned': len(results),
                                'unique_titles': results.course_title.nunique(),
                                'topical_count': int(results.similarity.gt(0).sum()),
                                'fallback_count': int(results.recommendation_type.eq('Popularity fallback').sum()),
                                'mean_title_similarity': float(results.similarity.mean())})
    comparison = pd.DataFrame(rows)
    comparison.to_csv(out / 'model_comparison.csv', index=False)
    pd.DataFrame(diagnostics).to_csv(out / 'diagnostics.csv', index=False)
    keys = ['persona', 'model', 'rank', 'course_title']
    template = comparison[keys + ['interests', 'recommendation_type']].copy()
    label_path = out / 'evaluation_template.csv'
    if label_path.exists():
        old = pd.read_csv(label_path)
        if old.duplicated(keys).any():
            raise ValueError('Duplicate evaluation keys; correct human label CSV before rerunning.')
        template = template.merge(old[keys + ['human_relevance_0_1']], on=keys, how='left', validate='one_to_one')
    else:
        template['human_relevance_0_1'] = pd.NA
    template.to_csv(label_path, index=False)
    evaluation = evaluate_precision_at_5(template)
    evaluation.to_csv(out / 'evaluation_summary.csv', index=False)
    versions = {'python': platform.python_version(), **{
        name: importlib.metadata.version(name) for name in ['pandas', 'numpy', 'scikit-learn', 'streamlit', 'matplotlib']}}
    (out / 'environment.json').write_text(json.dumps(versions, indent=2), encoding='utf-8')
    lines = ['# Actual data and recommendation evidence', '',
             f"Raw rows: {stats['raw_rows']}; unique cleaned titles: {len(df)}; organizations: {stats['organizations']}.",
             f"Duplicate titles removed: {stats['duplicate_titles_removed']}; average known rating: {df.course_rating.mean():.3f}.",
             '', 'All personas below are synthetic keyword examples. No human evaluation labels were generated.',
             'Baseline: 70% normalized log enrollment + 30% rating/5, then min-max normalized.',
             'Selected: title unigrams + bigrams; 15% popularity and 85% cosine similarity.',
             'Titles and queries share deterministic aliases: math/maths, AI, ML, stats; displayed titles remain original.',
             'This is a qualitative design choice: bigrams represent phrases; the lower popularity weight prioritizes title matches.',
             'Diagnostics compare vocabulary variants and weights; they are not accuracy, and similarities across vocabularies are not directly comparable.',
             'No configuration is claimed to be empirically optimal without human judgments.', '']
    for persona in PROFILES:
        lines += [f'## {persona}', '']
        for name in ['Popular', 'bigram_w15']:
            lines.append(f'### {name}')
            for row in comparison.loc[comparison.persona.eq(persona) & comparison.model.eq(name)].itertuples():
                lines.append(f'{row.rank}. {row.course_title} — {row.recommendation_type}; cosine {row.similarity:.3f}')
            lines.append('')
    selected = comparison.loc[comparison.model.eq('bigram_w15')]
    coverage = selected.course_title.nunique() / len(df)
    lines += [f'Catalog coverage across the three selected-model top-5 lists: {selected.course_title.nunique()}/{len(df)} ({coverage:.2%}).',
              'Scope: this small synthetic profile set only; not population-wide coverage.',
              f'Unique titles in every returned top-5: {bool(pd.DataFrame(diagnostics).unique_titles.eq(5).all())}.',
              '', '## Human evaluation',
              'Fill every returned item with 0 (irrelevant) or 1 (relevant) based on the stated interest query.',
              'Precision@5 is emitted only for a complete five-course model/persona group. Partial, invalid or missing labels remain unevaluated.',
              'Re-run analysis.py after labeling; existing labels for unchanged returned items are preserved.',
              'Human-label provenance is a team responsibility. The program checks completeness, not who entered the labels.']
    (out / 'results.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps(stats, ensure_ascii=True, indent=2))
    print(f'Generated {len(comparison)} actual recommendation rows; {len(evaluation)} evaluation groups.')
    print(evaluation.status.value_counts().to_string())
    print(f'Artifacts: {out}')

if __name__ == '__main__':
    main()
