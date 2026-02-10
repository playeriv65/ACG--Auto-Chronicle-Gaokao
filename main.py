from __future__ import annotations

import argparse
import io
import json
import os
import sys
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
sys.path.append(os.getcwd())

from config import Config
from novel_engine.core.ai_writer import writer
from novel_engine.core.being_engine import BeingEngine
from novel_engine.core.contracts import RuntimeState, WeeklyScript, WorldSettings
from novel_engine.core.presenters import render_student_detail

CHAPTER_DIR = Config.PATHS["CHAPTERS_DIR"]
SAVE_FILE = Config.PATHS["SAVE_STATE"]
WORLD_SETTINGS_FILE = Config.PATHS["WORLD_SETTINGS"]
WEEKLY_SCRIPT_FILE = Config.PATHS["WEEKLY_SCRIPT"]


class NovelGenerator:
    def __init__(self) -> None:
        self.engine = BeingEngine()
        self.total_chars: int = 0
        self.chapter_count: int = 1
        self.year: int = 1
        self.semester: int = 1
        self.week: int = 1
        self.world_settings: WorldSettings
        self.weekly_script: WeeklyScript
        self.load_prompt_data()
        self.load_state()

    def load_prompt_data(self) -> None:
        if not os.path.exists(WORLD_SETTINGS_FILE):
            raise FileNotFoundError(f"Missing world settings file: {WORLD_SETTINGS_FILE}")
        if not os.path.exists(WEEKLY_SCRIPT_FILE):
            raise FileNotFoundError(f"Missing weekly script file: {WEEKLY_SCRIPT_FILE}")

        with open(WORLD_SETTINGS_FILE, "r", encoding="utf-8") as f:
            self.world_settings = WorldSettings.model_validate(json.load(f))
        with open(WEEKLY_SCRIPT_FILE, "r", encoding="utf-8") as f:
            self.weekly_script = WeeklyScript.model_validate(json.load(f))

    def load_state(self) -> None:
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                runtime_state = RuntimeState.model_validate(json.load(f))

            self.total_chars = runtime_state.total_chars
            self.chapter_count = runtime_state.chapter_count
            self.year = runtime_state.year
            self.semester = runtime_state.semester
            self.week = runtime_state.week
            self.engine.from_state(runtime_state.engine_state)
            return

        self.engine.init_from_settings(self.world_settings)

    def save_state(self) -> None:
        runtime_state = RuntimeState(
            total_chars=self.total_chars,
            chapter_count=self.chapter_count,
            year=self.year,
            semester=self.semester,
            week=self.week,
            engine_state=self.engine.to_state(),
        )
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(runtime_state.model_dump(mode="json"), f, ensure_ascii=False, indent=2)

    def _build_system_instruction(self) -> str:
        prompt_config = self.world_settings.meta.system_prompt
        return (
            f"你是一个{prompt_config.role}。"
            f"风格要求：{prompt_config.style}。"
            f"创作要求：{prompt_config.requirements}。"
            "完结后输出 [CHAPTER_END]。"
        )

    def _build_prompt(self, date_key: str, battle_type: str, mc_detail_text: str, quiz_content: str | None) -> str:
        plan_data = self.weekly_script.weeks.get(date_key)
        if plan_data is None:
            raise KeyError(f"Missing weekly script entry: {date_key}")
        if not plan_data.details:
            raise ValueError(f"Weekly script details missing for {date_key}")

        details_text = "\n".join(plan_data.details)
        return (
            f"【世界观】\n{self.world_settings.meta.description}\n\n"
            f"【节点】{date_key} ({plan_data.date}) {battle_type}\n"
            f"【剧本大纲】\n{details_text}\n"
            f"【主角现状】{mc_detail_text}\n"
            f"【真题回顾】{quiz_content or '暂无'}"
        )

    def _advance_calendar(self) -> None:
        self.week += 1
        if self.week > Config.WEEKS_PER_SEMESTER:
            self.week = 1
            self.semester = 2 if self.semester == 1 else 1
            if self.semester == 1:
                self.year += 1
            self.engine.year = self.year
            self.engine.semester = self.semester

    def _write_chapter(self, date_key: str, content: str) -> None:
        writer.summarize_chapter(self.chapter_count, content)
        os.makedirs(CHAPTER_DIR, exist_ok=True)
        file_name = f"Chapter_{self.chapter_count:03d}_{date_key}.txt"
        with open(os.path.join(CHAPTER_DIR, file_name), "w", encoding="utf-8") as f:
            f.write(content)
        self.total_chars += len(content)
        self.chapter_count += 1
        self._advance_calendar()
        self.save_state()

    def run(self) -> None:
        while self.year <= Config.SCHOOL_YEARS:
            date_key = f"G{self.year}S{self.semester}_W{self.week:02d}"
            _logs, battle_type, quiz_result = self.engine.tick(self.week)
            mc_detail_dto = self.engine.build_student_detail(self.engine.protagonist.name)
            mc_detail_text = render_student_detail(mc_detail_dto)
            quiz_text = self.engine.build_quiz_prompt_payload(quiz_result)
            prompt = self._build_prompt(date_key, battle_type, mc_detail_text, quiz_text)
            system_instruction = self._build_system_instruction()

            print(f"[{time.strftime('%H:%M:%S')}] Forging: {date_key}...", end="", flush=True)
            content = writer.generate_scene(
                prompt,
                "维持高武侠风格，写满4000字。",
                system_instruction=system_instruction,
                min_length=Config.CHAPTER_MIN_LENGTH,
                max_length=2000,
            )
            self._write_chapter(date_key, content)
            print(f" Done ({len(content)} chars)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="天道自动写作大阵 - 核心推进器")
    parser.add_argument("--debug", action="store_true", help="开启调试模式，输出完整 AI 提示词")
    args = parser.parse_args()

    if args.debug:
        writer.debug = True
        print(" [SYSTEM] 已开启调试模式，将输出完整 AI 提示词。")

    NovelGenerator().run()
