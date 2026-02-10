import sys
import os
import json
import time
import io
import argparse
from typing import Any, Dict, Optional

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
sys.path.append(os.getcwd())

from novel_engine.core.being_engine import BeingEngine
from novel_engine.core.ai_writer import writer

from config import Config

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
        self.world_settings: Dict[str, Any] = {}
        self.weekly_script: Dict[str, Dict[str, Any]] = {}
        self.load_prompt_data()
        self.load_state()

    def load_prompt_data(self) -> None:
        if os.path.exists(WORLD_SETTINGS_FILE):
            with open(WORLD_SETTINGS_FILE, 'r', encoding='utf-8') as f:
                self.world_settings = json.load(f)
        
        if os.path.exists(WEEKLY_SCRIPT_FILE):
            with open(WEEKLY_SCRIPT_FILE, 'r', encoding='utf-8') as f:
                self.weekly_script = json.load(f).get("weeks", {})

    def load_state(self) -> None:
        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.total_chars, self.chapter_count = data.get('total_chars', 0), data.get('chapter_count', 1)
                    self.year, self.semester, self.week = data.get('year', 1), data.get('semester', 1), data.get('week', 1)
                    if "engine_state" in data:
                        self.engine.from_dict(data["engine_state"])
            except (OSError, ValueError, TypeError, json.JSONDecodeError):
                self.engine.init_from_settings(self.world_settings)
        else:
             # If no save exists, try to load characters from world_settings
            if self.world_settings:
                self.engine.init_from_settings(self.world_settings)
            else:
                self.engine.init_world()

    def save_state(self) -> None:
        state_data = {'total_chars': self.total_chars, 'chapter_count': self.chapter_count, 'year': self.year, 'semester': self.semester, 'week': self.week, 'engine_state': self.engine.to_dict()}
        with open(SAVE_FILE, 'w', encoding='utf-8') as f: json.dump(state_data, f, ensure_ascii=False, indent=2)

    def _get_date_key(self) -> str:
        return f"G{self.year}S{self.semester}_W{self.week:02d}"

    def _get_plan_context(self, date_key: str) -> Dict[str, Any]:
        return self.weekly_script.get(date_key, {})

    def _build_system_instruction(self) -> str:
        prompt_config = self.world_settings.get('meta', {}).get('system_prompt', {})
        role = prompt_config.get("role", "硬核校园爽文作家")
        style = prompt_config.get("style", "维持高武侠风格")
        reqs = prompt_config.get("requirements", "单章4000字，描写细腻")
        return f"你是一个{role}。风格要求：{style}。创作要求：{reqs}。完结后输出 [CHAPTER_END]。"

    def _build_prompt(self, date_key: str, battle_type: str, mc_detail: str, quiz_content: Any) -> str:
        plan_data = self._get_plan_context(date_key)
        plan_details = "\n".join(plan_data.get("details", ["无特殊剧本"]))
        real_date = plan_data.get("date", "未知日期")
        world_context = f"【世界观】\n{self.world_settings.get('meta', {}).get('description', '硬核高考修仙')}\n"
        return (
            f"{world_context}\n【节点】{date_key} ({real_date}) {battle_type}\n"
            f"【剧本大纲】\n{plan_details}\n【主角现状】{mc_detail}\n【真题回顾】{quiz_content or '暂无'}"
        )

    def _advance_calendar(self) -> None:
        self.week += 1
        if self.week > Config.WEEKS_PER_SEMESTER:
            self.week, self.semester = 1, (2 if self.semester == 1 else 1)
            if self.semester == 1:
                self.year += 1
            self.engine.year, self.engine.semester = self.year, self.semester

    def _write_chapter(self, date_key: str, content: str) -> None:
        writer.summarize_chapter(self.chapter_count, content)
        file_name = f"Chapter_{self.chapter_count:03d}_{date_key}.txt"
        with open(os.path.join(CHAPTER_DIR, file_name), "w", encoding="utf-8") as f:
            f.write(content)
        self.total_chars += len(content)
        self.chapter_count += 1
        self._advance_calendar()
        self.save_state()

    def run(self) -> None:
        while self.year <= Config.SCHOOL_YEARS:
            date_str = self._get_date_key()
            logs, battle_type, quiz_content = self.engine.tick(self.week)
            protagonist_name = self.engine.protagonist.name if self.engine.protagonist else ""
            mc_detail = self.engine.get_student_detail(protagonist_name)

            system_instruction = self._build_system_instruction()
            prompt = self._build_prompt(date_str, battle_type, mc_detail, quiz_content)
            print(f"[{time.strftime('%H:%M:%S')}] Forging: {date_str}...", end="", flush=True)
            
            try:
                content = writer.generate_scene(
                    prompt,
                    "维持高武侠风格，写满4000字。",
                    system_instruction=system_instruction,
                    min_length=Config.CHAPTER_MIN_LENGTH,
                )
                if content:
                    self._write_chapter(date_str, content)
                    print(f" Done ({len(content)} chars)")
            except Exception as e:
                print(f" Error: {e}")
                time.sleep(10)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="天道自动写作大阵 - 核心推进器")
    parser.add_argument("--debug", action="store_true", help="开启调试模式，输出完整 AI 提示词")
    args = parser.parse_args()
    
    if args.debug:
        writer.debug = True
        print(" [SYSTEM] 已开启调试模式，将输出完整 AI 提示词。")
        
    NovelGenerator().run()
