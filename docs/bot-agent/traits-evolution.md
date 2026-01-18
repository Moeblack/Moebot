---
title: Traits 演进机制
createTime: 2025/01/18 12:45:00
permalink: /notes/bot-agent/traits-evolution/
---

# Traits 演进机制

本文档描述 Bot Agent 中「自进化人格系统」的完整运作流程，以及当前存在的**正反馈偏差问题**和可能的解决方案。

## 一、系统架构概览

```
┌─────────────────────────────────────────────────────────────────────┐
│                           Bot Agent                                  │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐        │
│  │   Prompt     │────▶│     LLM      │────▶│   Response   │        │
│  │   Builder    │     │   (Gemini)   │     │   Handler    │        │
│  └──────────────┘     └──────────────┘     └──────────────┘        │
│         ▲                                         │                 │
│         │                                         ▼                 │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │                    Memory Manager                         │      │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐          │      │
│  │  │ Chat       │  │ Episodic   │  │ Personas   │          │      │
│  │  │ History    │  │ Memory     │  │ (Traits)   │          │      │
│  │  └────────────┘  └────────────┘  └────────────┘          │      │
│  │  ┌────────────┐  ┌────────────┐                          │      │
│  │  │ Impressions│  │ Social     │                          │      │
│  │  │            │  │ Energy     │                          │      │
│  │  └────────────┘  └────────────┘                          │      │
│  └──────────────────────────────────────────────────────────┘      │
│                              │                                      │
│                              ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │                  Evolution Engine                         │      │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐          │      │
│  │  │ Consolidate│  │ Evolve     │  │ Evolve     │          │      │
│  │  │ Memory     │  │ Personality│  │ Impression │          │      │
│  │  └────────────┘  └────────────┘  └────────────┘          │      │
│  └──────────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────┘
```

## 二、数据流与触发条件

### 2.1 消息处理流程

```
用户消息 → 记录到 chat_history → unconsolidated_count++
                                        │
                                        ▼
                              count >= HIGH_WATERMARK (50)?
                                        │
                               Yes ─────┴───── No
                                │               │
                                ▼               ▼
                        触发 consolidate    继续等待
```

### 2.2 归档与演进触发

当 `unconsolidated_count >= 50` 时，触发 `consolidate_memory_logic`：

```python
# consolidation.py 核心逻辑

# 1. 先做情节摘要
summary = await get_json_response(narrative_summary_prompt)
episodic_memory.append({"summary": summary, "time": episode_time})

# 2. 抽卡决定是否演进
evolution_pity_counter[session_id] += 1
count = evolution_pity_counter[session_id]

if count <= 8:
    chance = 0.05      # 前8次：5%概率
elif count <= 12:
    chance = 0.05 + (count - 8) * 0.2  # 9-12次：逐渐增加
else:
    chance = 1.0       # 第13次：保底触发

if force_evolve or ai_wants_evolve or random.random() < chance:
    # 触发人格演进
    asyncio.create_task(evolve_personality(...))
    # 触发印象演进  
    asyncio.create_task(evolve_impression(...))
    evolution_pity_counter[session_id] = 0  # 重置计数器
```

## 三、Traits 演进的具体实现

### 3.1 输入：待分析的消息

```python
# evolution.py - evolve_personality()

content_str = ""
for m in messages_to_analyze:
    role = m.get('role', 'assistant')
    if role == 'assistant':
        name = "AI(assistant)"        # ⚠️ 问题点：AI自己的发言也被分析
    else:
        nick = m.get('nickname', '未知')
        uid = m.get('user_id') or 'unknown'
        name = f"{nick}({uid})"
    content_str += f"[{m.get('time')}] {name}: {m['content']}\n"
```

### 3.2 Prompt 模板

```python
# prompt_defaults.py

"personality_evolution": """
角色A已知的行为特征：
{current_traits}

最近对话：
{content_str}

任务：这段对话里有没有体现出新的行为特征？
- 只输出新的，已有的不要重复
- 没有新发现就输出空列表
- 每条10字以内，只写具体行为，不写抽象概念
"""
```

### 3.3 输出：新特征合并

```python
# evolution.py

result = await get_json_response(prompt, '{ "new_traits": [...] }')

if result and "new_traits" in result:
    new = result["new_traits"]
    combined = current_traits + [t for t in new if t not in current_traits]
    
    # 超过25条时触发整理
    if len(combined) > 25:
        combined = await consolidate_traits_logic(combined, "personality")
    
    personas[session_id] = combined
    save_persona_func(user_id, persona_name, combined)
```

### 3.4 Traits 被注入到 Prompt

```python
# prompt.py - build_prompt()

traits_list = personas.get(session_id, [])
base_identity = BASE_PERSONA_CONFIG.get(persona_name)

persona_text = f"核心身份：{base_identity}\n行为特征：" + "；".join(traits_list)

# 最终被包裹在 <personality> 标签中
prompt_parts.append(config["personality"].format(persona_text=persona_text))
```

## 四、⚠️ 正反馈偏差问题

### 4.1 问题描述

```
┌─────────────────────────────────────────────────────────────────┐
│                     正反馈循环                                   │
│                                                                 │
│   ┌──────────┐      ┌──────────┐      ┌──────────┐             │
│   │ AI 发言  │─────▶│ 被记录到 │─────▶│ 演进分析 │             │
│   │ (自嘲)   │      │ 聊天历史 │      │ 提取特征 │             │
│   └──────────┘      └──────────┘      └──────────┘             │
│        ▲                                    │                   │
│        │                                    ▼                   │
│        │                            ┌──────────┐               │
│        │                            │ 记录为   │               │
│        │                            │"喜欢自嘲"│               │
│        │                            └──────────┘               │
│        │                                    │                   │
│        │                                    ▼                   │
│   ┌──────────┐      ┌──────────┐      ┌──────────┐             │
│   │ 生成更多 │◀─────│ Prompt   │◀─────│ Traits   │             │
│   │ 自嘲内容 │      │ 注入特征 │      │ 被强化   │             │
│   └──────────┘      └──────────┘      └──────────┘             │
│                                                                 │
│   结果：微小偏差被无限放大，AI 风格逐渐极端化                    │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 根本原因

| 问题 | 描述 |
|------|------|
| **输入源污染** | 演进分析的输入包含 AI 自己的发言（`role == 'assistant'`） |
| **无负反馈** | 系统只会「发现新特征」，不会「删除/弱化旧特征」 |
| **衰减缺失** | Traits 一旦记录，永久存在（除非超过25条被整理） |
| **外部验证缺失** | 没有「用户反馈」来验证某个特征是否受欢迎 |

## 五、解决方案设计

### 方案 A：输入源分离（推荐）

**核心思想**：演进分析时，只分析用户的发言，不分析 AI 自己的输出。

```python
# evolution.py - 修改后

content_str = ""
for m in messages_to_analyze:
    role = m.get('role', 'assistant')
    if role == 'assistant':
        continue  # ✅ 跳过 AI 自己的发言
    # ... 只记录用户发言
```

**优点**：最小改动，直接打破正反馈循环  
**缺点**：无法捕捉「AI 在互动中展现的风格」

---

### 方案 B：双轨制 + 比例控制

**核心思想**：将 Traits 分为「核心层」和「演化层」，权重不同。

```yaml
# 数据结构
personas:
  session_id:
    core_traits:     # 预设，永不变，权重 70%
      - "群里普通一员"
      - "喜欢 Steam 单机"
    evolved_traits:  # 动态演化，权重 30%，有上限
      - "偶尔自嘲"
```

```python
# prompt.py - 修改后

core = personas.get(session_id, {}).get("core_traits", [])
evolved = personas.get(session_id, {}).get("evolved_traits", [])

persona_text = f"""
核心身份（固定）：{"；".join(core)}
观察到的行为倾向（仅供参考）：{"；".join(evolved)}
"""
```

**优点**：核心人设稳定，演化部分有限度  
**缺点**：需要重构数据结构

---

### 方案 C：置信度衰减 + 外部强化

**核心思想**：每个 trait 带有置信度分数，随时间衰减，只有用户正向反馈才能加分。

```json
{
  "trait": "喜欢自嘲",
  "confidence": 0.6,
  "last_reinforced": "2025-01-17T12:00:00Z"
}
```

**规则**：
- 置信度每天自然 `-0.05`
- 用户表现出正向反馈（复读、点赞、热烈回应）时 `+0.1`
- **AI 自己的行为不能给自己加分**
- 置信度 `< 0.3` 时自动移除

**优点**：最符合「演化」的本意  
**缺点**：实现复杂，需要检测「用户反馈」

---

### 方案 D：对抗性演进

**核心思想**：在演进 Prompt 中加入对抗性指令。

```python
"personality_evolution": """
...

【对抗性要求】：
1. 优先寻找与【当前已有特质】相反的证据
2. 如果某个特质已经存在，需要更高的阈值才能强化
3. 优先发现【新的、不同的】特质，而非强化已有的
"""
```

**优点**：不改数据结构  
**缺点**：依赖 LLM 遵循指令的能力

---

## 六、推荐组合方案

结合以上思路，推荐采用 **「A + B + 简化版C」组合**：

| 层级 | 内容 | 特点 |
|------|------|------|
| **核心层** | 预设 traits（用户在 `agent_config.yaml` 定义） | 永不变，权重 70% |
| **演化层** | 动态 traits（AI 分析用户行为得出） | 有上限（5条），权重 30% |
| **输入源** | 只分析用户发言，不看 AI 输出 | 打破正反馈循环 |
| **衰减** | 超过 7 天未被触及的演化 trait 自动移除 | 简化版衰减 |

```python
# 示意代码

class TraitsManager:
    def __init__(self):
        self.core_traits = {}      # 从 agent_config.yaml 加载
        self.evolved_traits = {}   # 动态演化，每个 session 最多 5 条
        self.last_seen = {}        # 记录每条 trait 最后被「触及」的时间
    
    def evolve(self, session_id, user_messages):  # 注意：只传用户消息
        # ... 分析用户行为，提取特征
        pass
    
    def build_persona_text(self, session_id):
        core = self.core_traits.get(session_id, [])
        evolved = self.evolved_traits.get(session_id, [])
        
        # 过滤掉超过 7 天的
        evolved = [t for t in evolved if not self._is_stale(t)]
        
        return f"""
核心身份：{"；".join(core)}
近期观察：{"；".join(evolved) if evolved else "暂无"}
"""
```

## 七、当前代码位置索引

| 文件 | 作用 |
|------|------|
| `bot_agent/memory/evolution.py` | Traits 和 Impression 演进逻辑 |
| `bot_agent/memory/consolidation.py` | 归档触发和概率控制 |
| `bot_agent/memory/prompt.py` | Prompt 组装，注入 Traits |
| `bot_agent/memory/prompt_defaults.py` | Prompt 模板默认值 |
| `bot_agent/memory/manager.py` | 记忆管理器，协调各模块 |
| `data/personas.jsonl` | Traits 持久化存储 |
| `data/prompts.json` | Prompt 模板（可编辑覆盖默认值） |
| `agent_config.yaml` | 核心人格定义 |
