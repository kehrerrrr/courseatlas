# Actual data and recommendation evidence

Raw rows: 891; unique cleaned titles: 888; organizations: 154.
Duplicate titles removed: 3; average known rating: 4.677.

All personas below are synthetic keyword examples. No human evaluation labels were generated.
Baseline: 70% normalized log enrollment + 30% rating/5, then min-max normalized.
Selected: title unigrams + bigrams; 15% popularity and 85% cosine similarity.
Titles and queries share deterministic aliases: math/maths, AI, ML, stats; displayed titles remain original.
This is a qualitative design choice: bigrams represent phrases; the lower popularity weight prioritizes title matches.
Diagnostics compare vocabulary variants and weights; they are not accuracy, and similarities across vocabularies are not directly comparable.
No configuration is claimed to be empirically optimal without human judgments.

## Synthetic: data learner

### Popular
1. Machine Learning — Popular; cosine 0.592
2. The Science of Well-Being — Popular; cosine 0.305
3. Python for Everybody — Popular; cosine 0.132
4. Programming for Everybody (Getting Started with Python) — Popular; cosine 0.076
5. English for Career Development — Popular; cosine 0.000

### bigram_w15
1. Machine Learning — Title match; cosine 0.592
2. Data Science — Title match; cosine 0.534
3. Python for Data Science and AI — Title match; cosine 0.547
4. What is Data Science? — Title match; cosine 0.534
5. Data Science: Statistics and Machine Learning — Title match; cosine 0.542

## Synthetic: business learner

### Popular
1. Machine Learning — Popular; cosine 0.000
2. The Science of Well-Being — Popular; cosine 0.000
3. Python for Everybody — Popular; cosine 0.000
4. Programming for Everybody (Getting Started with Python) — Popular; cosine 0.000
5. English for Career Development — Popular; cosine 0.000

### bigram_w15
1. Finance for Non-Finance Professionals — Title match; cosine 0.354
2. Introduction to Marketing — Title match; cosine 0.314
3. Digital Marketing — Title match; cosine 0.293
4. Marketing Digital — Title match; cosine 0.301
5. Marketing Strategy — Title match; cosine 0.304

## Synthetic: wellbeing learner

### Popular
1. Machine Learning — Popular; cosine 0.000
2. The Science of Well-Being — Popular; cosine 0.000
3. Python for Everybody — Popular; cosine 0.000
4. Programming for Everybody (Getting Started with Python) — Popular; cosine 0.000
5. English for Career Development — Popular; cosine 0.000

### bigram_w15
1. Introduction to Psychology — Title match; cosine 0.367
2. A Life of Happiness and Fulfillment — Title match; cosine 0.357
3. Positive Psychology — Title match; cosine 0.356
4. Social Psychology — Title match; cosine 0.346
5. Foundations of Positive Psychology — Title match; cosine 0.271

Catalog coverage across the three selected-model top-5 lists: 15/888 (1.69%).
Scope: this small synthetic profile set only; not population-wide coverage.
Unique titles in every returned top-5: True.

## Human evaluation
Fill every returned item with 0 (irrelevant) or 1 (relevant) based on the stated interest query.
Precision@5 is emitted only for a complete five-course model/persona group. Partial, invalid or missing labels remain unevaluated.
Re-run analysis.py after labeling; existing labels for unchanged returned items are preserved.
Human-label provenance is a team responsibility. The program checks completeness, not who entered the labels.
