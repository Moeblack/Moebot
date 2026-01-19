import asyncio
from .. import config
from ..utils import get_now_timestamp, debug_print
from ..monitor import update_active_task, remove_active_task
from . import base
from .processor_utils import fetch_and_inject_history
from .decisions import fast_micro_decision, fast_macro_decision
from .reply import execute_persona_reply

async def start_focus_mode(session_id: str, is_group: bool) -> None:
    state = base.user_states.get(session_id)
    if not state:
        return
    if state.focus_task:
        state.focus_task.cancel()
    
    # 进入专注模式时，拉取历史消息注入
    await fetch_and_inject_history(session_id, is_group)
    
    state.is_in_focus, state.last_macro_eval_time = True, get_now_timestamp()
    state.focus_task = asyncio.create_task(run_focus_loop(session_id, is_group))
    debug_print(1, f"会话 {session_id} 已进入专注模式")

def stop_focus_mode(session_id: str) -> None:
    state = base.user_states.get(session_id)
    if not state:
        return
    state.is_in_focus = False
    if state.focus_task:
        state.focus_task.cancel()
        state.focus_task = None
    remove_active_task(session_id)
    debug_print(1, f"会话 {session_id} 已退出专注模式")

async def run_focus_loop(session_id: str, is_group: bool) -> None:
    state = base.user_states.get(session_id)
    if not state:
        return
    try:
        while state.is_in_focus:
            await asyncio.sleep(config.FOCUS_MICRO_INTERVAL)
            now = get_now_timestamp()
            if now - state.last_macro_eval_time >= config.FOCUS_MACRO_INTERVAL:
                update_active_task(session_id, "专注模式 (宏观评估中...)", 0)
                macro = await fast_macro_decision(session_id, is_group)
                if not macro.get("stay_focus", True):
                    stop_focus_mode(session_id)
                    break
                state.last_macro_eval_time = now
                update_active_task(session_id, "专注模式 (空闲)", 0)
            
            if state.message_queue:
                async with state.lock:
                    batch, state.message_queue = state.message_queue[:], []
                    try:
                        update_active_task(session_id, "专注模式 (微观决策中...)", len(batch))
                        micro = await asyncio.wait_for(fast_micro_decision(session_id, batch, is_group), timeout=15.0)
                        action, emoji_id, bot = micro.get("action", "ignore"), micro.get("emoji_id"), base._bot

                        # 微观决策触发“立即退出专注并静默”
                        if action == "ignore" and "退出专注" in str(micro.get("reason", "")):
                            stop_focus_mode(session_id)
                            break

                        if not bot:
                            continue
                        emoji_msg_id = None
                        if action in ("emoji", "reply"):
                            try:
                                target = str(emoji_id) if emoji_id is not None else str(config.EMOJI_ID_ACK)
                                res = await (bot.api.send_group_msg(group_id=int(session_id), message=[{"type": "face", "data": {"id": target}}]) if is_group else bot.api.send_private_msg(user_id=int(session_id), message=[{"type": "face", "data": {"id": target}}]))
                                emoji_msg_id = res.get("message_id") if isinstance(res, dict) else res
                            except Exception:
                                pass
                        if action == "reply":
                            update_active_task(session_id, "专注模式 (生成回复中...)", len(batch))
                            await asyncio.wait_for(execute_persona_reply(session_id, batch, bot, is_group), timeout=45.0)
                            state.last_interaction_time = state.last_macro_eval_time = get_now_timestamp()
                            if emoji_msg_id and micro.get("withdraw_emoji", True):
                                try:
                                    await bot.api.delete_msg(message_id=emoji_msg_id)
                                except Exception:
                                    pass
                    except (asyncio.TimeoutError, Exception) as e:
                        debug_print(2, f"会话 {session_id} 异常: {e}")
                        state.message_queue = batch + state.message_queue
                    update_active_task(session_id, "专注模式 (空闲)", len(state.message_queue))
    except asyncio.CancelledError:
        pass
    except Exception as e:
        debug_print(3, f"专注循环出错: {e}")
        stop_focus_mode(session_id)
