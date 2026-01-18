# 架构概览

Bot Agent 采用模块化设计，旨在通过清晰的职责分离提高系统的可维护性和 AI 辅助开发的效率。

## 目录结构

```text
bot_agent/
├── handlers/          # 核心业务处理逻辑
│   ├── base.py        # 基础状态定义
│   ├── processor.py   # 消息流处理器（防抖与调度）
│   ├── decisions.py   # 准入决策逻辑（是否回复、是否关注）
│   ├── reply.py       # 回复生成逻辑
│   └── ...            # 其他辅助处理模块
├── memory/            # 记忆与人格系统
│   ├── manager.py     # 记忆管理器总控
│   ├── persistence.py # 持久化处理
│   ├── logic.py       # 记忆整合与演化逻辑总控
│   ├── prompt.py      # Prompt 组装逻辑
│   └── ...            # 社交能量与 Prompt 默认值
├── monitor.py         # 监控日志记录（SQLite 写入）
├── monitor_query.py   # 监控日志查询
├── config.py          # 全局配置管理（支持动态加载与持久化）
└── llm.py             # LLM 接口层 (Gemini)
```

## 核心工作流

### 1. 决策流程建模 (Decision Workflow)
机器人的决策行为根据聊天类型（私聊/群聊）有显著差异：

- **群聊 (Group)**: 采用“三级过滤”机制（准入决策 -> 微观决策 -> 宏观决策），以模拟人类在群组中的社交带宽管理。
- **私聊 (Private)**: 直接进入即时决策，无需判断插话时机。

```mermaid
graph TD
    A[收到新消息] --> B{防抖处理 Debounce}
    B --> C{聊天类型?}
    
    subgraph Group_Decision_Path [群聊决策路径]
        C -- 群聊 --> D[准入决策 Entry Decision]
        D --> D1{是否回复?}
        D1 -- 否 --> D2[静默观察/记录]
        D1 -- 是 --> D3[执行回复]
        D3 --> D4[启动专注模式]
        D4 --> E[微观决策 Micro Decision]
        E --> E1{5s 无消息?}
        E1 -- 否 --> E2[判断是否立即插话]
        E1 -- 是 --> E
        D4 --> F[宏观决策 Macro Decision]
        F --> F1{60s 评估}
        F1 -- 话题结束 --> G[退出专注/进入被动模式]
        F1 -- 继续 --> F
    end

    subgraph Private_Decision_Path [私聊决策路径]
        C -- 私聊 --> P1[即时回复决策]
        P1 --> P2[执行回复]
    end
```

### 2. AI 回复建模 (AI Response Modeling)
不论何种决策路径，最终生成回复的流程是一致的。回复包含多模态处理（图片压缩）、情感状态同步和社交能量消耗。

```mermaid
sequenceDiagram
    participant P as Processor
    participant M as MemoryManager
    participant L as LLM (Gemini)
    participant B as Bot API

    P->>M: 请求生成 Prompt
    M->>M: 组装 XML (人格+记忆+印象+能量)
    M-->>P: 返回 Full Prompt
    P->>P: 处理图片 (WEBP 压缩)
    P->>L: 发送请求 (JSON Mode)
    L-->>P: 返回 {thought, replies, mood, energy_adj}
    P->>M: 同步心情 (mood) & 更新话题
    P->>M: 扣除社交能量 (energy_adj)
    loop 逐条回复
        P->>B: 发送消息/表情
        P->>M: 消息持久化 (History Storage)
    end
    P->>M: 触发水位线检查 (High Watermark)
```

### 3. AI 自动更新建模 (Evolution Modeling)
当对话积累到一定量时，机器人会分析交互并自动生成新的性格特质或对用户的印象。

```mermaid
graph LR
    A[归档触发] --> B[叙事总结 Narrative Summary]
    B --> C{演化抽卡 Pity Mechanism}
    C -- 触发演化 --> D[人格演化分析]
    C -- 触发演化 --> E[用户/群聊印象分析]
    C -- 跳过 --> F[仅完成基础归档]

    subgraph Analysis
        D --> D1[提取对话特征]
        D1 --> D2[合并/抽象新 Trait]
        E --> E1[分析用户行为模式]
        E1 --> E2[更新 Impression 标签]
    end

    D2 & E2 --> G[持久化到 personas/impressions.jsonl]
    G --> H[下次对话加载新特质]
```

### 4. 记忆维持建模 (Memory Maintenance)
采用“潮汐归档”机制，通过工作记忆与情节记忆的分层来处理长文本。

```mermaid
graph TD
    subgraph Working_Memory
        A[实时消息队列] -->|持久化| B[JSONL 文件存储]
        B -->|加载| C[内存 History List]
    end

    C -->|消息数 > High Watermark| D{归档 Consolidation}
    
    subgraph Long_Term_Memory
        D -->|LLM 总结成一段话| E[情节记忆 Episodic Memory]
        E -->|按条存入| F[episodic_memory.jsonl]
    end

    D -->|清理已归档部分| C
    F -->|Prompt 组装时| G[提取最近的情节记忆]
    C -->|Prompt 组装时| H[提取最近的对话原文]
```

## 设计原则

- **XML 语义化**: 所有的 Prompt 部分（人格、历史、情节记忆）均包裹在显式的 XML 标签中。
- **状态持久化**: 机器人重启后能恢复所有运行状态、社交能量和人格进度。
- **非阻塞 I/O**: 充分利用 `asyncio` 确保高并发场景下的响应性能。
