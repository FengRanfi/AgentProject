# Hugging Face 搜索轨迹数据集调研报告

> 调研日期：2026-07-05  
> 调研目标：核查 BrowseComp / BrowseComp-ZH / LiveBrowseComp、AssistantBench、WideSearch / DeepWideSearch、OpenResearcher、OpenSeeker / OpenSeeker-v2、WebLINX 是否在 Hugging Face 官网存在可用数据集，并判断其在 Agent 轨迹构造中的用途。

---

## 1. 结论摘要

本次调研的数据集可分为两类：

1. **自产轨迹任务源**：只使用数据集中的 task/question/query/problem，结合项目现有搜索 Agent 和 MCP 工具链自行生成搜索轨迹。
2. **现有轨迹源**：数据集本身已经包含 messages、trajectory、tool calls、action history 或浏览器操作序列，可直接用于轨迹混合、格式转换或 Judge 数据构造。

| 类别 | 数据集 | Hugging Face 状态 | 建议用途 |
|------|--------|-------------------|----------|
| 自产 task | BrowseComp | 有：`smolagents/browse_comp` | 抽取 `problem` 生成深搜索轨迹 |
| 自产 task | BrowseComp-ZH | 有：`PALIN2018/BrowseComp-ZH` | 抽取中文 `Question` 生成中文搜索轨迹 |
| 自产 task | LiveBrowseComp | 有：`Forival/LiveBrowseComp` | 抽取动态/时效类 `problem` 生成活网页轨迹 |
| 自产 task | AssistantBench | 有：`AssistantBench/AssistantBench` | 抽取真实耗时任务 `task` 生成复杂 Web Agent 轨迹 |
| 自产 task | WideSearch | 有：`ByteDance-Seed/WideSearch` | 抽取宽搜索 `query` 生成枚举/表格类轨迹 |
| 自产 task | DeepWideSearch | 有：`ATH-MaaS/DeepWideSearch` | 抽取宽+深搜索任务生成复杂信息收集轨迹 |
| 现有轨迹 | OpenResearcher | 有：`OpenResearcher/OpenResearcher-Dataset` | 直接使用 `messages` 中的工具调用轨迹 |
| 现有轨迹 | OpenSeeker | 有：`PolarSeeker/OpenSeeker-v1-Data` | 直接使用 `trajectory` 字段 |
| 现有轨迹 | OpenSeeker-v2 | 未查到独立 HF dataset | 暂不作为独立数据源计入 |
| 现有轨迹 | WebLINX | 有：`McGill-NLP/WebLINX` / `McGill-NLP/WebLINX-full` | 使用网页导航 action/action_history 轨迹 |

---

## 2. 自产轨迹 Task 源

### 2.1 BrowseComp

| 属性 | 内容 |
|------|------|
| Hugging Face | https://huggingface.co/datasets/smolagents/browse_comp |
| 数据集 ID | `smolagents/browse_comp` |
| 规模 | 约 1.27k rows |
| Split | `test` |
| 关键字段 | `problem`, `answer`, `problem_topic` |
| License | Apache-2.0 |
| 推荐用途 | 抽取 `problem` 作为用户问题，使用搜索 Agent 自行生成轨迹 |

BrowseComp 是典型的深搜索/难检索 QA 任务，适合测试 Agent 在多跳检索、网页阅读、证据整合上的能力。建议只将其作为 task 源，不直接使用答案生成训练轨迹；答案可用于自动校验或 Judge 标注。

### 2.2 BrowseComp-ZH

| 属性 | 内容 |
|------|------|
| Hugging Face | https://huggingface.co/datasets/PALIN2018/BrowseComp-ZH |
| 数据集 ID | `PALIN2018/BrowseComp-ZH` |
| 规模 | 289 rows |
| Split | `test` |
| 关键字段 | `Topic`, `Question`, `Answer` |
| License | Apache-2.0 |
| 推荐用途 | 中文搜索 Agent 轨迹生产 |

BrowseComp-ZH 面向中文信息生态，任务覆盖中文网页、中文实体和中文检索表达。对当前项目有两类价值：

- 构造中文搜索轨迹，补齐英文数据偏置。
- 评估 Agent 在中文 query rewrite、中文网页阅读、中文答案组织上的能力。

### 2.3 LiveBrowseComp

| 属性 | 内容 |
|------|------|
| Hugging Face | https://huggingface.co/datasets/Forival/LiveBrowseComp |
| 数据集 ID | `Forival/LiveBrowseComp` |
| 规模 | 335 rows |
| Split | `train` |
| 关键字段 | `idx`, `problem`, `answer` |
| 推荐用途 | 生成依赖实时网页/近期网页状态的搜索轨迹 |

LiveBrowseComp 更适合构造“活网页”类轨迹。使用时需要注意答案可能随时间变化，建议在生成轨迹时记录：

- 生成日期。
- 搜索 query。
- 访问 URL。
- 页面证据摘要。
- 最终答案与引用来源。

### 2.4 AssistantBench

| 属性 | 内容 |
|------|------|
| Hugging Face | https://huggingface.co/datasets/AssistantBench/AssistantBench |
| 数据集 ID | `AssistantBench/AssistantBench` |
| 规模 | 214 rows |
| Split | `validation`, `test` |
| 关键字段 | `task`, `answer`, `gold_url`, `explanation`, `difficulty` |
| License | Apache-2.0 |
| 推荐用途 | 复杂、真实、耗时 Web Agent 任务轨迹生产 |

AssistantBench 的任务更接近真实用户委托，不只是短答案 QA。建议使用 `task` 作为 Agent 输入，`gold_url` 和 `answer` 作为验证依据。适合产出长链路轨迹，例如：

- 多轮搜索。
- 多页面阅读。
- 对比和筛选。
- 最终结构化回答。

### 2.5 WideSearch

| 属性 | 内容 |
|------|------|
| Hugging Face | https://huggingface.co/datasets/ByteDance-Seed/WideSearch |
| 数据集 ID | `ByteDance-Seed/WideSearch` |
| 规模 | 200 rows |
| Split | `full` |
| 关键字段 | `instance_id`, `query`, `evaluation`, `language` |
| License | Other，使用前需查看数据卡说明 |
| 推荐用途 | 枚举型、宽覆盖信息收集轨迹生产 |

WideSearch 与 BrowseComp 的差异在于：BrowseComp 偏“找一个难找事实”，WideSearch 偏“找全一批分散但较易找到的信息”。适合训练 Agent 的：

- query 分解。
- 批量搜索。
- 覆盖率控制。
- 表格填充。
- 去重与缺失项检查。

### 2.6 DeepWideSearch

| 属性 | 内容 |
|------|------|
| Hugging Face | https://huggingface.co/datasets/ATH-MaaS/DeepWideSearch |
| 数据集 ID | `ATH-MaaS/DeepWideSearch` |
| 任务类型 | Table QA, Text Retrieval |
| License | Apache-2.0 |
| 推荐用途 | 宽搜索 + 深推理的复杂轨迹生产 |

DeepWideSearch 在 HF 上存在，但页面 viewer 可能存在列类型不一致或 cast error，建议通过文件列表或 `datasets` 脚本方式读取，而不是完全依赖在线 viewer。

它适合补足 WideSearch 的深度不足：任务既要求枚举多个对象，也要求对每个对象继续深挖属性、证据或多跳关系。

---

## 3. 现有轨迹数据源

### 3.1 OpenResearcher

| 属性 | 内容 |
|------|------|
| Hugging Face | https://huggingface.co/datasets/OpenResearcher/OpenResearcher-Dataset |
| 数据集 ID | `OpenResearcher/OpenResearcher-Dataset` |
| 规模 | 97,630 rows，约 7.46GB |
| 关键字段 | `question`, `answer`, `messages` |
| 推荐用途 | 直接作为 deep research / search Agent 轨迹源 |

OpenResearcher 的核心价值在于 `messages` 字段已经包含多轮交互、工具调用、观察结果和最终回答。适合直接转换成项目内部统一轨迹格式。

建议处理流程：

1. 解析 `messages`。
2. 提取 user question、assistant reasoning、tool call、tool observation、final answer。
3. 映射工具名到项目当前工具体系，例如 `search`、`read`、`fetch`、`jina_search`、`jina_reader`。
4. 按答案质量、工具调用次数、是否有异常 observation 进行过滤。

### 3.2 OpenSeeker / OpenSeeker-v1

| 属性 | 内容 |
|------|------|
| Hugging Face | https://huggingface.co/datasets/PolarSeeker/OpenSeeker-v1-Data |
| 数据集 ID | `PolarSeeker/OpenSeeker-v1-Data` |
| 规模 | 11,677 rows，约 3.22GB |
| 关键字段 | `question`, `answer`, `number of tool calls`, `trajectory`, `trajectory correctness` |
| License | MIT |
| 推荐用途 | 高质量搜索 Agent 轨迹源 |

OpenSeeker-v1-Data 是本次调研中最直接匹配“搜索轨迹”的现成数据集之一。其 `trajectory` 字段可直接用于 SFT 轨迹转换，`trajectory correctness` 可用于过滤低质量轨迹。

建议优先使用：

- `trajectory correctness = true` 或等价高质量标记的样本。
- 工具调用次数适中的样本，避免过短无训练价值或过长噪声过多。
- 与项目工具链兼容的 search/read 轨迹。

### 3.3 OpenSeeker-v2

| 属性 | 内容 |
|------|------|
| Hugging Face dataset API 查询 | 未查到 `OpenSeeker-v2` 独立数据集 |
| 当前结论 | 暂不作为独立 HF 数据源 |
| 替代方案 | 使用 `PolarSeeker/OpenSeeker-v1-Data`，后续再跟踪作者发布 |

本次在 Hugging Face datasets API 中按 `OpenSeeker-v2` 检索，返回为空。当前可确认的是 OpenSeeker-v1 数据集存在，v2 不应在数据清单中写成“已有可下载 HF dataset”，除非后续找到明确页面。

### 3.4 WebLINX

| 属性 | 内容 |
|------|------|
| Hugging Face | https://huggingface.co/datasets/McGill-NLP/WebLINX |
| Full 版本 | https://huggingface.co/datasets/McGill-NLP/WebLINX-full |
| BrowserGym 版本 | https://huggingface.co/datasets/McGill-NLP/weblinx-browsergym |
| 关键字段 | `action`, `action_history`, `utterances`, `candidates`, `clean_html`, `viewport` |
| License | CC-BY-NC-SA-4.0 |
| 推荐用途 | 浏览器导航、网页交互、元素选择类轨迹 |

WebLINX 与 OpenResearcher/OpenSeeker 的差异较大：它不是纯搜索问答轨迹，而是真实网站导航和多轮对话轨迹。适合补齐 Agent 的浏览器动作能力：

- 点击。
- 文本输入。
- 页面元素定位。
- 多轮用户意图跟踪。
- 页面状态理解。

如果当前项目主要是 `search -> read -> answer`，WebLINX 需要额外转换；如果后续引入浏览器环境或 BrowserGym，WebLINX 的价值会更高。

---

## 4. 推荐组合方案

### 4.1 自产轨迹任务池

建议将以下数据集统一抽象为 task pool：

| 来源 | 输入字段 | 答案字段 | 轨迹生成类型 |
|------|----------|----------|--------------|
| BrowseComp | `problem` | `answer` | 深搜索 QA |
| BrowseComp-ZH | `Question` | `Answer` | 中文深搜索 QA |
| LiveBrowseComp | `problem` | `answer` | 时效/活网页 QA |
| AssistantBench | `task` | `answer` | 真实复杂 Web 任务 |
| WideSearch | `query` | `evaluation` | 宽搜索/枚举/表格任务 |
| DeepWideSearch | 以数据文件字段为准 | 以数据文件字段为准 | 宽+深信息收集任务 |

统一 task schema 建议：

```json
{
  "source": "BrowseComp",
  "task_id": "source-specific-id",
  "language": "en",
  "task": "user-facing task text",
  "gold_answer": "optional answer",
  "gold_evidence": [],
  "task_type": "deep_search_qa",
  "metadata": {}
}
```

### 4.2 现有轨迹混合池

建议优先级如下：

1. `PolarSeeker/OpenSeeker-v1-Data`：最贴近搜索 Agent 轨迹。
2. `OpenResearcher/OpenResearcher-Dataset`：规模大，适合作为 deep research 主体数据。
3. `McGill-NLP/WebLINX` / `McGill-NLP/WebLINX-full`：用于补浏览器导航和网页动作能力。

统一 trajectory schema 建议：

```json
{
  "source": "OpenSeeker",
  "task": "question or user instruction",
  "answer": "final answer",
  "messages": [],
  "tool_calls": [],
  "observations": [],
  "quality": {
    "correct": true,
    "num_tool_calls": 6
  },
  "metadata": {}
}
```

---

## 5. 风险与注意事项

### 5.1 License 风险

不同数据集 License 不一致：

- Apache-2.0：BrowseComp-ZH、AssistantBench、DeepWideSearch 等较友好。
- MIT：OpenSeeker-v1-Data。
- CC-BY-NC-SA-4.0：WebLINX，包含非商业限制。
- WideSearch 标记为 `other`，使用前必须查看数据卡具体条款。

如果目标是商业化训练或发布模型，需要单独做 License 白名单。

### 5.2 数据泄漏风险

BrowseComp、AssistantBench、WideSearch、DeepWideSearch 都是评测基准或评测相关数据。若生成训练轨迹后再用同一 benchmark 评测，会产生污染。

建议：

- 将 benchmark task pool 与训练集严格分开。
- 记录每条轨迹来源。
- 对训练集和评测集做 source-level blacklist。

### 5.3 活网页漂移

LiveBrowseComp 和 Web 任务依赖实时页面，答案和证据可能变化。生成轨迹时必须保存 URL、页面摘要、访问时间，必要时保存网页快照或可复现证据。

### 5.4 格式兼容

OpenResearcher、OpenSeeker、WebLINX 的轨迹格式不同，不能直接混合训练。建议先转换成统一消息格式，再做质量过滤。

---

## 6. 最终建议

当前项目如果目标是“生产搜索 Agent 轨迹 + 构造 Judge 微调数据”，建议采用以下路线：

1. **第一批直接下载现有轨迹**：`OpenSeeker-v1-Data`、`OpenResearcher-Dataset`。
2. **第二批自产轨迹**：从 `AssistantBench`、`WideSearch`、`BrowseComp/BrowseComp-ZH` 抽 task，使用现有 MCP 搜索工具生成轨迹。
3. **第三批扩展浏览器动作轨迹**：引入 `WebLINX`，但仅在项目需要浏览器导航能力时使用。
4. **暂缓 OpenSeeker-v2**：目前未查到独立 HF dataset，不写入可下载清单。
5. **DeepWideSearch 单独处理**：HF 数据集存在，但在线 viewer 可能异常，读取时应以原始文件或 `datasets` 加载结果为准。

---

## 7. 只选 3+3 数据集的推荐方案

如果自采 task 和现成轨迹都只保留 3 个数据集，建议优先选择下面这个组合。选择标准是：覆盖任务类型尽量互补、数据读取风险可控、与搜索 Agent/Judge 数据构造的匹配度高。

### 7.1 自采 task 推荐 Top 3

| 优先级 | 数据集 | 数据集 ID | 推荐理由 | 主要风险 |
|--------|--------|-----------|----------|----------|
| 1 | AssistantBench | `AssistantBench/AssistantBench` | 最接近真实用户委托，任务复杂、耗时，适合生成高价值长轨迹 | 样本量小，只有 214 条 |
| 2 | WideSearch | `ByteDance-Seed/WideSearch` | 补齐宽搜索能力，适合训练枚举、覆盖率检查、表格填充和批量信息收集 | License 标记为 `other`，需单独核查 |
| 3 | BrowseComp-ZH | `PALIN2018/BrowseComp-ZH` | 中文深搜索 benchmark，可补齐中文搜索、中文网页阅读和中文答案组织能力 | 样本量小，只有 289 条 |

这三个数据集的组合覆盖三类关键能力：

- **AssistantBench**：真实复杂任务，适合生成“搜索 + 阅读 + 综合决策”的长链路轨迹。
- **WideSearch**：宽覆盖信息收集，适合生成“拆任务 + 多 query + 去重 + 表格化”的轨迹。
- **BrowseComp-ZH**：中文深搜索，适合生成中文场景下的困难检索和多跳推理轨迹。

如果项目第一阶段只做英文数据，可以将 `BrowseComp-ZH` 替换为 `smolagents/browse_comp`。如果项目更强调宽+深结合，可以在第二阶段加入 `ATH-MaaS/DeepWideSearch`，但不建议第一批就选它，因为 HF 在线 viewer 存在读取异常，需要额外处理原始文件格式。

### 7.2 现成轨迹推荐 Top 3

| 优先级 | 数据集 | 数据集 ID | 推荐理由 | 主要风险 |
|--------|--------|-----------|----------|----------|
| 1 | OpenSeeker-v1 | `PolarSeeker/OpenSeeker-v1-Data` | 最贴近搜索 Agent 轨迹，包含 `trajectory`、工具调用次数和正确性字段 | 需要做轨迹格式映射 |
| 2 | OpenResearcher | `OpenResearcher/OpenResearcher-Dataset` | 规模大，`messages` 中包含工具调用、观察和最终回答，适合做 deep research 主体数据 | 数据量大，清洗成本较高 |
| 3 | WebLINX | `McGill-NLP/WebLINX` 或 `McGill-NLP/WebLINX-full` | 补齐网页导航、点击、输入、元素选择等浏览器动作能力 | License 为 CC-BY-NC-SA-4.0，且格式与纯搜索轨迹差异大 |

这三个数据集分别承担不同角色：

- **OpenSeeker-v1**：作为搜索轨迹的高质量核心集，优先用于 SFT/Judge 正样本。
- **OpenResearcher**：作为规模型 deep research 轨迹来源，适合扩充覆盖面。
- **WebLINX**：作为浏览器动作轨迹补充，避免数据全部停留在 search/read/answer 模式。

如果当前项目暂时不做浏览器动作，只做文本搜索工具调用，可以将 `WebLINX` 暂缓，改为优先扩充 `OpenResearcher` 和 `OpenSeeker` 的高质量子集。但从长期 Agent 能力覆盖看，保留 WebLINX 更有价值。

### 7.3 不优先选择的数据集说明

| 数据集 | 不放入第一批 3 个的原因 | 后续使用建议 |
|--------|--------------------------|--------------|
| BrowseComp | 与 BrowseComp-ZH 能力类似，但缺少中文覆盖；若第一阶段只做英文，可替换 BrowseComp-ZH | 英文深搜索增强 |
| LiveBrowseComp | 活网页漂移明显，可复现性比静态 benchmark 弱 | 用于后续构造时效性任务 |
| DeepWideSearch | 任务价值高，但 HF viewer 存在异常，读取和清洗成本更高 | 第二阶段单独处理 |
| OpenSeeker-v2 | 暂未查到独立 HF dataset | 等作者发布明确数据集后再纳入 |

### 7.4 最小落地组合

第一批建议落地为：

```text
自采 task:
1. AssistantBench/AssistantBench
2. ByteDance-Seed/WideSearch
3. PALIN2018/BrowseComp-ZH

现成轨迹:
1. PolarSeeker/OpenSeeker-v1-Data
2. OpenResearcher/OpenResearcher-Dataset
3. McGill-NLP/WebLINX
```

推荐执行顺序：

1. 先下载并转换 `OpenSeeker-v1-Data`，快速得到一批最贴近项目目标的搜索轨迹。
2. 再处理 `OpenResearcher-Dataset`，按工具调用次数、回答完整性和异常 observation 做过滤。
3. 同步从 `AssistantBench`、`WideSearch`、`BrowseComp-ZH` 抽 task，使用现有 MCP 搜索工具自采轨迹。
4. 最后处理 `WebLINX`，仅抽取与当前工具体系能对齐的 action/action_history，或为后续浏览器 Agent 单独保留。

---

## 8. 参考链接

- BrowseComp: https://huggingface.co/datasets/smolagents/browse_comp
- BrowseComp-ZH: https://huggingface.co/datasets/PALIN2018/BrowseComp-ZH
- LiveBrowseComp: https://huggingface.co/datasets/Forival/LiveBrowseComp
- AssistantBench: https://huggingface.co/datasets/AssistantBench/AssistantBench
- WideSearch: https://huggingface.co/datasets/ByteDance-Seed/WideSearch
- DeepWideSearch: https://huggingface.co/datasets/ATH-MaaS/DeepWideSearch
- OpenResearcher-Dataset: https://huggingface.co/datasets/OpenResearcher/OpenResearcher-Dataset
- OpenSeeker-v1-Data: https://huggingface.co/datasets/PolarSeeker/OpenSeeker-v1-Data
- WebLINX: https://huggingface.co/datasets/McGill-NLP/WebLINX
- WebLINX-full: https://huggingface.co/datasets/McGill-NLP/WebLINX-full
- WebLINX BrowserGym: https://huggingface.co/datasets/McGill-NLP/weblinx-browsergym
