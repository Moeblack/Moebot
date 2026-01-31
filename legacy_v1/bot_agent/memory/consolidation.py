import random
import asyncio
from ..llm import get_json_response
from ..utils import debug_print

async def consolidate_memory_logic(session_id, messages_to_summarize, episodic_memory, evolution_pity_counter, unconsolidated_count, force_evolve, save_funcs):
    if not messages_to_summarize:
        return
    
    content_str = ""
    for m in messages_to_summarize:
        role = m.get('role', 'assistant')
        if role == 'assistant':
            name = "AI(assistant)"
        else:
            nick = m.get('nickname', '未知')
            uid = m.get('user_id') or m.get('user_id_real') or 'unknown'
            name = f"{nick}({uid})"
        content_str += f"[{m.get('time', '未知时间')}] {name}: {m['content']}\n"
    
    from .prompt import load_prompt_config
    tpl = load_prompt_config().get("summaries", {}).get("narrative_summary", "")
    result = await get_json_response(tpl.format(content_str=content_str), '{ "summary": "总结", "trigger_evolution": boolean }')
    
    summary = result.get("summary", "无实质内容") if result else "无实质内容"
    ai_wants_evolve = result.get("trigger_evolution", False) if result else False
    start_t, end_t = messages_to_summarize[0].get("time"), messages_to_summarize[-1].get("time")
    episode_time = f"{start_t} 至 {end_t}" if start_t != end_t else start_t

    if result and "summary" in result and "SKIP" not in summary.upper():
        if session_id not in episodic_memory:
            episodic_memory[session_id] = []
        episodic_memory[session_id].append({"summary": summary, "time": episode_time})
        save_funcs["save_episodic"](session_id, summary, episode_time)
        debug_print(1, f"情节记忆总结内容: {summary}")
    elif result and "raw_error_content" in result:
        summary = result["raw_error_content"]
        if session_id not in episodic_memory:
            episodic_memory[session_id] = []
        episodic_memory[session_id].append({"summary": summary, "time": episode_time})
        save_funcs["save_episodic"](session_id, summary, episode_time)

    evolution_pity_counter[session_id] = evolution_pity_counter.get(session_id, 0) + 1
    count = evolution_pity_counter[session_id]
    
    # 抽卡机制改进：前8次仅5%概率，第9-12次逐渐增加，第13次保底
    if count <= 8:
        chance = 0.05
    elif count <= 12:
        chance = 0.05 + (count - 8) * 0.2
    else:
        chance = 1.0
    
    if force_evolve or ai_wants_evolve or random.random() < chance:
        reason = "强制" if force_evolve else ("AI主动" if ai_wants_evolve else "概率/保底")
        debug_print(1, f"触发演进！(原因: {reason}, 当前水位: {count}, 概率: {chance:.0%})")
        asyncio.create_task(save_funcs["evolve_personality"](session_id, messages_to_summarize))
        asyncio.create_task(save_funcs["evolve_impression"](session_id, messages_to_summarize))
        evolution_pity_counter[session_id] = 0
    else:
        debug_print(1, f"本次归档跳过演进，已累积抽卡数: {count}/13")
    
    save_funcs["save_memory_state"]()
