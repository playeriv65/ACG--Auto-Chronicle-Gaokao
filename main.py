from __future__ import annotations

import argparse
import io
import json
import os
import random
import sys
import time
from typing import Tuple

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
sys.path.append(os.getcwd())

from config import Config
from novel_engine.core.ai_writer import writer
from novel_engine.core.being_engine import BeingEngine
from novel_engine.core.contracts import RuntimeState, WeeklyScript, WorldSettings
from novel_engine.core.presenters import render_student_detail
from novel_engine.data.database import get_random_event

CHAPTER_DIR = Config.PATHS["CHAPTERS_DIR"]
SAVE_FILE = Config.PATHS["SAVE_STATE"]
WORLD_SETTINGS_FILE = Config.PATHS["WORLD_SETTINGS"]
WEEKLY_SCRIPT_FILE = Config.PATHS["WEEKLY_SCRIPT"]


def parse_chapter_range(value: str) -> Tuple[int, int]:
    if "-" not in value:
        raise argparse.ArgumentTypeError("chapter range format must be START-END, e.g. 3-8")
    start_str, end_str = value.split("-", 1)
    if not start_str.isdigit() or not end_str.isdigit():
        raise argparse.ArgumentTypeError("chapter range START and END must be positive integers")
    start = int(start_str)
    end = int(end_str)
    if start <= 0 or end <= 0:
        raise argparse.ArgumentTypeError("chapter range values must be >= 1")
    if start > end:
        raise argparse.ArgumentTypeError("chapter range START must be <= END")
    return start, end


class NovelGenerator:
    def __init__(self) -> None:
        self.engine = BeingEngine()
        self.engine.simulation_source = "novel_generation"
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
        return Config.MAIN_SYSTEM_INSTRUCTION_TEMPLATE.format(
            role=prompt_config.role,
            style=prompt_config.style,
            requirements=prompt_config.requirements,
            chapter_end_marker=Config.CHAPTER_END_MARKER,
        )

    def _build_random_event_placeholders(self) -> dict[str, str]:
        names = [p.name for p in (self.engine.students + self.engine.teachers)]
        if not names:
            raise RuntimeError("Cannot build event placeholders: no characters in engine state")
        shuffled = random.sample(names, k=len(names))
        picked = shuffled[:4]
        while len(picked) < 4:
            picked.append(picked[0])
        return {f"p{i + 1}": picked[i] for i in range(4)}

    def _sample_dynamic_chapter_details(self) -> list[str]:
        details: list[str] = []
        for _ in range(Config.CHAPTER_DYNAMIC_EVENT_COUNT):
            placeholders = self._build_random_event_placeholders()
            event = get_random_event("ANY", placeholders=placeholders)
            details.append(f"【互动模板】{event.description}")
        return details

    def _build_prompt(self, date_key: str, battle_type: str, mc_detail_text: str, quiz_content: str | None) -> str:
        plan_data = self.weekly_script.weeks.get(date_key)
        if plan_data is None:
            raise KeyError(f"Missing weekly script entry: {date_key}")
        if not plan_data.details:
            raise ValueError(f"Weekly script details missing for {date_key}")

        details = list(plan_data.details)
        details.extend(self._sample_dynamic_chapter_details())
        details_text = "\n".join(details)
        return Config.MAIN_SCENE_PROMPT_TEMPLATE.format(
            world_description=self.world_settings.meta.description,
            date_key=date_key,
            plan_date=plan_data.date,
            battle_type=battle_type,
            details_text=details_text,
            mc_detail_text=mc_detail_text,
            quiz_text=quiz_content or Config.MAIN_QUIZ_EMPTY_TEXT,
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

    def _run_single_chapter(self) -> None:
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
            Config.MAIN_SCENE_STATS_CONTEXT,
            system_instruction=system_instruction,
            min_length=Config.CHAPTER_MIN_LENGTH,
            max_length=2000,
        )
        self._write_chapter(date_key, content)
        print(f" Done ({len(content)} chars)")

    def run(self) -> None:
        while self.year <= Config.SCHOOL_YEARS:
            self._run_single_chapter()

    def run_chapter_range(self, start_chapter: int, end_chapter: int) -> None:
        if start_chapter <= 0 or end_chapter <= 0:
            raise ValueError("chapter index must be >= 1")
        if start_chapter > end_chapter:
            raise ValueError("start_chapter must be <= end_chapter")
        if self.chapter_count != start_chapter:
            raise ValueError(
                f"Current chapter_count is {self.chapter_count}, but requested range starts at {start_chapter}. "
                "Please align save_state.json with the range start."
            )

        while self.year <= Config.SCHOOL_YEARS and self.chapter_count <= end_chapter:
            self._run_single_chapter()

        if self.chapter_count <= end_chapter:
            raise RuntimeError(
                f"Reached timeline end before chapter {end_chapter}. Current chapter_count={self.chapter_count}."
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="天道自动写作大阵 - 核心推进器")
    parser.add_argument("--debug", action="store_true", help="开启调试模式，输出完整 AI 提示词")
    parser.add_argument("--chapter", type=int, help="只写指定章节（例如: --chapter 6）")
    parser.add_argument("--chapter-range", type=parse_chapter_range, help="只写指定章节范围（例如: --chapter-range 6-10）")
    args = parser.parse_args()

    if args.debug:
        writer.debug = True
        print(" [SYSTEM] 已开启调试模式，将输出完整 AI 提示词。")

    if args.chapter is not None and args.chapter_range is not None:
        raise ValueError("--chapter and --chapter-range are mutually exclusive")

    generator = NovelGenerator()
    if args.chapter is not None:
        generator.run_chapter_range(args.chapter, args.chapter)
    elif args.chapter_range is not None:
        start, end = args.chapter_range
        generator.run_chapter_range(start, end)
    else:
        generator.run()
