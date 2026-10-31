# AI Learning Architect — implementation and report evidence

## Actual feature scope

The user requested a goal-based planner added to the existing CourseAtlas application, with no external LLM/API, no invented prerequisite data, and working refinements. `app.py` now has Discover courses and AI Learning Architect tabs. The established recommendation formulas, data and shared `CourseRecommender.eligible_courses` are reused unchanged. `roadmap.py` contains topic maps, goal matching, planning and pure refinement updates. No new dependency was installed. No final PDF/PPT was generated.

## Local planning method

Shared deterministic normalization covers math/maths, AI, ML and stats; a small explicit goal pattern map recognizes Data Analyst, Machine Learning, Business Analytics and Python Programming. The earliest recognized goal phrase before but/however/without is used; this is limited clause matching, not general language understanding. An explicit no-programming-experience phrase applies Beginner planning rules. Unknown goals use non-boilerplate title TF-IDF terms from the goal clause and show that no curated progression was recognized. Unmatched terms yield gaps, not fabricated courses.

Five-topic manual sequences:

| Family | Foundation (2) | Core Learning (2) | Advanced Exploration (1) |
| --- | --- | --- | --- |
| Data Analyst | Python basics, Statistics | SQL, Data analysis | Visualization |
| Machine Learning | Python basics, Mathematics | Statistics, Machine learning | Deep learning |
| Business Analytics | Excel, Statistics | Business analytics, Data analysis | Visualization |
| Python Programming | Python basics, Python practice | Python data structures, Python data analysis | Python applications |

A three-course request uses slots 1, 4, 5, one per stage. Topic regex constraints require actual title support (Python foundations also need an introductory/programming title cue); only positive title-similarity courses are candidates. CourseRecommender performs shared exclusions and source-difficulty filtering. Beginner foundation slots require Beginner; later Beginner slots allow Beginner/Intermediate/Mixed. Intermediate foundations also exclude Advanced. Make it easier lowers the planning level, then restricts every slot to Beginner. Mixed is a source label, not a verified difficulty measurement.

Topic order is fixed by the map, not by sorting every course by difficulty. Within a topic, score = 0.75 × existing match_score + 0.20 × focus cosine similarity + 0.05 × preferred-difficulty indicator. These weights are planning heuristics, not trained or evaluated parameters. Exact normalized known-topic phrases exclude matching titles. Completed and previously selected courses are excluded through the shared interface, ensuring unique real courses. No-match/popularity fallback items are discarded. Gaps remain in their original stages and are explicitly explained.

Regeneration increments a revision counter and rotates among up to three top eligible candidates per topic; deterministic repetition or unchanged sparse slots is expected. Focus changes candidates within the existing topic map and cannot turn an unsupported goal into a verified career pathway. The form and active refinement request are separated visibly so it is clear which inputs produced the timeline.

## Actual checks and adjustments

- Six deterministic planner tests cover all four maps at lengths 3/5, metadata fidelity, sequencing, uniqueness, exclusions, known topics, empty/unknown goals, synonyms/context, level rules, missing SQL stage and every refinement update.
- Existing 10 recommendation/evaluation tests are retained unchanged.
- One persistent Streamlit smoke test exercises initial render, five-step build, easier, selected-course exclusion, shortening, focus, regeneration, both recommendation modes, unsupported goal and empty input.
- During implementation, the first smoke test used a relative app path that Streamlit resolved under tests/. Fixed it to the project ROOT. A second test tried to click a still-disabled focus button before processing the input rerun; the test now follows the real input-change/rerun/click lifecycle.
- A background-experience clause could otherwise supply misleading terms for an unknown goal. Both goal recognition and generic matching now isolate the main clause before but/however/without; an unsupported goal followed by no-programming-experience context is tested.
- Visual inspection caught a stage-badge CSS selector affecting nested heading spans. Narrowed it to the direct badge child so stage headings stay readable.
- Actual browser inspection showed the new form and a five-step Data Analyst roadmap with verified organizations, difficulties and ratings. No synthetic learner is claimed as a real user.

## Honest limitations for the report

No verified prerequisites, skills, descriptions, learning outcomes, durations or completion histories exist in the source. The suggested order is not an official Coursera pathway and cannot guarantee readiness, mastery or even content fit. Titles and rounded historical ratings are weak evidence. Known-topic exclusion is literal and can over-exclude or miss synonyms outside the small map. Negation, multiple goals and nuanced English are not fully understood. User level and claimed knowledge are self-reported inputs. Advanced Exploration is a planning stage, not a claim that the course is advanced. Human relevance labels and accuracy remain absent. Use genuine screenshots only; do not fabricate evaluations or conversations.

## Final verification evidence

`python -m unittest discover -s tests -v`: 17 tests passed (10 existing, 6 deterministic planner tests, 1 Streamlit end-to-end smoke test). Actual default Data Analyst output is saved in artifacts/roadmap_example.json, explicitly marked as a synthetic example goal. No relevance/evaluation labels were generated.

Final visual recheck confirmed readable Core Learning stage heading and course timeline at the narrow in-app browser width. A genuine screenshot was viewed during inspection; browser-tool filesystem writes were denied, so no screenshot artifact is claimed or included. Team A can capture the live tab for the report.
