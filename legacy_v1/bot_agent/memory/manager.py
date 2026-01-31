import os
import asyncio
import datetime
from ..config import DATA_DIR
from ..utils import format_timestamp, debug_print
from . import persistence, logic, prompt
from .social import SocialManager

class MemoryManager:
    def __init__(self):
        self.chat_history, self.episodic_memory, self.personas, self.impressions = {}, {}, {}, {}
        self.active_personas, self.is_consolidating, self.evolution_pity_counter, self.unconsolidated_count = {}, {}, {}, {}
        self.current_topics = {}
        self.social_managers = {}
        self._ensure_data_dir()
        self.load_all_data()

    def _ensure_data_dir(self): os.makedirs(DATA_DIR, exist_ok=True)

    def load_all_data(self):
        state = persistence.load_memory_state()
        self.evolution_pity_counter = state.get("evolution_pity_counter", {})
        self.unconsolidated_count = state.get("unconsolidated_count", {})
        self.current_topics = state.get("current_topics", {})
        social_states = persistence.load_social_state()
        for sid, sstate in social_states.items():
            sm = SocialManager()
            sm.social_energy = sstate.get("social_energy", 200.0)
            sm.mood = sstate.get("mood", "normal")
            sm.last_update_ts = sstate.get("last_update_ts", 0)
            self.social_managers[sid] = sm
        self.active_personas, self.personas, self.impressions = persistence.load_active_personas(), persistence.load_personas(), persistence.load_impressions()
        self.chat_history, self.episodic_memory = persistence.load_chat_history(self.unconsolidated_count), persistence.load_episodic_memory()

    def save_memory_state(self): persistence.save_memory_state(self.evolution_pity_counter, self.unconsolidated_count, self.current_topics)
    
    def save_social_state(self):
        social_states = {
            sid: {
                "social_energy": sm.social_energy,
                "mood": sm.mood,
                "last_update_ts": sm.last_update_ts
            } for sid, sm in self.social_managers.items()
        }
        persistence.save_social_state(social_states)
    def save_active_personas(self): persistence.save_active_personas(self.active_personas)
    
    def check_and_trigger_consolidation(self, sid, is_group=False):
        """检查是否需要触发记忆归档（归档、总结、性格演进）"""
        from .. import config
        if self.unconsolidated_count.get(sid, 0) >= config.HIGH_WATERMARK and not self.is_consolidating.get(sid):
            self.is_consolidating[sid] = True
            count = config.SUMMARY_INTERVAL
            to_sum = self.chat_history.get(sid, [])[:count]
            if to_sum:
                asyncio.create_task(self.consolidate_memory(sid, to_sum, len(to_sum), is_group=is_group))
                return True
            else:
                self.is_consolidating[sid] = False
        return False

    def update_topic(self, sid, topic):
        if not topic or topic == "未知" or topic == "无":
            return
        self.current_topics[sid] = topic
        self.save_memory_state()

    def get_topic(self, sid): return self.current_topics.get(sid, "正在观察话题中...")
    def save_persona_to_file(self, uid, pn, t): persistence.save_persona_to_file(uid, pn, t)
    def save_impression_to_file(self, uid, pn, i): persistence.save_impression_to_file(uid, pn, i)
    def get_social_manager(self, sid):
        # 使用基础 session_id (去掉 persona 后缀)
        base_sid = sid.split(":")[0]
        if base_sid not in self.social_managers:
            self.social_managers[base_sid] = SocialManager()
        return self.social_managers[base_sid]

    def update_social_energy(self, sid): 
        from .. import config
        if not config.ENABLE_SOCIAL_ENERGY:
            return
        self.get_social_manager(sid).update(self.save_social_state)
    
    def consume_social_energy(self, sid, amount=1.0): 
        from .. import config
        if not config.ENABLE_SOCIAL_ENERGY:
            return
        self.get_social_manager(sid).consume(amount, self.save_social_state)
    
    def change_mood(self, sid, mood): 
        from .. import config
        if not config.ENABLE_SOCIAL_ENERGY:
            return
        self.get_social_manager(sid).set_mood(mood, self.save_social_state)
    
    def get_social_energy(self, sid):
        from .. import config
        if not config.ENABLE_SOCIAL_ENERGY:
            return 200.0
        return self.get_social_manager(sid).social_energy
    
    def get_mood(self, sid):
        from .. import config
        if not config.ENABLE_SOCIAL_ENERGY:
            return "normal"
        return self.get_social_manager(sid).mood

    def save_message_to_file(self, sid, role, content, ts=None, nickname=None, user_id=None):
        ts_val = ts or int(datetime.datetime.now().timestamp())
        persistence.save_message_to_file(sid, role, content, format_timestamp(ts_val), nickname=nickname, user_id=user_id)
        self.unconsolidated_count[sid] = self.unconsolidated_count.get(sid, 0) + 1
        self.save_memory_state()

    def generate_prompt(self, sid, msg, time=None, is_group=False):
        self.update_social_energy(sid)
        return prompt.build_prompt(sid, msg, self.chat_history, self.episodic_memory, self.personas, self.impressions, self.get_social_energy(sid), self.get_mood(sid), self.current_topics, time, is_group)

    async def consolidate_memory(self, sid, msgs, count, is_group=False, force=False):
        async def evolve_personality_local(s, m):
            return await logic.evolve_personality(s, m, self.personas, persistence.save_persona_to_file)

        async def evolve_impression_local(s, m):
            return await logic.evolve_impression(s, m, self.impressions, persistence.save_impression_to_file, is_group=is_group)

        try:
            save_funcs = {
                "save_episodic": persistence.save_episodic_to_file,
                "save_memory_state": self.save_memory_state,
                "evolve_personality": evolve_personality_local,
                "evolve_impression": evolve_impression_local
            }
            await logic.consolidate_memory_logic(sid, msgs, self.episodic_memory, self.evolution_pity_counter, self.unconsolidated_count, force, save_funcs)
            if sid in self.chat_history and count > 0 and len(self.chat_history[sid]) >= count:
                self.chat_history[sid] = self.chat_history[sid][count:]
                self.unconsolidated_count[sid] = max(0, self.unconsolidated_count.get(sid, 0) - count)
                self.save_memory_state()
                debug_print(1, f"归档完成: {sid}, 剩余: {self.unconsolidated_count[sid]}")
        except Exception as e:
            debug_print(1, f"归档出错: {e}")
        finally:
            self.is_consolidating[sid] = False

    async def manual_consolidate(self, sid):
        if sid not in self.chat_history or not self.chat_history[sid] or self.is_consolidating.get(sid):
            return "Error"
        self.is_consolidating[sid] = True
        to_sum = list(self.chat_history[sid])
        is_group = sid.startswith("group_") or (sid.split(":")[0].isdigit() and len(sid.split(":")[0]) > 6) # 粗略判断
        actual_count = len(to_sum)
        asyncio.create_task(self.consolidate_memory(sid, to_sum, actual_count, is_group=is_group, force=True))
        return f"Started for {actual_count} msgs"
