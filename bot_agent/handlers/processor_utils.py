from typing import Union
from ncatbot.core.event import PrivateMessageEvent, GroupMessageEvent
from ncatbot.core.event.message_segment import Image, Text, At, Face, PlainText, AtAll, Reply
from ncatbot.utils import ncatbot_config
from ..memory import memory_manager
from .. import config
from ..utils import format_timestamp
from ..monitor import record_user_activity

def parse_event_message(event: Union[PrivateMessageEvent, GroupMessageEvent], bot_uin: str) -> str:
    """解析消息事件中的消息段，转换为文本描述"""
    content_parts = []
    for seg in event.message:
        if isinstance(seg, (Text, PlainText)):
            content_parts.append(seg.text)
        elif isinstance(seg, Image):
            content_parts.append("[图片]")
        elif isinstance(seg, Face):
            content_parts.append(f"(face:{seg.id})")
        elif isinstance(seg, At):
            content_parts.append("@assistant " if str(seg.qq) == bot_uin else f"@{seg.qq} ")
        elif isinstance(seg, AtAll):
            content_parts.append("@全体成员 ")
        elif isinstance(seg, Reply):
            content_parts.append("[回复] ")
    return "".join(content_parts).strip() or event.raw_message

def format_batch_to_xml(batch: list[Union[PrivateMessageEvent, GroupMessageEvent]]) -> str:
    """将消息批次格式化为 XML 文本"""
    bot_uin = str(ncatbot_config.bt_uin) if ncatbot_config.bt_uin else ""
    batch_texts = []
    for event in batch:
        uid = event.user_id
        nick = event.sender.nickname
        msg_text = parse_event_message(event, bot_uin)
        time_str = format_timestamp(event.time)
        batch_texts.append(f'<turn role="user" name="{nick}" id="{uid}" time="{time_str}">\n{msg_text}\n</turn>')
    return "\n".join(batch_texts)

def format_history_to_xml(history: list[dict]) -> str:
    """将历史记录列表格式化为 XML 文本"""
    xml_parts = []
    for m in history:
        role = m.get("role", "user")
        time_str = m.get("time", "未知时间")
        content = m.get("content", "")
        if role == "assistant":
            xml_parts.append(f'<turn role="assistant" time="{time_str}">\n{content}\n</turn>')
        else:
            nick = m.get("nickname", "未知")
            uid = m.get("user_id") or m.get("user_id_real") or "unknown"
            xml_parts.append(f'<turn role="user" name="{nick}" id="{uid}" time="{time_str}">\n{content}\n</turn>')
    return "\n".join(xml_parts)

async def record_session_batch(session_id: str, batch: list[Union[PrivateMessageEvent, GroupMessageEvent]], is_group: bool) -> None:
    """统一记录消息批次到历史记录"""
    persona_name = memory_manager.active_personas.get(session_id, config.DEFAULT_PERSONA_NAME)
    full_session_id = f"{session_id}:{persona_name}"
    if full_session_id not in memory_manager.chat_history:
        memory_manager.chat_history[full_session_id] = []
    bot_uin = str(ncatbot_config.bt_uin) if ncatbot_config.bt_uin else ""
    for event in batch:
        content = parse_event_message(event, bot_uin)
        time_str = format_timestamp(event.time)
        nick = event.sender.nickname if hasattr(event, "sender") and event.sender else "未知"
        uid = str(event.user_id)
        role_name = f"{nick}({uid})"
        msg_obj = {"role": role_name, "nickname": nick, "user_id": uid, "content": content, "time": time_str}
        memory_manager.chat_history[full_session_id].append(msg_obj)
        memory_manager.save_message_to_file(full_session_id, role_name, content, event.time, nickname=nick, user_id=uid)
        record_user_activity(session_id, uid, nick)
    
    # 检查是否需要触发记忆归档
    memory_manager.check_and_trigger_consolidation(full_session_id, is_group=is_group)

async def fetch_and_inject_history(session_id: str, is_group: bool, count: int = 0) -> None:
    """从平台拉取历史消息并注入到工作记忆中（用于进入专注模式时补全上下文）"""
    if not is_group:
        return
    if count == 0:
        count = config.HISTORY_INJECT_COUNT
    from . import base
    from ..utils import debug_print
    bot = base._bot
    if not bot:
        return
    
    try:
        # 获取群历史消息
        history_events = await bot.api.get_group_msg_history(group_id=int(session_id), message_seq=0, count=count)
        if not history_events:
            return
            
        persona_name = memory_manager.active_personas.get(session_id, config.DEFAULT_PERSONA_NAME)
        full_session_id = f"{session_id}:{persona_name}"
        if full_session_id not in memory_manager.chat_history:
            memory_manager.chat_history[full_session_id] = []
            
        existing_contents = {(m.get("content"), m.get("time")) for m in memory_manager.chat_history[full_session_id]}
        
        bot_uin = str(ncatbot_config.bt_uin) if ncatbot_config.bt_uin else ""
        new_msgs = []
        for event in history_events:
            # 排除机器人自己的消息（防止重复注入）
            if str(event.user_id) == bot_uin:
                continue

            content = parse_event_message(event, bot_uin)
            time_str = format_timestamp(event.time)
            
            if (content, time_str) not in existing_contents:
                nick = event.sender.nickname if hasattr(event, "sender") and event.sender else "未知"
                uid = str(event.user_id)
                msg_obj = {
                    "role": f"{nick}({uid})", 
                    "nickname": nick, 
                    "user_id": uid, 
                    "content": content, 
                    "time": time_str
                }
                new_msgs.append(msg_obj)
                # 同时持久化到文件
                memory_manager.save_message_to_file(
                    full_session_id, 
                    f"{nick}({uid})", 
                    content, 
                    event.time, 
                    nickname=nick, 
                    user_id=uid
                )
        
        if new_msgs:
            # 合并并按时间排序
            all_history = memory_manager.chat_history[full_session_id] + new_msgs
            # 去重：以内容和时间为准
            seen = set()
            unique_history = []
            for m in sorted(all_history, key=lambda x: x.get("time", "")):
                key = (m.get("content"), m.get("time"))
                if key not in seen:
                    unique_history.append(m)
                    seen.add(key)
            
            memory_manager.chat_history[full_session_id] = unique_history[-config.MAX_HISTORY_LENGTH*2:]
            debug_print(1, f"已为会话 {session_id} 注入并持久化 {len(new_msgs)} 条历史消息")
    except Exception as e:
        debug_print(2, f"拉取历史消息失败: {e}")
