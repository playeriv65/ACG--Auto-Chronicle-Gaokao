from __future__ import annotations

"""Build world settings and weekly scripts from simulation output."""

import os
import sqlite3
import time
from typing import Any, Callable, Dict, List, Optional, Protocol, TypedDict

from config import Config
from novel_engine.core.being_engine import BeingEngine

KEY_LOG_PREFIXES = ("【突发】", "【战报】", "【道心抉择】", "【突破】")
INFO_TRACK_EVENT_TEXT = "开启信奥"
AI_GENERATED_QUIZ_TYPE = "AI_GENERATED"


class WeeklyRankings(TypedDict):
    mc_report: str
    top_student: str


class WeeklyData(TypedDict):
    event: str
    date: str
    details: List[str]
    quiz: Optional[str]
    rankings: WeeklyRankings


class QuizGenerator(Protocol):
    """Callable signature for quiz generation integration."""

    def __call__(self, subject: str, topic: str) -> Optional[str]:
        ...


class PlanBuilder:
    """Builds world settings and weekly script artifacts for three school years."""

    def __init__(self, quiz_db_path: str, quiz_generator: QuizGenerator):
        self.quiz_db_path = quiz_db_path
        self.quiz_generator = quiz_generator

    def build(self, engine: BeingEngine) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """Run full-year simulation and return JSON-ready artifacts."""
        # Outer loops define the canonical chronological traversal for script materialization.
        world_settings = self._build_world_settings_template(engine)
        weekly_script = self._build_weekly_script_template()

        for year in range(1, Config.SCHOOL_YEARS + 1):
            engine.year = year
            for semester in range(1, Config.SEMESTERS_PER_YEAR + 1):
                engine.semester = semester
                print(f" -> 正在推演: 高{year}{'上' if semester == 1 else '下'}...")

                for week in range(1, Config.WEEKS_PER_SEMESTER + 1):
                    logs, battle_type, quiz_raw = engine.tick(week)
                    abs_week = self._to_abs_week(year, semester, week)
                    quiz_final = self._resolve_quiz_content(abs_week, week, quiz_raw)

                    date_key = self._to_date_key(year, semester, week)
                    weekly_script["weeks"][date_key] = self._build_week_data(
                        engine=engine,
                        battle_type=battle_type,
                        logs=logs,
                        quiz_final=quiz_final,
                        abs_week=abs_week,
                    )

        return world_settings, weekly_script

    def _to_abs_week(self, year: int, semester: int, week: int) -> int:
        return (year - 1) * Config.WEEKS_PER_YEAR + (semester - 1) * Config.WEEKS_PER_SEMESTER + week

    def _to_date_key(self, year: int, semester: int, week: int) -> str:
        return f"G{year}S{semester}_W{week:02d}"

    def _get_week_date_from_db(self, abs_week: int) -> str:
        if not os.path.exists(self.quiz_db_path):
            return "未知日期"

        try:
            with sqlite3.connect(self.quiz_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT start_date FROM curriculum WHERE week=?", (abs_week,))
                row = cursor.fetchone()
                return row[0] if row else "未知日期"
        except sqlite3.Error:
            return "未知日期"

    # Cache table stores already generated questions for deterministic replay.
    def _get_cached_quiz(self, week: int, subject: str, topic: str) -> Optional[str]:
        if not os.path.exists(self.quiz_db_path):
            return None

        try:
            with sqlite3.connect(self.quiz_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT content FROM quiz WHERE week=? AND subject=? AND topic=?",
                    (week, subject, topic),
                )
                row = cursor.fetchone()
                return row[0] if row else None
        except sqlite3.Error:
            return None

    def _save_quiz_to_cache(self, week: int, subject: str, topic: str, content: str) -> None:
        try:
            with sqlite3.connect(self.quiz_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "CREATE TABLE IF NOT EXISTS quiz "
                    "(id INTEGER PRIMARY KEY AUTOINCREMENT, week INTEGER, subject TEXT, topic TEXT, content TEXT, "
                    "UNIQUE(week, subject, topic))"
                )
                cursor.execute(
                    "INSERT OR REPLACE INTO quiz (week, subject, topic, content) VALUES (?, ?, ?, ?)",
                    (week, subject, topic, content),
                )
                conn.commit()
        except sqlite3.Error as e:
            print(f" [DB Error] {e}")

    def _extract_key_details(self, logs: List[str]) -> List[str]:
        details: List[str] = []
        for log in logs:
            if log.startswith(KEY_LOG_PREFIXES) or INFO_TRACK_EVENT_TEXT in log:
                details.append(log)
        return details

    def _build_world_settings_template(self, engine: BeingEngine) -> Dict[str, Any]:
        generated_at = time.strftime("%Y-%m-%d %H:%M:%S")
        world_settings: Dict[str, Any] = {
            "meta": {
                "title": "《拮抗中学：众生相》",
                "generated_at": generated_at,
                "description": "Static world data and character settings.",
                "system_prompt": {
                    "role": "顶级爽文作家",
                    "style": "维持高武侠风格，细致入微，热血沸腾",
                    "background": "硬核高考修仙世界观",
                    "requirements": "单章4000字，禁止烂尾，多用短句，节奏紧凑",
                },
            },
            "characters": [],
        }

        # Snapshot the initialized cast so later generation can replay the same setup.
        for student in engine.students:
            world_settings["characters"].append(
                {
                    "name": student.name,
                    "gender": student.gender,
                    "background": student.get_soul_desc(),
                    "tags": str(student.tags),
                }
            )
        return world_settings

    def _build_weekly_script_template(self) -> Dict[str, Any]:
        return {
            "meta": {
                "title": "《拮抗中学：三年因果》",
                "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "description": "Dynamic weekly events and plot points.",
            },
            "weeks": {},
        }

    def _resolve_quiz_content(self, abs_week: int, week: int, quiz_raw: Any) -> Any:
        # Only AI placeholder payloads enter cache/generate path; concrete quiz text passes through unchanged.
        # Only AI placeholders need cache + generation workflow.
        if not (quiz_raw and isinstance(quiz_raw, dict) and quiz_raw.get("type") == AI_GENERATED_QUIZ_TYPE):
            return quiz_raw

        subject = quiz_raw["subject"]
        topic = quiz_raw["topic"]

        cached = self._get_cached_quiz(abs_week, subject, topic)
        if cached:
            return cached

        print(f"    [Week {week:02d}] 正在请‘判官’命题: {topic}...")
        generated = self.quiz_generator(subject, topic)
        if generated:
            self._save_quiz_to_cache(abs_week, subject, topic, generated)
        return generated

    def _build_week_data(
        self,
        engine: BeingEngine,
        battle_type: str,
        logs: List[str],
        quiz_final: Any,
        abs_week: int,
    ) -> WeeklyData:
        """Assemble one week entry with event, ranking and quiz data."""
        rankings = engine.get_rankings()
        top_student = rankings[0].name if rankings else ""

        return {
            "event": battle_type,
            "date": self._get_week_date_from_db(abs_week),
            "details": self._extract_key_details(logs),
            "quiz": str(quiz_final) if quiz_final else None,
            "rankings": {
                "mc_report": engine.get_mc_report(),
                "top_student": top_student,
            },
        }
