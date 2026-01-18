# 核心逻辑参数说明

本文档介绍了 `bot_agent/constants.py` 中定义的内部逻辑参数。这些参数控制着 AI 决策、记忆处理和交互频率的核心逻辑。

## 1. AI 决策相关 (LLM)

| 参数名 | 默认值 | 说明 |
| :--- | :--- | :--- |
| `DEFAULT_THINKING_BUDGET` | `128` | AI 进行“内心活动”或“决策推理”时的 Token 预算（适用于支持 Thinking 模式的模型）。 |
| `DECISION_HISTORY_LIMIT` | `50` | 在进行准入（Entry）、微观（Micro）或宏观（Macro）决策时，AI 参考的最近消息条数。 |

## 2. 交互与触发相关

| 参数名 | 默认值 | 说明 |
| :--- | :--- | :--- |
| `COMMAND_PREFIX` | `"/"` | 机器人指令的前缀（如 `/reset`, `/persona`）。 |
| `DUPLICATE_QUEUE_SIZE` | `100` | 消息去重队列的大小，用于防止重复处理同一条消息。 |
| `HISTORY_INJECT_COUNT` | `20` | 当机器人被唤醒或进入专注模式时，主动从平台拉取并注入“工作记忆”的历史消息条数。 |

## 3. 记忆与演化相关

| 参数名 | 默认值 | 说明 |
| :--- | :--- | :--- |
| `CONSOLIDATION_THRESHOLD` | `20` | [保留参数] 触发记忆归档或性格演化的消息水位阈值。 |

## 4. 社交与情感相关

| 参数名 | 默认值 | 说明 |
| :--- | :--- | :--- |
| `MAX_SOCIAL_ENERGY` | `200.0` | 社交能量的满额值。 |
| `MOOD_LABEL_MAP` | `{...}` | 心情枚举值（positive, normal, negative）对应的中文 Prompt 标签。 |

---

> **注意**：目前这些参数通过 `bot_agent/constants.py` 统一管理。如果需要通过 `agent_config.yaml` 动态配置，需在 `config_defaults.py` 中进行映射。
