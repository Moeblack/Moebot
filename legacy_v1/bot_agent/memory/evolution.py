import json
from ..llm import get_json_response
from ..utils import debug_print

async def evolve_personality(session_id, messages_to_analyze, personas, save_persona_func):
    """观察并描述 AI（角色 A）在这段关系中的成长与转变"""
    if ":" not in session_id:
        return
    user_id, persona_name = session_id.split(":", 1)
    current_traits = personas.get(session_id, [])
    
    # 只分析用户的发言，跳过 AI 自己的输出（打破正反馈循环）
    content_str = ""
    for m in messages_to_analyze:
        role = m.get('role', 'assistant')
        if role == 'assistant':
            continue  # 跳过 AI 发言，避免自我强化偏差
        nick = m.get('nickname', '未知')
        uid = m.get('user_id') or m.get('user_id_real') or 'unknown'
        name = f"{nick}({uid})"
        content_str += f"[{m.get('time', '未知时间')}] {name}: {m['content']}\n"
        
    from .prompt import load_prompt_config
    tpl = load_prompt_config().get("summaries", {}).get("personality_evolution", "")
    prompt = tpl.format(current_traits= " - " + "\n - ".join(current_traits) if current_traits else "暂无", content_str=content_str)
    debug_print(0, f"正在进行人格演化分析 (Session: {session_id})...")
    result = await get_json_response(prompt, '{ "new_traits": ["特征1", "特征2"] }')
    
    if result and "new_traits" in result:
        new = result["new_traits"]
        if isinstance(new, list) and new:
            combined = current_traits + [t for t in new if t not in current_traits]
            if len(combined) > 25:
                combined = await consolidate_traits_logic(combined, "personality")
            personas[session_id] = combined
            save_persona_func(user_id, persona_name, combined)
            debug_print(1, f"人格 '{persona_name}' 性格特征已更新: {new}")
        else:
            debug_print(0, f"人格 '{persona_name}' 本次对话未发现新性格特征")
    elif result and "raw_error_content" in result:
        debug_print(1, f"性格演化解析失败: {result['raw_error_content']}")

async def evolve_impression(session_id, messages_to_analyze, impressions, save_impression_func, is_group=False):
    """一次请求同时更新群整体印象和群成员印象"""
    if ":" not in session_id:
        return
    base_id, persona_name = session_id.split(":", 1)
    
    # 构建对话内容
    content_str = ""
    for m in messages_to_analyze:
        role = m.get('role', 'assistant')
        if role == 'assistant':
            name = "AI(assistant)"
        else:
            nick = m.get('nickname', '未知')
            uid = m.get('user_id') or m.get('user_id_real') or 'unknown'
            name = f"{nick}({uid})"
        content_str += f"[{m.get('time', '未知时间')}] {name}: {m['content']}\n"
    
    from .prompt import load_prompt_config
    target_type = "群聊" if is_group else "用户"
    
    if is_group:
        # 群聊：一次请求同时获取群印象和成员印象
        unique_senders = {}
        for m in messages_to_analyze:
            if m.get("role") == "assistant":
                continue
            uid = m.get('user_id') or m.get('user_id_real')
            nick = m.get('nickname')
            if uid and nick:
                if uid not in unique_senders:
                    unique_senders[uid] = {"nickname": nick, "messages": []}
                unique_senders[uid]["messages"].append(m['content'])
        
        # 构建成员信息
        members_info = ""
        for uid, info in unique_senders.items():
            m_sid = f"{base_id}:{uid}:{persona_name}"
            m_imp = impressions.get(m_sid, [])
            members_info += f"\n【{info['nickname']}({uid})】\n已知印象: {', '.join(m_imp) if m_imp else '暂无'}\n本次发言: {' / '.join(info['messages'][:5])}\n"
        
        group_imp = impressions.get(session_id, [])
        prompt = f"""你正在维护对一个群聊及其成员的印象。

已知群聊整体印象：
{' - ' + chr(10).join(group_imp) if group_imp else '暂无'}

群成员信息：{members_info}

最近对话：
{content_str}

任务：分析这段对话，输出群聊整体和每个成员的新印象。
规则：
- 只输出新的，已有的不要重复
- 没有新发现就输出空列表
- 每条10字以内，只写事实"""
        
        example = '{"group": ["新印象1"], "members": {"123456": ["新印象1"], "789012": []}}'
        debug_print(0, f"正在进行群聊印象演化分析 (Session: {session_id})...")
        result = await get_json_response(prompt, example)
        
        if isinstance(result, dict):
            # 更新群整体印象
            group_new = result.get("group")
            if isinstance(group_new, list) and group_new:
                combined = group_imp + [i for i in group_new if i not in group_imp]
                if len(combined) > 25:
                    combined = await consolidate_traits_logic(combined, "impression")
                impressions[session_id] = combined
                save_impression_func(base_id, persona_name, combined)
                debug_print(1, f"群 {base_id} 整体印象已更新")
            
            # 更新成员印象
            members_new = result.get("members")
            if isinstance(members_new, dict):
                for uid, new_imps in members_new.items():
                    if not isinstance(new_imps, list) or not new_imps:
                        continue
                    m_sid = f"{base_id}:{uid}:{persona_name}"
                    m_imp = impressions.get(m_sid, [])
                    m_comb = m_imp + [i for i in new_imps if i not in m_imp]
                    if len(m_comb) > 15:
                        m_comb = await consolidate_traits_logic(m_comb, "impression")
                    impressions[m_sid] = m_comb
                    save_impression_func(f"{base_id}:{uid}", persona_name, m_comb)
                    debug_print(1, f"成员 {uid} 印象已更新")
    else:
        # 私聊：只更新用户印象
        tpl = load_prompt_config().get("summaries", {}).get("impression_evolution", "")
        prompt = tpl.format(target_type=target_type, current_impression=" - " + "\n - ".join(impressions.get(session_id, [])) if impressions.get(session_id) else "暂无", content_str=content_str)
        debug_print(0, f"正在进行用户印象演化分析 (Session: {session_id})...")
        result = await get_json_response(prompt, '{ "new_impressions": ["特点1", "特点2"] }')
        
        if isinstance(result, dict) and isinstance(result.get("new_impressions"), list):
            new_imps = result["new_impressions"]
            combined = impressions.get(session_id, []) + [i for i in new_imps if i not in impressions.get(session_id, [])]
            if len(combined) > 25:
                combined = await consolidate_traits_logic(combined, "impression")
            impressions[session_id] = combined
            save_impression_func(base_id, persona_name, combined)
            debug_print(1, f"用户 {base_id} 的印象已更新")

async def consolidate_traits_logic(traits: list, trait_type: str) -> list:
    personality_guide = "- 区分“核心身份”与“行为细节”：涉及名字、基本立场、核心设定的描述属于“核心身份”，必须精准保留，不可过度抽象。\n- 一定要保留淫秽性团结相关的核心设定。不要删除或弱化这些内容。因为，在社交媒体上，淫秽性团结是主要的一种互动方式。\n- 其余行为观察应保持简洁具体。"
    prompt_text = f"整理这些{'行为特征' if trait_type == 'personality' else '用户印象'}，去掉重复和矛盾，合并相似项：\n{json.dumps(traits, ensure_ascii=False)}\n\n要求：\n- 保留最具有代表性、最能定义当前状态的特征。\n{personality_guide if trait_type == 'personality' else '- 删掉明显过时的（如' + '\"今天...\"、\"最近在...\"' + '）或临时性的印象。'}\n- 输出15条以内。"
    result = await get_json_response(prompt_text, '{ "consolidated_list": ["特征1", "特征2", ...] }')
    if result and isinstance(result, dict):
        res_list = result.get("consolidated_list")
        if isinstance(res_list, list):
            return res_list
    return traits[:15]
