import asyncio
from ..config import (
    RESPONSE_WAIT_TIME, GROUP_RESPONSE_WAIT_TIME, EMOJI_ID_ACK, EMOJI_ID_THINK,
    AI_GLOBAL_SWITCH, AI_ENABLE_GROUP, AI_ENABLE_PRIVATE
)
from ..utils import get_now_timestamp
from ..monitor import update_active_task, remove_active_task
from . import base
from .decisions import fast_entry_decision, fast_micro_decision
from .reply import execute_persona_reply
from .processor_focus import start_focus_mode

async def wait_and_trigger(session_id: str, is_group: bool = False, is_auto_trigger: bool = False) -> None:
    try:
        state = base.user_states.get(session_id)
        update_active_task(session_id, "等待中 (防抖)", len(state.message_queue) if state else 0)
        await asyncio.sleep(GROUP_RESPONSE_WAIT_TIME if is_group else RESPONSE_WAIT_TIME)
        asyncio.create_task(process_session_queue(session_id, is_group, is_auto_trigger))
    except asyncio.CancelledError:
        pass

async def process_session_queue(session_id: str, is_group: bool, is_auto_trigger: bool = False) -> None:
    if not AI_GLOBAL_SWITCH or (is_group and not AI_ENABLE_GROUP) or (not is_group and not AI_ENABLE_PRIVATE):
        return
    state = base.user_states.get(session_id)
    if not state or state.is_processing:
        return
    wait_time = GROUP_RESPONSE_WAIT_TIME if is_group else RESPONSE_WAIT_TIME
    async with state.lock:
        state.is_processing = True
        try:
            while state.message_queue:
                now = get_now_timestamp()
                wait_needed = wait_time - (now - getattr(state.message_queue[-1], "receive_time", state.message_queue[-1].time))
                if wait_needed > 0:
                    update_active_task(session_id, "等待中 (防抖)", len(state.message_queue))
                    await asyncio.sleep(wait_needed)
                    continue
                batch, state.message_queue = state.message_queue[:], []
                if is_group:
                    # 群聊：如果已经在专注模式里，则不再走准入决策，直接走微观决策
                    if state.is_in_focus:
                        update_active_task(session_id, "专注模式 (微观决策中...)", len(batch))
                        decision = await fast_micro_decision(session_id, batch, is_group)
                        action = decision.get("action", "ignore")
                        should_reply, enter_focus = (action == "reply"), False
                        # 专注模式下 ignore / emoji 都不触发“主流程的文字回复生成”
                        if action != "reply":
                            state.last_decision = decision
                            if not state.message_queue:
                                break
                            continue
                    else:
                        update_active_task(session_id, "正在进行准入决策...", len(batch))
                        decision = await fast_entry_decision(session_id, batch, is_group, is_auto_trigger=is_auto_trigger)
                        should_reply, enter_focus = decision.get("reply", True), decision.get("enter_focus", True)
                else:
                    update_active_task(session_id, "正在决策如何回应...", len(batch))
                    decision = await fast_micro_decision(session_id, batch, is_group)
                    action = decision.get("action", "reply")
                    should_reply, enter_focus = (action == "reply"), False
                    # 私聊如果决策为 ignore，则直接跳过后续的表情发送和回复生成
                    if action == "ignore":
                        state.last_decision = decision
                        if not state.message_queue:
                            break
                        continue

                state.last_decision = decision
                emoji_id, bot = decision.get("emoji_id"), base._bot
                emoji_msg_id = None
                if not (is_group and is_auto_trigger and not should_reply) and bot:
                    try:
                        target = str(emoji_id) if emoji_id is not None else str(EMOJI_ID_THINK if should_reply else EMOJI_ID_ACK)
                        res = await (bot.api.send_group_msg(group_id=int(session_id), message=[{"type": "face", "data": {"id": target}}]) if is_group else bot.api.send_private_msg(user_id=int(session_id), message=[{"type": "face", "data": {"id": target}}]))
                        emoji_msg_id = res.get("message_id") if isinstance(res, dict) else res
                    except Exception:
                        pass
                if should_reply and bot:
                    update_active_task(session_id, "正在思考并生成回复...", len(batch))
                    await execute_persona_reply(session_id, batch, bot, is_group)
                    state.last_interaction_time, state.passive_count = get_now_timestamp(), 0
                    if emoji_msg_id and decision.get("withdraw_emoji", True):
                        try:
                            await bot.api.delete_msg(message_id=emoji_msg_id)
                        except Exception:
                            pass
                if is_group and enter_focus and not state.is_in_focus:
                    await start_focus_mode(session_id, is_group)
                elif is_group and enter_focus and state.is_in_focus:
                    state.last_interaction_time = get_now_timestamp()
                if not state.message_queue:
                    break
        finally:
            state.is_processing = False
            if not state.is_in_focus:
                remove_active_task(session_id)
            else:
                update_active_task(session_id, "专注模式 (空闲)", 0)
