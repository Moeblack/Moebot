from __future__ import annotations

from typing import Iterable, Union

from ncatbot.core.event import GroupMessageEvent, PrivateMessageEvent
from ncatbot.core.event.message_segment import Json, XML, Share

from ...utils import debug_print
from .bilibili_card import (
    extract_urls_from_segments_text,
    choose_best_bilibili_url,
    shorten_url,
)


def try_extract_and_shorten_bilibili_from_event(
    event: Union[GroupMessageEvent, PrivateMessageEvent],
) -> str | None:
    """从事件中尝试识别 B 站卡片/链接并转短链。

    设计目标：
    - 兼容 QQ 常见卡片段：Share / Json / XML
    - raw_message 可能没有链接，因此需要扫描卡片 data/url 字段
    - 仅做“识别 + 转短链”，不负责鉴权/是否回复，由上层 handler 决定

    返回：
    - 成功：短链接字符串
    - 失败：None
    """

    raw_msg = (event.raw_message or "").strip()

    candidate_texts: list[str] = [raw_msg]
    for seg in event.message:
        if isinstance(seg, Share):
            candidate_texts.append(seg.url)
        elif isinstance(seg, (Json, XML)):
            candidate_texts.append(seg.data)

    urls = extract_urls_from_segments_text(candidate_texts)

    bili_url = choose_best_bilibili_url(urls)
    if not bili_url:
        return None

    short = shorten_url(bili_url)
    debug_print(0, f"[bili-shortener] shortened={short}")
    if not short:
        debug_print(1, f"B站链接转短链失败，原始链接: {bili_url}")
        return None

    # 避免“原本就是短链”时重复回复
    if short == bili_url:
        return None

    return short
