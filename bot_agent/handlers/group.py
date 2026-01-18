import asyncio
import random
from ncatbot.core.event import GroupMessageEvent
from ncatbot.utils import ncatbot_config
from ncatbot.core.event.message_segment import At

from ..memory import memory_manager
from .. import config
from ..utils import get_now_timestamp, debug_print
from . import base
from .base import SessionState
from .processor import wait_and_trigger
from .processor_utils import record_session_batch, fetch_and_inject_history
from .commands import handle_commands

async def handle_group_message(event: GroupMessageEvent):
    """群聊消息处理器"""
    config.config_manager.check_and_reload()
    if not config.AI_GLOBAL_SWITCH or not config.AI_ENABLE_GROUP:
        return

    group_id = str(event.group_id)
    now = get_now_timestamp()
    
    # 1. 检查触发条件（被 @ 或提到名字）
    is_at_me = False
    bot_uin = str(ncatbot_config.bt_uin)
    for seg in event.message:
        if isinstance(seg, At) and str(seg.qq) == bot_uin:
            is_at_me = True
            break
    
    raw_msg = event.raw_message.strip()
    # 2. 获取或创建群聊状态
    if group_id not in base.user_states:
        base.user_states[group_id] = SessionState()
    state = base.user_states[group_id]

    # 3. 鉴权与过滤：Root、白名单群、处于专注模式、或触发消息
    is_root_msg = event.user_id == ncatbot_config.root
    is_whitelisted_group = event.group_id in config.GROUP_WHITELIST
    # 专注模式判断：显式专注位 或 时间窗口
    is_in_focus_window = (now - state.last_interaction_time) < config.GROUP_FOCUS_WINDOW

    # 提到名字触发 (从配置动态获取默认人格名称作为唤醒词)
    trigger_name = config.DEFAULT_PERSONA_NAME
    is_named = trigger_name.lower() in raw_msg.lower()
    should_trigger = is_at_me or is_named
    
    # 仅在提及模式下的触发逻辑修正
    if config.AI_MENTION_ONLY and not should_trigger:
        is_active = False # 即使在专注模式，如果不被提，也不活动
    else:
        is_active = is_root_msg or is_whitelisted_group or state.is_in_focus or is_in_focus_window or should_trigger
    
    if not is_active:
        return

    # 4. 初始化默认人格（如果尚未初始化）
    if group_id not in memory_manager.active_personas:
        debug_print(1, f"为新群 {group_id} 初始化默认人格: {config.DEFAULT_PERSONA_NAME}")
        memory_manager.active_personas[group_id] = config.DEFAULT_PERSONA_NAME
        memory_manager.save_active_personas()
    
    # 4.1 确保当前人格的初始特质已加载
    current_persona = memory_manager.active_personas.get(group_id, config.DEFAULT_PERSONA_NAME)
    sid = f"{group_id}:{current_persona}"
    if not memory_manager.personas.get(sid):
        from ..config import INITIAL_TRAITS
        initial_traits = INITIAL_TRAITS.get(current_persona, [])
        if initial_traits:
            memory_manager.personas[sid] = initial_traits
            memory_manager.save_persona_to_file(group_id, current_persona, initial_traits)
            debug_print(1, f"已为群 {group_id} 的人格 {current_persona} 初始化预设特质")

    # 4.5 指令处理
    if raw_msg.startswith(config.COMMAND_PREFIX):
        await handle_commands(event, group_id, raw_msg, is_group=True)
        return

    # 5. 消息去重
    if event.message_id in state.seen_messages:
        return
    state.seen_messages.add(event.message_id)
    if len(state.seen_messages) > config.DUPLICATE_QUEUE_SIZE:
        state.seen_messages.clear()

    # 6. 处理消息记录逻辑
    event.receive_time = now  # type: ignore
    
    # 决定是否记录此消息
    should_record = False
    if is_root_msg or state.is_in_focus or is_in_focus_window:
        should_record = True
    elif random.random() < config.GROUP_PASSIVE_RECORD_CHANCE:
        should_record = True
        debug_print(0, f"群聊 {group_id} 处于低专注模式，抽样记录背景消息")

    if should_record:
        # 立即记录消息，确保 AI 回复时能看到
        await record_session_batch(group_id, [event], is_group=True)

    # 7. 触发回复逻辑
    if state.is_in_focus:
        # 专注模式下，只需将消息放入队列，由 run_focus_loop 处理
        state.message_queue.append(event)
        debug_print(0, f"群聊 {group_id} 处于专注模式，消息已入队等待 5s 扫描")
    elif should_trigger:
        # 非专注模式但触发了 AI，走准入决策
        # 如果是被 @，立即尝试拉取历史上下文
        if is_at_me:
            asyncio.create_task(fetch_and_inject_history(group_id, is_group=True, count=config.HISTORY_INJECT_COUNT))
            
        state.message_queue.append(event)
        if state.timer_task:
            state.timer_task.cancel()
        state.timer_task = asyncio.create_task(wait_and_trigger(group_id, is_group=True))
    else:
        # 非触发消息，如果是记录的消息且不在专注模式，累加计数尝试自动插话
        if should_record:
            state.passive_count += 1
            if state.passive_count >= config.GROUP_PASSIVE_SAMPLING_THRESHOLD:
                debug_print(1, f"群聊 {group_id} 背景消息累计达标，触发插话决策")
                state.passive_count = 0
                
                # 在触发插话决策前，主动拉取历史上下文
                asyncio.create_task(fetch_and_inject_history(group_id, is_group=True, count=config.HISTORY_INJECT_COUNT))
                
                state.message_queue.append(event)
                if state.timer_task:
                    state.timer_task.cancel()
                state.timer_task = asyncio.create_task(wait_and_trigger(group_id, is_group=True, is_auto_trigger=True))
