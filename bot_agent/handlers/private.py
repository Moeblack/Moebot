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

async def handle_private_message(event: PrivateMessageEvent):
    """私聊消息处理器"""
    config.config_manager.check_and_reload()
    if not config.AI_GLOBAL_SWITCH or not config.AI_ENABLE_PRIVATE:
        return

    # 鉴权：root 或在白名单中
    is_root = event.user_id == ncatbot_config.root
    is_whitelisted = event.user_id in config.WHITELIST
    
    if not (is_root or is_whitelisted):
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
