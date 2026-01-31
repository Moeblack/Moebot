# Current Checkpoint

## 已完成任务

1. 克隆了 NcatBotDocs 到 `docs/` 目录。
2. 删除了 `docs/.git` 以保持根目录 Git 仓库的纯净。
3. 根据项目文档（配置项、私有工作目录、日志、测试等）更新了根目录的 `.gitignore` 文件。
4. 编写了 `docs/assembler_format.md`，详细说明了 `assembler.py` 中消息拼接和“一层化”历史记录的理解与实现细节。
5. 更新了 `main.py` 为 NcatBot 基础代码，并将 Python 版本升级至 3.13。
6. 完成了代码提交 (Commit)，遵循 Conventional Commits 规范。
7. 在 `LIMCODE.md` 中补充了必须使用 `./.venv/bin/python` 的技术细节。
8. 完善了 `LIMCODE.md` 中的项目概述 pill 和 AI 服务使用规范。
9. 创建了 `scripts/ask_ai.py` 工具脚本，作为调用 Gravity AI API 的标准示例。
10. 在项目中添加了 `httpx` 依赖。
11. 完成了代码提交 (Commit)，包含 `LIMCODE.md` 更新及相关的 Git 操作。
12. 更新了 `LIMCODE.md`，设置项目首推模型为 `gemini-3-flash`。
13. 创建了 `config.yaml` 配置文件，用于配置 root 账号和机器人 QQ。
14. 更新了 `main.py`，实现了基于 Gemini 格式的 root 账号私聊 AI 对话功能。
15. 同步更新了 `scripts/ask_ai.py` 和 `LIMCODE.md` 中的模型信息，确认当前仅支持 Gemini 2.5 - 3 系列模型（已统一更新为 `gemini-3-flash`）。
16. 创建了 `pyrightconfig.json` 以解决 Pylance 针对 `ncatbot` 无类型存根的报错问题。
17. 更新了 `main.py` 中的 `get_gemini_response` 函数：
    - 增加了可选参数 `role`，以支持自定义消息角色（默认为 "user"）。
    - 增加了可选参数 `file` (类型为 `dict | None`)，以支持多模态输入（图片/文件），并在 payload 构建时将其加入 `parts`。
    - 修复了 Gemini API 调用时的 SSL 证书校验失败问题（通过 `verify=False`）。
18. 更新了所有相关文件（`main.py`, `LIMCODE.md`, `scripts/ask_ai.py`），将 AI API 域名从 `gravity.moeblack.top` 迁移至 `gravity.kuronet.top`。
19. 优化了 `main.py` 中的 AI 回复提取逻辑：
    - 遍历 `parts` 数组。
    - 过滤掉带有 `thought` 字段的推理部分。
    - 仅合并带有 `text` 字段的正文部分，解决了“将思考过程（think）发送给用户”的问题。
20. **实现了内存级对话历史管理 (`chat_history`)**：
    - 采用 **Assembler 风格的手动拼接** 策略，而非 API 原生的 `contents` 数组。
    - 编写了 `build_prompt` 函数，将历史记录组装为 XML 格式 (`<conversation_history>`, `<turn role="...">`)。
    - 实现了 **滑动窗口机制**，限制历史记录为最近 20 条，防止 Token 溢出。
    - **优化了 Role 标识**：用户消息使用 `user_id` 作为 role，AI 回复使用 `assistant` 作为 role，为未来多用户/群聊场景预留了身份溯源能力。
    - 修改了 API 调用逻辑，每次发送包含完整上下文的单次 Prompt。
21. **实现了 JSONL 持久化存储**：
    - 增加了 `load_history` 和 `save_message_to_file` 函数。
    - 消息记录存储在 `data/chat_history.jsonl`，确保重启后记忆不丢失。
    - 采用追加写入模式，保证性能 and 数据安全。
22. **答疑与认知同步**：
    - 解释了 `.jsonl` 文件的存储格式及 `user_id`, `role`, `content` 三个关键字段的作用。
    - 详细解答了关于“滑动窗口”机制中的双重截断逻辑（加载时截断和运行时截断）及其必要性。
    - 解释了 Python 中 `if not line.strip(): continue` 过滤空行的小技巧。
    - 更新了 Role 格式：将用户消息的 `role` 字段从纯 `user_id` 修改为 `Nickname(ID)` 格式。
    - **实现了分层记忆架构**：引入了“工作记忆” (Working Memory) 和“情节记忆” (Episodic Memory)。
    - **实现了潮汐归档法 (Tidal Archiving)**：当工作记忆达到 50 条时自动触发归档。
23. **实现自进化人格系统 (Persona System)**：
    - **人格 XML 标签**：在 Prompt 头部引入 `<personality>` 标签。
    - **记忆完全隔离**：不同人格之间拥有完全独立的“工作记忆” and “情节记忆”。
    - **管理指令**：实现了 `/persona list`, `/persona switch`, `/persona init` 指令。
24. **实现群聊适配与主动决策机制**：
    - **双重印象系统**：维护群组整体印象及成员个人印象。
    - **智能观察与主动介入**：10% 概率记录背景，自动触发插话决策。
25. **实现 AI 交互监控系统与管理后台**：
    - **可视化管理**：基于 FastAPI 的网页监控后台，实时展示 AI 请求、决策和配置变更。
    - **全面编辑功能**：支持基础人格定义、初始特质、运行时演化特质、用户印象、情节记忆的在线编辑。
    - **提示词结构重构**：将 Prompt Builder 模板迁移至 `data/prompts.json`，并提供可视化编辑界面，实现提示词结构的动态管理。
    - **实时配置修改**：支持在后台直接编辑和保存 JSON 格式的全局配置。
26. **修复红字报错与代码优化**：
    - **修复导入路径**：在 `scripts/monitor_web.py` 中将 `from bot_agent.memory.manager import memory_manager` 修正为正确的 `from bot_agent.memory import memory_manager`。
    - **解决 Pylance 误报与方法重命名**：将 `MemoryManager.build_prompt` 方法重命名为 `generate_prompt`，以消除与 `prompt` 模块下 `build_prompt` 函数重名导致的 IDE 识别困惑。
    - **增强代码健壮性**：在 `manager.py` 调用底层 `prompt.build_prompt` 时，改用全显式关键字参数，确保参数映射 100% 准确。
    - **同步调用点**：更新了 `bot_agent/handlers/logic.py` 中的相应调用。
27. **重构记忆管理页面**：
    - **条目化管理**：将原有的 `prompt(JSON)` 编辑方式重构为基于模态框的条目化 (Item-based) 管理界面。
    - **全卡片点击**：将聊天、情节、印象记忆卡片设为全区域可点击，增强交互性。
    - **聊天历史增强**：采用分栏布局，支持编辑角色、内容、时间、昵称及 QQ ID，实现深度调试。
    - **情节记忆增强**：提供摘要和时间的结构化编辑条目。
    - **印象系统增强**：将长字符串编辑转变为可动态增删的条目化管理。
    - **后端适配**：修复了持久化字段名不一致的问题，确保 Web 端修改能正确同步到 Bot。
28. **优化决策机制与 Prompt 策略**：
    - **倾向于不回复**：在 `entry_decision` Prompt 中明确了“节能观察”原则，要求 AI 在非被提及且话题无关时保持沉默（不回复且不发表情）。
    - **50条上下文**：将历史记录加载上限从 20 条提升至 50 条，并确保决策时参考最近 50 条上下文。
    - **鲁棒性处理**：当 passive sampling (10% 概率记录) 触发决策且 AI 超时或解析失败时，默认选择“不回复”和“不进入专注模式”。
29. **增强记忆管理可视化**：
    - **条目化过滤**：为印象、历史、情节记忆列表增加了实时搜索过滤功能。
    - **时间轴视图**：重构了情节记忆的管理界面，采用垂直时间轴线展示摘要和时间。
    - **数据概览**：在列表卡片上展示了消息总数、印象条数及最近一条内容的预览。
    - **交互优化**：增加了“刷新记忆数据”按钮，提升管理体验。
30. **完成了管理后台的大规模重构与组件化**：
    - **HTML 拆解**：将原有的 2000+ 行 `index.html` 拆解为 10+ 个独立的 Jinja2 组件，存放在 `templates/components/` 目录下。
    - **CSS 提取**：将所有内联样式迁移至 `static/css/monitor.css`。
    - **JS 模块化**：将巨型 JS 逻辑拆分为 `api.js`, `dashboard.js`, `logs.js`, `config.js`, `personas.js`, `memories.js`, `prompts.js`, `utils.js`, `main.js` 等多个功能模块，并进一步细化了 `memories_chat.js`, `memories_episodic.js`, `personas_traits.js` 等。
    - **代码规范对齐**：所有拆分后的文件均保持在 150 行以内（除个别 flat API 列表外），显著提升了 AI 的代码阅读和理解效率。
    - **导航与数据同步优化**：重构了页面初始化与导航逻辑，确保各模块独立加载且数据实时同步。
31. **完成了 Bot 后端代码的大规模重构与拆解**：
    - **逻辑拆分**：将巨型文件 `bot_agent/handlers/logic.py` (400+行) 拆解为 `decisions.py` 和 `reply.py`。
    - **处理器拆分**：将 `bot_agent/handlers/processor.py` 拆解为 `processor.py`, `processor_focus.py` 和 `processor_utils.py`。
    - **记忆管理拆解**：将 `bot_agent/memory/persistence.py` 拆解为 `persistence_state.py` 和 `persistence_content.py`；将 `bot_agent/memory/logic.py` 拆解为 `evolution.py` 和 `consolidation.py`。
    - **模块化增强**：引入了 `SocialManager` (于 `social.py`) 独立管理社交能量，并将默认 Prompt 迁移至 `prompt_defaults.py`。
    - **配置与常量分离**：创建了 `constants.py` 和 `config_defaults.py`，显著降低了 `config.py` 的复杂度。
    - **监控系统分层**：将监控日志的写入 (`monitor.py`) 与查询 (`monitor_query.py`) 逻辑分离。
    - **代码规范达标**：除极个别边界文件外，所有 Python 文件均缩减至 150 行以内，极大提升了 AI 辅助开发的效率。
32. **编写了 Bot Agent 开发者文档**：
    - 在 `ncatbotdocs/docs/notes/bot-agent/` 目录下创建了一套完整的开发者文档，涵盖架构、记忆系统、处理器决策、监控后台和配置说明。
    - 同步更新了 VuePress 配置 (`notes/index.ts`, `plume.config.js`)，在导航栏中增加了 "Bot Agent" 入口。
    - 文档采用中文编写，详细介绍了 XML 架构、潮汐归档、自进化人格等核心概念，旨在提升 AI 辅助开发的效率。
 33. **完成代码规范化与报错修复**：
    - **修复方法缺失**：修复了 `ConfigManager` 中 `remove_initial_trait` 方法因缩进错误导致无法访问的问题。
    - **纠正导入路径**：修复了 `group.py` 和 `private.py` 中 `record_session_batch` 的错误导入路径（从 `.processor` 改为 `.processor_utils`）。
    - **消除冗余导入**：移除了 `processor.py`, `processor_focus.py`, `reply.py`, `evolution.py` 等多个文件中的未使用导入。
    - **规范代码格式**：将多个文件中的单行多语句（使用分号或冒号连接）拆分为标准多行结构，解决了 Ruff 的格式警告。
    - **显式常量导出**：在 `config.py` 中将 `from .constants import *` 替换为显式的 `as` 别名导入，确保了跨模块调用的可见性并消除了 Ruff 警告。
    - **修复损坏字符**：修复了 `processor_focus.py` 中因编码问题导致的乱码中文字符。
    - **抑制 TS 模块报错**：在 `ncatbotdocs/docs/.vuepress/` 目录下创建了 `env.d.ts` 类型声明文件，解决了 IDE 在无 `node_modules` 时对 `vuepress-theme-plume` 等模块的找不到定义报错。

 34. **优化专注模式与决策机制**：
    - **历史注入**：当 AI 从非专注模式进入专注模式时，会自动从群聊平台拉取最近 25 条历史消息并注入到工作记忆中，以保证对话上下文的连贯性。
    - **统一 XML 格式**：统一了决策模式和回复模式的消息历史格式，全部采用 `<turn role="..." name="..." id="..." time="...">content</turn>` 结构的 XML 标签。
    - **时间感决策**：更新了准入决策、微观决策和宏观评估的提示词，要求 AI 在决策时必须参考消息的时间戳，分析对话的时效性、紧凑程度以及话题是否已结束。
    - **工具函数增强**：在 `processor_utils.py` 中新增了 `format_history_to_xml` 和 `fetch_and_inject_history` 两个核心工具函数。

 35. **实现话题聚焦与用户活跃度统计**：
    - **话题聚焦 (Topic Focus)**：在 `MemoryManager` 中增加了对“当前活跃话题”的追踪与持久化。AI 现在会在决策和回复时自动提取并更新当前话题，并将其作为上下文信息注入 Prompt，显著提升了多话题群聊环境下的对话稳定性。
    - **用户活跃度统计 (User Activity)**：在监控系统中引入了 `user_activity` 数据表，实时记录并统计各会话中用户的发言频率及最后活跃时间。
    - **可视化增强**：在管理后台仪表盘增加了“用户活跃度排行”板块，支持实时查看活跃用户 Top 榜单，提升了对机器人社交状态的洞察力。
    - **后端适配**：更新了 `monitor_query.py` 和 `monitor_web.py`，新增了相关的 API 查询端点，并修复了部分类型标注错误。

 36. **优化系统生命周期管理与内网访问**：
    - **同步运行与退出**：重构了 `main.py` 的进程管理逻辑，通过 `subprocess.Popen` 维护监控后台进程，并注册了 `atexit` 钩子和信号处理函数 (`SIGINT`, `SIGTERM`)，确保机器人退出时监控后台也能同步关闭。
    - **内网监听支持**：将监控后台的监听地址统一配置并声明为 `0.0.0.0`，使其支持内网其他设备访问，并修正了启动时的日志输出信息。

 37. **优化机器人被提及标识与消息处理**：
    - 将机器人被提及时的标识符从 `@我` 统一更换为 `@assistant`。
    - 修复了在群聊中被 @ 时，后续消息可能丢失的问题（通过增加对 `PlainText`、`Face`、`AtAll`、`Reply` 等消息段类型的支持）。
    - 更新了所有相关的提示词模板（`data/prompts.json` 和 `bot_agent/memory/prompt_defaults.py`）。

 38. **修复私聊专注模式问题**：
    - 修正了私聊消息会进入 5 秒扫描的“专注模式”的问题。现在私聊消息将绕过专注模式逻辑，直接进入 AI 决策流程。
    - 修改了 `private.py` 以移除对 `is_in_focus` 的检查，确保私聊始终触发准入决策。
    - 修改了 `processor.py`，限制仅在群聊场景下允许进入专注模式。

 39. **优化被 @ 时的上下文拉取与历史记录规范化**：
    - **即时历史补全**：在群聊中被 `@Assistant` 提及且不在专注模式时，会立即触发异步任务拉取最近 20 条历史消息并注入到工作记忆中，确保 AI 拥有充足处对话上下文。
    - **历史记录持久化**：优化了 `fetch_and_inject_history` 函数，使其在拉取历史消息时不仅更新内存，还会同步持久化到 JSONL 文件，并自动过滤掉机器人自身的发言。
    - **身份标识规范化**：统一了 `fetch_and_inject_history` 和 `record_session_batch` 中的角色标识格式，采用 `Nickname(ID)` 作为 `role` 字段，并确保 `nickname` 和 `user_id` 始终被记录，增强了历史记录的可读性和溯源能力。
    - **去重与排序增强**：在注入历史时增加了基于内容和时间戳的严格去重逻辑，并自动按时间线进行重排序。

 40. **重构社交能量系统并修复决策异常**：
    - **社交能量去中心化**：将社交能量（Social Energy）从全局状态重构为按会话（Session）隔离。每个群聊现在拥有独立的社交能量和心情状态。
    - **跨天重置逻辑**：实现了每日首次对话前自动回满至 200 点能量的机制，心情回归 normal。
    - **精准衰减规则**：能量 > 100 时每小时衰减 5 点，<= 100 时停止衰减。
    - **修复 Prompt 渲染 Bug**：修复了在专注模式下，微观决策（micro_decision）和宏观评估（macro_decision）因缺少 `social_state_desc` 变量导致 Prompt 渲染失败。
    - **状态持久化升级**：更新了 `persistence_state.py`，支持以字典格式存储并加载多个会话的社交状态。
    - **管理端增强**：在监控后台新增了 `/api/social-states` 接口，为未来在可视化面板展示各群聊社交状态预留了支持。

 - 41. 修复情节记忆更新触发机制：
    - 解决了情节记忆（Episodic Memory）仅在 AI 回复时才触发归档的缺陷。
    - 在 `MemoryManager` 中提取了 `check_and_trigger_consolidation` 统一检查方法。
    - 将触发逻辑集成到 `record_session_batch` 中，确保 AI 在静默观察群聊时也能根据积压消息量自动完成记忆归档与性格演进。
    - 移除了 `processor.py` 和 `processor_focus.py` 中的冗余逻辑，保持代码简洁。
    - 优化了群聊静默插话决策：当背景消息累计达到阈值触发插话决策前，也会像被 `@` 一样自动拉取最近 20 条历史记录，确保 AI 决策时具备充足的语境信息。

## 修复 Bug

1. **修复了 `config.py` 中的 `NameError`**：
   - 在 `ConfigManager._apply_config` 方法中，修复了 `INT_CONF` 变量在定义前被引用的问题。
   - 确保 `INT_CONF` 从 `self._config.get("interaction", {})` 正确初始化后再进行子项赋值。
   - 验证了 Bot 的启动流程，确保配置加载逻辑正常运行。

### 修复与优化

1. **修复群聊记忆演进异常**：
   - 修正了 `evolution.py` 中 `is_group` 的判断逻辑。原逻辑依赖 `base_id.startswith("group_")`，但在 NcatBot 中群 ID 是纯数字字符串，导致群聊常被误判为私聊。
   - 重构了 `MemoryManager` 的 `consolidate_memory` 方法及相关调用链，显式传递 `is_group` 状态，确保演进逻辑准确识别场景。
   - 优化了演进与归档时的消息格式化逻辑，统一采用 `[时间] 昵称(ID): 内容` 格式，并解决了原 f-string 嵌套引号可能导致的解析或兼容性问题。
   - 增强了角色识别，在演进 Prompt 中明确区分 AI (`AI(assistant)`) 与用户。
   - 完善了群成员个人印象更新的正则匹配，使其更稳健地从 `Nickname(ID)` 格式中提取用户 ID。
   - 增加了演进过程的调试日志输出，便于追踪 AI 是否发现新的性格特征或印象。

 42. **优化 Traits 演进提示词规范**：
    - **禁止具体用词**：修改了 `personality_evolution` 提示词，明确禁止记录具体词汇（如 `"以电子垃圾自嘲"`），避免 AI 陷入复读循环。
    - **禁止限制性规范**：禁止记录 `"拒绝/规避XX话题"` 类型的 trait，因为 AI 应融入群聊文化而非充当道德卫士。
    - **增加正反示例**：在提示词中提供了明确的正确写法（抽象性格特质）和错误写法（具体用词/限制性规范）。
    - **数据清理**：将 `"以电子垃圾自嘲"` 替换为 `"喜欢自嘲"`，删除了 `"拒绝并规避色情话题"`。

 43. **修复代码解析与类型安全问题**：
    - **修复 Pylance 报错**：在 `evolution.py` 中增加了对 AI 返回的 JSON 结果的 `isinstance(result, dict)` 和字段类型的显式检查，解决了 `无法访问类“str”的属性“items”` 的报错，并增强了代码的鲁棒性。
    - **同步演进概率逻辑**：更新了 `consolidation.py` 中的演进触发概率，使其与文档描述一致：前 8 次归档仅 5% 概率，随后逐渐增加，第 13 次保底触发。
    - **优化图片描述处理**：在 `reply.py` 中统一了图片占位符的描述，增加了对群聊未提及机器人时忽略图片的明确标识。

 - 46. 完成代码提交 (Commit) 并合并至 `main` 分支：
    - 涵盖了社交能量重构（按会话隔离、跨天重置、衰减规则）。
    - 修复了情节记忆更新触发机制（静默观察时也能触发归档）。
    - 优化了 Traits 演进规范（禁止具体用词、禁止限制性规范）。
    - 修复了代码解析与类型安全问题（显式检查 JSON 结果类型）。
    - 定义并应用了「互联网碎片体」说话风格。
    - 优化了印象演进机制，将群聊场景下的多次 AI 请求合并为一次，并降低了触发频率。
    - 完成了从 `feature/group-chat` 到 `main` 的 Fast-forward 合并，并删除了特性分支。

## 最新文档

47. **编写 Traits 演进机制完整文档**：
    - 创建了 `ncatbotdocs/docs/notes/bot-agent/traits-evolution.md`
    - 详细描述了从消息记录 → 归档触发 → 演进分析 → Prompt 注入的完整数据流
    - 分析了「正反馈偏差」问题的根本原因（AI 分析自己的输出导致自我强化）
    - 提出了四种解决方案：输入源分离、双轨制、置信度衰减、对抗性演进
    - 给出了推荐组合方案（A + B + 简化版C）

48. **修复 Traits 正反馈偏差问题**：

49. **专注模式体验优化（基于提示词与路由）**：
    - 更新 `prompt_defaults.py`：在 `entry_decision` / `micro_decision` / `macro_decision` 中加入“群里任何成员表达不满意→必须静默并退出专注”的强制规则。
    - 进一步收紧 `entry_decision` 的准入标准：默认不回复/不进入专注，仅在强信号（明确 @、点名要求回应、能显著推进话题）下才允许回复；enter_focus 需要同时满足密集时效+强相关+无反感信号。
    - 将准入/准出规则块移动到聊天记录之后（紧贴最新输入），以降低模型遗忘概率。
    - 优化群聊专注期路由：当群聊 `state.is_in_focus=True` 时，`processor.py` 不再走 `entry_decision`，而是直接走 `micro_decision`。
    - 在 `processor_focus.py` 中增加对微观决策“退出专注”信号的处理：当 `action=ignore` 且 reason 包含“退出专注”时，立即停止专注循环并静默。
    - 更新 `prompt_defaults.py`：在 `entry_decision` / `micro_decision` / `macro_decision` 中加入“群里任何成员表达不满意→必须静默并退出专注”的强制规则。
    - 优化群聊专注期路由：当群聊 `state.is_in_focus=True` 时，`processor.py` 不再走 `entry_decision`，而是直接走 `micro_decision`。
    - 在 `processor_focus.py` 中增加对微观决策“退出专注”信号的处理：当 `action=ignore` 且 reason 包含“退出专注”时，立即停止专注循环并静默。

49. **修复群聊 AI 触发绕过白名单的问题**：
    - 在 `bot_agent/handlers/group.py` 中修正群聊 `is_active` 判定：非 Root 且非白名单群直接 return。
    - 避免某群一旦进入过专注/专注窗口或命中唤醒词后，即使不在白名单也持续触发 AI 的“全群随机触发”现象。
    - 清理了重复的 AI 准入鉴权与二次 `is_active` 计算，防止逻辑漂移。
    - **输入源分离**：修改 `evolution.py`，演进分析时跳过 AI 自己的发言（`role == 'assistant'`），只分析用户消息
    - **视角转换**：将演进提示词从「AI表现出什么特征」改为「群友们希望 Assistant 是什么风格」
    - **同步更新**：`data/prompts.json` 和 `bot_agent/memory/prompt_defaults.py` 的 `personality_evolution` 模板
    - **效果**：打破正反馈循环，Traits 现在反映「用户期望」而非「AI 自我表演」

 49. **重构话题检测 (Topic Detection) 提示词逻辑**：
    - 将话题检测指令从默认 Prompt 模板中移除。
    - 引入 `{topic_instr}` 占位符，仅在 `ENABLE_TOPIC_DETECTION` 开启时动态注入指令。
    - 解决了原先依靠 `replace()` 硬匹配字符串导致的逻辑脆弱问题，确保指令控制的准确性。
    - 同步更新了准入决策、微观决策、宏观评估及正式回复的提示词模板。

## 最新修复

43. **修复人格自称老实人问题**：


44. **定义「互联网碎片体」说话风格**：
    - 在 `data/prompts.json` 和 `prompt_defaults.py` 的 footer 模板中更新了说话风格指南。
    - 核心规则：碎片化、省略、情绪外泄、点到为止、禁止解释自己、禁止总结。
    - 目标：让 AI 的发言从「书面口语混合体」转变为更贴近真实群聊的「互联网碎片体」。

45. **优化印象演进机制，减少 AI 调用次数**：
    - **问题**：原逻辑每次演进时会为群整体 + 每个发言成员分别调用 AI，导致 N+1 次请求。
    - **解决方案**：重构 `evolve_impression` 函数，群聊场景下合并为**一次 AI 请求**，同时返回群整体印象和各成员印象。
    - **降低触发频率**：修改 `consolidation.py` 中的概率机制，前8次仅5%概率触发，第13次保底，显著减少无意义的演进调用。



# 当前进度：项目概览与文档完善 (进行中)

## 状态摘要
- [x] 代码库从旧项目迁移完成。
- [x] 核心逻辑到位并实现了自动配置生成。
- [x] 补全了开源所需的配置文件。
- [x] 更新了 `docs/bot-agent/` 下的所有核心文档，使其与当前代码实现一致。
- [x] 完成了项目主页 `README.md` 的编写，明确了核心理念与路线图。
- [x] 明确了项目的 **AI 原生设计理念**：项目架构旨在使 AI 辅助开发更高效。
- [x] 细化了路线图第三阶段：转向更广泛的工具调用（画图、搜索、具身智能等）。
- [x] 在 README 中补充了“记忆复习机制”（艾宾浩斯遗忘曲线）与“结构化提示词设计”的技术细节。
- [x] 在 README 中明确了 AI 原生设计理念，并指引用户查看 `docs/` 和 `LIMCODE.md`。
- [x] 优化 README 结构：将“遗忘曲线”从路线图移动至专门的“记忆哲学”章节，强调其作为持续探索方向的地位。

## 最近变更
- **完善依赖清单**: 在 `requirements.txt` 中补充了 `Pillow` (PIL) 依赖，解决了机器人启动时的模块缺失问题。
- **AI 协同设计规范化**: 在 `LIMCODE.md` 中明确了本项目“设计之初即考虑 AI 辅助开发”的理念，并在 `README.md` 中增加了相关说明 and 文档指引。同时在 `LIMCODE.md` 中增加了 Lim Code 插件的推荐信息。
- 编写了根目录 `README.md`：详细介绍了 XML 安全层、记忆压缩架构、JSON Schema 驱动决策等核心概念。
- 规划了项目路线图：包含框架解耦、插件化、多模态支持等后续阶段。
- 实现了社交能量模块的深度隐藏：当 `enable_social_energy` 关闭时，提示词和 JSON Schema 中将不再出现社交能量、心情及能量调整相关的字段，确保 AI 不会感知到该系统。
- 为社交能量模块增加了 `enable_social_energy` 开关，默认设为关闭。
- 更新了 `docs/bot-agent/prompts.md`：在文档中包含了当前使用的核心提示词正文，并新增了“胡子变量”详细说明章节。
- 更新了 `docs/bot-agent/architecture.md`：区分了私聊与群聊的决策建模。
- 增加了 `config.example.yaml`：提供 ncatbot 基础框架的配置示例。
- 更新了 `docs/bot-agent/README.md`：明确了初次运行前设置 QQ 号的步骤。
- 更新了 `docs/bot-agent/config.md`：区分了框架基础配置和 Agent 逻辑配置。
- 明确了 `ncatbot` 的限定安装方式（必须使用阿里云镜像源更新）。
- 更新了 `docs/bot-agent/monitor.md`：说明了监控后台随机器人自动启动的特性。
- 更新了 `docs/bot-agent/README.md`：增加了“快速开始”小节。
- 更新了 `docs/bot-agent/architecture.md`：修正了文件目录结构的描述。
- 在 `README.md` 中新增了“可视化监控与动态管理”章节，强调了 Web 后台对 AI 决策透明化和实时干预的重要性。
- **修复 KeyError: 'native'**: 修正了 `bot_agent/memory/prompt.py` 中因硬编码 `"native"` 作为默认人格名且在配置中不存在而导致的崩溃。现在使用 `DEFAULT_PERSONA_NAME` 并增加了安全回退机制。
- **同步监控后台**: 将 `scripts/monitor_web.py` 中的默认人格名从 `"native"` 同步为 `DEFAULT_PERSONA_NAME`。
- **清理硬编码与优化逻辑**: 
    - 提取了决策条数、Thinking Budget、指令前缀等 10 余处硬编码至 `constants.py`。
    - 删除了 `prompt.py` 中过时的长特质检测逻辑，统一了 Prompt 结构。
    - 编写了 `docs/bot-agent/parameters.md` 对核心参数进行了归档说明。

 50. **优化私聊决策路径**：
    - 私聊在 2s 防抖结束后，由调用“准入决策”改为直接调用“微观决策”。
    - 实现了私聊 `ignore` 动作的完全静默处理（不发送任何内容）。
    - 统一了私聊与群聊专注模式下的决策 Schema。

 51. **项目正式开源 (GitHub Open Source)**: 
    - 成功识别并配置了用户提供的 SSH 私钥 (`logs/id_ed25519`)。
    - 验证了与 GitHub 的 SSH 连接 (Hi Moeblack!)。
    - 关联了远程仓库 `git@github.com:Moeblack/MoeBot.git`。
    - 执行了强行推送 (`git push -f origin main`)，将 MoeBot 框架正式发布至 GitHub。
    - 使用 `gh` 工具将仓库设置为公开状态 (Public)。
    - 确认提交身份为 `Moeblack <kuroinekorachi@gmail.com>`。

## 待办事项
1. [x] 验证 `requirements.txt` 中的依赖是否完整。
2. [ ] 准备开源发布的发布说明。

## 下一步行动

- 已将「B 站卡片/链接 → 短链」抽成通用函数 `try_extract_and_shorten_bilibili_from_event()`，群聊/私聊共用。
- 私聊侧：白名单用户（含 root，root 默认视为白名单成员）收到 B 站卡片/链接会自动回复短链，并在入队与 AI 决策之前提前返回。
- 如需增加开关/只处理卡片段（不处理纯文本）等更细粒度控制，再继续补充配置项与过滤规则。

- 进行中：排查「私聊发送 B 站卡片/b23 链接未触发短链回复」问题：
  - 在 `link_utils/card_shortener.py` 增加了候选文本/URL/选中链接/短链结果的 debug 日志。
  - 在 `handlers/private.py` 增加了命中与未命中的 debug 日志，便于确认是否走到短链分支、以及 raw_message 实际内容。
  - 已定位原因：QQ 小程序卡片把链接中的 `&` 编码成了 `&amp;`，导致 URL 正则把链接截断在 `...share_source=qq` 之前，从而丢失 `b23.tv` 域名，识别失败。
  - 已修复：在 `link_utils/bilibili_card.py` 增加 `preprocess_card_text()`，对 `&amp;`/`&#44;`/`\\/` 做预解码后再提取 URL。
  - 已修复：`PrivateMessageEvent.reply()` 不支持 `at` 参数，私聊发送链接改为 `await event.reply(text=...)`。
  - 调整需求：用户不需要转短链，改为固定输出 `https://www.bilibili.com/video/BV...` 这种 BV 直链；实现方式为：b23 展开一次跳转 + 清追踪参数 + 正则提取 BV 并格式化输出。
  - 已完成：关闭 `card_shortener.py` 内用于排查的 `[bili-shortener]` debug 输出，避免刷屏。
  - 已完成：将「B站链接提取服务」与 AI 开关解耦，新增配置项：
    - `interaction.bilibili_link_extract_private`（私聊默认 true）
    - `interaction.bilibili_link_extract_groups`（群聊单独列表，只有这些群启用）
  - 已完成：私聊侧增加降噪触发条件：仅当消息含 Json/XML/Share 段或文本含 b23/bilibili 提示时才尝试解析。

- 修复：白名单群 @ 机器人未进入决策模式
  - git 最新提交 `3155d44` 在 `handlers/group.py` 里误删了“消息入队 + 防抖触发 wait_and_trigger”这一段，导致通过鉴权后直接 return。
  - 已在 `bot_agent/handlers/group.py` 恢复：鉴权通过后将 event 追加到 `state.message_queue`，并创建 `state.timer_task = asyncio.create_task(wait_and_trigger(...))` 进入决策流程。