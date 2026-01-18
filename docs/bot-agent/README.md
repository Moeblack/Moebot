# Bot Agent

Bot Agent 是一个基于 NcatBot 的智能机器人框架，具备自进化人格、分层记忆管理、主动社交决策和可视化监控后台。

## 核心特性

- **分层记忆系统**: 包含工作记忆 (Working Memory) 和情节记忆 (Episodic Memory)，支持潮汐归档机制。
- **自进化人格**: AI 会根据交互历史自动演化性格特质 (Traits) 和对用户的印象 (Impressions)。
- **智能社交决策**: 具备主动介入对话、节能观察模式以及社交能量 (Social Energy) 管理。
- **XML 架构**: 采用高度结构化的 XML 标签进行 Prompt 组装，确保 AI 认知的稳定性和可追溯性。
- **管理后台**: 提供实时的 AI 交互监控、配置管理、记忆编辑和提示词调试功能。

## 快速开始

1. **环境准备**:
   由于 `ncatbot` 框架更新频繁且依赖特定源，**请务必使用以下命令进行安装或更新**（限定使用该镜像源）：
   ```bash
   pip install ncatbot -U -i https://mirrors.aliyun.com/pypi/simple/
   ```
   随后安装其他必要依赖：
   ```bash
   pip install -r requirements.txt
   ```
2. **配置 API 与 身份**: 
   - 复制 `.env.example` 为 `.env`，填入你的 `GEMINI_API_KEY`。
   - 复制 `config.example.yaml` 为 `config.yaml`，填入你的机器人 QQ 号 (`bt_uin`) 和管理员 QQ 号 (`root`)。
3. **运行**:
   ```bash
   python main.py
   ```
   首次运行将自动生成 `agent_config.yaml`（Agent 逻辑配置）。

## 目录结构

- [架构概览](./architecture.md)
- [记忆系统](./memory.md)
- [处理器与决策](./handlers.md)
- [监控与管理后台](./monitor.md)
- [配置说明](./config.md)
