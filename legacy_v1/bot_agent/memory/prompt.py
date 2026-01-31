import os
import json
from ..utils import format_timestamp, get_now_timestamp
from ..config import BASE_PERSONA_CONFIG, DATA_DIR, DEFAULT_PERSONA_NAME
from .prompt_defaults import DEFAULT_PROMPT_CONFIG

PROMPT_FILE = os.path.join(DATA_DIR, "prompts.json")
_prompt_cache = None

def load_prompt_config():
    global _prompt_cache
    if _prompt_cache is not None:
        return _prompt_cache
    if os.path.exists(PROMPT_FILE):
        try:
            with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
                _prompt_cache = json.load(f)
                return _prompt_cache
        except Exception as e:
            print(f"加载提示词配置失败: {e}")
    return DEFAULT_PROMPT_CONFIG

def clear_prompt_cache():
    global _prompt_cache
    _prompt_cache = None

def build_prompt(session_id, current_message, chat_history, episodic_memory, personas, impressions, social_energy, mood, current_topics, current_time=None, is_group=False):
    config = load_prompt_config().get("templates", {})
    history, summaries = chat_history.get(session_id, []), episodic_memory.get(session_id, [])
    persona_name = session_id.split(":")[-1] if ":" in session_id else DEFAULT_PERSONA_NAME
    traits_list = personas.get(session_id, [])
    
    # 获取基础人格描述，优先匹配当前名称，其次匹配全局默认名称，最后取第一个或提供保底
    base_identity = BASE_PERSONA_CONFIG.get(persona_name)
    if not base_identity:
        base_identity = BASE_PERSONA_CONFIG.get(DEFAULT_PERSONA_NAME)
    if not base_identity and BASE_PERSONA_CONFIG:
        base_identity = next(iter(BASE_PERSONA_CONFIG.values()))
    if not base_identity:
        base_identity = "一个通用的 AI 助手。"
    
    traits_text = "；".join(traits_list) if traits_list else "表现自然即可。"
    persona_text = f"核心身份：{base_identity}\n行为特征：{traits_text}"
    
    user_impression = "对用户的印象：" + "；".join(impressions.get(session_id, [])) if impressions.get(session_id) else "暂无印象，处于初次接触阶段。"
    from .. import config as global_config
    social_state_parts = []
    if global_config.ENABLE_SOCIAL_ENERGY:
        mood_label = global_config.MOOD_LABEL_MAP.get(mood, mood)
        social_state_parts.append(f"当前社交能量: {social_energy:.1f}/{global_config.MAX_SOCIAL_ENERGY} (能量越低表示你越不想社交)")
        social_state_parts.append(f"当前心情: {mood_label}")
    
    if global_config.ENABLE_TOPIC_DETECTION:
        social_state_parts.append(f"当前活跃话题: {current_topics.get(session_id, '正在观察中...')}")
    
    social_state_text = "\n".join(social_state_parts) if social_state_parts else "当前无额外社交状态。"
    now_str = format_timestamp(current_time or get_now_timestamp())
    
    prompt_parts = [
        config["system_info"].format(now_str=now_str, social_state_text=social_state_text),
        config["personality"].format(persona_text=persona_text),
        config["user_impression"].format(user_impression=user_impression)
    ]
    
    if summaries:
        formatted_episodes = []
        for i, e in enumerate(summaries):
            if isinstance(e, dict):
                time_str = f" [{e.get('time')}]" if e.get('time') else ""
                summary_text = e.get('summary', '无内容')
                formatted_episodes.append(f"[情节 #{i+1}]{time_str}: {summary_text}")
            else:
                formatted_episodes.append(f"[情节 #{i+1}]: {e}")
        episodic_content = "\n".join(formatted_episodes)
        prompt_parts.append(config["episodic_memory"].format(episodic_content=episodic_content))

    from ..handlers.processor_utils import format_history_to_xml
    history_content = format_history_to_xml(history)
    prompt_parts.append(config["conversation_history"].format(history_content=history_content))
    prompt_parts.append(config["current_message"].format(msg_time_str=format_timestamp(current_time) if current_time else now_str, current_message=current_message))
    topic_instr = ""
    if global_config.ENABLE_TOPIC_DETECTION:
        topic_instr = "\n\n[额外要求]:\n- 当前话题 (current_topic): 简练描述当前大家正在聊的话题（10字以内）。如果发现话题已经转移，请更新它。"

    prompt_parts.append(config["footer"].format(now_str=now_str, topic_instr=topic_instr))

    # [已禁用] 群聊首次见面自我介绍 - 避免 AI 过度表演
    # 原因：首次见面时的自我介绍会让 AI 刻意表演，破坏自然融入群聊的体验
    # if not summaries and not any(msg["role"] == "assistant" for msg in history):
    #     prompt_parts.append(config.get("first_meeting_group" if is_group else "first_meeting_private", ""))
    
    # 仅保留私聊的首次见面提示
    if not is_group and not summaries and not any(msg["role"] == "assistant" for msg in history):
        prompt_parts.append(config.get("first_meeting_private", ""))
    
    return "\n".join(prompt_parts)
