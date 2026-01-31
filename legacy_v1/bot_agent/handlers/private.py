import asyncio
from ncatbot.core.event import PrivateMessageEvent
from ncatbot.utils import ncatbot_config

from ..memory import memory_manager
from .. import config
from ..utils import get_now_timestamp, debug_print
from . import base
from .base import SessionState
from .processor import wait_and_trigger
from .processor_utils import record_session_batch
from .commands import handle_commands
from .link_utils.card_shortener import try_extract_and_shorten_bilibili_from_event

async def handle_private_message(event: PrivateMessageEvent):
    """私聊消息处理器"""
    config.config_manager.check_and_reload()
    if not config.AI_GLOBAL_SWITCH or not config.AI_ENABLE_PRIVATE:
        return

    # 鉴权：root 或在白名单中（root 默认视为白名单成员）
    is_root = event.user_id == ncatbot_config.root
    is_whitelisted = is_root or (str(event.user_id) in {str(u) for u in config.WHITELIST})
    
    if not is_whitelisted:
        return

    user_id = str(event.user_id)
    raw_msg = event.raw_message.strip()
    
    # 初始化新用户的默认人格
    if user_id not in memory_manager.active_personas:
        debug_print(1, f"为新用户 {user_id} 初始化默认人格: {config.DEFAULT_PERSONA_NAME}")
        memory_manager.active_personas[user_id] = config.DEFAULT_PERSONA_NAME
        memory_manager.save_active_personas()
        
    # 确保当前人格的初始特质已加载
    current_persona = memory_manager.active_personas.get(user_id, config.DEFAULT_PERSONA_NAME)
    sid = f"{user_id}:{current_persona}"
    if not memory_manager.personas.get(sid):
        from ..config import INITIAL_TRAITS
        initial_traits = INITIAL_TRAITS.get(current_persona, [])
        if initial_traits:
            memory_manager.personas[sid] = initial_traits
            memory_manager.save_persona_to_file(user_id, current_persona, initial_traits)
            debug_print(1, f"已为用户 {user_id} 的人格 {current_persona} 初始化预设特质")

    # 1. 指令处理
    if raw_msg.startswith(config.COMMAND_PREFIX):
        await handle_commands(event, user_id, raw_msg, is_group=False)
        return

    # 1.1 私聊：B 站卡片/链接提取服务（与 AI 功能解耦）
    # - 私聊默认开启（但仍受 whitelist/root 鉴权约束）
    # - 为了降噪：仅在消息里出现 Json/XML/Share 段，或文本里明确包含 b23/bilibili 时才尝试解析
    if config.BILIBILI_LINK_EXTRACT_PRIVATE:
        has_card_seg = any(seg.msg_seg_type in ("json", "xml", "share") for seg in event.message)
        has_hint = ("b23.tv" in raw_msg) or ("bilibili.com" in raw_msg) or ("[CQ:json" in raw_msg) or ("[CQ:xml" in raw_msg)
        if has_card_seg or has_hint:
            short = try_extract_and_shorten_bilibili_from_event(event)
            if short:
                debug_print(1, f"私聊检测到B站卡片/链接，提取链接: {short}")
                # ncatbot 的私聊 reply 不支持 at 参数
                await event.reply(text=short)
                return

    # 2. 获取或创建用户状态
    if user_id not in base.user_states:
        base.user_states[user_id] = SessionState()
    state = base.user_states[user_id]

    # 2.5 消息去重
    if event.message_id in state.seen_messages:
        return
    state.seen_messages.add(event.message_id)
    if len(state.seen_messages) > config.DUPLICATE_QUEUE_SIZE:
        state.seen_messages.clear()

    # 3. 消息记录与入队
    event.receive_time = get_now_timestamp()  # type: ignore
    await record_session_batch(user_id, [event], is_group=False)
    state.message_queue.append(event)
    
    # 4. 触发回复逻辑 (私聊不使用专注模式)
    if state.timer_task:
        state.timer_task.cancel()
    state.timer_task = asyncio.create_task(wait_and_trigger(user_id))
