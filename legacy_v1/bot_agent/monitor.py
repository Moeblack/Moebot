import sqlite3
import json
import os

DB_PATH = "data/ai_monitor.db"

def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS ai_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, request_payload TEXT, response_body TEXT, model TEXT, duration REAL)')
    cursor.execute('CREATE TABLE IF NOT EXISTS ai_decisions (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, decision_type TEXT, session_id TEXT, decision_result TEXT, reason TEXT, prompt TEXT, duration REAL)')
    cursor.execute('CREATE TABLE IF NOT EXISTS config_changes (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, config_section TEXT, config_key TEXT, old_value TEXT, new_value TEXT, change_source TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS active_tasks (session_id TEXT PRIMARY KEY, status TEXT, message_count INTEGER, last_update DATETIME DEFAULT CURRENT_TIMESTAMP)')
    cursor.execute('CREATE TABLE IF NOT EXISTS user_activity (session_id TEXT, user_id TEXT, nickname TEXT, message_count INTEGER DEFAULT 1, last_message_time DATETIME DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (session_id, user_id))')
    conn.commit()
    conn.close()

def update_active_task(session_id: str, status: str, message_count: int = 0):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.cursor().execute("INSERT OR REPLACE INTO active_tasks (session_id, status, message_count, last_update) VALUES (?, ?, ?, CURRENT_TIMESTAMP)", (session_id, status, message_count))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Failed to update active task: {e}")

def remove_active_task(session_id: str):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.cursor().execute("DELETE FROM active_tasks WHERE session_id = ?", (session_id,))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Failed to remove active task: {e}")

def log_ai_interaction(payload: dict, response: str | dict, model: str, duration: float):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.cursor().execute("INSERT INTO ai_logs (request_payload, response_body, model, duration) VALUES (?, ?, ?, ?)", (json.dumps(payload, ensure_ascii=False), json.dumps(response, ensure_ascii=False) if isinstance(response, dict) else response, model, duration))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Failed to log AI interaction: {e}")

def log_ai_decision(decision_type: str, session_id: str, decision_result, reason: str, prompt: str, duration: float):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.cursor().execute("INSERT INTO ai_decisions (decision_type, session_id, decision_result, reason, prompt, duration) VALUES (?, ?, ?, ?, ?, ?)", (decision_type, session_id, json.dumps(decision_result, ensure_ascii=False), reason, prompt, duration))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Failed to log AI decision: {e}")

def log_config_change(section: str, key: str, old, new, source: str = "unknown"):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.cursor().execute("INSERT INTO config_changes (config_section, config_key, old_value, new_value, change_source) VALUES (?, ?, ?, ?, ?)", (section, key, str(old) if old is not None else None, str(new) if new is not None else None, source))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Failed to log config change: {e}")

def record_user_activity(session_id: str, user_id: str, nickname: str):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.cursor().execute("""
            INSERT INTO user_activity (session_id, user_id, nickname, message_count, last_message_time) 
            VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)
            ON CONFLICT(session_id, user_id) DO UPDATE SET 
                message_count = message_count + 1,
                nickname = excluded.nickname,
                last_message_time = CURRENT_TIMESTAMP
        """, (session_id, user_id, nickname))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Failed to record user activity: {e}")
