import os
import yaml
from .config_defaults import DEFAULT_CONFIG
from .constants import (
    EMOJI_ID_ACK as EMOJI_ID_ACK,
    EMOJI_ID_THINK as EMOJI_ID_THINK,
    MAX_SOCIAL_ENERGY as MAX_SOCIAL_ENERGY, 
    ENERGY_DECAY_THRESHOLD as ENERGY_DECAY_THRESHOLD,
    ENERGY_DECAY_RATE_PER_MIN as ENERGY_DECAY_RATE_PER_MIN,
    MOOD_RECOVERY_RATES as MOOD_RECOVERY_RATES,
    GEMINI_MODEL as GEMINI_MODEL,
    GEMINI_API_KEY as GEMINI_API_KEY,
    GEMINI_URL as GEMINI_URL,
    LOG_LEVEL as LOG_LEVEL,
    TIMEZONE_OFFSET as TIMEZONE_OFFSET,
    MOOD_LABEL_MAP as MOOD_LABEL_MAP,
    DEFAULT_THINKING_BUDGET as DEFAULT_THINKING_BUDGET,
    DECISION_HISTORY_LIMIT as DECISION_HISTORY_LIMIT,
    COMMAND_PREFIX as COMMAND_PREFIX,
    DUPLICATE_QUEUE_SIZE as DUPLICATE_QUEUE_SIZE,
    HISTORY_INJECT_COUNT as HISTORY_INJECT_COUNT,
    CONSOLIDATION_THRESHOLD as CONSOLIDATION_THRESHOLD
)

# 基础文件路径
DATA_DIR = "data"
HISTORY_FILE = os.path.join(DATA_DIR, "chat_history.jsonl")
EPISODIC_FILE = os.path.join(DATA_DIR, "episodic_memory.jsonl")
PERSONA_FILE = os.path.join(DATA_DIR, "personas.jsonl")
IMPRESSION_FILE = os.path.join(DATA_DIR, "user_impressions.jsonl")
ACTIVE_PERSONA_FILE = os.path.join(DATA_DIR, "active_personas.json")
MEMORY_STATE_FILE = os.path.join(DATA_DIR, "memory_state.json")
SOCIAL_STATE_FILE = os.path.join(DATA_DIR, "social_state.json")
AGENT_CONFIG_FILE = "agent_config.yaml"

class ConfigManager:
    def __init__(self):
        self._last_load_time = 0
        if not os.path.exists(AGENT_CONFIG_FILE):
            self._config = DEFAULT_CONFIG.copy()
            self.save_config()
            print(f"[Config] 首次运行，已自动生成默认配置文件: {AGENT_CONFIG_FILE}")
        else:
            self._config = self.load_config()
            
        self._apply_config()
        if os.path.exists(AGENT_CONFIG_FILE):
            self._last_load_time = os.path.getmtime(AGENT_CONFIG_FILE)
    
    def load_config(self):
        if os.path.exists(AGENT_CONFIG_FILE):
            try:
                with open(AGENT_CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            except Exception as e:
                print(f"加载配置文件失败: {e}")
        return DEFAULT_CONFIG.copy()
    
    def save_config(self):
        try:
            with open(AGENT_CONFIG_FILE, 'w', encoding='utf-8') as f:
                yaml.dump(self._config, f, allow_unicode=True, default_flow_style=False)
            if os.path.exists(AGENT_CONFIG_FILE):
                self._last_load_time = os.path.getmtime(AGENT_CONFIG_FILE)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False
    
    def _apply_config(self):
        global MEM_CONF, HIGH_WATERMARK, SUMMARY_INTERVAL, MAX_HISTORY_LENGTH
        global INT_CONF, RESPONSE_WAIT_TIME, GROUP_RESPONSE_WAIT_TIME, GROUP_FOCUS_WINDOW
        global GROUP_PASSIVE_RECORD_CHANCE, GROUP_PASSIVE_SAMPLING_THRESHOLD
        global FOCUS_MICRO_INTERVAL, FOCUS_MACRO_INTERVAL, WHITELIST, GROUP_WHITELIST, DEFAULT_PERSONA_NAME, ENABLE_SOCIAL_ENERGY, ENABLE_TOPIC_DETECTION
        global MULTI_CONF, COMPRESS_TO_WEBP, GROUP_IMAGE_MODE
        global AI_CONF, AI_GLOBAL_SWITCH, AI_MENTION_ONLY, AI_ENABLE_GROUP, AI_ENABLE_PRIVATE, AI_SHOW_THINKING, AI_FORCE_NO_THINK_INST, AI_INTRO_WAIT_TIME
        global BASE_PERSONA_CONFIG, INITIAL_TRAITS
        
        merged = DEFAULT_CONFIG.copy()
        for s, c in self._config.items():
            if s in merged and isinstance(merged[s], dict):
                merged[s].update(c)
            else:
                merged[s] = c
        self._config = merged
        
        MEM_CONF = self._config.get("memory", {})
        HIGH_WATERMARK = MEM_CONF.get("high_watermark", 50)
        SUMMARY_INTERVAL = MEM_CONF.get("summary_interval", 35)
        MAX_HISTORY_LENGTH = HIGH_WATERMARK
        
        INT_CONF = self._config.get("interaction", {})
        RESPONSE_WAIT_TIME = INT_CONF.get("response_wait_time", 2)
        GROUP_RESPONSE_WAIT_TIME = INT_CONF.get("group_response_wait_time", 5)
        GROUP_FOCUS_WINDOW = INT_CONF.get("group_focus_window", 300)
        GROUP_PASSIVE_RECORD_CHANCE = INT_CONF.get("group_passive_record_chance", 0.1)
        GROUP_PASSIVE_SAMPLING_THRESHOLD = INT_CONF.get("group_passive_sampling_threshold", 10)
        FOCUS_MICRO_INTERVAL = INT_CONF.get("focus_micro_interval", 5)
        FOCUS_MACRO_INTERVAL = INT_CONF.get("focus_macro_interval", 60)
        WHITELIST = INT_CONF.get("whitelist", [])
        GROUP_WHITELIST = INT_CONF.get("group_whitelist", [])
        DEFAULT_PERSONA_NAME = INT_CONF.get("default_persona", "default")
        ENABLE_SOCIAL_ENERGY = INT_CONF.get("enable_social_energy", False)
        ENABLE_TOPIC_DETECTION = INT_CONF.get("enable_topic_detection", False)
        
        MULTI_CONF = self._config.get("multimodal", {})
        COMPRESS_TO_WEBP = MULTI_CONF.get("compress_to_webp", True)
        GROUP_IMAGE_MODE = MULTI_CONF.get("group_image_mode", "mention")
        
        AI_CONF = self._config.get("ai", {})
        AI_GLOBAL_SWITCH = AI_CONF.get("global_switch", True)
        AI_MENTION_ONLY = AI_CONF.get("mention_mode_only", False)
        AI_ENABLE_GROUP = AI_CONF.get("enable_group", True)
        AI_ENABLE_PRIVATE = AI_CONF.get("enable_private", True)
        AI_SHOW_THINKING = AI_CONF.get("show_thinking", False)
        AI_FORCE_NO_THINK_INST = AI_CONF.get("force_no_thinking_instruction", True)
        AI_INTRO_WAIT_TIME = AI_CONF.get("intro_wait_time", 2)

        self._base_persona_config, self._initial_traits = self._config.get("persona_definitions", {}), self._config.get("initial_traits", {})
        if 'BASE_PERSONA_CONFIG' in globals():
            BASE_PERSONA_CONFIG.clear()
            BASE_PERSONA_CONFIG.update(self._base_persona_config)
        else:
            BASE_PERSONA_CONFIG = self._base_persona_config
        if 'INITIAL_TRAITS' in globals():
            INITIAL_TRAITS.clear()
            INITIAL_TRAITS.update(self._initial_traits)
        else:
            INITIAL_TRAITS = self._initial_traits
    
    def get_config(self): return self._config.copy()
    def get_section(self, section): return self._config.get(section, {})
    def reset_config(self):
        self._config = DEFAULT_CONFIG.copy()
        self._apply_config()
        return self.save_config()
    
    def update_config(self, section, key, value, source="api"):
        if section not in self._config:
            self._config[section] = {}
        old = self._config[section].get(key)
        self._config[section][key] = value
        self._apply_config()
        from .monitor import log_config_change
        log_config_change(section, key, old, value, source)
        return self.save_config()

    def update_section(self, section, config, source="api"):
        old = self._config.get(section, {})
        self._config[section] = config
        self._apply_config()
        from .monitor import log_config_change
        for k, v in config.items():
            if v != old.get(k):
                log_config_change(section, k, old.get(k), v, source)
        for k in old.keys():
            if k not in config:
                log_config_change(section, k, old[k], None, source)
        return self.save_config()

    def get_base_persona_config(self): return self._base_persona_config.copy()
    def get_initial_traits(self): return self._initial_traits.copy()
    
    def check_and_reload(self):
        """检查配置文件是否有更新，如果有则重新加载"""
        if not os.path.exists(AGENT_CONFIG_FILE):
            return
        mtime = os.path.getmtime(AGENT_CONFIG_FILE)
        if mtime > self._last_load_time:
            print(f"[Config] 检测到配置文件 {AGENT_CONFIG_FILE} 已更新，正在重新加载...")
            self._config = self.load_config()
            self._apply_config()
            self._last_load_time = mtime

    def add_base_persona(self, n, d):
        if n in self._base_persona_config:
            raise ValueError(f"'{n}' exists")
        self._base_persona_config[n] = d
        self._config["persona_definitions"] = self._base_persona_config
        self._apply_config()
        from .monitor import log_config_change
        log_config_change("persona", "add", None, n, "api")
        return self.save_config()

    def update_base_persona(self, n, d):
        if n not in self._base_persona_config:
            raise ValueError(f"'{n}' not exists")
        old = self._base_persona_config[n]
        self._base_persona_config[n] = d
        self._config["persona_definitions"] = self._base_persona_config
        self._apply_config()
        from .monitor import log_config_change
        log_config_change("persona", "update", old, d, "api")
        return self.save_config()

    def delete_base_persona(self, n):
        if n not in self._base_persona_config:
            raise ValueError(f"'{n}' not exists")
        if n == DEFAULT_PERSONA_NAME:
            raise ValueError(f"Cannot delete '{DEFAULT_PERSONA_NAME}'")
        old = self._base_persona_config.pop(n)
        self._config["persona_definitions"] = self._base_persona_config
        self._apply_config()
        from .monitor import log_config_change
        log_config_change("persona", "delete", old, None, "api")
        return self.save_config()

    def add_initial_trait(self, pn, t):
        if pn not in self._initial_traits:
            self._initial_traits[pn] = []
        if t not in self._initial_traits[pn]:
            self._initial_traits[pn].append(t)
        self._config["initial_traits"] = self._initial_traits
        self._apply_config()
        from .monitor import log_config_change
        log_config_change("persona", "trait_add", None, f"{pn}:{t}", "api")
        return self.save_config()

    def remove_initial_trait(self, pn, t):
        if pn not in self._initial_traits or t not in self._initial_traits[pn]:
            raise ValueError("Not exists")
        self._initial_traits[pn].remove(t)
        self._config["initial_traits"] = self._initial_traits
        self._apply_config()
        from .monitor import log_config_change
        log_config_change("persona", "trait_remove", t, None, "api")
        return self.save_config()

config_manager = ConfigManager()
config = config_manager.get_config()
MEM_CONF, INT_CONF, MULTI_CONF, AI_CONF = (
    config_manager.get_section("memory"),
    config_manager.get_section("interaction"),
    config_manager.get_section("multimodal"),
    config_manager.get_section("ai")
)
BASE_PERSONA_CONFIG, INITIAL_TRAITS = (
    config_manager.get_base_persona_config(),
    config_manager.get_initial_traits()
)
