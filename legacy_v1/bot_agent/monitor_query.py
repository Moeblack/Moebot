import sqlite3
from .monitor import DB_PATH

def get_active_tasks():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("DELETE FROM active_tasks WHERE last_update < datetime('now', '-5 minutes')")
        conn.commit()
        cursor.execute("SELECT * FROM active_tasks ORDER BY last_update DESC")
        tasks = cursor.fetchall()
        conn.close()
        return [dict(t) for t in tasks]
    except Exception as e:
        print(f"Failed to get active tasks: {e}")
        return []

def get_ai_logs(limit: int = 50):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ai_logs ORDER BY timestamp DESC LIMIT ?", (limit,))
        logs = cursor.fetchall()
        conn.close()
        return [dict(log) for log in logs]
    except Exception:
        return []

def get_ai_decisions(limit: int = 50):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ai_decisions ORDER BY timestamp DESC LIMIT ?", (limit,))
        decisions = cursor.fetchall()
        conn.close()
        return [dict(d) for d in decisions]
    except Exception:
        return []

def get_config_changes(limit: int = 50):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM config_changes ORDER BY timestamp DESC LIMIT ?", (limit,))
        changes = cursor.fetchall()
        conn.close()
        return [dict(c) for c in changes]
    except Exception:
        return []

def get_user_activity(session_id: str | None = None, limit: int = 20):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        if session_id:
            cursor.execute("SELECT * FROM user_activity WHERE session_id = ? ORDER BY message_count DESC LIMIT ?", (session_id, limit))
        else:
            cursor.execute("SELECT * FROM user_activity ORDER BY message_count DESC LIMIT ?", (limit,))
        activity = cursor.fetchall()
        conn.close()
        return [dict(a) for a in activity]
    except Exception:
        return []

def clear_ai_logs():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ai_logs")
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

def clear_ai_decisions():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ai_decisions")
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

def clear_config_changes():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM config_changes")
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False
