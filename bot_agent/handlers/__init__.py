from ncatbot.core import BotClient
from . import base
from .private import handle_private_message
from .group import handle_group_message

def register_handlers(bot: BotClient):
    """在机器人实例上注册所有处理器"""
    base._bot = bot
    bot.on_private_message()(handle_private_message)  # type: ignore
    bot.on_group_message()(handle_group_message)      # type: ignore
