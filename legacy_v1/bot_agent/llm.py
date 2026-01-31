import httpx
import json
import time
import asyncio
from typing import Any
from .config import GEMINI_URL, GEMINI_API_KEY
from .monitor import log_ai_interaction
from .utils import debug_print

async def get_gemini_response(prompt: str, role: str = "user", files: list[dict[str, Any]] | None = None, thinking_budget: int | None = None, system_instruction: str | None = None):
    """调用 Gemini API 获取响应"""
    start_time = time.time()
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY
    }
    # ... (中间代码省略，apply_diff 会处理)
    
    actual_prompt = prompt
    if system_instruction:
        actual_prompt = f"# SYSTEM PROMPT: {system_instruction}\n\n{prompt}"

    parts = [{"text": actual_prompt}]
    if files:
        parts.extend(files)

    payload: dict = {
        "contents": [
            {
                "role": role,
                "parts": parts
            }
        ]
    }

    # if thinking_budget is not None:
    #     payload["generationConfig"] = {
    #         "thinking_config": {
    #             "include_thoughts": True,
    #             "thinking_budget_tokens": thinking_budget
    #         }
    #     }
    
    async with httpx.AsyncClient(verify=False) as client:
        try:
            resp = await client.post(GEMINI_URL, headers=headers, json=payload, timeout=60)
            duration = time.time() - start_time
            resp.raise_for_status()
            data = resp.json()
            
            # 记录原始交互到监控数据库
            from .config import GEMINI_MODEL
            log_ai_interaction(payload, data, GEMINI_MODEL, duration)

            # 提取生成的文本内容，过滤掉推理部分 (thought)
            candidates = data.get('candidates', [])
            if not candidates:
                return f"Gemini 没有返回候选结果 (可能是内容被屏蔽): {data}"
            
            parts = candidates[0].get('content', {}).get('parts', [])
            final_text = ""
            for part in parts:
                if "text" in part:
                    # 如果 AI 返回了 thought 字段，说明启用了 thinking 模式
                    if "thought" in part:
                        from .config import AI_SHOW_THINKING
                        if AI_SHOW_THINKING:
                            final_text += f"> [Thinking]\n> {part['thought']}\n\n"
                    else:
                        final_text += part["text"]
            return final_text.strip() or "AI 没有返回有效文本"
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text
            return f"Gemini 调用失败: {e.response.status_code} - {error_detail}"
        except Exception as e:
            return f"Gemini 调用失败: {e}"

async def get_json_response(prompt: str, schema_desc: str, files: list[dict[str, Any]] | None = None, max_retries: int = 3, thinking_budget: int | None = None, system_instruction: str | None = None):
    """获取 AI 的 JSON 响应，支持重试和清理"""
    full_prompt = f"{prompt}\n\n请严格按照以下 JSON 格式输出：\n{schema_desc}\n注意：只返回 JSON 字符串，不要包含任何 markdown 格式标记。"
    
    for attempt in range(max_retries):
        response = await get_gemini_response(full_prompt, files=files, thinking_budget=thinking_budget, system_instruction=system_instruction)
        # 尝试清理可能存在的 markdown 代码块
        clean_response = response.strip()
        if clean_response.startswith("```json"):
            clean_response = clean_response[7:]
        if clean_response.endswith("```"):
            clean_response = clean_response[:-3]
        clean_response = clean_response.strip()

        try:
            return json.loads(clean_response)
        except json.JSONDecodeError as e:
            debug_print(0, f"JSON 解析失败 (尝试 {attempt + 1}/{max_retries}): {e}")
            debug_print(0, f"原始响应内容: {clean_response[:200]}...") # 打印前200字符辅助排查
            if attempt < max_retries - 1:
                await asyncio.sleep(1) # 重试前稍作等待
            else:
                return {"raw_error_content": response}
    return None
