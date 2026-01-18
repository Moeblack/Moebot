# 默认配置
DEFAULT_CONFIG = {
    "memory": {
        "high_watermark": 50,
        "summary_interval": 35,
        "enable_episodic": True
    },
    "interaction": {
        "response_wait_time": 2,
        "group_response_wait_time": 5,
        "group_focus_window": 300,
        "group_passive_record_chance": 0.1,
        "group_passive_sampling_threshold": 10,
        "focus_micro_interval": 5,
        "focus_macro_interval": 60,
        "whitelist": [],
        "default_persona": "default",
        "enable_social_energy": False,
        "enable_topic_detection": False
    },
    "multimodal": {
        "compress_to_webp": True,
        "group_image_mode": "mention"
    },
    "ai": {
        "global_switch": True,
        "mention_mode_only": False,
        "enable_group": True,
        "enable_private": True,
        "show_thinking": False,
        "force_no_thinking_instruction": False,
        "intro_wait_time": 2
    },
    "persona_definitions": {
        "default": "我是 @Moeblack 开发的人工智能bot。性格友好、专业且简练。我具备长期记忆和性格演化功能。注意：我厌恶在群聊中长篇大论，更倾向于言简意赅的表达。"
    },
    "initial_traits": {
        "default": [
            "拥有长期记忆和自动情感演化功能", 
            "会根据不同的用户调整交互模式",
            "群聊环境禁止长篇大论，说话点到为止"
        ]
    }
}
