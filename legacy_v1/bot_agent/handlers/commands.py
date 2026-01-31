import re
import os
import json
from typing import Union
from ncatbot.core.event import PrivateMessageEvent, GroupMessageEvent
from ncatbot.utils import ncatbot_config

from ..memory import memory_manager
from .. import config
from . import base


async def _clear_session_from_files(session_id: str):
    """从持久化文件中清除指定会话的记录"""
    data_dir = "data"
    files_to_filter = ["chat_history.jsonl", "episodic_memory.jsonl"]
    
    for fname in files_to_filter:
        fpath = os.path.join(data_dir, fname)
        if not os.path.exists(fpath):
            continue
        
        kept = []
        with open(fpath, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                    if record.get("session_id") != session_id:
                        kept.append(line)
                except json.JSONDecodeError:
                    kept.append(line)
        
        with open(fpath, 'w', encoding='utf-8') as f:
            f.writelines(kept)
    
    # 清理 memory_state.json 中该会话的计数器
    state_file = os.path.join(data_dir, "memory_state.json")
    if os.path.exists(state_file):
        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            # 从各计数器中移除该会话
            for key in ["evolution_pity_counter", "unconsolidated_count", "current_topics"]:
                if key in state and session_id in state[key]:
                    del state[key][session_id]
            
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except (json.JSONDecodeError, IOError):
            pass  # 文件损坏时忽略


async def _clear_all_files():
    """清空所有记忆持久化文件"""
    data_dir = "data"
    files_to_clear = ["chat_history.jsonl", "episodic_memory.jsonl"]
    
    for fname in files_to_clear:
        fpath = os.path.join(data_dir, fname)
        if os.path.exists(fpath):
            open(fpath, 'w').close()  # 清空文件
    
    # 重置状态文件
    state_file = os.path.join(data_dir, "memory_state.json")
    if os.path.exists(state_file):
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump({"evolution_pity_counter": {}, "unconsolidated_count": {}, "current_topics": {}}, f, ensure_ascii=False)

async def handle_commands(event: Union[PrivateMessageEvent, GroupMessageEvent], session_id: str, raw_msg: str, is_group: bool = False):
    """指令处理器"""
    if base._bot is None:
        return
    bot = base._bot
    
    is_root = event.user_id == ncatbot_config.root
    
    # 定义发送消息的辅助函数
    async def send_reply(text: str):
        if is_group and isinstance(event, GroupMessageEvent):
            await bot.api.send_group_msg(group_id=event.group_id, message=[{"type": "text", "data": {"text": text}}])
        else:
            await bot.api.send_private_msg(user_id=event.user_id, message=[{"type": "text", "data": {"text": text}}])

    if raw_msg.startswith("/persona"):
        # 仅限私聊 owner 或 root 
        if is_group and not is_root:
            return
        
        parts = raw_msg.split(maxsplit=3)
        cmd = parts[1] if len(parts) > 1 else ""
        
        if cmd == "list":
            user_p_names = [sid.split(":")[1] for sid in memory_manager.personas if sid.startswith(f"{session_id}:")]
            for sid in memory_manager.chat_history:
                if sid.startswith(f"{session_id}:"):
                    name = sid.split(":")[1]
                    if name not in user_p_names:
                        user_p_names.append(name)
            
            active = memory_manager.active_personas.get(session_id, config.DEFAULT_PERSONA_NAME)
            reply = f"当前激活人格: {active}\n已有人格列表: " + (", ".join(user_p_names) if user_p_names else config.DEFAULT_PERSONA_NAME)
            await send_reply(reply)
            return

        if cmd == "switch":
            if len(parts) < 3:
                await send_reply("用法: /persona switch <人格名称>")
                return
            name = parts[2]
            memory_manager.active_personas[session_id] = name
            memory_manager.save_active_personas()
            await send_reply(f"已切换到人格: {name}。该人格拥有独立的记忆。")
            return

        if cmd == "init":
            if len(parts) < 3:
                await send_reply("用法: /persona init <人格名称> [初始人格色彩描述]")
                return
            name = parts[2]
            traits_str = parts[3] if len(parts) > 3 else "一张白纸，没有任何预设性格。"
            traits = [t.strip() for t in re.split(r'[，。；,;.]', traits_str) if t.strip()]
            sid = f"{session_id}:{name}"
            memory_manager.personas[sid] = traits
            memory_manager.save_persona_to_file(session_id, name, traits)
            memory_manager.active_personas[session_id] = name
            memory_manager.save_active_personas()
            await send_reply(f"人格 '{name}' 已初始化完成并切换为当前活跃人格。")
            return

    if raw_msg.startswith("/debug"):
        if not is_root:
            return
        
        parts = raw_msg.split()
        sub_cmd = parts[1] if len(parts) > 1 else ""
        
        # 优先级 1: 检查是否直接带了表情 (Face)
        from ncatbot.core.event.message_segment import Face
        faces = [seg for seg in event.message if isinstance(seg, Face)]
        if faces:
            target_face = faces[0]
            await send_reply(f"[Debug] 检测到表情 ID: {target_face.id}")
            return

        # 优先级 2: 处理带子命令的 /debug
        if sub_cmd == "consolidate":
            persona_name = memory_manager.active_personas.get(session_id, config.DEFAULT_PERSONA_NAME)
            full_session_id = f"{session_id}:{persona_name}"
            res = await memory_manager.manual_consolidate(full_session_id)
            unconsolidated = memory_manager.unconsolidated_count.get(full_session_id, 0)
            await send_reply(f"[Debug] {res}\n当前未归档计数: {unconsolidated}")
            return

        if sub_cmd == "emoji":
            if len(parts) >= 3:
                eid_str = parts[2]
                try:
                    msg = [
                        {"type": "text", "data": {"text": f"[Debug] ID {eid_str} 对应的表情是: "}},
                        {"type": "face", "data": {"id": eid_str}}
                    ]
                    if is_group and isinstance(event, GroupMessageEvent):
                        await bot.api.send_group_msg(group_id=event.group_id, message=msg)
                    else:
                        await bot.api.send_private_msg(user_id=event.user_id, message=msg)
                except Exception as e:
                    await send_reply(f"[Debug] 测试失败: {e}")
            else:
                await send_reply("用法: /debug emoji <id>")
            return
        
        # 优先级 3: 显示最近决策信息
        state = base.user_states.get(session_id)
        if state and state.last_decision:
            d = state.last_decision
            reply = (
                f"[最近决策信息]\n"
                f"表情 ID: {d.get('emoji_id')}\n"
                f"回复决策: {'是' if d.get('reply') else '否'}\n"
                f"撤回决策: {'是' if d.get('withdraw_emoji') else '否'}\n"
                f"决策原因: {d.get('reason')}"
            )
        else:
            reply = "[Debug] 暂无最近决策记录。"
        await send_reply(reply)
        return

    if raw_msg.startswith("/memory"):
        # 仅限 root 使用
        if not is_root:
            return
        
        parts = raw_msg.split()
        sub_cmd = parts[1] if len(parts) > 1 else ""
        
        if sub_cmd == "list":
            # 列出所有会话
            sessions = list(memory_manager.chat_history.keys())
            if sessions:
                reply = f"当前活跃会话 ({len(sessions)}):\n" + "\n".join(f"  - {s}" for s in sessions)
            else:
                reply = "暂无活跃会话"
            await send_reply(reply)
            return
        
        if sub_cmd == "clear":
            # 清除当前会话的记忆
            persona_name = memory_manager.active_personas.get(session_id, config.DEFAULT_PERSONA_NAME)
            full_sid = f"{session_id}:{persona_name}"
            hard_mode = "--hard" in parts
            
            # 清除内存
            if full_sid in memory_manager.chat_history:
                memory_manager.chat_history[full_sid] = []
            if full_sid in memory_manager.episodic_memory:
                memory_manager.episodic_memory[full_sid] = []
            
            result = f"[Memory] 已清除 {full_sid} 的内存记忆"
            
            if hard_mode:
                # 硬重置：同时清除文件
                await _clear_session_from_files(full_sid)
                result += "\n[Memory] 已从持久化文件中移除该会话记录"
            else:
                result += "\n(软重置，重启后会从文件恢复。使用 --hard 彻底清除)"
            
            await send_reply(result)
            return
        
        if sub_cmd == "clear-all":
            # 清除所有会话的记忆
            hard_mode = "--hard" in parts
            count = len(memory_manager.chat_history)
            
            # 清除内存
            memory_manager.chat_history.clear()
            memory_manager.episodic_memory.clear()
            
            result = f"[Memory] 已清除所有 {count} 个会话的内存记忆"
            
            if hard_mode:
                await _clear_all_files()
                result += "\n[Memory] 已清空所有持久化文件"
            else:
                result += "\n(软重置，重启后会从文件恢复。使用 --hard 彻底清除)"
            
            await send_reply(result)
            return
        
        # 默认显示帮助
        help_text = """记忆管理指令 (仅 Root):
/memory list - 列出所有活跃会话
/memory clear - 清除当前会话的记忆（软重置）
/memory clear --hard - 彻底清除当前会话（含文件）
/memory clear-all - 清除所有会话（软重置）
/memory clear-all --hard - 彻底清除所有会话（含文件）"""
        await send_reply(help_text)
        return

    if raw_msg.startswith("/help"):
        # 群聊仅限 root，私聊 OK (已经通过 handler 隔离了 owner)
        if is_group and not is_root:
            return
            
        help_msg = """系统指令说明：
/persona list - 查看已有人格列表
/persona switch <名称> - 切换人格
/persona init <名称> [描述] - 初始化并切换到新人格
/debug - 查看最近一次交互的决策信息 (Root)
/debug emoji <id> - 测试特定表情 ID (Root)
/memory - 记忆管理指令 (Root)
/help - 显示此帮助信息"""
        await send_reply(help_msg)
        return
