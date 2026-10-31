"""Local rule-based learning sequence suggestions; no verified prerequisites."""
import re
from copy import deepcopy
from recommender import normalize_learning_terms

LEVELS = ['Beginner', 'Intermediate', 'Advanced']
STAGES = ['Foundation', 'Core Learning', 'Advanced Exploration']
# query, required title pattern. These are planning topics, never claimed course skills.
TOPICS = {
    'Python basics': ('introduction python programming', r'\bpython\b'),
    'Python practice': ('python programming everybody', r'\bpython\b'),
    'Mathematics': ('mathematics linear algebra calculus', r'\b(?:mathematics|linear algebra|calculus)\b'),
    'Statistics': ('statistics probability', r'\b(?:statistics|statistical|probability)\b'),
    'SQL': ('sql databases data', r'\b(?:sql|mysql|databases?)\b'),
    'Data analysis': ('data analysis analytics', r'\bdata\s+(?:analysis|analytics)\b'),
    'Visualization': ('data visualization tableau', r'\b(?:visualization|visualisation|tableau|plotting)\b'),
    'Machine learning': ('machine learning', r'\bmachine learning\b'),
    'Deep learning': ('deep learning neural networks', r'\b(?:deep learning|neural networks?|tensorflow)\b'),
    'Excel': ('excel business essentials', r'\bexcel\b'),
    'Business analytics': ('business analytics', r'\bbusiness\s+(?:analytics|analysis|intelligence)\b'),
    'Python data structures': ('python data structures', r'(?=.*\bpython\b)(?=.*\bdata structures\b)'),
    'Python data analysis': ('python data analysis', r'(?=.*\bpython\b)(?=.*\b(?:data|analysis)\b)'),
    'Python applications': ('python applications databases web', r'(?=.*\bpython\b)(?=.*\b(?:databases|web|applied|automation|capstone)\b)'),
}
PROGRESSIONS = {
    'Data Analyst': (r'\bdata\s+(?:analysts?|analysis|analytics)\b',
                     ['Python basics', 'Statistics', 'SQL', 'Data analysis', 'Visualization']),
    'Machine Learning': (r'\b(?:machine learning|artificial intelligence|deep learning)\b',
                         ['Python basics', 'Mathematics', 'Statistics', 'Machine learning', 'Deep learning']),
    'Business Analytics': (r'\bbusiness\s+(?:analysts?|analytics|analysis|intelligence)\b',
                           ['Excel', 'Statistics', 'Business analytics', 'Data analysis', 'Visualization']),
    'Python Programming': (r'\bpython\b',
                           ['Python basics', 'Python practice', 'Python data structures', 'Python data analysis', 'Python applications']),
}
_NO_EXPERIENCE = re.compile(r"\b(?:(?:no|zero|without)\s+(?:prior\s+)?(?:programming|coding)\s+experience|never\s+(?:coded|programmed)|new to\s+(?:programming|coding))\b")
_BOILERPLATE = {'i', 'want', 'become', 'learn', 'learning', 'career', 'goal', 'work',
                'experience', 'please', 'help', 'interested', 'like', 'need', 'start'}

def normalized(text):
    text = normalize_learning_terms(text)
    return re.sub(r'\b(?:data scientist)\b', 'data science', text)

def known_topic_list(text):
    return [normalized(t).strip() for t in re.split(r'[,;\n]+', text or '') if t.strip()]

def goal_intent(goal):
    # Keep the main goal clause separate from experience context.
    intent = re.split(r'\b(?:but|however|without)\b', normalized(goal), maxsplit=1)[0]
    matches = [(m.start(), name) for name, (pattern, _) in PROGRESSIONS.items()
               if (m := re.search(pattern, intent))]
    return min(matches)[1] if matches else None

def refine_request(request, action, course='', focus=''):
    updated = deepcopy(request)
    if action == 'easier':
        index = LEVELS.index(updated['level'])
        if index:
            updated['level'] = LEVELS[index - 1]
        else:
            updated['easier'] = True
    elif action == 'known':
        if course and course not in updated['completed']:
            updated['completed'].append(course)
    elif action == 'shorten':
        updated['length'] = 3
    elif action == 'focus':
        updated['focus'] = focus.strip()
    elif action == 'regenerate':
        updated['variant'] = updated.get('variant', 0) + 1
    else:
        raise ValueError('Unknown refinement action.')
    return updated

def plan_roadmap(model, goal, level='Beginner', completed=(), known_topics='', length=5,
                 focus='', easier=False, variant=0):
    if level not in LEVELS or length not in [3, 5] or variant < 0:
        raise ValueError('Use a supported level, path length 3/5 and nonnegative variant.')
    result = {'steps': [], 'gaps': [], 'notes': [], 'goal_type': None,
              'effective_level': level, 'strategy': 'Curated topic progression'}
    if not goal.strip():
        result['notes'].append('Enter a learning goal to build a roadmap.')
        return result
    if _NO_EXPERIENCE.search(normalized(goal)):
        level = 'Beginner'
        result['effective_level'] = level
        result['notes'].append('The goal states no programming experience; Beginner planning rules are applied.')
    intent = goal_intent(goal)
    result['goal_type'] = intent
    if intent:
        topics = PROGRESSIONS[intent][1]
    else:
        # Strip conversational boilerplate; never pretend to recognize a new profession.
        intent_text = re.split(r'\b(?:but|however|without)\b', normalized(goal), maxsplit=1)[0]
        tokens = model.vectorizer.build_analyzer()(intent_text)
        generic_query = ' '.join(dict.fromkeys(t for t in tokens if ' ' not in t and t not in _BOILERPLATE))
        topics = [generic_query] * 5
        result['strategy'] = 'Title-based exploration only'
        result['notes'].append('No curated progression recognizes this goal. Any results are title-keyword exploration, not an understood career pathway or verified progression.')
    slots = [0, 3, 4] if length == 3 else list(range(5))
    stage_ids = [0, 0, 1, 1, 2]
    known = known_topic_list(known_topics)
    excluded = list(completed)
    all_eligible = model.eligible_courses(completed=excluded)
    # Explicit topic exclusions match title phrases only; no inferred skills/history.
    known_titles = []
    for row in all_eligible.itertuples():
        title = normalized(row.course_title)
        if any(re.search(r'\b' + re.escape(t) + r'\b', title) for t in known):
            known_titles.append(row.course_title)
    excluded.extend(known_titles)
    if known:
        result['notes'].append('Known topics exclude titles containing those exact normalized phrases; no mastery is inferred.')
    focus_results = model.recommend(normalized(focus), completed=excluded, k=len(model.courses)) if focus.strip() else None
    focus_scores = dict(zip(focus_results.course_title, focus_results.similarity)) if focus_results is not None else {}
    if focus.strip() and not any(v > 0 for v in focus_scores.values()):
        result['notes'].append('The focus has no matching title terms; it cannot influence this roadmap.')
    for slot in slots:
        stage = stage_ids[slot]
        topic = topics[slot]
        topic_label = topic if intent else 'Goal title keywords'
        query, pattern = TOPICS[topic] if intent else (topic, None)
        allowed = (['Beginner'] if easier else
                   ['Beginner'] if stage == 0 and level == 'Beginner' else
                   ['Beginner', 'Intermediate', 'Mixed'] if level == 'Beginner' else
                   ['Beginner', 'Intermediate', 'Mixed'] if stage == 0 else
                   ['Beginner', 'Intermediate', 'Mixed', 'Advanced'])
        allowed_titles = set()
        for difficulty in allowed:
            allowed_titles.update(model.eligible_courses(difficulty, excluded).course_title)
        retrieved = model.recommend(query, completed=excluded, k=len(model.courses))
        candidates = retrieved.loc[retrieved.similarity.gt(0) & retrieved.course_title.isin(allowed_titles)].copy()
        if pattern:
            candidates = candidates.loc[candidates.course_title.map(lambda title: bool(re.search(pattern, normalized(title))))].copy()
        if candidates.empty:
            result['gaps'].append({'stage': stage + 1, 'stage_name': STAGES[stage], 'topic': topic_label,
                                  'message': f'No unused title-supported course for {topic_label} under the level, known-topic and completed-course exclusions.'})
            continue
        preferred = 'Beginner' if stage == 0 or level == 'Beginner' or easier else 'Intermediate' if level == 'Intermediate' else 'Advanced'
        # Progression fixes topic order; difficulty is only a within-topic preference.
        candidates['planning_score'] = (.75 * candidates.match_score
                                        + .20 * candidates.course_title.map(focus_scores).fillna(0)
                                        + .05 * candidates.course_difficulty.eq(preferred).astype(float))
        candidates = candidates.sort_values(['planning_score', 'title_key'], ascending=[False, True]).head(3)
        chosen = candidates.iloc[variant % len(candidates)]
        step = {field: chosen[field] for field in ['course_title', 'course_organization', 'course_difficulty', 'course_rating']}
        step.update({'stage': stage + 1, 'stage_name': STAGES[stage], 'topic': topic_label,
                     'step': len(result['steps']) + 1,
                     'reason': f'Planning heuristic: {topic_label} at {STAGES[stage].lower()}. {chosen["reason"]}. Source difficulty: {chosen.course_difficulty}; level preference: {preferred}.',
                     'similarity': float(chosen.similarity)})
        if focus_scores.get(chosen.course_title, 0) > 0:
            step['reason'] += ' Focus terms also match this title.'
        result['steps'].append(step)
        excluded.append(chosen.course_title)
    if len(result['steps']) < length:
        result['notes'].append(f'Only {len(result["steps"])} of {length} requested steps are supported. Gaps are not filled with unrelated popular courses.')
    if variant:
        result['notes'].append('Regeneration deterministically rotates among up to three top title-supported candidates per topic. A topic with only one candidate may stay unchanged.')
    return result
