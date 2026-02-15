from __future__ import annotations

import os
from typing import Any, Dict, Mapping

import yaml
from dotenv import load_dotenv

load_dotenv()


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _require_prompt_str(prompts: Mapping[str, Any], *path: str) -> str:
    current: Any = prompts
    visited: list[str] = []
    for key in path:
        visited.append(key)
        if not isinstance(current, Mapping) or key not in current:
            raise RuntimeError(f"Missing prompts.yaml key: {'.'.join(visited)}")
        current = current[key]
    if not isinstance(current, str):
        raise RuntimeError(f"Invalid prompts.yaml value type for {'.'.join(path)}: expected str")
    return current


class Config:
    OPENAI_API_BASE: str = _require_env("BASE_URL")
    OPENAI_API_KEY: str = _require_env("API_KEY")
    MODEL_NAME: str = _require_env("MODEL_NAME")

    MAX_TOKENS: int = 16384
    TEMPERATURE: float = 0.7
    ENABLE_THINKING: bool = True

    with open("text_for_gen/prompts.yaml", "r", encoding="utf-8") as f:
        _prompts_raw = yaml.safe_load(f)
        if not isinstance(_prompts_raw, dict):
            raise RuntimeError("Invalid prompts.yaml format: expected mapping")
        _prompts: dict[str, Any] = _prompts_raw
        SYSTEM_PROMPT: str = f"{_require_prompt_str(_prompts, 'writer_prompt')}\n{_require_prompt_str(_prompts, 'background_prompt')}"

        CHAPTER_END_MARKER: str = _require_prompt_str(_prompts, "ai_writer", "chapter_end_marker")
        CONTINUE_EXPAND_PROMPT: str = _require_prompt_str(_prompts, "ai_writer", "continue_expand_prompt")
        TRUNCATION_NOTICE: str = _require_prompt_str(_prompts, "ai_writer", "truncation_notice")
        SCENE_USER_PROMPT_TEMPLATE: str = _require_prompt_str(_prompts, "ai_writer", "scene", "user_template")
        QUIZ_SYSTEM_PROMPT: str = _require_prompt_str(_prompts, "ai_writer", "quiz", "system")
        QUIZ_USER_PROMPT_TEMPLATE: str = _require_prompt_str(_prompts, "ai_writer", "quiz", "user_template")
        SUMMARY_SYSTEM_PROMPT: str = _require_prompt_str(_prompts, "ai_writer", "summary", "system")
        SUMMARY_INSTRUCTION_TEMPLATE: str = _require_prompt_str(_prompts, "ai_writer", "summary", "instruction_template")
        SUMMARY_USER_PROMPT_TEMPLATE: str = _require_prompt_str(_prompts, "ai_writer", "summary", "user_template")
        MAIN_SCENE_STATS_CONTEXT: str = _require_prompt_str(_prompts, "main", "scene_stats_context")
        MAIN_SYSTEM_INSTRUCTION_TEMPLATE: str = _require_prompt_str(_prompts, "main", "system_instruction_template")
        MAIN_SCENE_PROMPT_TEMPLATE: str = _require_prompt_str(_prompts, "main", "scene_prompt_template")
        MAIN_QUIZ_EMPTY_TEXT: str = _require_prompt_str(_prompts, "main", "quiz_empty_text")

    PATHS: Dict[str, str] = {
        "WORLD_SETTINGS": "world_settings.json",
        "WEEKLY_SCRIPT": "weekly_script.json",
        "SAVE_STATE": "save_state.json",
        "SIMULATION_LOG": "simulation_trace.jsonl",
        "COURSE_DB": "novel_engine/data/storage/course_data.db",
        "WORLD_DB": "novel_engine/data/storage/world_data.db",
        "CHAPTERS_DIR": "novel_chapters",
    }

    SCHOOL_YEARS: int = 3
    SEMESTERS_PER_YEAR: int = 2
    WEEKS_PER_SEMESTER: int = 20
    WEEKS_PER_YEAR: int = WEEKS_PER_SEMESTER * SEMESTERS_PER_YEAR
    MONTHLY_EXAM_INTERVAL: int = 4

    DEFAULT_CLASSMATE_COUNT: int = 28
    RANDOM_EVENT_FOCUS_COUNT: int = 3
    INFO_OLYMPIAD_UNLOCK_ABS_WEEK: int = 11

    PROTAGONIST_SKILL_BREAKTHROUGH_PROB: float = 0.4
    NORMAL_STUDENT_SKILL_BREAKTHROUGH_PROB: float = 0.1
    INFO_OLYMPIAD_CONFLICT_PROB: float = 0.15

    PROTAGONIST_NAME: str = "叶凌天"
    RIVAL_NAME: str = "顾辞远"
    FALLBACK_RANK: int = 999

    CHAPTER_MIN_LENGTH: int = 4000
    CHAPTER_DYNAMIC_EVENT_COUNT: int = 2

    PROTAGONIST_BASE_TALENT: int = 100
    PROTAGONIST_INFO_TALENT: int = 300
    PROTAGONIST_MASTERY_MIN: int = 100
    PROTAGONIST_MASTERY_MAX: int = 400
    PROTAGONIST_INFO_MASTERY: float = 0.0

    ELITE_TAGS = ("天赋怪", "卷王")
    ELITE_TALENT_MIN: int = 120
    ELITE_TALENT_MAX: int = 180
    NORMAL_TALENT_MIN: int = 90
    NORMAL_TALENT_MAX: int = 130
    ELITE_MASTERY_MIN: int = 2500
    ELITE_MASTERY_MAX: int = 4000
    NORMAL_MASTERY_MIN: int = 800
    NORMAL_MASTERY_MAX: int = 1500

    DEFAULT_MOOD: int = 50
    DEFAULT_STRESS: int = 0
    DEFAULT_FATIGUE: int = 0
    DEFAULT_LAST_WEEK_RANK: int = 0

    EXAM_STRESS_INCREMENT: int = 15
    INFO_OPTIONAL_START_WEEK: int = 10
    INFO_OPTIONAL_FOCUS_PROB: float = 0.5
    FATIGUE_BREAKDOWN_THRESHOLD: int = 90
    FATIGUE_RESET_AFTER_BREAKDOWN: int = 40
    BREAKDOWN_MASTERY_PENALTY: float = 0.95

    BASE_GROWTH_FACTOR: float = 5.0
    ELITE_GROWTH_MULTIPLIER: float = 1.3
    INFO_GROWTH_MULTIPLIER: float = 2.5
    NON_FOCUS_GROWTH_MULTIPLIER: float = 0.2
    FOCUS_FATIGUE_COST: int = 5

    EXAM_SCORE_CAP: int = 150
    EXAM_SCORE_DIVISOR: float = 50.0
    EXAM_PENALTY_DIVISOR: float = 500.0
    SKILL_SUBJECT_BONUS: float = 100.0
