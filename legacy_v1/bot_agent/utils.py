import datetime
import os
import re
from .config import LOG_LEVEL, TIMEZONE_OFFSET

def get_timezone():
    """根据配置获取 timezone 对象"""
    return datetime.timezone(datetime.timedelta(hours=TIMEZONE_OFFSET))

def format_timestamp(ts: int | str) -> str:
    """将 Unix 时间戳转换为指定时区的可读时间"""
    if isinstance(ts, str):
        return ts
    dt = datetime.datetime.fromtimestamp(ts, tz=get_timezone())
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def get_now_timestamp() -> int:
    """获取当前 Unix 时间戳"""
    # timestamp() 本身是 UTC 的，不需要处理时区
    return int(datetime.datetime.now().timestamp())

def get_now_str() -> str:
    """获取当前时区的格式化时间字符串"""
    return datetime.datetime.now(tz=get_timezone()).strftime('%Y-%m-%d %H:%M:%S')

def debug_print(level: int, message: str):
    """
    等级过滤打印
    0: DEBUG, 1: INFO, 2: WARNING, 3: ERROR
    """
    if level >= LOG_LEVEL:
        levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
        prefix = levels[level] if level < len(levels) else "LOG"
        now_str = datetime.datetime.now(tz=get_timezone()).strftime('%H:%M:%S')
        print(f"[{prefix}] [{now_str}] {message}")

def load_emoji_list() -> str:
    """读取并缓存表情列表"""
    path = "memory/emoji_list.md"
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            return ""
    return ""

def parse_cq_codes(text: str) -> list[dict]:
    """
    将包含 CQ 码或正式格式 (face:ID) 的字符串解析为 NcatBot 消息段列表。
    支持 [CQ:face,id=123] 和 (face:123)
    """
    # 匹配 [CQ:face,id=123] 或 (face:123)
    pattern = r'\[CQ:face,id=(\d+)\]|\(face:(\d+)\)'
    segments = []
    last_idx = 0
    
    for match in re.finditer(pattern, text):
        # 添加之前的文本段
        if match.start() > last_idx:
            segments.append({"type": "text", "data": {"text": text[last_idx:match.start()]}})
        
        # 提取表情 ID
        # match.group(1) 对应 CQ 格式，match.group(2) 对应 (face:ID) 格式
        eid = match.group(1) or match.group(2)
        segments.append({"type": "face", "data": {"id": eid}})
            
        last_idx = match.end()
    
    if last_idx < len(text):
        segments.append({"type": "text", "data": {"text": text[last_idx:]}})
    
    # 如果没有任何匹配，返回单文本段
    if not segments and text:
        return [{"type": "text", "data": {"text": text}}]
        
    return segments
