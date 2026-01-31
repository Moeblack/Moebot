import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# API 配置
GEMINI_MODEL = "gemini-3-flash"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_API_KEY_HERE")
DEFAULT_GEMINI_URL = f"https://gravity.kuronet.top/v1beta/models/{GEMINI_MODEL}:generateContent"
GEMINI_URL = os.getenv("GEMINI_URL", DEFAULT_GEMINI_URL)

# 日志配置: 0-DEBUG, 1-INFO, 2-WARNING, 3-ERROR
LOG_LEVEL = 0 

# 时区配置
TIMEZONE_OFFSET = 8

# 表情配置
EMOJI_ID_ACK = 76    # 朕已阅 (点赞)
EMOJI_ID_THINK = 324 # 思考中 (思考)

# 社交能量配置
MAX_SOCIAL_ENERGY = 200.0
ENERGY_DECAY_THRESHOLD = 100.0
ENERGY_DECAY_RATE_PER_MIN = 5.0 / 60.0  # 每小时衰减 5 点，转换为每分钟

# 心情对应的中文标签
MOOD_LABEL_MAP = {
    "positive": "愉快",
    "normal": "平静",
    "negative": "低落/疲惫"
}

# 心情对应的回复速率 (每小时)
MOOD_RECOVERY_RATES = {
    "positive": 10.0,
    "normal": 5.0,
    "negative": 2.0
}

# 决策与逻辑硬编码提取
DEFAULT_THINKING_BUDGET = 128
DECISION_HISTORY_LIMIT = 50
COMMAND_PREFIX = "/"
DUPLICATE_QUEUE_SIZE = 100
HISTORY_INJECT_COUNT = 20
CONSOLIDATION_THRESHOLD = 20
