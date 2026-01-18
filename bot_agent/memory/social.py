import time
import datetime
from ..config import (
    MAX_SOCIAL_ENERGY, ENERGY_DECAY_THRESHOLD, 
    ENERGY_DECAY_RATE_PER_MIN, MOOD_RECOVERY_RATES
)
from ..utils import debug_print, get_timezone

class SocialManager:
    def __init__(self):
        self.social_energy = 200.0
        self.mood = "normal"
        self.last_update_ts = time.time()

    def update(self, save_func):
        now = time.time()
        # 跨天检测：如果上一次更新是在昨天或更久以前，直接回满能量并重置心情
        last_dt = datetime.datetime.fromtimestamp(self.last_update_ts, tz=get_timezone())
        now_dt = datetime.datetime.fromtimestamp(now, tz=get_timezone())
        if now_dt.date() > last_dt.date():
            self.social_energy = MAX_SOCIAL_ENERGY
            self.mood = "normal"
            self.last_update_ts = now
            save_func()
            debug_print(1, "新的一天，社交能量已重置为 200")
            return

        elapsed = (now - self.last_update_ts) / 60.0
        if elapsed < 1/6:
            return # < 10s
        
        recovered = elapsed * (MOOD_RECOVERY_RATES.get(self.mood, 5.0) / 60.0)
        decay = elapsed * ENERGY_DECAY_RATE_PER_MIN if self.social_energy > ENERGY_DECAY_THRESHOLD else 0.0
        
        self.social_energy = max(0.0, min(MAX_SOCIAL_ENERGY, self.social_energy + recovered - decay))
        self.last_update_ts = now
        save_func()
        debug_print(0, f"社交能量: {self.social_energy:.2f} (+{recovered:.2f}/-{decay:.2f})")

    def consume(self, amount, save_func):
        self.update(save_func)
        self.social_energy = max(0.0, self.social_energy - amount)
        save_func()

    def set_mood(self, mood, save_func):
        if mood in MOOD_RECOVERY_RATES:
            self.mood = mood
            save_func()
