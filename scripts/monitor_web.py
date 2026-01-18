"""
===============================================================================
TOOL SCRIPT: Monitor Web Backend
DESCRIPTION: 用于查看 AI 请求和决策记录的可视化网页后台
STATUS: EXPERIMENTAL
--------------------------------------------------------------------------------
USAGE:
    ./.venv/bin/python scripts/monitor_web.py

DEPENDENCIES:
    - fastapi
    - uvicorn
    - sqlite3
===============================================================================
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import sqlite3
import json
import uvicorn

app = FastAPI(title="AI Interaction Monitor")

# 配置静态文件和模板
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

DB_PATH = "data/ai_monitor.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# API 端点

@app.get("/api/ai-logs")
async def get_ai_logs(limit: int = 50):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ai_logs ORDER BY timestamp DESC LIMIT ?", (limit,))
    logs = cursor.fetchall()
    conn.close()
    return JSONResponse(content=[dict(log) for log in logs])

@app.get("/api/ai-decisions")
async def get_ai_decisions(limit: int = 50):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ai_decisions ORDER BY timestamp DESC LIMIT ?", (limit,))
    decisions = cursor.fetchall()
    conn.close()
    return JSONResponse(content=[dict(decision) for decision in decisions])

@app.get("/api/active-tasks")
async def get_active_tasks():
    from bot_agent.monitor_query import get_active_tasks
    tasks = get_active_tasks()
    return JSONResponse(content=tasks)

@app.get("/api/user-activity")
async def get_user_activity(session_id: str | None = None, limit: int = 20):
    from bot_agent.monitor_query import get_user_activity
    activity = get_user_activity(session_id, limit)
    return JSONResponse(content=activity)

@app.get("/api/config-changes")
async def get_config_changes(limit: int = 50):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM config_changes ORDER BY timestamp DESC LIMIT ?", (limit,))
    changes = cursor.fetchall()
    conn.close()
    return JSONResponse(content=[dict(change) for change in changes])

@app.get("/api/config")
async def get_config():
    from bot_agent.config import config_manager
    return JSONResponse(content=config_manager.get_config())

@app.post("/api/config")
async def update_config(request: Request):
    data = await request.json()
    from bot_agent.config import config_manager
    
    try:
        for section, section_config in data.items():
            config_manager.update_section(section, section_config, "web")
        return JSONResponse(content={"success": True, "message": "配置更新成功"})
    except Exception as e:
        return JSONResponse(content={"success": False, "message": str(e)}, status_code=500)

@app.post("/api/config/section")
async def update_section(section: str = Form(...), config: str = Form(...)):
    from bot_agent.config import config_manager
    
    try:
        config_data = json.loads(config)
        config_manager.update_section(section, config_data, "web")
        return JSONResponse(content={"success": True, "message": f"配置节 {section} 更新成功"})
    except Exception as e:
        return JSONResponse(content={"success": False, "message": str(e)}, status_code=500)

@app.post("/api/config/reset")
async def reset_config():
    from bot_agent.config import config_manager
    
    try:
        config_manager.reset_config()
        return JSONResponse(content={"success": True, "message": "配置已重置为默认值"})
    except Exception as e:
        return JSONResponse(content={"success": False, "message": str(e)}, status_code=500)

# Persona 管理 API
@app.get("/api/personas")
async def get_personas():
    from bot_agent.memory import memory_manager
    return JSONResponse(content=memory_manager.personas)

@app.get("/api/active-personas")
async def get_active_personas():
    from bot_agent.memory import memory_manager
    return JSONResponse(content=memory_manager.active_personas)

# 社交状态 API
@app.get("/api/social-states")
async def get_social_states():
    from bot_agent.memory import memory_manager
    states = {
        sid: {
            "social_energy": sm.social_energy,
            "mood": sm.mood,
            "last_update_ts": sm.last_update_ts
        } for sid, sm in memory_manager.social_managers.items()
    }
    return JSONResponse(content=states)

# 基础人格管理 API
@app.get("/api/base-personas")
async def get_base_personas():
    from bot_agent.config import config_manager
    return JSONResponse(content=config_manager.get_base_persona_config())

@app.post("/api/base-personas")
async def add_base_persona(request: Request):
    from bot_agent.config import config_manager
    data = await request.json()
    
    try:
        name = data["name"]
        description = data["description"]
        config_manager.add_base_persona(name, description)
        return JSONResponse(content={"success": True, "message": f"人格 '{name}' 添加成功"})
    except Exception as e:
        return JSONResponse(content={"success": False, "message": str(e)}, status_code=500)

@app.put("/api/base-personas")
async def update_base_persona(request: Request):
    from bot_agent.config import config_manager
    data = await request.json()
    
    try:
        name = data["name"]
        description = data["description"]
        config_manager.update_base_persona(name, description)
        return JSONResponse(content={"success": True, "message": f"人格 '{name}' 更新成功"})
    except Exception as e:
        return JSONResponse(content={"success": False, "message": str(e)}, status_code=500)

@app.delete("/api/base-personas")
async def delete_base_persona(request: Request):
    from bot_agent.config import config_manager
    data = await request.json()
    
    try:
        name = data["name"]
        config_manager.delete_base_persona(name)
        return JSONResponse(content={"success": True, "message": f"人格 '{name}' 删除成功"})
    except Exception as e:
        return JSONResponse(content={"success": False, "message": str(e)}, status_code=500)

# 初始人格特质管理 API
@app.get("/api/initial-traits")
async def get_initial_traits():
    from bot_agent.config import config_manager
    return JSONResponse(content=config_manager.get_initial_traits())

@app.post("/api/initial-traits")
async def add_initial_trait(request: Request):
    from bot_agent.config import config_manager
    data = await request.json()
    
    try:
        persona_name = data["persona_name"]
        trait = data["trait"]
        config_manager.add_initial_trait(persona_name, trait)
        return JSONResponse(content={"success": True, "message": f"特质 '{trait}' 添加成功"})
    except Exception as e:
        return JSONResponse(content={"success": False, "message": str(e)}, status_code=500)

@app.delete("/api/initial-traits")
async def remove_initial_trait(request: Request):
    from bot_agent.config import config_manager
    data = await request.json()
    
    try:
        persona_name = data["persona_name"]
        trait = data["trait"]
        config_manager.remove_initial_trait(persona_name, trait)
        return JSONResponse(content={"success": True, "message": f"特质 '{trait}' 删除成功"})
    except Exception as e:
        return JSONResponse(content={"success": False, "message": str(e)}, status_code=500)

# 记忆管理 API
@app.get("/api/impressions")
async def get_impressions():
    from bot_agent.memory import memory_manager
    return JSONResponse(content=memory_manager.impressions)

@app.put("/api/impressions")
async def update_impressions(request: Request):
    data = await request.json()
    try:
        session_id = data["session_id"]
        impressions = data["impressions"]
        if isinstance(impressions, str):
            import re
            impressions = [i.strip() for i in re.split(r'[，。；,;.]', impressions) if i.strip()]
        
        # 解析 session_id
        from bot_agent.config import DEFAULT_PERSONA_NAME
        if ":" in session_id:
            user_id, persona_name = session_id.split(":", 1)
        else:
            user_id, persona_name = session_id, DEFAULT_PERSONA_NAME
            
        from bot_agent.memory.persistence import save_impression_to_file
        save_impression_to_file(user_id, persona_name, impressions)
        return JSONResponse(content={"success": True, "message": "印象更新成功"})
    except Exception as e:
        return JSONResponse(content={"success": False, "message": str(e)}, status_code=500)

@app.get("/api/chat-history")
async def get_chat_history():
    from bot_agent.memory import memory_manager
    return JSONResponse(content=memory_manager.chat_history)

@app.put("/api/chat-history")
async def update_chat_history(request: Request):
    data = await request.json()
    try:
        session_id = data["session_id"]
        messages = data["messages"] # 预期是对象列表 [{"role": "...", "content": "...", "time": "..."}]
        
        from bot_agent.memory import memory_manager
        memory_manager.chat_history[session_id] = messages
        
        # 保存到文件
        from bot_agent.config import DATA_DIR
        history_file = os.path.join(DATA_DIR, "chat_history.jsonl")
        
        # 这是一个大动作，我们需要重写整个历史文件，或者至少过滤掉该 session 的再重新追加。
        # 对于开发工具，我们先采用简单重写方案（如果文件不是特别大）。
        all_history = []
        if os.path.exists(history_file):
            with open(history_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        item = json.loads(line)
                        if item.get("user_id") != session_id:
                            all_history.append(item)
        
        for m in messages:
            all_history.append({
                "user_id": session_id,
                "role": m["role"],
                "content": m["content"],
                "time": m.get("time"),
                "nickname": m.get("nickname"),
                "user_id_real": m.get("user_id") # 注意：内存中的 user_id 是发送者 ID
            })
            
        with open(history_file, 'w', encoding='utf-8') as f:
            for item in all_history:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
                
        return JSONResponse(content={"success": True, "message": "聊天历史更新成功"})
    except Exception as e:
        return JSONResponse(content={"success": False, "message": str(e)}, status_code=500)

@app.get("/api/episodic-memory")
async def get_episodic_memory():
    from bot_agent.memory import memory_manager
    return JSONResponse(content=memory_manager.episodic_memory)

@app.put("/api/episodic-memory")
async def update_episodic_memory(request: Request):
    data = await request.json()
    try:
        session_id = data["session_id"]
        memories = data["memories"] # 预期是对象列表 [{"summary": "...", "time": "..."}]
        
        # 情节记忆是追加型的，但在管理界面我们可能想替换。
        # 这里为了简单，我们先实现追加，或者如果以后需要替换，可以重写整个文件。
        # 考虑到需求是“编辑”，我们可能需要重写文件。
        from bot_agent.config import EPISODIC_FILE
        import json
        
        # 读取现有，替换特定 session 的，写回
        all_memories = []
        if os.path.exists(EPISODIC_FILE):
            with open(EPISODIC_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        item = json.loads(line)
                        if item.get("user_id") != session_id:
                            all_memories.append(item)
        
        for m in memories:
            all_memories.append({
                "user_id": session_id,
                "summary": m["summary"],
                "time": m.get("time")
            })
            
        with open(EPISODIC_FILE, 'w', encoding='utf-8') as f:
            for item in all_memories:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
                
        return JSONResponse(content={"success": True, "message": "情节记忆更新成功"})
    except Exception as e:
        return JSONResponse(content={"success": False, "message": str(e)}, status_code=500)

# Prompt 管理 API
@app.get("/api/prompts")
async def get_prompts():
    from bot_agent.memory.prompt import load_prompt_config
    return JSONResponse(content=load_prompt_config())

@app.post("/api/prompts")
async def update_prompts(request: Request):
    data = await request.json()
    from bot_agent.config import DATA_DIR
    import os
    PROMPT_FILE = os.path.join(DATA_DIR, "prompts.json")
    try:
        with open(PROMPT_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        from bot_agent.memory.prompt import clear_prompt_cache
        clear_prompt_cache()
        return JSONResponse(content={"success": True, "message": "提示词配置更新成功"})
    except Exception as e:
        return JSONResponse(content={"success": False, "message": str(e)}, status_code=500)

# 活跃人格特质编辑
@app.put("/api/active-personas/traits")
async def update_active_persona_traits(request: Request):
    data = await request.json()
    try:
        session_id = data["session_id"]
        traits = data["traits"]
        if isinstance(traits, str):
            import re
            traits = [t.strip() for t in re.split(r'[，。；,;.]', traits) if t.strip()]
            
        if ":" in session_id:
            user_id, persona_name = session_id.split(":", 1)
        else:
            from bot_agent.config import DEFAULT_PERSONA_NAME
            user_id, persona_name = session_id, DEFAULT_PERSONA_NAME
            
        from bot_agent.memory.persistence import save_persona_to_file
        save_persona_to_file(user_id, persona_name, traits)
        return JSONResponse(content={"success": True, "message": "运行时特质更新成功"})
    except Exception as e:
        return JSONResponse(content={"success": False, "message": str(e)}, status_code=500)

@app.post("/api/logs/clear")
async def clear_logs(log_type: str = Form(...)):
    from bot_agent.monitor_query import clear_ai_logs, clear_ai_decisions, clear_config_changes
    
    try:
        if log_type == "ai_logs":
            clear_ai_logs()
        elif log_type == "ai_decisions":
            clear_ai_decisions()
        elif log_type == "config_changes":
            clear_config_changes()
        elif log_type == "all":
            clear_ai_logs()
            clear_ai_decisions()
            clear_config_changes()
        else:
            return JSONResponse(content={"success": False, "message": "无效的日志类型"}, status_code=400)
        
        return JSONResponse(content={"success": True, "message": "日志已清除"})
    except Exception as e:
        return JSONResponse(content={"success": False, "message": str(e)}, status_code=500)

if __name__ == "__main__":
    # 确保数据库已初始化
    from bot_agent.monitor import init_db
    init_db()
    
    print("Starting monitor server at http://0.0.0.0:8000 (accessible from intranet)")
    uvicorn.run(app, host="0.0.0.0", port=8000)
