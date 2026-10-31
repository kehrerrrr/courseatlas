# CourseAtlas — Discover your next course

基于真实 Coursera 课程标题的可解释 Top-5 推荐模型，配有热门基线、Streamlit 演示、EDA 图表、参数对比和人工评价模板。Group W 数据挖掘作业用；本项目不生成最终 PDF/PPT。

## Windows 快速运行

当前项目已配置 `.venv`，无需重复安装：

```powershell
Set-Location 'C:\Users\James\Documents\ChatGPT\选课模型搭建'
$env:PYTHONIOENCODING = 'utf-8'
.\.venv\Scripts\python.exe analysis.py
.\.venv\Scripts\python.exe -m unittest discover -s tests
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --browser.gatherUsageStats false
```

打开 http://127.0.0.1:8501 。终端按 Ctrl+C 停止。也可以激活虚拟环境后运行 `python analysis.py`、`python -m unittest discover -s tests` 和 `streamlit run app.py`。

在另一台电脑安装（Python 3.12）：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe analysis.py
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1
```

默认模式为 **Personalized**。首次使用输入英文兴趣关键词，选择数据中存在的难度，可排除学过的课程，点击 **Recommend 5 courses**。切换 **Personalized / Popular** 比较同一筛选条件下的两种结果。Popular 明示兴趣关键词不参与排名，且只显示热门得分解释。Personalized 显示本次 Top-5 的标题匹配/热门补位数量及筛选后全部可选课程数。页面并排展示相同筛选下的真实两组 Top-5 与共享课程的名次变化；不在另一组 Top-5 中的课程不推算名次。这是结果对照，不是效果指标。所有补位课程均标注 **Popularity fallback**。空白、停用词、词表外输入会退回热门排序；筛选不足五门时仅返回真实可用的课程。

## 数据来源与处理

siddharthm1698, *Coursera Course Dataset*, Kaggle：
https://www.kaggle.com/datasets/siddharthm1698/coursera-course-dataset/data

本次直接下载公开 Kaggle API（未使用替代镜像）：
https://www.kaggle.com/api/v1/datasets/download/siddharthm1698/coursera-course-dataset

原始文件保存在 `data/raw/coursea_data.csv`，891 行。移除多余索引列，清理空格，解析 k/m/逗号形式的选课人数，对同名课程按规范化标题去重，得到 888 个唯一课程标题。重复标题优先保留人数较高、其次评分较高的一行，稳定保留原始行次序作为最后决胜规则。原始数据保持不变；来源 SHA-256、缺失值等详见 `artifacts/cleaning_summary.json`。

如缺少数据，从上述 Kaggle 页面下载并解压，将唯一 CSV 放在 `data/raw/`，再运行 `analysis.py`。不会自动改用其他数据或生成虚构行。数据许可和再分发条件应以 Kaggle 来源页面为准。

## 方法与证据

- 热门基线：70% 归一化 log1p(人数) + 30% 评分/5，再对组合值 min-max 归一化。
- 关键词归一化：在标题和查询中使用确定性整词映射 math/maths→mathematics、AI→artificial intelligence、ML→machine learning、stats→statistics。保留原始展示标题，不调用外部服务；这是少量词汇规则，不是语义理解。
- 个性化：真实标题 TF-IDF，英文停用词，unigram+bigram；先筛选难度与排除已学课程，再以 `0.85 * cosine + 0.15 * normalized_baseline` 排序所有标题匹配项。不足五门以热门补位。
- 参数对比：unigram 与 unigram+bigram，热门权重 0.15 与 0.30，在三个明确标注的合成兴趣画像上生成实际 Top-5，共 75 行（含热门基线）。所选参数是透明的定性设计选择，不是由虚构准确率确定。
- 评价：`artifacts/evaluation_template.csv` 的 `human_relevance_0_1` 默认留空。请真人针对兴趣填写 0/1；重跑 `analysis.py` 只对五条标签全部有效的画像/模型组合计算 Precision@5。相同推荐的既有标签会保留。
- 测试中的 0/1 仅为评价函数单元测试输入，不会写入实际评价模板。

## 文件

| 文件 | 用途 |
| --- | --- |
| `app.py` | 单一 Streamlit 演示界面 |
| `.streamlit/config.toml` | 浅色主题、品牌色与本机服务配置 |
| `recommender.py` | 清洗、热门基线、TF-IDF 推荐 |
| `analysis.py` | 图表、参数对比、诊断、人工评价 |
| `data/processed/courses_cleaned.csv` | 实际清洗结果 |
| `artifacts/results.md` | 三组兴趣的实际热门与个性化 Top-5、覆盖诊断 |
| `artifacts/model_comparison.csv` | 四套参数和热门基线的实际推荐 |
| `artifacts/diagnostics.csv` | 重复、条数、匹配与补位诊断 |
| `artifacts/*distribution.png` | 英文 EDA 图表 |
| `artifacts/evaluation_template.csv` | 留空的人工相关性标签 |
| `artifacts/evaluation_summary.csv` | 完整人工标签才生成的 Precision@5 |
| `artifacts/environment.json` | 实际运行依赖版本 |
| `docs/methodology.md` | 方法、优化说明和局限 |
| `docs/ai_process.md` | 真实 AI 使用与调整记录、截图采集指引 |
| `docs/report_slides_handoff.md` | <=10 页报告与 15 分钟汇报结构 |

## 诚实的限制

这是历史课程快照，不代表现在可报名课程、实时评分或课程人数。数据无个人历史、描述、技能、课程网址或封面。匹配分数是排序启发式，不是成功率或喜欢概率；不使用协同过滤，没有监督训练或真实用户测试。标题相似不等于内容合适。缺失评分/人数保留缺失、显示 unavailable；仅在基线计算中按 0 处理，绝不展示为真实评分。原始非英文标题可保留，但英文关键词与停用词设置会限制跨语言匹配。

## AI Learning Architect — local goal-based roadmaps

Open the **AI Learning Architect** tab, describe a goal, choose Beginner/Intermediate/Advanced and a 3- or 5-course path, then select **Build my roadmap**. Optional completed-course exclusions and comma-separated known topics are respected. Known topics exclude exact normalized title phrases, not inferred skills. Active inputs are shown above the timeline; form edits apply only when rebuilding.

The local planner recognizes four manually curated goal families: Data Analyst, Machine Learning (including AI/ML aliases), Business Analytics, and Python Programming. It suggests Foundation → Core Learning → Advanced Exploration topic slots. Other goals get explicitly labeled title-keyword exploration only. Course metadata is copied from the existing real dataset; no descriptions, skills, durations or prerequisites are generated.

Working refinements: **Make it easier** lowers the level and eventually restricts all steps to Beginner; **I already know this** excludes the selected actual course; **Shorten my path** selects three slots; **Apply focus** biases within-topic ranking with title keywords; **Regenerate roadmap** rotates deterministically among up to three top candidates per topic. Unavailable actions are disabled. Inputs and rankings are recomputed; identical courses can remain when candidates are limited or a focus provides no extra distinction.

Implementation: `roadmap.py`, integrated in `app.py`; deterministic tests in `tests/test_roadmap.py` and the persistent Streamlit smoke test in `tests/test_roadmap_app.py`. No new dependency, API key or external model. See `docs/learning_architect.md` for the group-report method and actual evidence.

This is a suggested learning sequence, not an official Coursera prerequisite pathway. Stage labels do not imply verified skills, completion history or outcomes; Advanced Exploration does not require an Advanced source difficulty. Missing stages stay visible, without unrelated popular replacements. The planner does not guarantee career readiness or mastery, and its keyword rules can miss goals or misread ambiguous language.
