import time
from typing import Union
from ncatbot.core.event import PrivateMessageEvent, GroupMessageEvent

from .. import config
from ..memory import memory_manager
from ..llm import get_json_response
from ..utils import load_emoji_list
from ..monitor import log_ai_decision

from .processor_utils import format_batch_to_xml, format_history_to_xml

async def fast_entry_decision(session_id: str, batch: list[Union[PrivateMessageEvent, GroupMessageEvent]], is_group: bool = False, is_auto_trigger: bool = False) -> dict:
    """准入决策：判断是否需要回复，以及是否需要进入专注模式"""
    start_time = time.time()
    combined_text = format_batch_to_xml(batch)
    persona_name = memory_manager.active_personas.get(session_id, config.DEFAULT_PERSONA_NAME)
    full_session_id = f"{session_id}:{persona_name}"
    
    traits_list = memory_manager.personas.get(full_session_id, [])
    persona_traits = "；".join(traits_list) if traits_list else "暂无特定性格。"
    
    impression_list = memory_manager.impressions.get(full_session_id, [])
    impression_str = "；".join(impression_list) if impression_list else "暂无印象。"
    
    member_impressions_str = ""
    if is_group:
        member_impressions = []
        seen_users = set()
        for event in batch:
            uid = str(event.user_id)
            if uid not in seen_users:
                m_sid = f"{session_id}:{uid}:{persona_name}"
                m_imp_list = memory_manager.impressions.get(m_sid, [])
                if m_imp_list:
                    member_impressions.append(f"{event.sender.nickname}: {'；'.join(m_imp_list)}")
                seen_users.add(uid)
        if member_impressions:
            member_impressions_str = "\n<member_impressions>\n" + "\n".join(member_impressions) + "\n</member_impressions>"

    history = memory_manager.chat_history.get(full_session_id, [])[-config.DECISION_HISTORY_LIMIT:]
    history_str = format_history_to_xml(history)

    emoji_list_str = load_emoji_list()
    emoji_instr = f"\n[可用表情列表]:\n{emoji_list_str}\n" if emoji_list_str else ""

    memory_manager.update_social_energy(session_id)
    social_energy = memory_manager.get_social_energy(session_id)
    mood = memory_manager.get_mood(session_id)
    
    social_state_parts = []
    if config.ENABLE_SOCIAL_ENERGY:
        mood_label = config.MOOD_LABEL_MAP.get(mood, mood)
        social_state_parts.append(f"当前社交能量: {social_energy:.1f}/{config.MAX_SOCIAL_ENERGY}，心情: {mood_label}。")
    if config.ENABLE_TOPIC_DETECTION:
        topic = memory_manager.get_topic(full_session_id)
        social_state_parts.append(f"当前活跃话题: {topic}")
    social_state_desc = " ".join(social_state_parts) if social_state_parts else "目前无特殊状态。"

    from ..memory.prompt import load_prompt_config
    prompt_config = load_prompt_config().get("decisions", {})
    prompt_tpl = prompt_config.get("entry_decision", "")
    
    topic_instr = ""
    if config.ENABLE_TOPIC_DETECTION:
        topic_instr = "\n\n[额外要求]:\n- 当前话题 (current_topic): 简练描述当前大家正在聊的话题（10字以内）。如果发现话题已经转移，请更新它。"

    prompt = prompt_tpl.format(
        chat_type_desc=f"群聊(群号:{session_id})" if is_group else "私聊",
        mode_desc="被动观察模式（触发准入决策）" if is_auto_trigger else "主动触发模式",
        social_state_desc=social_state_desc,
        persona_traits=persona_traits,
        impression_tag='group_impression' if is_group else 'user_impression',
        impression_str=impression_str,
        member_impressions_str=member_impressions_str,
        history_str=history_str,
        combined_text=combined_text,
        emoji_instr=emoji_instr,
        topic_instr=topic_instr
    )

    schema_parts = ['"reply": boolean', '"enter_focus": boolean', '"emoji_id": number', '"withdraw_emoji": boolean', '"reason": "理由"']
    if config.ENABLE_TOPIC_DETECTION:
        schema_parts.append('"current_topic": "string"')
    schema = '{' + ", ".join(schema_parts) + '}'
    
    sys_instr = "SPECIAL INSTRUCTION: not think silently at all. Silent thinking token budget: 0." if config.AI_FORCE_NO_THINK_INST else ""
    result = await get_json_response(prompt, schema, thinking_budget=config.DEFAULT_THINKING_BUDGET, system_instruction=sys_instr)
    if result and config.ENABLE_TOPIC_DETECTION and result.get("current_topic"):
        memory_manager.update_topic(full_session_id, result["current_topic"])
    if config.AI_FORCE_NO_THINK_INST and isinstance(result, dict) and result.get("reason"):
        if "SPECIAL INSTRUCTION" in str(result["reason"]):
            result["reason"] = result["reason"].split("SPECIAL INSTRUCTION")[0].strip()
    
    duration = time.time() - start_time
    log_ai_decision("entry", session_id, result, result.get("reason", "") if isinstance(result, dict) else "Unknown", prompt, duration)
    
    default_res = {"reply": not is_auto_trigger, "enter_focus": not is_auto_trigger, "emoji_id": config.EMOJI_ID_THINK, "withdraw_emoji": True}
    return result if result else default_res

async def fast_micro_decision(session_id: str, batch: list[Union[PrivateMessageEvent, GroupMessageEvent]], is_group: bool = False) -> dict:
    """微观决策：专注模式下每 5s 执行一次，判断是否回复或发表情或忽略"""
    start_time = time.time()
    combined_text = format_batch_to_xml(batch)
    persona_name = memory_manager.active_personas.get(session_id, config.DEFAULT_PERSONA_NAME)
    full_session_id = f"{session_id}:{persona_name}"
    
    traits_list = memory_manager.personas.get(full_session_id, [])
    persona_traits = "；".join(traits_list) if traits_list else "暂无特定性格。"
    
    history = memory_manager.chat_history.get(full_session_id, [])[-config.DECISION_HISTORY_LIMIT:]
    history_str = format_history_to_xml(history)

    emoji_list_str = load_emoji_list()
    emoji_instr = f"\n[可用表情列表]:\n{emoji_list_str}\n" if emoji_list_str else ""

    memory_manager.update_social_energy(session_id)
    social_energy = memory_manager.get_social_energy(session_id)
    mood = memory_manager.get_mood(session_id)
    
    social_state_parts = []
    if config.ENABLE_SOCIAL_ENERGY:
        mood_label = config.MOOD_LABEL_MAP.get(mood, mood)
        social_state_parts.append(f"当前社交能量: {social_energy:.1f}/{config.MAX_SOCIAL_ENERGY}，心情: {mood_label}。")
    if config.ENABLE_TOPIC_DETECTION:
        topic = memory_manager.get_topic(full_session_id)
        social_state_parts.append(f"当前活跃话题: {topic}")
    social_state_desc = " ".join(social_state_parts) if social_state_parts else "目前无特殊状态。"

    from ..memory.prompt import load_prompt_config
    prompt_config = load_prompt_config().get("decisions", {})
    prompt_tpl = prompt_config.get("micro_decision", "")
    
    topic_instr = ""
    if config.ENABLE_TOPIC_DETECTION:
        topic_instr = "\n\n[额外要求]:\n- 当前话题 (current_topic): 简练描述当前大家正在聊的话题（10字以内）。"

    prompt = prompt_tpl.format(
        is_group='群' if is_group else '私聊',
        social_state_desc=social_state_desc,
        persona_traits=persona_traits,
        history_str=history_str,
        combined_text=combined_text,
        emoji_instr=emoji_instr,
        topic_instr=topic_instr
    )

    schema_parts = ['"action": "ignore"|"emoji"|"reply"', '"emoji_id": number', '"withdraw_emoji": boolean', '"reason": "理由"']
    if config.ENABLE_TOPIC_DETECTION:
        schema_parts.append('"current_topic": "string"')
    schema = '{' + ", ".join(schema_parts) + '}'
    
    sys_instr = "SPECIAL INSTRUCTION: not think silently at all. Silent thinking token budget: 0." if config.AI_FORCE_NO_THINK_INST else ""
    result = await get_json_response(prompt, schema, thinking_budget=config.DEFAULT_THINKING_BUDGET, system_instruction=sys_instr)
    if result and config.ENABLE_TOPIC_DETECTION and result.get("current_topic"):
        memory_manager.update_topic(full_session_id, result["current_topic"])
    if config.AI_FORCE_NO_THINK_INST and isinstance(result, dict) and result.get("reason"):
        if "SPECIAL INSTRUCTION" in result["reason"]:
            result["reason"] = result["reason"].split("SPECIAL INSTRUCTION")[0].strip()
    
    duration = time.time() - start_time
    log_ai_decision("micro", session_id, result, result.get("reason", "") if isinstance(result, dict) else "Unknown", prompt, duration)
    
    return result if result else {"action": "ignore", "reason": "超时默认忽略"}

async def fast_macro_decision(session_id: str, is_group: bool = False) -> dict:
    """宏观决策：专注模式下每 60s 执行一次，判断是否保持专注"""
    start_time = time.time()
    
    persona_name = memory_manager.active_personas.get(session_id, config.DEFAULT_PERSONA_NAME)
    full_session_id = f"{session_id}:{persona_name}"
    
    traits_list = memory_manager.personas.get(full_session_id, [])
    persona_traits = "；".join(traits_list) if traits_list else "暂无特定性格。"
    
    history = memory_manager.chat_history.get(full_session_id, [])[-config.DECISION_HISTORY_LIMIT:]
    history_str = format_history_to_xml(history)

    memory_manager.update_social_energy(session_id)
    social_energy = memory_manager.get_social_energy(session_id)
    mood = memory_manager.get_mood(session_id)
    
    social_state_parts = []
    if config.ENABLE_SOCIAL_ENERGY:
        mood_label = config.MOOD_LABEL_MAP.get(mood, mood)
        social_state_parts.append(f"当前社交能量: {social_energy:.1f}/{config.MAX_SOCIAL_ENERGY}，心情: {mood_label}。")
    if config.ENABLE_TOPIC_DETECTION:
        topic = memory_manager.get_topic(full_session_id)
        social_state_parts.append(f"当前活跃话题: {topic}")
    social_state_desc = " ".join(social_state_parts) if social_state_parts else "目前无特殊状态。"

    from ..memory.prompt import load_prompt_config
    prompt_config = load_prompt_config().get("decisions", {})
    prompt_tpl = prompt_config.get("macro_decision", "")
    
    topic_instr = ""
    if config.ENABLE_TOPIC_DETECTION:
        topic_instr = "\n\n[额外要求]:\n- 当前话题 (current_topic): 简练描述当前话题（10字以内）。"

    prompt = prompt_tpl.format(
        is_group='群' if is_group else '私聊',
        social_state_desc=social_state_desc,
        persona_traits=persona_traits,
        history_str=history_str,
        topic_instr=topic_instr
    )

    schema_parts = ['"stay_focus": boolean', '"reason": "理由"']
    if config.ENABLE_TOPIC_DETECTION:
        schema_parts.append('"current_topic": "string"')
    schema = '{' + ", ".join(schema_parts) + '}'
    
    sys_instr = "SPECIAL INSTRUCTION: not think silently at all. Silent thinking token budget: 0." if config.AI_FORCE_NO_THINK_INST else ""
    result = await get_json_response(prompt, schema, thinking_budget=config.DEFAULT_THINKING_BUDGET, system_instruction=sys_instr)
    if result and config.ENABLE_TOPIC_DETECTION and result.get("current_topic"):
        memory_manager.update_topic(full_session_id, result["current_topic"])
    if config.AI_FORCE_NO_THINK_INST and isinstance(result, dict) and result.get("reason"):
        if "SPECIAL INSTRUCTION" in str(result["reason"]):
            result["reason"] = result["reason"].split("SPECIAL INSTRUCTION")[0].strip()
    
    duration = time.time() - start_time
    log_ai_decision("macro", session_id, result, result.get("reason", "") if isinstance(result, dict) else "Unknown", prompt, duration)
    
    return result if result else {"stay_focus": True, "reason": "默认保持"}
