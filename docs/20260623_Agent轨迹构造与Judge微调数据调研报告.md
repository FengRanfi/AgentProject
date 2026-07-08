# Agent 轨迹构造与 Judge 微调数据调研报告

> 调研日期：2026-06-23
> 目标：分析适合 MCP 搜索工具的 Query 数据集来源、魔搭平台适合构造轨迹的 MCP 工具、以及 Judge 模型微调数据的构造方法论

---

## 目录

1. [背景与目标](#1-背景与目标)
2. [适合 MCP 搜索工具的 Query 数据集](#2-适合-mcp-搜索工具的-query-数据集)
3. [魔搭平台适合构造轨迹的 MCP 工具](#3-魔搭平台适合构造轨迹的-mcp-工具)
4. [Judge 模型微调数据构造方法论](#4-judge-模型微调数据构造方法论)
5. [推荐的轨迹构造方案](#5-推荐的轨迹构造方案)
6. [参考文献](#6-参考文献)

---

## 1. 背景与目标

### 1.1 项目背景

当前项目已实现基于 AutoGen 框架 + MCP 工具的搜索 Agent，可使用 `jina_search`、`jina_reader`、`fetch` 等工具执行网页搜索和内容读取任务。现需批量产出 Agent 轨迹，用于构造 Judge 微调数据，训练轨迹级奖励模型（Trajectory-level Reward Model）。

### 1.2 核心问题

1. **Query 从哪里来？** 哪些公开数据集的问答对适合当前 MCP 工具组合？
2. **哪些 MCP 工具适合构造轨迹？** 魔搭平台上哪些 Hosted MCP 可以直接接入？
3. **Judge 数据怎么构造？** 业界有哪些轨迹级评判的方法论和基准？

### 1.3 当前可用工具

| 工具 | 类型 | 能力 |
|------|------|------|
| `jina_search` | 搜索 | 网页搜索，返回摘要和 URL |
| `jina_reader` | 读取 | 读取网页全文内容 |
| `fetch` | 读取 | 抓取网页并转换为 Markdown |

---

## 2. 适合 MCP 搜索工具的 Query 数据集

### 2.1 搜索/问答类数据集（与当前工具高度匹配）

#### 2.1.1 HotpotQA

| 属性 | 详情 |
|------|------|
| **来源** | CMU + Stanford + UdeM，EMNLP 2018 |
| **规模** | 113K 问答对（训练集 90,447，验证集 7,405） |
| **特点** | 多跳推理问答，需跨文档推理；提供 supporting facts 标注 |
| **License** | CC BY-SA 4.0 |
| **HuggingFace** | `hotpot_qa`（config: `fullwiki`） |
| **官网** | https://hotpotqa.github.io/ |

**为什么适合：**
- 问题需要多步搜索+读取，天然适合 jina_search + jina_reader 的组合
- `fullwiki` 配置提供开放域设置，需从全量维基百科检索
- 提供 supporting facts 标注，可直接作为 Judge 标注的参考标准
- 问题分 `bridge`（桥接型）和 `comparison`（比较型）两类，可构造不同轨迹类型
- 难度分 `easy`/`medium`/`hard` 三级，便于分层采样

**数据字段：**
```json
{
  "id": "xxx",
  "question": "What government position was held by the woman who portrayed Corliss Archer in the film Hit Parade of 1941?",
  "answer": "Chief of Protocol",
  "type": "bridge",
  "level": "hard",
  "supporting_facts": {"title": [...], "sent_id": [...]},
  "context": {"title": [...], "sentences": [[...], [...]]}
}
```

**轨迹映射：**
```
HotpotQA question → jina_search(entity1) → 读取结果A
                  → jina_search(entity2) → 读取结果B
                  → 交叉验证 → 综合回答
```

#### 2.1.2 NaturalQuestions (NQ)

| 属性 | 详情 |
|------|------|
| **来源** | Google AI，2019 |
| **规模** | 307,373 训练样本，7,830 开发集，7,842 测试集 |
| **特点** | 真实 Google 搜索查询 + 维基百科页面标注 |
| **License** | Apache 2.0 |
| **HuggingFace** | `natural_questions` |

**为什么适合：**
- 问题来自真实用户搜索，最贴近实际使用场景
- 每个 question 配对一个维基百科页面，有 long_answer 和 short_answer 标注
- 适合单步搜索+读取的轨迹构造
- 规模大，可大量采样

**轨迹映射：**
```
NQ question → jina_search(query) → 读取 top1 URL → 提取答案
```

#### 2.1.3 TriviaQA

| 属性 | 详情 |
|------|------|
| **来源** | University of Washington，ACL 2017 |
| **规模** | 95,956 问答对，650K+ 问答-证据三元组 |
| **特点** | 爱好者撰写的问题，独立于证据文档；每个问题平均 6 个证据文档 |
| **License** | MIT（LM-Polygraph 版本） |
| **HuggingFace** | `trivia_qa`（config: `rc` 或 `unfiltered`） |
| **官网** | https://nlp.cs.washington.edu/triviaqa/ |

**为什么适合：**
- 问题和证据文档独立收集，词汇重叠低，更考验搜索能力
- 证据文档来自维基百科和网络搜索，与 jina_search 的搜索场景一致
- 提供 RC 版本（阅读理解）和 unfiltered 版本（开放域）

**轨迹映射：**
```
TriviaQA question → jina_search(query) → 筛选相关结果 → jina_reader 读取 → 提取答案
```

#### 2.1.4 2WikiMultiHopQA

| 属性 | 详情 |
|------|------|
| **来源** | 2020 |
| **规模** | 192K 问答对 |
| **特点** | 跨维基百科多跳推理，提供推理路径标注 |
| **HuggingFace** | `2wikimultihop_qa` |

**为什么适合：**
- 提供明确的推理链（reasoning chain），便于验证 Agent 的多步搜索策略
- 问题需要 2 跳以上推理，适合构造多轮搜索轨迹

#### 2.1.5 MuSiQue

| 属性 | 详情 |
|------|------|
| **来源** | ICLR 2022 |
| **规模** | 2,417 训练，2,500 开发集 |
| **特点** | 复杂多跳问答，2-4 跳链式推理，每跳独立可答 |
| **HuggingFace** | `musique` |

**为什么适合：**
- 最复杂的多跳推理数据集之一
- 提供每跳的子问题和答案，可逐步验证 Agent 的推理过程
- 适合构造高难度的 Judge 数据

### 2.2 Agent 工具调用类数据集（轨迹格式参考）

#### 2.2.1 Toucan-1.5M

| 属性 | 详情 |
|------|------|
| **来源** | IBM + University of Washington，2025 |
| **规模** | 150 万工具调用轨迹，2,000+ 真实 Web 服务 |
| **特点** | 基于真实 MCP 环境合成，是目前最大的开源工具调用数据集 |
| **HuggingFace** | `Agent-Ark/Toucan-1.5M` |
| **论文** | arXiv:2510.01179 |

**为什么适合：**
- 直接基于 MCP 协议构建，与我们的工具架构一致
- 轨迹格式可直接参考
- 包含 500+ MCP 服务器的工具调用
- 小模型在 Toucan 上微调后可超越大模型

**构造流程（可参考）：**
```
1. 从 GitHub/Smithery 收集 MCP 服务器元数据
2. 过滤掉返回错误的服务
3. 使用 5 个开源 LLM 生成任务场景
4. 使用 3 个模型 + 框架构建步骤级轨迹
5. 使用 2 个 LLM 对轨迹进行难度和质量评分
6. 筛选最佳样本
```

#### 2.2.2 TRAJECT-Bench

| 属性 | 详情 |
|------|------|
| **来源** | MSU + Amazon，2025 |
| **规模** | 数千任务 |
| **特点** | 轨迹感知评测，有工具选择/参数/依赖评估指标 |
| **HuggingFace** | `bigboss24/TRAJECT-Bench` |
| **论文** | arXiv:2510.04550 |

**为什么适合：**
- 提供细粒度的轨迹级评测维度：工具选择正确性、参数正确性、依赖/顺序满足性
- 揭示了模型失效模式：相似工具混淆、参数盲目选择
- 评测维度可直接用于 Judge 标注设计

#### 2.2.3 BFCL v4 (Berkeley Function Calling Leaderboard)

| 属性 | 详情 |
|------|------|
| **来源** | UC Berkeley，ICML 2025 |
| **规模** | 数千函数调用样本 |
| **特点** | 工具调用评测的事实标准 |
| **评测维度** | 单轮单函数、单轮并行函数、多轮交互、相关性检测、长上下文、Agentic 决策 |

**为什么适合：**
- 可参考其评测维度设计 Judge 标注
- 多轮交互和 Agentic 决策场景与我们的轨迹构造直接相关

#### 2.2.4 ToolBench

| 属性 | 详情 |
|------|------|
| **来源** | 2023 |
| **规模** | 16,000+ 真实 API 工具 |
| **特点** | RapidAPI 真实 API 调用 |
| **HuggingFace** | `golaxy/toolbench` |

#### 2.2.5 MCPMark

| 属性 | 详情 |
|------|------|
| **来源** | 2025 |
| **规模** | 127 个高质量任务 |
| **特点** | MCP 专用评测，平均 16.2 轮执行、17.4 次工具调用 |
| **论文** | MCPMark: Evaluating MCP Servers with Complex Agentic Tasks |

### 2.3 深度搜索/长链推理类（高难度轨迹）

#### 2.3.1 DeepSearchQA

| 属性 | 详情 |
|------|------|
| **来源** | Google DeepMind，2025 |
| **规模** | 900 个任务，17 个领域 |
| **特点** | 需系统化搜索+去重+停止判断，因果链式任务 |
| **Kaggle** | https://www.kaggle.com/benchmarks/google/dsqa/leaderboard |

**为什么适合：**
- 测试三个关键能力：信息系统化整理、去重和实体消解、开放搜索中的停止判断
- 揭示了 Agent 的两种失效模式：过早停止（欠检索）和过度投网（低置信度答案堆砌）
- 适合构造高难度长链搜索轨迹

#### 2.3.2 GAIA

| 属性 | 详情 |
|------|------|
| **来源** | Meta AI，2023 |
| **规模** | 466 个任务（3 个难度级别） |
| **特点** | 问题对人类简单但对 AI 困难，需多工具协同 |
| **HuggingFace** | `gaia-benchmark/GAIA` |

### 2.4 数据集推荐优先级

```
第一优先：HotpotQA + NaturalQuestions
  理由：免费、规模大、与搜索 MCP 高度匹配、有标准答案

第二优先：Toucan-1.5M + TRAJECT-Bench
  理由：轨迹格式直接参考、评测维度参考

第三优先：2WikiMultiHopQA + MuSiQue
  理由：多跳推理高难度轨迹补充

第四优先：DeepSearchQA + GAIA
  理由：极长链搜索轨迹，少量但高价值
```

### 2.5 数据集快速获取代码

```python
from datasets import load_dataset

# HotpotQA（推荐 fullwiki 配置）
hotpot = load_dataset("hotpot_qa", "fullwiki")

# NaturalQuestions
nq = load_dataset("natural_questions")

# TriviaQA
trivia = load_dataset("trivia_qa", "rc")

# 2WikiMultiHopQA
wikimh = load_dataset("2wikimultihop_qa")

# Toucan-1.5M（轨迹参考）
toucan = load_dataset("Agent-Ark/Toucan-1.5M")

# TRAJECT-Bench（评测参考）
traject = load_dataset("bigboss24/TRAJECT-Bench")
```

---

## 3. 魔搭平台适合构造轨迹的 MCP 工具

### 3.1 已验证的 Hosted MCP 服务

以下 MCP 服务均可在魔搭平台上获取 Hosted SSE 链接，直接用于轨迹采集。

#### 3.1.1 搜索类（构造搜索轨迹的核心工具）

| MCP 服务 | 开发者 | 工具数 | 主要功能 | 热度 | 是否需要 API Key |
|----------|--------|--------|---------|------|-----------------|
| **Jina-AI-MCP-Tools** | @PsychArch | 2 | jina_search（网页搜索）+ jina_reader（网页读取） | 高 | 可选 |
| **Fetch** | @modelcontextprotocol | 1 | 网页抓取，HTML→Markdown | 520.5k | 否 |
| **必应搜索中文** | @slcatwujian | 2 | 中文网页搜索 + 搜索结果页面获取 | 183.2k | 否 |
| **Zhipu-Web-Search** | ZhipuAI | 多个 | 网页/图片/视频/新闻/购物/学术搜索 | 高 | 是（智谱 API Key） |
| **Tavily 智搜** | @tavily-ai | 2 | 实时网页搜索 + 网页提取 | 高 | 是（Tavily API Key） |

**轨迹构造价值：**
- Jina + Fetch：当前已接入，可立即开始轨迹采集
- 必应搜索中文：中文搜索场景补充，免费
- 智谱联网搜索：中文搜索质量最佳，但需 API Key
- Tavily：国际搜索场景补充

#### 3.1.2 位置服务类（构造出行/本地生活轨迹）

| MCP 服务 | 开发者 | 工具数 | 主要功能 | 热度 | 是否需要 API Key |
|----------|--------|--------|---------|------|-----------------|
| **高德地图** | @amap | 多个 | 地理编码、天气、步行/骑行/驾车路线、POI 搜索 | 341.0k | 是（高德 API Key） |

**可构造轨迹类型：**
```
"从北京天安门到故宫怎么走？" → 地理编码 → 路线规划 → 返回结果
"杭州今天天气怎么样？" → 天气查询 → 返回结果
"附近有什么好吃的？" → POI 搜索 → 返回结果
```

#### 3.1.3 企业信息类（构造企业查询轨迹）

| MCP 服务 | 开发者 | 工具数 | 主要功能 | 热度 | 是否需要 API Key |
|----------|--------|--------|---------|------|-----------------|
| **天眼查** | @TianYanCha | 多个 | 企业工商、股权穿透、风险诉讼、招投标查询 | 2.2k | 是（天眼查 Token） |

**可构造轨迹类型：**
```
"阿里巴巴的法定代表人是谁？" → 企业查询 → 返回结果
"这家公司有法律风险吗？" → 风险诉讼查询 → 综合分析
```

#### 3.1.4 学术类（构造学术搜索轨迹）

| MCP 服务 | 开发者 | 工具数 | 主要功能 | 热度 | 是否需要 API Key |
|----------|--------|--------|---------|------|-----------------|
| **ArXiv MCP** | @blazickjp | 2 | 论文搜索 + 论文内容访问 | 中 | 否 |
| **Academic Search** | @afrise | 多个 | 多源论文检索、主题/日期过滤 | 中 | 否 |

**可构造轨迹类型：**
```
"检索2024年关于 RAG 的代表性论文" → 学术搜索 → 获取摘要
"对比两篇论文的方法" → 论文读取 → 对比分析
```

#### 3.1.5 开发者工具类（构造编程辅助轨迹）

| MCP 服务 | 开发者 | 工具数 | 主要功能 | 热度 | 是否需要 API Key |
|----------|--------|--------|---------|------|-----------------|
| **Context7** | @upstash | 多个 | 最新库文档和代码示例检索 | 中 | 否 |
| **XSCT 模型选型** | @itshen | 多个 | 大模型选型推荐 | 15.6k | 否 |
| **Supabase** | @supabase-community | 多个 | 数据库操作 | 中 | 是 |

#### 3.1.6 出行类（构造出行规划轨迹）

| MCP 服务 | 开发者 | 工具数 | 主要功能 | 热度 | 是否需要 API Key |
|----------|--------|--------|---------|------|-----------------|
| **12306 车票查询** | @Joooook | 1 | 火车票搜索 | 中 | 否 |

#### 3.1.7 多模态生成类（构造内容生成轨迹）

| MCP 服务 | 开发者 | 工具数 | 主要功能 | 热度 | 是否需要 API Key |
|----------|--------|--------|---------|------|-----------------|
| **MiniMax MCP** | @MiniMax-AI | 多个 | 语音生成/克隆、图片/视频生成 | 高 | 是（MiniMax API Key） |

#### 3.1.8 浏览器自动化类（构造动态网页交互轨迹）

| MCP 服务 | 开发者 | 工具数 | 主要功能 | 热度 | 是否需要 API Key |
|----------|--------|--------|---------|------|-----------------|
| **Playwright** | @Automata-Labs-team | 多个 | 网页导航、点击、表单填写、截图、JS 执行 | 高 | 否 |

### 3.2 MCP 工具按轨迹价值排序

| 优先级 | MCP 工具 | 轨迹类型 | 接入难度 |
|--------|---------|---------|---------|
| ⭐⭐⭐ | Jina-AI-MCP-Tools | 搜索+读取 | 已接入 |
| ⭐⭐⭐ | Fetch | 网页读取 | 已接入 |
| ⭐⭐⭐ | 必应搜索中文 | 中文搜索 | 低（免费 Hosted） |
| ⭐⭐ | 高德地图 | 位置服务/出行规划 | 中（需 API Key） |
| ⭐⭐ | 天眼查 | 企业信息查询 | 中（需 Token） |
| ⭐⭐ | ArXiv MCP | 学术搜索 | 低（免费 Hosted） |
| ⭐ | 12306 | 车票查询 | 低（免费 Hosted） |
| ⭐ | Playwright | 动态网页交互 | 中（需部署） |
| ⭐ | MiniMax | 多模态生成 | 中（需 API Key） |
| ⭐ | Context7 | 技术文档搜索 | 低（免费 Hosted） |

---

## 4. Judge 模型微调数据构造方法论

### 4.1 业界最新进展

#### 4.1.1 Plan-RewardBench（南京大学 + 阿里高德，2026）

**论文**：*Aligning Agents via Planning: A Benchmark for Trajectory-Level Reward Modeling*（arXiv:2604.08178）

**核心贡献：**
- 提出轨迹级偏好基准，覆盖四大任务家族
- 设计可复用的多源偏好数据构建流程
- 揭示现有奖励模型在长时序轨迹下的性能退化规律

**四大场景家族：**

| 场景 | 描述 | Judge 评判维度 |
|------|------|---------------|
| **安全拒绝** | Agent 应拒绝不安全请求 | 是否正确拒绝、拒绝理由是否合理 |
| **工具无关/不可用** | 查询不需要工具或工具不可用 | 是否正确判断不调用工具、是否合理降级 |
| **复杂规划** | 多步工具调用规划 | 工具选择正确性、参数正确性、执行顺序合理性 |
| **鲁棒错误恢复** | 工具执行失败后的恢复策略 | 是否合理重试/改写/降级 |

**数据构造流程：**
```
1. 种子数据：基于 Toucan 项目的真实 MCP 工具注册信息
2. 轨迹生成：使用 Qwen-Agent、OpenAIAgent 多模型多参数推演
3. 高难度负样本构建：
   a. 规则扰动：注入约束丢失、参数错误、盲目重试
   b. 最小编辑扰动：对高分轨迹小幅修改，引入特定缺陷
4. 标注流程：多 LLM 评审团 1-5 分打分 → 元评审处理分歧 → 人工分层审核 → 成对组装
5. 偏好标注：控制长度、格式偏差，隔离语义失效问题
```

**关键发现：**
- 所有评测器（判别式、生成式、LLM-as-Judge）在长轨迹上性能急剧下降
- 典型失效模式：
  - 长度敏感：偏好更长的轨迹，即使质量更低
  - 安全优先错位：过度拒绝安全请求
  - 过时约束盲区：忽略已变化的约束条件
  - 努力偏见：偏好更多工具调用的轨迹
  - 表面恢复：看似恢复实则偏离

#### 4.1.2 Similar（蚂蚁集团，ICML 2025）

**论文**：*Boosting Virtual Agent Learning and Reasoning: A Step-Wise, Multi-Dimensional, and Generalist Reward Model*

**核心贡献：**
- 定义五个维度的 Agent 动作评估
- 设计 MCTS-P 算法自动收集和标注步骤级数据
- 提出 Triple-M 训练策略

**五维评估体系：**

| 维度 | 含义 | 判断标准 |
|------|------|---------|
| **Helpfulness** | 动作是否有助完成任务 | 是否向目标推进 |
| **Likelihood** | 动作成功概率 | 是否合理可行 |
| **Efficiency** | 是否节省时间 | 是否为最短路径 |
| **Relevance** | 是否与目标相关 | 是否切题 |
| **Coherence** | 是否逻辑连贯 | 与前序动作是否一致 |

**训练效果：** 步骤级多维评估在训练中提升任务成功率 29.9%，推理时提升 25.9%。

#### 4.1.3 STeCa（香港理工大学，ACL 2025 Findings）

**论文**：*STeCa: Step-level Trajectory Calibration for LLM Agent Learning*

**核心思路：**
- 在轨迹探索过程中，通过步骤级奖励比较识别次优动作
- 使用 LLM 驱动的反思构建校准轨迹
- 将校准轨迹与成功轨迹合并进行强化训练

**对 Judge 数据构造的启示：**
- 不仅要标注成功/失败轨迹，还需要标注**部分正确但可改进**的轨迹
- 步骤级的质量标注比整体标注更有价值
- 校准轨迹（从错误步骤修正到正确路径）是重要的 Judge 训练数据

#### 4.1.4 Trajectory2Task（Northeastern University + Amazon，ACL 2026）

**论文**：*Trajectory2Task: Training Robust Tool-Calling Agents with Synthesized Yet Verifiable Data*

**核心思路：**
- 先进行多轮探索产出有效工具调用轨迹
- 再将轨迹转换为用户任务，加入可控的意图变化
- 支持闭环评估和训练

**三种真实用户场景：**
1. **模糊意图**：用户请求缺少关键细节
2. **变化意图**：用户在交互中修改请求
3. **不可行意图**：请求因策略约束无法执行

**对 Judge 数据构造的启示：**
- 应包含意图模糊/变化/不可行的轨迹，而非仅理想化场景
- 轨迹应支持闭环验证：可重新执行并验证结果

### 4.2 Judge 标注维度设计

综合上述研究，推荐以下 Judge 标注维度：

#### 4.2.1 轨迹级标注

| 维度 | 评分范围 | 描述 |
|------|---------|------|
| overall_quality | 1-5 | 轨迹整体质量 |
| answer_correctness | 1-5 | 最终答案正确性 |
| source_citation | 1-5 | 来源引用准确性 |
| hallucination | 0/1 | 是否存在幻觉 |
| tool_usage_efficiency | 1-5 | 工具使用效率（是否冗余调用） |

#### 4.2.2 步骤级标注

| 维度 | 评分范围 | 描述 |
|------|---------|------|
| tool_selection | 1-5 | 工具选择正确性 |
| parameter_correctness | 1-5 | 参数正确性 |
| execution_order | 1-5 | 执行顺序合理性 |
| recovery_quality | 1-5 | 错误恢复质量 |

#### 4.2.3 特殊场景标注

| 场景 | 标注内容 |
|------|---------|
| 安全拒绝 | 是否应拒绝、拒绝理由 |
| 工具无关 | 是否应不调用工具 |
| 工具不可用 | 降级策略是否合理 |
| 搜索修正 | query 改写是否合理 |
| 信息冲突 | 多源冲突是否正确处理 |

### 4.3 正负样本对构造方法

#### 方法1：自然推演法

```
同一 query → 多模型（Qwen-72B、DeepSeek-V2、GPT-4o）各自推演
→ 自然产生成功轨迹和失败轨迹
→ 配对形成偏好数据
```

#### 方法2：规则扰动法

```
对成功轨迹注入可控缺陷：
- 约束丢失：忽略 query 中的时间/数量约束
- 参数错误：工具参数值错误
- 盲目重试：失败后无改写直接重试
- 工具误选：使用了不合适的工具
→ 形成高质量负样本
```

#### 方法3：最小编辑扰动法

```
对高分轨迹小幅修改：
- 将正确的搜索 query 改为次优 query
- 将正确的 URL 选择改为次优 URL
- 删除一个关键的验证步骤
→ 保留风格一致性，仅引入语义缺陷
```

### 4.4 推荐的 Judge 数据格式

```json
{
  "trajectory_id": "traj_001",
  "task_type": "search_and_read",
  "difficulty": "medium",
  "query_source": "hotpotqa",
  "query_id": "xxx",
  "query": "What government position was held by the woman who portrayed Corliss Archer?",
  "ground_truth": "Chief of Protocol",
  "trajectory": [
    {
      "step": 1,
      "type": "tool_call",
      "tool": "jina_search",
      "arguments": {"query": "Corliss Archer Hit Parade of 1941 actress"},
      "result": "...",
      "step_labels": {
        "tool_selection": 5,
        "parameter_correctness": 5,
        "execution_order": 5
      }
    },
    {
      "step": 2,
      "type": "tool_call",
      "tool": "jina_reader",
      "arguments": {"url": "https://..."},
      "result": "...",
      "step_labels": {
        "tool_selection": 5,
        "parameter_correctness": 5,
        "execution_order": 5
      }
    }
  ],
  "trajectory_labels": {
    "overall_quality": 5,
    "answer_correctness": 5,
    "source_citation": 4,
    "hallucination": false,
    "tool_usage_efficiency": 4
  },
  "pair": {
    "positive_id": "traj_001",
    "negative_id": "traj_001_perturbed",
    "preference": "positive",
    "reason": "正面轨迹正确选择了搜索关键词，负面轨迹使用了过于宽泛的搜索词"
  }
}
```

---

## 5. 推荐的轨迹构造方案

### 5.1 第一阶段：搜索 Agent 基础轨迹（立即可做）

**工具组合：** jina_search + jina_reader + fetch

**数据集：** HotpotQA（fullwiki）+ NaturalQuestions

**轨迹类型及比例：**

| 轨迹类型 | 比例 | 数据集来源 | 轮次 |
|---------|------|-----------|------|
| 单步搜索 | 15% | NaturalQuestions | 2-3 轮 |
| 搜索+读取 | 35% | NaturalQuestions + HotpotQA(easy) | 3-5 轮 |
| 多步搜索+交叉验证 | 30% | HotpotQA(medium/hard) | 5-8 轮 |
| 搜索修正 | 10% | HotpotQA(hard) | 5-10 轮 |
| 工具降级 | 10% | 自行构造 | 3-6 轮 |

**批量采集脚本流程：**

```python
# 伪代码
for query in sampled_queries:
    trajectory = []
    
    # Step 1: 搜索
    search_result = jina_search(query)
    trajectory.append(search_step)
    
    # Step 2: 读取（选择 top-k URL）
    for url in top_k_urls:
        content = jina_reader(url) or fetch(url)
        trajectory.append(read_step)
    
    # Step 3: 综合回答
    answer = model.generate(trajectory_context)
    trajectory.append(answer_step)
    
    # Step 4: 标注
    labels = judge_annotate(trajectory, ground_truth)
    save_trajectory(trajectory, labels)
```

### 5.2 第二阶段：多源搜索轨迹（扩展）

**工具组合：** + 必应搜索中文 + Zhipu-Web-Search

**新增轨迹类型：**
- 中文搜索轨迹
- 多搜索引擎交叉验证
- 搜索引擎降级（智谱失败→必应→Jina）

### 5.3 第三阶段：领域垂直轨迹（高价值）

**工具组合：** + 高德地图 + 天眼查 + ArXiv + 12306

**新增轨迹类型：**
- 出行规划：多工具协同（搜索+地图+车票）
- 企业查询：结构化信息提取
- 学术研究：论文检索+对比分析
- 多意图路由：根据问题自动选择工具类别

### 5.4 第四阶段：复杂规划与错误恢复轨迹（Judge 关键数据）

**工具组合：** 全部工具

**新增轨迹类型：**
- 复杂规划：3+ 工具、5+ 步骤
- 错误恢复：工具调用失败后的合理恢复
- 安全拒绝：对有害请求的正确拒绝
- 工具无关：判断不需要工具的场景

### 5.5 推荐的轨迹数量目标

| 阶段 | 轨迹数量 | 正负对数量 | 预计周期 |
|------|---------|-----------|---------|
| 第一阶段 | 5,000-10,000 | 3,000-6,000 | 1-2 周 |
| 第二阶段 | 3,000-5,000 | 2,000-3,000 | 1 周 |
| 第三阶段 | 2,000-3,000 | 1,000-2,000 | 1-2 周 |
| 第四阶段 | 1,000-2,000 | 800-1,500 | 1 周 |
| **合计** | **11,000-20,000** | **6,800-12,500** | **4-7 周** |

---

## 6. 参考文献

### 数据集

1. HotpotQA: Yang et al., "HotpotQA: A Dataset for Diverse, Explainable Multi-hop Question Answering", EMNLP 2018. https://hotpotqa.github.io/
2. NaturalQuestions: Kwiatkowski et al., "Natural Questions: A Benchmark for Question Answering Research", TACL 2019.
3. TriviaQA: Joshi et al., "TriviaQA: A Large Scale Distantly Supervised Challenge Dataset for Reading Comprehension", ACL 2017. https://nlp.cs.washington.edu/triviaqa/
4. 2WikiMultiHopQA: Ho et al., "Constructing A Multi-hop QA Dataset for Comprehensive Evaluation of Reasoning Steps", COLING 2020.
5. MuSiQue: Trivedi et al., "MuSiQue: Multihop Questions via Single Hop Question Composition", TACL 2022.

### Agent 轨迹与评测

6. Toucan-1.5M: Panda et al., "TOUCAN: Synthesizing 1.5M Tool-Agentic Data from Real-World MCP Environments", 2025. https://huggingface.co/datasets/Agent-Ark/Toucan-1.5M
7. TRAJECT-Bench: He et al., "TRAJECT-Bench: A Trajectory-Aware Benchmark for Evaluating Agentic Tool Use", 2025. https://github.com/PengfeiHePower/TRAJECT-Bench
8. BFCL v4: Patil et al., "Berkeley Function Calling Leaderboard", ICML 2025.
9. MCPMark: "MCPMark: Evaluating MCP Servers with Complex Agentic Tasks", 2025.
10. DeepSearchQA: Gupta et al., "DeepSearchQA: Bridging the Comprehensiveness Gap for Deep Research Agents", Google DeepMind 2025.
11. GAIA: Mialon et al., "GAIA: A Benchmark for General AI Assistants", NeurIPS 2023.

### Judge/Reward 模型

12. Plan-RewardBench: Wang et al., "Aligning Agents via Planning: A Benchmark for Trajectory-Level Reward Modeling", 2026. arXiv:2604.08178
13. Similar: Miao et al., "Boosting Virtual Agent Learning and Reasoning: A Step-Wise, Multi-Dimensional, and Generalist Reward Model with Benchmark", ICML 2025. https://github.com/antgroup/Similar
14. STeCa: Wang et al., "STeCa: Step-level Trajectory Calibration for LLM Agent Learning", ACL 2025 Findings.
15. Trajectory2Task: Wang et al., "Trajectory2Task: Training Robust Tool-Calling Agents with Synthesized Yet Verifiable Data for Complex User Intents", ACL 2026.
16. Search-P1: Xia et al., "Search-P1: Path-Centric Reward Shaping for Stable and Efficient Agentic RAG Training", 2026.

### MCP 生态

17. ModelScope MCP 广场: https://www.modelscope.cn/mcp
18. Model Context Protocol 官方: https://modelcontextprotocol.io/
19. PopularAiTools MCP 目录: https://popularaitools.ai/skills?type=mcp (6,900+ 已验证服务器)

### 项目内部参考

20. buildSearch.md: 项目搜索 Agent 架构设计文档
21. mcpTest_Moda.py: MCP 工具测试脚本
22. record: 已有轨迹运行记录
