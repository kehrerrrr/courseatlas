"""CourseAtlas — a local, explainable Coursera course discovery demo."""
from html import escape
from hashlib import sha256
from importlib import reload
import pandas as pd
import streamlit as st
import recommender
import roadmap
from recommender import ROOT

st.set_page_config(page_title='CourseAtlas | Discover your next course', page_icon='\U0001f393', layout='wide')
st.markdown('''
<style>
:root {--ink:#172033;--violet:#6658E8;}
.stApp {background:#F7F8FC;color:var(--ink);}
.block-container {max-width:1160px;padding-top:1.8rem;padding-bottom:3rem;}
[data-testid="stHeader"] {background:transparent;}
h1,h2,h3 {color:#172033;letter-spacing:-.035em;}
.hero {padding:4px 0 10px;max-width:900px;}
.eyebrow {color:#6658E8;font-size:12px;font-weight:750;letter-spacing:.16em;}
.hero h1 {font-size:clamp(32px,4.5vw,49px);line-height:1.12;margin:10px 0;}
.hero p {color:#45516A;font-size:16px;line-height:1.6;}
.brand {font-weight:800;font-size:21px;letter-spacing:-.6px;margin-bottom:16px;}
.brand span {color:#6658E8;}
.stat-row {display:flex;flex-wrap:wrap;gap:10px;margin:0 0 16px;}
.stat {border:1px solid #E5E9F2;background:white;padding:8px 14px;border-radius:50px;font-size:13px;color:#45516A;}
.stat b {color:#172033;font-size:15px;margin-right:5px;}
[data-testid="stForm"] {background:white;border:1px solid #E5E9F2;border-radius:18px;padding:18px;}
.stButton>button[kind="primary"],.stFormSubmitButton>button {background:#6658E8;border-color:#6658E8;border-radius:10px;min-height:44px;font-weight:650;}
.course-card {background:#fff;border:1px solid #E5E9F2;border-radius:14px;padding:14px 18px;margin:8px 0;box-shadow:0 5px 18px rgba(23,32,51,.035);}
.card-head {display:flex;gap:12px;align-items:flex-start;}
.number {background:#F0EEFF;color:#6658E8;min-width:32px;height:32px;border-radius:9px;display:grid;place-items:center;font-weight:750;}
.course-card h3 {font-size:18px;line-height:1.35;margin:0 0 5px;}
.org {font-size:13px;color:#45516A;}
.meta {display:flex;flex-wrap:wrap;gap:7px;margin:10px 0 8px;}
.pill {font-size:12px;border:1px solid #E5E9F2;border-radius:7px;padding:5px 9px;color:#45516A;}
.tag {font-size:12px;background:#E4F6EE;color:#267456;padding:5px 9px;border-radius:7px;}
.fallback {background:#FFF3DC;color:#8B651C;}
.reason {color:#45516A;font-size:13px;line-height:1.6;margin:0;}
.small-note {font-size:12px;color:#45516A;line-height:1.6;margin:12px 0;}
@media(max-width:640px){.block-container{padding-top:1.4rem}.course-card{padding:13px}.hero h1{font-size:34px}}
.card-fallback {border-left:4px solid #C58C28;}
.breakdown {display:flex;flex-wrap:wrap;gap:9px;margin:12px 0;}
.breakdown .stat {border-radius:10px;}
.comparison-grid {display:grid;grid-template-columns:1fr 1fr;gap:18px;}
.comparison-grid section {min-width:0;}
.comparison-grid h4 {font-size:16px;color:#172033;margin:4px 0 10px;}
.comparison-grid ol {list-style:none;padding:0;margin:0;}
.comparison-grid li {display:flex;gap:10px;border-top:1px solid #E5E9F2;padding:10px 0;font-size:14px;line-height:1.45;}
.comparison-grid .position {font-weight:750;color:#6658E8;min-width:18px;}
.comparison-grid small {display:block;color:#45516A;font-size:12px;margin-top:3px;}
.comparison-grid .fallback-note {color:#795511;}
@media(max-width:640px){.comparison-grid{grid-template-columns:1fr;gap:14px}.meta{gap:6px}.stat{padding:8px 11px}}
.architect-hero {background:linear-gradient(125deg,#F0EEFF,#E4F6EE);border:1px solid #E5E9F2;border-radius:20px;padding:24px;margin:18px 0 12px;}
.architect-hero h2 {margin:10px 0;font-size:30px;}
.architect-hero p {color:#45516A;line-height:1.6;}
.road-stage {display:flex;align-items:center;gap:12px;margin:20px 0 8px;}
.road-stage > span {background:#6658E8;color:white;border-radius:50%;width:34px;height:34px;display:grid;place-items:center;font-weight:750;}
.road-stage h3 {font-size:19px;margin:0;}
.road-step {border-left:3px solid #B7ACEF;margin-left:16px;padding:16px 20px;}
.road-step .eyebrow {font-size:11px;letter-spacing:.07em;margin-bottom:7px;}
@media(max-width:640px){.architect-hero{padding:18px}.architect-hero h2{font-size:25px}.road-step{margin-left:10px;padding:13px}}
</style>
''', unsafe_allow_html=True)

@st.cache_resource
def load_model(path, modified, model_source_hash):
    # Streamlit reruns app.py but may retain an older imported model class.
    # Reload on a cache miss; the source hash invalidates resources after edits.
    return reload(recommender).CourseRecommender(pd.read_csv(path))

path = ROOT / 'data/processed/courses_cleaned.csv'
if not path.exists():
    st.error('Course data is missing. Run python analysis.py after placing the Kaggle CSV in data/raw/.')
    st.stop()
try:
    model_source_hash = sha256((ROOT / 'recommender.py').read_bytes()).hexdigest()
    model = load_model(str(path), path.stat().st_mtime_ns, model_source_hash)
except (ValueError, OSError) as exc:
    st.error(f'Unable to load course data: {exc}')
    st.stop()
df = model.courses
st.markdown('<div class="brand"><span>◈</span> CourseAtlas</div><div class="hero"><div class="eyebrow">CURIOUS MINDS. CLEAR NEXT STEPS.</div><h1>Discover your next course.</h1><p>Turn your interests into a learning shortlist, with transparent recommendations from real Coursera course titles.</p></div>', unsafe_allow_html=True)
orgs = df.loc[df.course_organization.ne('Unknown'), 'course_organization'].nunique()
rating = f'{df.course_rating.mean():.2f}' if df.course_rating.notna().any() else 'N/A'
st.markdown(f'<div class="stat-row"><div class="stat"><b>{len(df):,}</b> unique courses</div><div class="stat"><b>{orgs}</b> organizations</div><div class="stat"><b>{rating}/5</b> average known rating</div></div>', unsafe_allow_html=True)
discovery_tab, architect_tab = st.tabs(['Discover courses', 'AI Learning Architect'])
with discovery_tab:
    with st.form('discovery'):
        st.subheader('What would you like to learn?')
        interests = st.text_input('Your interests (English keywords)', value='python data science', placeholder='e.g. business finance, psychology, machine learning')
        left, right = st.columns([1, 2])
        with left:
            difficulty = st.selectbox('Difficulty', ['All levels'] + sorted(df.course_difficulty.unique().tolist()))
        with right:
            completed = st.multiselect('Courses you have already taken (optional)', df.course_title.tolist(), placeholder='Exclude completed courses')
        submitted = st.form_submit_button('Recommend 5 courses', type='primary')
    if submitted or 'request' not in st.session_state:
        st.session_state.request = (interests, difficulty, completed)
    query, chosen_level, taken = st.session_state.request
    st.markdown('### Your learning shortlist')
    mode = st.radio('Recommendation approach', ['Personalized', 'Popular'], index=0,
                    horizontal=True, key='recommendation_mode')
    personalized = model.recommend(query, chosen_level, taken, 'Personalized')
    popular = model.recommend(query, chosen_level, taken, 'Popular')
    results = personalized if mode == 'Personalized' else popular
    eligible_count = len(model.eligible_courses(chosen_level, taken))
    filter_note = f'{chosen_level} | {len(taken)} completed courses excluded | {eligible_count:,} eligible courses'
    if mode == 'Personalized':
        st.caption(f'Interest keywords: {query.strip() or "Blank query"} | {filter_note}')
        topical_count = int(results.recommendation_type.eq('Title match').sum())
        fallback_count = int(results.recommendation_type.eq('Popularity fallback').sum())
        st.markdown(f'<div class="breakdown"><div class="stat"><b>{topical_count}</b> Topical matches</div><div class="stat"><b>{fallback_count}</b> Popularity fallbacks</div><div class="stat"><b>{eligible_count:,}</b> Eligible courses</div></div>', unsafe_allow_html=True)
        st.caption('Match and fallback counts describe this shortlist. Eligibility includes all courses after difficulty filtering and completed-course exclusions.')
        if fallback_count:
            st.info(f'{fallback_count} popularity fallback item(s) have no interest match. Blank or unrecognized keywords use popularity for all results.')
    else:
        st.caption(filter_note)
        st.info('Popular ranks by enrollment and rating only. Your interest keywords are not used for ranking; the order is the same for everyone with these filters and exclusions.')
    st.caption('Edit the controls and press Recommend to update both shortlists.')
    if results.empty:
        st.info('No eligible courses remain. Choose another difficulty or remove some completed-course exclusions.')
    else:
        if len(results) < 5:
            st.info(f'Only {len(results)} eligible course(s) remain under these filters.')
        for row in results.itertuples():
            rating_text = f'{row.course_rating:.1f}/5 rating' if pd.notna(row.course_rating) else 'Rating unavailable'
            enrolled = f'{int(row.enrolled_count):,} enrolled' if pd.notna(row.enrolled_count) else 'Enrollment unavailable'
            is_match = row.recommendation_type == 'Title match'
            is_fallback = row.recommendation_type == 'Popularity fallback'
            score = f'Match score {row.match_score:.3f}' if is_match else f'Popularity score {row.baseline_score:.3f}'
            badge_class = 'tag fallback' if is_fallback else 'tag'
            badge = 'Popularity fallback: no interest match' if is_fallback else ('Topical title match' if is_match else 'Popular')
            card_class = 'course-card card-fallback' if is_fallback else 'course-card'
            st.markdown(f'<article class="{card_class}"><div class="card-head"><div class="number">{row.rank:02d}</div><div><h3>{escape(row.course_title)}</h3><div class="org">{escape(row.course_organization)}</div></div></div><div class="meta"><span class="{badge_class}">{badge}</span><span class="pill">{escape(row.course_difficulty)}</span><span class="pill">{rating_text}</span><span class="pill">{enrolled}</span><span class="pill">{score}</span></div><p class="reason">{escape(row.reason)}</p></article>', unsafe_allow_html=True)
    if mode == 'Personalized':
        score_note = 'For topical matches: match score = 85% title cosine similarity + 15% normalized popularity. Fallbacks show popularity scores only; they have no title-term match. Neither score is a probability of enjoyment.'
    else:
        score_note = 'Popularity score: 70% min-max normalized log enrollment + 30% rating/5, then the combined score is min-max normalized across the catalog. Missing values contribute zero. This is a relative ranking score, not a probability of enjoyment.'
    st.markdown(f'<p class="small-note">{score_note}</p>', unsafe_allow_html=True)

    def comparison_column(shortlist, other, name, other_name):
        other_ranks = dict(zip(other.course_title, other['rank']))
        items = []
        for row in shortlist.itertuples():
            other_rank = other_ranks.get(row.course_title)
            if other_rank is None:
                movement = f'Not in {other_name} Top 5'
            else:
                change = other_rank - row.rank
                movement = (f'Up {change}' if change > 0 else f'Down {-change}' if change < 0 else 'Same rank')
                movement += f' vs {other_name} (#{other_rank})'
            fallback = row.recommendation_type == 'Popularity fallback'
            kind = 'No interest match: popularity fallback' if fallback else row.recommendation_type
            kind_class = 'fallback-note' if fallback else ''
            items.append(f'<li><span class="position">{row.rank}</span><div>{escape(row.course_title)}<small>{escape(movement)}</small><small class="{kind_class}">{escape(kind)}</small></div></li>')
        body = '<ol>' + ''.join(items) + '</ol>' if items else '<p>No eligible courses.</p>'
        return f'<section><h4>{name}</h4>{body}</section>'

    with st.expander('Compare Personalized and Popular Top 5', expanded=True):
        st.caption('Same difficulty and completed-course exclusions. Rank changes compare only shared courses in these two Top 5 lists; a course outside the other list has no inferred rank. This comparison is not an evaluation metric.')
        st.markdown('<div class="comparison-grid">' + comparison_column(personalized, popular, 'Personalized', 'Popular') + comparison_column(popular, personalized, 'Popular', 'Personalized') + '</div>', unsafe_allow_html=True)
    with st.expander('How it works'):
        if mode == 'Personalized':
            st.write('A small deterministic map normalizes math/maths to mathematics, AI to artificial intelligence, ML to machine learning, and stats to statistics in both titles and queries. English keywords are matched against these normalized titles with TF-IDF unigrams and bigrams. Original course titles are displayed. Matching titles rank first; clearly labeled popularity fallback items fill any gaps after filters and exclusions.')
        else:
            st.write('Courses rank by enrollment and rating after difficulty filtering and completed-course exclusions. Interest keywords do not affect this ranking. The comparison also shows a separate Personalized shortlist using your submitted keywords.')
    with st.expander('Data limitations & source'):
        st.write('This historical Kaggle snapshot has titles, organizations, certificate types, ratings, difficulty and enrollment counts. It has no course descriptions, URLs, verified images or learner histories. Enrollment figures are rounded source estimates; course availability and ratings may have changed. Shared title terms are weak evidence of fit, not a skill assessment. Mixed is a source difficulty label.')
        st.markdown('[Dataset by siddharthm1698 on Kaggle](https://www.kaggle.com/datasets/siddharthm1698/coursera-course-dataset/data)')
        st.caption('This application makes no claim of affiliation with Coursera.')
    st.markdown('### Explore the catalog')
    difficulty_tab, distribution_tab = st.tabs(['Difficulty', 'Ratings & enrollment'])
    for panel, name in [(difficulty_tab, 'difficulty_distribution.png'), (distribution_tab, 'rating_enrollment_distribution.png')]:
        with panel:
            chart = ROOT / 'artifacts' / name
            if chart.exists():
                st.image(str(chart), width='stretch')
            else:
                st.caption('Run python analysis.py to generate catalog charts.')

with architect_tab:
    st.markdown('<div class="architect-hero"><div class="eyebrow">COURSEATLAS AI LEARNING ARCHITECT</div><h2>A goal. A direction. Your next steps.</h2><p>Build a suggested course sequence from real titles, with clear reasoning at every stage.</p><span class="tag">Local rules + TF-IDF | No external AI model</span></div>', unsafe_allow_html=True)
    st.caption('Suggested learning sequence, not an official Coursera prerequisite pathway. No guarantee of career readiness or skill mastery. No verified prerequisites, skills, outcomes, descriptions, durations or completion histories are available.')
    with st.form('architect_form'):
        goal = st.text_area('Learning or career goal', value='I want to become a data analyst, but I have no programming experience.', key='architect_goal', height=90)
        c1, c2 = st.columns([2, 1])
        with c1:
            current_level = st.selectbox('Current knowledge level', roadmap.LEVELS, key='architect_level')
        with c2:
            path_length = st.selectbox('Desired path length', [5, 3], key='architect_length')
        completed_path = st.multiselect('Completed or known courses (optional)', df.course_title.tolist(), key='architect_completed')
        known_topics = st.text_input('Known topics (optional, comma-separated)', placeholder='e.g. python, SQL', key='architect_topics')
        st.caption('Known topics exclude titles containing those exact normalized phrases. This may leave gaps; it does not verify what a course teaches.')
        build = st.form_submit_button('Build my roadmap', type='primary')
    if build:
        st.session_state.architect_request = dict(goal=goal, level=current_level, completed=list(completed_path),
            known_topics=known_topics, length=path_length, focus='', easier=False, variant=0)
        st.session_state.architect_notice = 'Roadmap built from your submitted goal and knowledge inputs.'
    if 'architect_request' not in st.session_state:
        st.info('Describe a goal and select Build my roadmap to start. You can refine the result below.')
    else:
        request = st.session_state.architect_request
        # Only planner rules are refreshed; the fitted course model stays cached.
        roadmap = reload(roadmap)
        planned = roadmap.plan_roadmap(model, **request)
        st.markdown('### Your learning roadmap')
        st.caption(f'Active goal: {request["goal"].strip() or "Empty goal"} | Planning level: {planned["effective_level"]} | Requested: {request["length"]} courses | Focus: {request["focus"] or "None"} | Excluded courses: {len(request["completed"])} | Known topics: {request["known_topics"] or "None"} | Revision: {request["variant"]}')
        st.caption('Form edits take effect with Build my roadmap. Refinements below update the active request immediately; the form remains available to start a fresh plan.')
        if st.session_state.get('architect_notice'):
            st.success(st.session_state.architect_notice)
        st.markdown(f'**{planned["goal_type"] or "Unrecognized goal"}** · {planned["strategy"]}')
        for note in planned['notes']:
            st.info(note)
        for stage_number, stage_name in enumerate(roadmap.STAGES, 1):
            st.markdown(f'<div class="road-stage"><span>{stage_number:02d}</span><h3>{stage_name}</h3></div>', unsafe_allow_html=True)
            for step in (item for item in planned['steps'] if item['stage'] == stage_number):
                rating = f'{step["course_rating"]:.1f}/5 rating' if pd.notna(step['course_rating']) else 'Rating unavailable'
                st.markdown(f'<article class="course-card road-step"><div class="eyebrow">STEP {step["step"]} · {escape(step["topic"])}</div><h3>{escape(step["course_title"])}</h3><div class="org">{escape(step["course_organization"])}</div><div class="meta"><span class="pill">{escape(step["course_difficulty"])}</span><span class="pill">{rating}</span><span class="tag">Suggested sequence</span></div><p class="reason">{escape(step["reason"])}</p></article>', unsafe_allow_html=True)
            for gap in (item for item in planned['gaps'] if item['stage'] == stage_number):
                st.warning(gap['message'])
        with st.expander('Why this order?', expanded=True):
            st.write('For recognized goals, a manually curated topic map sets Foundation → Core Learning → Advanced Exploration. A three-course path selects one topic per stage; a five-course path allocates two foundation topics, two core topics and one exploration topic. This is a planning heuristic, not verified prerequisite knowledge. Advanced Exploration is a planning stage, not necessarily an Advanced source difficulty label.')
            st.write('Within each topic, the existing title TF-IDF ranking contributes 75%, optional focus title similarity 20%, and a suitable source-difficulty preference 5%. Beginner foundations require Beginner courses; later Beginner stages allow Beginner, Intermediate or Mixed. Make it easier eventually restricts every stage to Beginner. No popularity-only course fills a gap.')
            st.write('For other goals, only non-boilerplate title keywords are used: stages are provisional exploration labels and no topic progression is claimed. Exact known-topic phrases and completed courses are excluded throughout. The data cannot confirm whether a course covers a skill or prepares you for a later course.')
        st.markdown('#### Refine your roadmap')
        def update_roadmap(action, course='', focus=''):
            st.session_state.architect_request = roadmap.refine_request(request, action, course, focus)
            st.session_state.architect_notice = {
                'easier': 'Planning difficulty reduced; the roadmap was recomputed.',
                'known': 'Selected course added to your exclusions; the roadmap was recomputed.',
                'shorten': 'Path length changed to three; the roadmap was recomputed.',
                'focus': 'Focus keywords updated; the roadmap was recomputed within the same topic progression.',
                'regenerate': 'Alternative candidate revision requested; the roadmap was recomputed.'}[action]
            st.rerun()
        r1, r2, r3 = st.columns(3)
        with r1:
            if st.button('Make it easier', disabled=request['level'] == 'Beginner' and request['easier'], key='road_easier'):
                update_roadmap('easier')
        with r2:
            if st.button('Shorten my path', disabled=request['length'] == 3, key='road_shorter'):
                update_roadmap('shorten')
        with r3:
            if st.button('Regenerate roadmap', key='road_regenerate'):
                update_roadmap('regenerate')
        k1, k2 = st.columns([3, 1])
        with k1:
            known_course = st.selectbox('Which step do you already know?', [s['course_title'] for s in planned['steps']], index=0 if planned['steps'] else None, key='road_known_step')
        with k2:
            if st.button('I already know this', disabled=not planned['steps'], key='road_known'):
                update_roadmap('known', course=known_course)
        f1, f2 = st.columns([3, 1])
        with f1:
            focus_topic = st.text_input('Focus more on [topic]', placeholder='e.g. Python, statistics, visualization', key='road_focus_topic')
        with f2:
            if st.button('Apply focus', disabled=not focus_topic.strip() or focus_topic.strip() == request['focus'], key='road_focus'):
                update_roadmap('focus', focus=focus_topic)
