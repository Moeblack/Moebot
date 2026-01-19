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
from .link_utils.card_shortener import try_extract_and_shorten_bilibili_from_event

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
    # 兼容配置里群号是 int 或 str 的情况
    is_whitelisted_group = str(event.group_id) in {str(g) for g in config.GROUP_WHITELIST}
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
        # 指令也需要鉴权：只有 root 或白名单群允许
        if is_root_msg or is_whitelisted_group:
            await handle_commands(event, group_id, raw_msg, is_group=True)
        return

    # 4.6 B站链接提取服务（与 AI 功能解耦，独立鉴权）
    if str(event.group_id) in {str(g) for g in config.BILIBILI_LINK_EXTRACT_GROUPS}:
        short = try_extract_and_shorten_bilibili_from_event(event)
        if short:
            await event.reply(text=short, at=False)
            return

    # --- AI 准入鉴权 ---
    # 只有 Root 消息或白名单群才允许继续 AI 逻辑
    if not (is_root_msg or is_whitelisted_group):
        return

    # 仅在提及模式下的触发逻辑修正
    if config.AI_MENTION_ONLY and not should_trigger:
        is_active = False 
    else:
        # 此时已知是在白名单或 Root，只要满足触发条件或处于专注状态即活跃
        is_active = state.is_in_focus or is_in_focus_window or should_trigger or is_root_msg
    
    if not is_active:
        return
