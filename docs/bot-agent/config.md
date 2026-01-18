# 配置说明

Bot Agent 的配置由框架基础配置、逻辑配置和环境变量组成。

## 框架基础配置 (`config.yaml`)

这是 `ncatbot` 基础框架的配置文件，主要用于定义机器人的身份。

- `bt_uin`: 机器人的 QQ 号。
- `root`: 管理员（开发者）的 QQ 号，用于执行管理指令。
- `napcat`: 定义与 NapCat 的连接方式（WebSocket 地址及 Token）。

## 逻辑配置 (`agent_config.yaml`)

这是机器人的主配置文件。**在程序首次启动时，系统会自动根据默认值生成该文件。**

你可以参考 `agent_config.example.yaml` 进行手动配置。

### 核心配置项
- **memory**: 控制对话历史的高水位线和压缩策略。
- **interaction**: 设置不同场景下的响应延迟、白名单以及默认人格。
  - `enable_social_energy`: 是否启用社交能量模块。**注：该模块目前处于实验性阶段，功能逻辑尚不完善，设计意图不清晰，建议保持关闭。**
  - `enable_topic_detection`: [实验功能] 是否启用话题检测。**注：该功能设计的并不好，目的不清晰，功能不完善，建议保持关闭。**
- **ai**: 全局开关、是否仅响应艾特、是否显示思考过程等。
- **persona_definitions**: 定义不同人格的背景设定。
- **initial_traits**: 定义各人格的初始性格特质。

## 环境变量与 `.env`

项目支持通过 `.env` 文件管理敏感信息。你可以通过复制 `.env.example` 并重命名为 `.env` 来开始配置。

- `GEMINI_API_KEY`: API 访问凭据（必需）。
- `GEMINI_URL`: 自定义 API 请求地址（可选）。

## 全局常量与默认值

默认配置定义在 `bot_agent/config_defaults.py` 中。
- **防抖延迟**: `response_wait_time` (私聊), `group_response_wait_time` (群聊)。
- **归档阈值**: `high_watermark` (达到此消息数量触发压缩总结)。
- **社交能量**: `MAX_SOCIAL_ENERGY` 等参数在 `bot_agent/constants.py` 中定义。

## 提示词配置 (`data/prompts.json`)

系统内置了多套提示词模板，可以通过管理后台实时修改：
- `system_prompt`: 总系统提示词。
- `entry_decision`: 准入决策提示词。
- `personality_evolution`: 人格演化提示词。
- `impression_evolution`: 印象演化提示词。
- `memory_consolidation`: 记忆总结提示词。

## 环境变量

- `GEMINI_API_KEY`: API 访问凭据。
- `GEMINI_URL`: 可选，自定义的 API 代理地址。
