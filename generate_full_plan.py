from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict

sys.path.append(os.getcwd())

from novel_engine.core.ai_writer import writer
from novel_engine.core.being_engine import BeingEngine
from novel_engine.core.plan_builder import PlanBuilder

WORLD_SETTINGS_FILE = "world_settings.json"
WEEKLY_SCRIPT_FILE = "weekly_script.json"
QUIZ_DB = "novel_engine/data/storage/course_data.db"


def save_plan_outputs(world_settings: Dict[str, Any], weekly_script: Dict[str, Any]) -> None:
    with open(WORLD_SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(world_settings, f, ensure_ascii=False, indent=2)
    print(f"[SUCCESS] 世界观设定已刻录: {WORLD_SETTINGS_FILE}")

    with open(WEEKLY_SCRIPT_FILE, "w", encoding="utf-8") as f:
        json.dump(weekly_script, f, ensure_ascii=False, indent=2)
    print(f"[SUCCESS] 三年因果剧本已刻录: {WEEKLY_SCRIPT_FILE}")


def run_plan() -> None:
    print("正在开启‘造化鼎’（缓存增强版），推演拮抗中学三年因果...")

    engine = BeingEngine()
    engine.init_world()

    builder = PlanBuilder(quiz_db_path=QUIZ_DB, quiz_generator=writer.generate_quiz)
    world_settings, weekly_script = builder.build(engine)
    save_plan_outputs(world_settings, weekly_script)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="造化鼎 - 三年剧本推演工具")
    parser.add_argument("--debug", action="store_true", help="开启调试模式，输出完整 AI 提示词")
    args = parser.parse_args()

    if args.debug:
        writer.debug = True
        print(" [SYSTEM] 已开启调试模式，将输出完整 AI 提示词。")

    run_plan()
