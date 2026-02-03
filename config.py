
import os
import yaml
from dotenv import load_dotenv

# 加载 .env 环境变量
load_dotenv()

class Config:
    # API 配置
    OPENAI_API_BASE = os.getenv("BASE_URL")
    OPENAI_API_KEY = os.getenv("API_KEY")
    
    # 模型默认参数
    MODEL_NAME = "z-ai/glm4.7"
    MAX_TOKENS = 16384
    TEMPERATURE = 0.7
    ENABLE_THINKING = True
    
    # 系统提示词
    with open("text_for_gen/prompts.yaml", "r", encoding="utf-8") as f:
        _prompts = yaml.safe_load(f)
        SYSTEM_PROMPT = _prompts["writer_prompt"] + "\n" + _prompts["background_prompt"]
    
    # 路径配置
    PATHS = {
        "WORLD_SETTINGS": "world_settings.json",
        "WEEKLY_SCRIPT": "weekly_script.json",
        "SAVE_STATE": "save_state.json",
        "COURSE_DB": "novel_engine/data/storage/course_data.db",
        "WORLD_DB": "novel_engine/data/storage/world_data.db",
        "CHAPTERS_DIR": "novel_chapters"
    }
