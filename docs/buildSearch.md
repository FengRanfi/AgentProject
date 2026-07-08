## 结论

通用搜索 Agent 不应把十几个 MCP 全部挂到一个 `AssistantAgent` 上。更合理的是：

```text
Router / Planner
├── 通用网页检索 Agent
├── 新闻时效 Agent
├── 学术检索 Agent
├── 技术文档 Agent
├── 本地生活 Agent
└── 浏览器兜底 Agent
```

其中网页读取、内容提取和引用整理属于共享能力，不必单独做成业务 Agent。

## 推荐分类与魔搭 MCP

| 类别         | 首选 MCP                                      | 备用或增强 MCP                                   |     优先级 |
| ---------- | ------------------------------------------- | ------------------------------------------- | ------: |
| 通用网页搜索     | `ZhipuAI/Zhipu-Web-Search`                  | `@tavily-ai/tavily-mcp`                     |      必须 |
| 网页正文读取     | `@modelcontextprotocol/fetch`               | `@PsychArch/Jina-AI-MCP-Tools`              |      必须 |
| 动态网页处理     | `@Automata-Labs-team/MCP-Server-Playwright` | Chrome DevTools MCP                         | 必须但按需调用 |
| 新闻与热点      | 智谱联网搜索                                      | `@wopal-cn/mcp-hotnews-server`、Brave Search |      推荐 |
| 学术论文       | `@afrise/academic-search-mcp-server`        | `@blazickjp/arxiv-mcp-server`               |      推荐 |
| 编程文档与仓库    | `@upstash/context7-mcp`                     | `@idosal/git-mcp`                           |      推荐 |
| 地图、本地生活、出行 | `@amap/amap-maps`                           | 百度地图 MCP                                    |    后续增加 |
| 多页面网站抓取    | Firecrawl MCP                               | Jina Reader                                 |    后续增加 |

---

## 1. 通用网页检索 Agent

### 首选：智谱联网搜索

建议将 `ZhipuAI/Zhipu-Web-Search` 作为中文和综合检索的主入口。

它在魔搭页面中覆盖网页、图片、视频、新闻、购物、学术和地图等多种搜索类型，适合作为通用 Agent 的默认搜索源。它需要智谱 BigModel API Key，平台提供一定免费额度。([ModelScope][1])

推荐工具组合：

```text
GeneralWebAgent
├── Zhipu Web Search
└── Fetch
```

典型任务：

```text
“什么是 AgentJudge？”
“最近有哪些 Agent 评估框架？”
“查找某家公司、产品或技术的信息”
“搜索一项政策或行业动态”
```

### 备用：Tavily

`@tavily-ai/tavily-mcp` 提供实时网页搜索和网页提取工具，更偏向 Agent 和研究场景。它适合作为：

* 智谱搜索结果不足时的备用搜索源；
* 国际英文资料搜索；
* 限定域名检索；
* 深度研究任务。

Tavily 需要单独的 API Key。([ModelScope][2])

不要让智谱和 Tavily 每次同时搜索。建议采用：

```text
先调用智谱
    ↓
结果不足、来源单一或英文资料缺失
    ↓
再调用 Tavily
```

### Brave 的定位

魔搭的 Brave Search MCP 支持网页、新闻、文章、本地搜索、分页和新鲜度控制。它适合对发布时间敏感的国际搜索，但与智谱、Tavily 重叠较大，第一版不必同时配置三者。([ModelScope][3])

推荐选择关系：

```text
国内和中文优先：智谱 + Tavily
国际和英文优先：Brave + Tavily
预算有限：智谱单搜索源
```

---

## 2. 网页正文读取能力

搜索结果只提供标题、URL 和摘要。通用 Agent 必须进一步读取网页正文，不能直接把搜索摘要当作事实依据。

### 默认：Fetch MCP

`@modelcontextprotocol/fetch` 可以获取指定 URL，把 HTML 转换成 Markdown，适合静态网页、官方文档、博客和新闻正文。([ModelScope][4])

推荐组合：

```text
搜索 MCP → 获得 URL
Fetch MCP → 读取正文
LLM → 提取证据并回答
```

Fetch 的优势是简单、无搜索 API Key、工具边界明确。第一版优先使用它。

### 增强：Jina AI MCP Tools

`@PsychArch/Jina-AI-MCP-Tools` 同时提供网页搜索和 Web Reader。其 Reader 工具可以在没有 Jina API Key 时运行；更完整的搜索能力需要 API Key。([ModelScope][5])

Jina 更适合：

* Fetch 提取结果包含大量导航和广告；
* PDF、图片较多的页面；
* 页面结构复杂；
* 希望搜索和读取整合在一个服务中。

第一版不要同时把 Fetch、Jina、Firecrawl 全部暴露给同一个 Agent。推荐：

```text
默认 Fetch
失败后 Jina Reader
```

---

## 3. 动态网页与浏览器兜底 Agent

普通 HTTP 抓取经常无法处理：

* JavaScript 动态渲染；
* 点击后加载；
* 分页；
* 表单；
* Cookie；
* 登录；
* 无限滚动；
* 页面内交互。

魔搭上的 `@Automata-Labs-team/MCP-Server-Playwright` 支持网页导航、点击、表单填写、截图、控制台日志和 JavaScript 执行。([ModelScope][6])

建议独立成：

```text
BrowserFallbackAgent
└── Playwright MCP
```

调用规则：

```text
优先 Fetch
    ↓ 读取失败、正文为空或明显不完整
再调用 Playwright
```

不要让所有查询都经过 Playwright。浏览器方式延迟高、轨迹长，也更容易遇到验证码和页面状态问题。

Chrome DevTools MCP 更偏浏览器调试、网络请求分析和前端问题定位；对普通搜索 Agent，Playwright 更直接。魔搭的 Chrome DevTools MCP 能控制并检查实时 Chrome 浏览器。([ModelScope][7])

---

## 4. 新闻与时效信息 Agent

新闻检索需要特殊处理：

* 必须比较发布时间；
* 区分“网页发布时间”和“事件发生时间”；
* 优先多个独立来源；
* 热搜排行不能当作事实证据。

建议配置：

```text
NewsAgent
├── Zhipu Web Search
├── Hotnews MCP
└── Fetch
```

智谱本身已经支持新闻搜索，可以作为新闻正文发现入口。([ModelScope][1])

`@wopal-cn/mcp-hotnews-server` 聚合中国多个主要社交和新闻平台的实时热点，适合回答：

```text
“现在大家在关注什么？”
“今天国内有哪些热点？”
“哪些话题正在上升？”
```

但它应被视为**热点发现工具**，不能单独用于验证事件真实性。([ModelScope][8])

国际新闻可以使用 Brave Search 的新鲜度控制或 DuckDuckGo News。魔搭的 DuckDuckGo MCP 提供新闻搜索工具，但这类非正式网页接口的稳定性通常不如正式 API。([ModelScope][9])

---

## 5. 学术检索 Agent

通用 Agent 遇到“论文、基准、研究、方法、实验结果”等查询时，不应只调用普通网页搜索。

建议配置：

```text
AcademicAgent
├── Academic Search MCP
├── ArXiv MCP
└── Fetch
```

### 首选：Academic Search MCP

`@afrise/academic-search-mcp-server` 支持从多个来源检索论文，返回题目、作者、发表场所、开放访问状态、PDF URL、摘要和可用的 TL;DR，并支持主题和日期范围过滤。([ModelScope][10])

它适合：

```text
查找某领域的代表论文
按时间范围检索
寻找正式发表版本
比较论文元数据
```

### 补充：ArXiv MCP

`@blazickjp/arxiv-mcp-server` 专门连接 arXiv，支持搜索论文和访问论文内容。适合人工智能、计算机科学和预印本检索。([ModelScope][11])

推荐路由：

```text
广泛学术检索 → Academic Search
AI/CS 最新预印本 → ArXiv
已有私人文献库 → Zotero MCP
```

Zotero MCP 更适合检索用户自己的研究库，而不是公共互联网搜索。([ModelScope][12])

---

## 6. 编程文档与代码仓库检索 Agent

你的代码执行部分由 SWE-agent 负责，但 AutoGen 搜索 Agent 可以提前生成 `research_bundle.md`，为 SWE-agent 提供库文档、API 示例和仓库背景。

推荐配置：

```text
DeveloperResearchAgent
├── Context7
├── GitMCP
└── Fetch
```

### Context7

`@upstash/context7-mcp` 用于检索最新、版本相关的库文档和代码示例，适合查询：

```text
某个 Python/JavaScript 库当前 API
特定版本的配置方式
框架迁移说明
正确的代码示例
```

它可以减少模型使用过时 API 或虚构接口的问题。([ModelScope][13])

### GitMCP

`@idosal/git-mcp` 可以把 GitHub 仓库或 GitHub 页面转换成可供 Agent 查询的文档中心，适合：

```text
理解开源仓库结构
搜索 README 和文档
查找具体功能的实现位置
为 SWE-agent 准备仓库背景材料
```

它不是本地 Git 修改工具，也不应替代 SWE-agent 的代码执行环境。([ModelScope][14])

---

## 7. 本地生活与出行 Agent

真正的通用 Agent 后续会面对：

```text
附近有什么？
如何去某地？
两地距离多少？
某地天气怎样？
规划步行、骑行或驾车路线
```

这类问题应调用结构化地图服务，而不是普通网页搜索。

### 推荐：高德地图 MCP

魔搭的 `@amap/amap-maps` 覆盖地理编码、逆地理编码、IP 定位、天气、步行、骑行和驾车路线等服务；通常需要配置相应 API Key。([ModelScope][15])

配置：

```text
LocalAgent
└── Amap MCP
```

如果主要服务中国大陆用户，高德和百度二选一即可。百度地图 MCP 也提供地点检索、逆地理编码和路线规划。([ModelScope][16])

不要同时配置高德和百度作为默认工具，否则模型会经常在两个近似工具间犹豫。

---

## 8. Firecrawl 应放在哪一层

Firecrawl 不是普通搜索源，而是较重的网站抓取和结构化提取工具。魔搭的 `@mendableai/firecrawl-mcp-server` 提供网页爬取能力，并要求配置 `FIRECRAWL_API_KEY`。([ModelScope][17])

适合：

```text
抓取一个网站的多个页面
遍历文档站
提取结构化字段
制作网站级知识包
```

不适合每个普通搜索问题都调用。

合理顺序：

```text
单页面：Fetch
复杂单页：Jina 或 Playwright
多页面网站：Firecrawl
```

---

## 推荐的 AutoGen 架构

```yaml
router:
  routes:
    general_web:
      mcps:
        - Zhipu-Web-Search
        - Fetch

    international_or_deep_search:
      mcps:
        - Tavily
        - Fetch

    news:
      mcps:
        - Zhipu-Web-Search
        - Hotnews
        - Fetch

    academic:
      mcps:
        - Academic-Search
        - ArXiv
        - Fetch

    developer_docs:
      mcps:
        - Context7
        - GitMCP
        - Fetch

    local_services:
      mcps:
        - Amap

    browser_fallback:
      mcps:
        - Playwright
```

关键点是：**每次任务只把当前类别的 2～4 个工具暴露给对应 Agent**。

AutoGen 可以通过 MCP 适配器连接本地 stdio、远程 SSE 和 Streamable HTTP MCP；`AssistantAgent` 还可以通过 `max_tool_iterations` 完成连续搜索、读取和再次搜索。为提高轨迹可复现性，可关闭并行工具调用。([Microsoft GitHub][18])

---

## 你当前最适合的第一版

先只接以下五个：

```text
1. Zhipu Web Search       通用搜索
2. Fetch                  网页正文读取
3. Playwright             动态网页兜底
4. Context7               技术文档搜索
5. Academic Search        学术检索
```

再按需求增加：

```text
6. Tavily                 国际搜索和备用搜索
7. GitMCP                 GitHub 仓库资料
8. Hotnews                国内热点发现
9. ArXiv                  AI/CS 预印本
10. Amap                  地图和本地服务
11. Firecrawl             多页面网站抓取
```

对于服务器免代理部署，优先在魔搭广场使用 `Hosted` 筛选，并优先选择带“已验证”标识的服务。魔搭文档说明 Hosted MCP 可提供平台托管的 SSE 连接；但第三方 API Key 和对应额度仍然由服务提供商管理。([ModelScope][19])

最终建议的核心链路是：

```text
意图路由
  → 智谱或专业检索 MCP
  → Fetch 读取正文
  → Playwright 失败兜底
  → 多来源交叉验证
  → 输出标准化 Evidence Bundle
```

这套结构既覆盖通用搜索，又能为后续 AgentJudge 轨迹保存清晰的“查询—搜索结果—网页证据—最终结论”链路。

[1]: https://modelscope.cn/mcp/servers/ZhipuAI/Zhipu-Web-Search?utm_source=chatgpt.com "智谱联网搜索"
[2]: https://modelscope.cn/mcp/servers/%40tavily-ai/tavily-mcp?rb=&utm_source=chatgpt.com "Tavily智搜"
[3]: https://modelscope.cn/mcp/servers/%40w-jeon/mcp-brave-search?utm_source=chatgpt.com "Brave Search MCP 服务器"
[4]: https://www.modelscope.cn/mcp/servers/%40modelcontextprotocol/fetch?utm_source=chatgpt.com "Fetch网页内容抓取"
[5]: https://www.modelscope.cn/mcp/servers/%40PsychArch/Jina-AI-MCP-Tools?utm_source=chatgpt.com "Jina-AI-MCP-Tools"
[6]: https://modelscope.cn/mcp/servers/%40Automata-Labs-team/MCP-Server-Playwright?utm_source=chatgpt.com "MCP Server Playwright - 网页自动化助手"
[7]: https://modelscope.cn/mcp/servers/%40ChromeDevTools/chrome-devtools-mcp?utm_source=chatgpt.com "Chrome开发者工具MCP"
[8]: https://modelscope.cn/mcp/servers/%40wopal-cn/mcp-hotnews-server?rb=&utm_source=chatgpt.com "热闻社媒服务"
[9]: https://modelscope.cn/mcp/servers/%40misanthropic-ai/ddg-mcp?utm_source=chatgpt.com "DuckDuckGo搜索服务"
[10]: https://modelscope.cn/mcp/servers/%40afrise/academic-search-mcp-server?utm_source=chatgpt.com "学术论文搜索MCP 服务器"
[11]: https://www.modelscope.cn/mcp/servers/%40blazickjp/arxiv-mcp-server?utm_source=chatgpt.com "ArXiv AI搜索服务"
[12]: https://modelscope.cn/mcp/servers/%4054yyyu/zotero-mcp?utm_source=chatgpt.com "Zotero MCP: 您的研究库在Claude 中"
[13]: https://modelscope.cn/mcp/servers/%40upstash/context7-mcp?utm_source=chatgpt.com "Context7 MCP - 任何提示的最新文档"
[14]: https://www.modelscope.cn/mcp/servers/%40idosal/git-mcp?utm_source=chatgpt.com "GitHub MCP 转换服务"
[15]: https://modelscope.cn/mcp/servers/%40amap/amap-maps?utm_source=chatgpt.com "高德地图开放平台通用级SSE 协议MCP 服务解决方案"
[16]: https://modelscope.cn/mcp/servers/%40baidu-maps/mcp?utm_source=chatgpt.com "百度地图MCP Server"
[17]: https://modelscope.cn/mcp/servers/%40mendableai/firecrawl-mcp-server?utm_source=chatgpt.com "FireCrawl网络抓取服务器"
[18]: https://microsoft.github.io/autogen/stable//user-guide/agentchat-user-guide/tutorial/agents.html?utm_source=chatgpt.com "Agents — AutoGen"
[19]: https://modelscope.cn/docs/mcp/intro?utm_source=chatgpt.com "MCP广场简介"
