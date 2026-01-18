import os
import json
import re
from ..config import HISTORY_FILE, EPISODIC_FILE, PERSONA_FILE, IMPRESSION_FILE
from ..utils import debug_print

def load_personas():
    personas = {}
    if os.path.exists(PERSONA_FILE):
        try:
            with open(PERSONA_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        item = json.loads(line)
                        sid = f"{item['user_id']}:{item['persona_name']}"
                        traits = item.get('traits', [])
                        if isinstance(traits, str):
                            traits = [t.strip() for t in re.split(r'[，。；,;.]', traits) if t.strip()]
                        personas[sid] = traits
        except Exception as e:
            print(f"加载人格数据失败: {e}")
    return personas

def save_persona_to_file(user_id, persona_name, traits):
    item = {"user_id": user_id, "persona_name": persona_name, "traits": traits}
    try:
        with open(PERSONA_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"保存人格描述失败: {e}")

def load_impressions():
    impressions = {}
    if os.path.exists(IMPRESSION_FILE):
        try:
            with open(IMPRESSION_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        item = json.loads(line)
                        sid = f"{item['user_id']}:{item['persona_name']}"
                        impression = item.get('impression', [])
                        if isinstance(impression, str):
                            impression = [i.strip() for i in re.split(r'[，。；,;.]', impression) if i.strip()]
                        impressions[sid] = impression
        except Exception as e:
            print(f"加载印象数据失败: {e}")
    return impressions

def save_impression_to_file(user_id, persona_name, impression):
    item = {"user_id": user_id, "persona_name": persona_name, "impression": impression}
    try:
        with open(IMPRESSION_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"保存印象失败: {e}")

def load_chat_history(unconsolidated_count):
    chat_history = {}
    if os.path.exists(HISTORY_FILE):
        try:
            temp_history = {}
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    item = json.loads(line)
                    sid = str(item.get("user_id"))
                    if sid not in temp_history:
                        temp_history[sid] = []
                    msg_data = {
                        "role": item.get("role"),
                        "content": item.get("content"),
                        "nickname": item.get("nickname"),
                        "user_id": item.get("user_id_real")
                    }
                    if "time" in item:
                        msg_data["time"] = item["time"]
                    temp_history[sid].append(msg_data)
            
            for sid, messages in temp_history.items():
                count = unconsolidated_count.get(sid, 0)
                load_count = max(count, 50)
                chat_history[sid] = messages[-load_count:] if load_count > 0 else []
                debug_print(1, f"会话 {sid} 加载了 {len(chat_history[sid])} 条历史记录 (未归档数: {count})")
        except Exception as e:
            print(f"加载工作记忆失败: {e}")
    return chat_history

def save_message_to_file(session_id,role, content, ts_str, nickname=None, user_id=None):
    item = {"user_id": session_id, "role": role, "content": content, "time": ts_str}
    if nickname:
        item["nickname"] = nickname
    if user_id:
        item["user_id_real"] = user_id
    try:
        with open(HISTORY_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"保存消息失败: {e}")

def load_episodic_memory():
    episodic_memory = {}
    if os.path.exists(EPISODIC_FILE):
        try:
            with open(EPISODIC_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        item = json.loads(line)
                        sid = str(item.get("user_id"))
                        if sid not in episodic_memory:
                            episodic_memory[sid] = []
                        episodic_memory[sid].append({"summary": item.get("summary"), "time": item.get("time")})
        except Exception as e:
            print(f"加载情节记忆失败: {e}")
    return episodic_memory

def save_episodic_to_file(session_id, summary, time_str):
    item = {"user_id": session_id, "summary": summary}
    if time_str:
        item["time"] = time_str
    try:
        with open(EPISODIC_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"保存情节记忆失败: {e}")
