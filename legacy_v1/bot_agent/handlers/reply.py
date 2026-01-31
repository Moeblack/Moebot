import base64
import io
import httpx
import asyncio
from typing import Any, Union, Dict
from PIL import Image as PILImage
from ncatbot.core import BotClient
from ncatbot.core.event import PrivateMessageEvent, GroupMessageEvent
from ncatbot.core.event.message_segment import Image, Text, At, Face, PlainText, AtAll, Reply
from ncatbot.utils import ncatbot_config

from .. import config
from ..memory import memory_manager
from ..llm import get_json_response
from ..utils import (
    format_timestamp, get_now_timestamp, debug_print, parse_cq_codes
)
from ..monitor import update_active_task

async def process_image_segment(seg: Image, session_id: str, is_group: bool, current_image_count: int, total_count: int) -> tuple[dict, str]:
    """处理消息段中的图片，返回 (image_part, debug_text)"""
    try:
        img_url = seg.url
        async with httpx.AsyncClient(verify=False) as client:
            img_resp = await client.get(img_url, timeout=10)
            img_resp.raise_for_status()
            img_data = img_resp.content
            
            if is_group and len(img_data) > 1024 * 1024:
                debug_print(1, f"群聊图片过大 ({len(img_data) // 1024}KB)，跳过上传")
                return {}, "[图片(过大已跳过)]"

            mime_type = img_resp.headers.get("Content-Type", "image/jpeg")
            if config.COMPRESS_TO_WEBP or "image/gif" in mime_type:
                target_format = "WEBP" if config.COMPRESS_TO_WEBP else "PNG"
                target_mime = "image/webp" if config.COMPRESS_TO_WEBP else "image/png"
                debug_print(1, f"正在处理图片: {mime_type} -> {target_mime}...")
                update_active_task(session_id, f"正在处理图片 ({current_image_count}/{total_count})...", total_count)
                
                with PILImage.open(io.BytesIO(img_data)) as img:
                    img = img.convert("RGBA" if img.mode in ("RGBA", "P") else "RGB")
                    output = io.BytesIO()
                    save_kwargs: Dict[str, Any] = {"format": target_format}
                    if target_format == "WEBP":
                        save_kwargs["quality"] = 80
                    img.save(output, **save_kwargs)
                    img_data = output.getvalue()
                    mime_type = target_mime
            
            img_base64 = base64.b64encode(img_data).decode("utf-8")
            return {"inline_data": {"mime_type": mime_type, "data": img_base64}}, "[图片]"
    except Exception as e:
        debug_print(1, f"图片下载或转换失败: {e}")
        return {}, "[图片(处理失败)]"

async def execute_persona_reply(session_id: str, batch: list[Union[PrivateMessageEvent, GroupMessageEvent]], bot: BotClient, is_group: bool = False) -> None:
    """执行正式的人格回复逻辑"""
    persona_name = memory_manager.active_personas.get(session_id, config.DEFAULT_PERSONA_NAME)
    full_session_id = f"{session_id}:{persona_name}"
    bot_uin = str(ncatbot_config.bt_uin) if ncatbot_config.bt_uin else ""
    batch_texts, image_parts = [], []
    
    for event in batch:
        content_parts = []
        skip_images = is_group and (config.GROUP_IMAGE_MODE == "none" or (config.GROUP_IMAGE_MODE == "mention" and not any(isinstance(seg, At) and str(seg.qq) == bot_uin for seg in event.message)))
        
        for seg in event.message:
            if isinstance(seg, (Text, PlainText)):
                content_parts.append(seg.text)
            elif isinstance(seg, Image):
                if skip_images:
                    content_parts.append("[图片(群聊未提及机器人，已忽略)]")
                else:
                    img_part, text_desc = await process_image_segment(seg, session_id, is_group, len(image_parts)+1, len(batch))
                    if img_part:
                        image_parts.append(img_part)
                    content_parts.append(text_desc)
            elif isinstance(seg, Face):
                content_parts.append(f"(face:{seg.id})")
            elif isinstance(seg, At):
                content_parts.append("@assistant " if str(seg.qq) == bot_uin else f"@{seg.qq} ")
            elif isinstance(seg, AtAll):
                content_parts.append("@全体成员 ")
            elif isinstance(seg, Reply):
                content_parts.append("[回复] ")
        
        msg_text = "".join(content_parts).strip() or event.raw_message
        batch_texts.append(f'<user nick="{event.sender.nickname}" id="{event.user_id}">{msg_text}</user>')

    full_prompt = memory_manager.generate_prompt(full_session_id, "\n".join(batch_texts).strip(), batch[-1].time, is_group=is_group)
    if not full_prompt:
        return
    
    if is_group:
        m_imps = [f"{e.sender.nickname}: {'；'.join(memory_manager.impressions.get(f'{session_id}:{e.user_id}:{persona_name}', []))}" for e in {ev.user_id: ev for ev in batch}.values() if memory_manager.impressions.get(f'{session_id}:{e.user_id}:{persona_name}', [])]
        if m_imps:
            full_prompt = full_prompt.replace("</personality>", "</personality>\n<member_impressions>\n" + "\n".join(m_imps) + "\n</member_impressions>")

    update_active_task(session_id, "正在生成回复内容...", len(batch))
    
    schema_parts = ['"thought": "string"', '"replies": ["string"]']
    if config.ENABLE_SOCIAL_ENERGY:
        schema_parts.extend(['"mood": "string"', '"energy_adjustment": "number"'])
    if config.ENABLE_TOPIC_DETECTION:
        schema_parts.append('"current_topic": "string"')
    schema = '{' + ", ".join(schema_parts) + '}'
    
    sys_instr = "SPECIAL INSTRUCTION: not think silently at all. Silent thinking token budget: 0." if config.AI_FORCE_NO_THINK_INST else ""
    result = await get_json_response(full_prompt, schema, files=image_parts, system_instruction=sys_instr)
    
    if not result:
        await (bot.api.send_group_msg(group_id=int(session_id), message=[{"type": "text", "data": {"text": "AI 思考超时了喵，请稍后再试。"}}] ) if is_group else bot.api.send_private_msg(user_id=int(session_id), message=[{"type": "text", "data": {"text": "AI 思考超时了喵，请稍后再试。"}}] ))
        return

    replies = result.get("replies", []) or ([result["raw_error_content"]] if "raw_error_content" in result else ["AI 陷入了沉思，没有给出具体回复。"])
    if result.get("mood"):
        memory_manager.change_mood(session_id, result["mood"])
    if config.ENABLE_TOPIC_DETECTION and result.get("current_topic"):
        memory_manager.update_topic(full_session_id, result["current_topic"])
    
    # 仅在启用时扣除能量，否则按回复条数记录（内部 logic 会拦截但这里调用的语义更清晰）
    energy_used = len(replies) - float(result.get("energy_adjustment", 0)) if config.ENABLE_SOCIAL_ENERGY else 0
    memory_manager.consume_social_energy(session_id, energy_used)

    for reply_text in replies:
        if not reply_text.strip():
            continue
        try:
            await (bot.api.send_group_msg(group_id=int(session_id), message=parse_cq_codes(reply_text)) if is_group else bot.api.send_private_msg(user_id=int(session_id), message=parse_cq_codes(reply_text)))
        except Exception as e:
            debug_print(2, f"发送回复失败: {e}")
        now_ts = get_now_timestamp()
        memory_manager.chat_history[full_session_id].append({"role": "assistant", "content": reply_text, "time": format_timestamp(now_ts)})
        memory_manager.save_message_to_file(full_session_id, "assistant", reply_text, now_ts)
        await asyncio.sleep(0.5)

    memory_manager.check_and_trigger_consolidation(full_session_id, is_group=is_group)
