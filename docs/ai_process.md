# 实际 AI 工作过程与截图指引

## 真实任务来源

用户提供 `C:\Users\James\Desktop\课程选课模型\SKILL.md`，随后明确要求：“按它搭建课程选课模型”。技能名 coursera-recommender。没有补造此前对话、人工反馈或未发生的模型实验。

实际实现目标来自该技能：使用指定 Kaggle 数据，先检查再清洗，实现热门与标题 TF-IDF 推荐、四套轻量参数比较、真实数据图表、留空人工标签模板、Streamlit UI 与 smoke tests；不生成最终 PDF/PPT。

## 本次可核验的调整

| 观察到的问题或事实 | 实际处理 | 结果/证据 |
| --- | --- | --- |
| 初始工作目录仅有 Git 元数据，无 CSV 或应用代码 | 从指定公开 Kaggle API 下载 coursea_data.csv，保留原件 | 891 行，来源哈希见 cleaning_summary.json |
| 内置 Python 有 pandas/numpy，缺少 sklearn/streamlit/matplotlib | 在项目 .venv 安装缺少的依赖，复用已有 pandas/numpy | requirements.txt 与 environment.json |
| 首次打印样例标题时，Windows GBK 控制台无法编码上标字符 | 将输出编码设为 UTF-8，重新检查三条实际标题 | 数据下载与文件未受影响；不删除课程字符 |
| 规范化标题出现 3 个重复项 | 优先保留人数高、评分高的同名行，稳定去重 | 888 个唯一标题，清洗统计自动输出 |
| 数据没有用户历史、描述、技能或链接 | 只在真实标题上拟合 TF-IDF，以输入关键词个性化，并明示热门补位 | recommender.py、实际推荐和 UI 解释 |

| 实际浏览器中系统深色主题使白色卡片内的表单标签对比度偏低 | 添加 .streamlit/config.toml 明确浅色主题、品牌色和文字色 | 重新检查浏览器中的标签、输入控件与课程卡片 |

## 实际验证记录

- `analysis.py` 已从真实数据生成 75 行推荐比较、两幅 EDA 图和 15 组空白人工评价。没有生成任何真实评价标签。
- `python -m unittest discover -s tests -v`：8 项通过，包括解析、去重、真实字段、排除、难度、空白/OOV 和评价完整性。
- Streamlit AppTest：首次渲染和五张卡片、模式切换、OOV、空白、Beginner 筛选及排除 The Science of Well-Being 全部通过，无应用异常。
- `python -m streamlit run app.py` 成功监听 127.0.0.1:8501，实际浏览器显示 CourseAtlas 与真实课程数据。

## 由团队 A 采集的真实截图（占位指引）

1. [待采集] 本聊天中用户提供技能与“按它搭建课程选课模型”的真实消息。
2. [待采集] 本聊天中数据检查、编码问题及修复、真实测试结果的工具输出。
3. [待采集] 参数对比 CSV 与 results.md 中真实三组兴趣结果；人工标签空白状态。
4. [待采集] 自己在 CourseAtlas 输入兴趣、切换 Popular/Personalized、排除已学课程的真实页面。
5. [待采集] 若后续由团队真人标注，截图保留标注依据与重跑的 Precision@5 结果。

这些是采集指引，不是已存在的图片。禁止制作伪造聊天截图或把合成兴趣画像称为真实受试者。可直接引用本聊天作为 AI 任务提示证据；报告中写明后续人工调整和观察，不能将建议写成已完成实验。

## 后续界面与关键词改进（实际完成）

用户要求：“Improve the existing CourseAtlas Streamlit application without rebuilding it from scratch.” 本次保留数据、项目结构及排名公式，增加五组确定性关键词别名（math/maths 共用 mathematics），默认 Personalized、条件化模型解释、匹配/补位/候选数量，以及相同筛选下两组实际 Top-5 和共享课程名次变化。卡片变紧凑、文字对比度增强、图表改为全宽标签页，小屏对比列表自动纵向排列。模型缓存增加版本键，防止服务继续使用旧的未归一化词表。

实际验证：analysis.py 成功生成更新后的真实结果；10 项 unittest 全部通过；Streamlit AppTest 验证默认模式、Popular 不展示个性化公式或 Applied interests、候选数/匹配/补位数、真实课程与名次变化、空白/OOV、同义词、筛选排除和无候选情况。人工标签仍全部空白。HTTP 首页与健康端点均返回 200。最终浏览器连接不可用，未声称完成本轮视觉复查或产生新截图；自动应用交互检查已通过。

## Goal-based roadmap feature

Actual new request: “CourseAtlas AI Learning Architect — Goal-Based Learning Path Planner.” Implemented an isolated tab and local roadmap.py using existing title TF-IDF and shared filters, with real courses and working refinement controls. Actual implementation, adjustments, limitations and test evidence are recorded in docs/learning_architect.md. No external AI model, new dependency or fabricated course metadata was added.
