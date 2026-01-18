import os
import json
from ..config import MEMORY_STATE_FILE, SOCIAL_STATE_FILE, ACTIVE_PERSONA_FILE

def load_memory_state():
    """加载持久化的计数器状态"""
    if os.path.exists(MEMORY_STATE_FILE):
        try:
            with open(MEMORY_STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载记忆状态失败: {e}")
    return {}

def save_memory_state(evolution_pity_counter, unconsolidated_count, current_topics=None):
    """保存计数器状态"""
    try:
        state = {
            "evolution_pity_counter": evolution_pity_counter,
            "unconsolidated_count": unconsolidated_count,
            "current_topics": current_topics or {}
        }
        with open(MEMORY_STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存记忆状态失败: {e}")

def load_social_state():
    """加载社交能量与心情状态"""
    if os.path.exists(SOCIAL_STATE_FILE):
        try:
            with open(SOCIAL_STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载社交状态失败: {e}")
    return {}

def save_social_state(social_states):
    """保存社交能量与心情状态"""
    try:
        with open(SOCIAL_STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(social_states, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存社交状态失败: {e}")

def load_active_personas():
    if os.path.exists(ACTIVE_PERSONA_FILE):
        try:
            with open(ACTIVE_PERSONA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载活跃人格失败: {e}")
    return {}

def save_active_personas(active_personas):
    try:
        with open(ACTIVE_PERSONA_FILE, 'w', encoding='utf-8') as f:
            json.dump(active_personas, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存活跃人格失败: {e}")
