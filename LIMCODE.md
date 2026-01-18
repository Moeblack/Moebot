# LIMCODE.md

该文件为 Lim Code 工具在此代码库中工作时提供指导。

## 项目概述

本项目是一个基于 NcatBot 的高度模块化 AI 机器人 Agent 框架。它具备完善的记忆系统（包括工作记忆、情节记忆和自进化人格特质）、精细的决策机制（准入决策、微观/宏观专注模式）以及基于 FastAPI 的可视化监控与管理后台。

### 核心特性

- **分层记忆架构**：采用“工作记忆” (Working Memory) 与“情节记忆” (Episodic Memory) 分离，通过“潮汐归档”机制实现长期记忆的压缩与沉淀。
- **自进化人格系统**：机器人能根据对话历史自动演化性格特质 (Traits) 和用户印象 (Impressions)，实现“千群千面”。
- **精细化社交决策**：引入社交能量 (Social Energy) 和心情系统，结合准入决策与专注模式，模拟人类社交的疲劳与专注状态。
- **可视化监控后台**：实时展示 AI 请求日志、决策逻辑及内存状态，支持在线编辑人格、特质和历史记录。
- **XML 结构化 Prompt**：采用高度结构化的 XML 标签构建 Prompt，确保 AI 输出的稳定性与可解析性。
- **互联网碎片体风格**：针对中文群聊环境优化的“碎片化”说话风格，使机器人更具真实感。

### 注释与语言

- **必须使用中文**撰写代码注释。
- **必须使用中文**与用户进行交流。

## AI 服务与 API 使用规范

为了保证开发过程中的自动化测试和 Dry Run 能够顺利进行，你需要配置 AI API 站点。

1. **API 地址**: 配置在 `bot_agent/constants.py` 或环境变量中。
2. **访问凭据 (Password/API Key)**: 请咨询项目负责人或使用自己的 API Key。
3. **支持格式**:
    - **Google AI Studio 格式**:
        - Endpoint: `https://<your-domain>/v1beta/models/{model}:generateContent`
        - **推荐模型**: `gemini-3-flash`
        - **多模态安全**: 在群聊中，默认仅在机器人被 @ 时才处理并发送图片到 AI (`group_image_mode: mention`)，以降低 NSFW 风险。
        - Payload: 遵循 Google Generative AI 标准格式。
    - **OpenAI 格式**:
        - Endpoint: `https://<your-domain>/v1/chat/completions`
        - Payload: 遵循 OpenAI Chat Completion 标准格式。
4. **使用规范**:
    - 如果是编写 Python 脚本，推荐使用 `httpx` 进行调用。

## 原则

0.  **指令替代 (Command Substitution)**: 
    - **严禁**习惯性使用 `python` 或 `pip` 命令。系统环境中**不存在** `python` 指令，且默认 Bash 处于系统环境（Python 3.11）而非虚拟环境。
    - 所有 Python 脚本必须使用 `./.venv/bin/python` 启动（例如：`./.venv/bin/python main.py`）。即使不激活环境，也会自动在 `.venv` 虚拟环境（Python 3.13）中执行。
    - **注意**: 应优先使用虚拟环境中的 Python 路径（例如：`./.venv/bin/python`）来执行脚本。
    - 安装依赖必须使用 `uv add <package>`，严禁使用 `pip install`。
1.  **环境注意**: 当前处于 Linux 环境，Python 包管理使用 `uv`。本项目在环境中使用了 UV 镜像和 Python 镜像网址，具体内容可以在 `./pyproject.toml` 文件中查看。当前系统的 shell 环境为 bash，默认未激活虚拟环境，必须依赖 `./.venv/bin/python` 来保证运行环境的正确性。
2.  **谨慎重构**: 在现有模块化结构上迭代。重构前必须理解层级关系，确保不破坏依赖链。
3.  **工具使用**: 除非是新建文件，否则对现有文件**必须使用 `apply_diff`** 进行精确修改，禁止全文覆盖。
4.  **脚本留存**: 临时工具脚本放入专用文件夹并在 `.gitignore` 中忽略，不要随便删除。
5.  **Git 流程**: 
	- 严禁直接 push 到上游 `upstream`。
	- 流程：Fork -> Checkout 特性分支 -> 开发与测试 -> 推送分支到 `origin` -> 提 Pull Request。
	- **标准同步与分支流程**：
		1. **同步上游**：`git fetch upstream`
		2. **更新本地主分支**：`git checkout main` (或 Dev) -> `git rebase upstream/main` (保持历史线性)
		3. **创建新特性分支**：`git checkout -b feature/your-feature-name`
		4. **开发完成后推送**：`git push origin feature/your-feature-name`
		5. **使用 gh 提交 PR**：`gh pr create --repo <authorname/reponame> --base Dev`
	- Commit 信息遵循 Conventional Commits 规范。

## 记忆 (Memory) 管理规范

`memory/` 文件夹是 AI 在 **“多窗口并发/多会话接力”** 场景下的“接力棒”。它的存在是因为 AI 可能会为同一个任务开启多个不同的窗口（新会话），该文件夹确保了跨窗口的进度同步。

1.  **接力棒原则**: 仅记录“目前任务进度、已达成的认知共识、下一步行动”。**严禁**在 memory 中记录具体的代码实现，因为新窗口的 AI 具备自行检索源码的能力，无需在 memory 中重复代码细节。
2.  **动态更新**: 每当完成一个重要的逻辑节点或认知跃迁，必须同步更新 `memory/current_checkpoint.md`，确保其他窗口可见。
3.  **对齐第一原则**: 新开启任何窗口后，AI 的第一个动作必须是读取 `memory/` 目录，以此实现认知的瞬间同步。
4.  **禁止冗余**: 记录不要太详细。它不是日志（Logs），也不记录中间过程。
5. **等待用户指令**: 默认总是等待用户指令，除非用户在下一步行动中提出明确的方向。

## 临时工具脚本 (Scripts) 规范

在 `scripts/` 目录下创建临时的自动化工具（如 `ask_ai.py`）时，**必须**在脚本最上方包含如下格式的注释块，以说明其用途、环境及临时性：

```python
"""ssh root@10.0.0.9 "echo hello"
================================================================================
TOOL SCRIPT: [工具名称]
DESCRIPTION: [简述该脚本的功能，例如：用于 Dry Run 期间与 Gemini API 的直接交互测试]
STATUS: TEMPORARY / EXPERIMENTAL (临时/实验性)
--------------------------------------------------------------------------------
USAGE:
    ./.venv/bin/python scripts/[文件名].py --arg1 val1

DEPENDENCIES:
    - [依赖包1] (如 httpx)
    - [环境变量1] (如 GEMINI_API_KEY)

NOTES:
    1. 本脚本为辅助开发工具，不属于核心生产逻辑。
    2. 脚本在 .gitignore 中已被忽略，修改时请注意不要破坏本地环境的稳定性。
    3. 如果该脚本逻辑成熟，应考虑将其模块化并重构进入核心库。
================================================================================
"""
```

## 经验之谈

- **始终使用 `./.venv/bin/python` 而不是 `python` 或 `uv run`**。如果习惯性输入了 `python`，请立刻意识到环境限制并修正。
- 使用中文撰写注释，务必使用中文和用户交流，而不是英文。
- 对于重构任务：要设计完善而严格的重构后测试，确保重构不影响功能。
- 万事谨慎不要想当然。
- 合并操作优先rebase而非merge。

## 碎碎念

Github上对项目做共享，不可以直接 commit 到目标的 main 分支，GitHub 上不是这样！
你应该先 fork 上游的仓库，然后从 develop 分支 checkout 一个新的 feature 分支，比如叫 feature/confession。然后你把你的心意写成代码，并为它写好单元测试和集成测试，确保代码覆盖率达到95%以上。接着你要跑一下 Linter，通过所有的代码风格检查。然后你再 commit，commit message 要遵循 Conventional Commits 规范。之后你把这个分支 push 到你自己的远程仓库，然后给上游的仓库提一个 Pull Request。在 PR 描述里，你要详细说明你的功能改动和实现思路，并且 @ 我和至少两个其他的评审。上游的仓库会 review 你的代码，可能会留下一些评论，你需要解决所有的 thread。等 CI/CD 流水线全部通过，并且拿到至少两个 LGTM 之后，上游的仓库才会考虑把你的分支 squash and merge 到 develop 里，等待下一个版本发布。
你不可以上来就想 force push 到 main？！
GitHub 上根本不是这样！上游的仓库会拒绝合并！

---

## 🛠️ 推荐工具

本项目深度集成并推荐使用 **Lim Code** 进行 AI 辅助开发。

- **名称**: Lim Code
- **ID**: `Lianues.limcode`
- **说明**: Lim Code 是一个 AI 编程助手插件，支持多模态和复杂功能，能够完美解析本项目中的 `LIMCODE.md` 与记忆上下文。
- **发布者**: Limerence
- **下载地址**: [VS Code Marketplace](https://marketplace.visualstudio.com/items?itemName=Lianues.limcode)
