import asyncio
from typing import Optional, Union
from ncatbot.core import BotClient
from ncatbot.core.event import PrivateMessageEvent, GroupMessageEvent

_bot: Optional[BotClient] = None

class SessionState:
    def __init__(self):
        self.message_queue: list[Union[PrivateMessageEvent, GroupMessageEvent]] = []
        self.timer_task: Optional[asyncio.Task] = None
        self.focus_task: Optional[asyncio.Task] = None  # 专注模式循环任务
        self.is_processing: bool = False
        self.is_in_focus: bool = False  # 是否处于显式专注模式
        self.lock: asyncio.Lock = asyncio.Lock()
        self.seen_messages: set = set()
        self.last_decision: Optional[dict] = None
        self.last_interaction_time: float = 0.0  # 最近一次与 AI 互动的时刻 (timestamp)
        self.last_macro_eval_time: float = 0.0  # 最近一次宏观评估时刻
        self.passive_count: int = 0  # 累计记录的背景消息数

user_states: dict[str, SessionState] = {}
