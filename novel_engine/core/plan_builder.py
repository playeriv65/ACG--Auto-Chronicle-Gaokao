from __future__ import annotations

"""Build world settings and weekly scripts from simulation output."""

import os
import sqlite3
import time
from typing import List, Protocol

from config import Config
from novel_engine.core.being_engine import BeingEngine
from novel_engine.core.contracts import (
    QuizContent,
    SystemPrompt,
    WeeklyEntry,
    WeeklyRankings,
    WeeklyScript,
    WeeklyScriptMeta,
    WorldSettings,
    WorldSettingsMeta,
)
from novel_engine.core.presenters import render_mc_report

KEY_LOG_PREFIXES = ("【突发】", "【战报】", "【道心抉择】", "【突破】")
INFO_TRACK_EVENT_TEXT = "开启信奥"


class QuizGenerator(Protocol):
    def __call__(self, subject: str, topic: str) -> str:
        ...


class PlanBuilder:
    """Builds world settings and weekly script artifacts for three school years."""

    def __init__(self, quiz_db_path: str, quiz_generator: QuizGenerator):
        if not os.path.exists(quiz_db_path):
            raise FileNotFoundError(f"Quiz DB not found: {quiz_db_path}")
        self.quiz_db_path = quiz_db_path
        self.quiz_generator = quiz_generator

    def build(self, engine: BeingEngine) -> tuple[WorldSettings, WeeklyScript]:
        world_settings = self._build_world_settings_template(engine)
        weekly_script = self._build_weekly_script_template()

        for year in range(1, Config.SCHOOL_YEARS + 1):
            engine.year = year
            for semester in range(1, Config.SEMESTERS_PER_YEAR + 1):
                engine.semester = semester
                print(f" -> 正在推演: 高{year}{'上' if semester == 1 else '下'}...")

                for week in range(1, Config.WEEKS_PER_SEMESTER + 1):
                    date_key, entry = self._build_week_entry(engine, year, semester, week)
                    weekly_script.weeks[date_key] = entry

        return world_settings, weekly_script

    def _get_week_date_from_db(self, abs_week: int) -> str:
        with sqlite3.connect(self.quiz_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT start_date FROM curriculum WHERE week=?", (abs_week,))
            row = cursor.fetchone()

        if row is None or not row[0]:
            raise ValueError(f"Missing curriculum date for abs_week={abs_week}")
        return str(row[0])

    def _upsert_or_read_quiz_cache(self, week: int, subject: str, topic: str, content: str | None = None) -> str | None:
        with sqlite3.connect(self.quiz_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "CREATE TABLE IF NOT EXISTS quiz "
                "(id INTEGER PRIMARY KEY AUTOINCREMENT, week INTEGER, subject TEXT, topic TEXT, content TEXT, "
                "UNIQUE(week, subject, topic))"
            )
            if content is None:
                cursor.execute(
                    "SELECT content FROM quiz WHERE week=? AND subject=? AND topic=?",
                    (week, subject, topic),
                )
                row = cursor.fetchone()
                return str(row[0]) if row and row[0] else None

            cursor.execute(
                "INSERT OR REPLACE INTO quiz (week, subject, topic, content) VALUES (?, ?, ?, ?)",
                (week, subject, topic, content),
            )
            conn.commit()
            return content

    def _extract_key_details(self, logs: List[str]) -> List[str]:
        details: List[str] = []
        for log in logs:
            if log.startswith(KEY_LOG_PREFIXES) or INFO_TRACK_EVENT_TEXT in log:
                details.append(log)
        return details

    def _build_world_settings_template(self, engine: BeingEngine) -> WorldSettings:
        return WorldSettings(
            meta=WorldSettingsMeta(
                title="《拮抗中学：众生相》",
                generated_at=time.strftime("%Y-%m-%d %H:%M:%S"),
                description="Static world data and character settings.",
                system_prompt=SystemPrompt(
                    role="顶级爽文作家",
                    style="维持高武侠风格，细致入微，热血沸腾",
                    background="硬核高考修仙世界观",
                    requirements="单章4000字，禁止烂尾，多用短句，节奏紧凑",
                ),
            ),
            characters=[engine.build_character_profile(student) for student in engine.students],
        )

    def _build_weekly_script_template(self) -> WeeklyScript:
        return WeeklyScript(
            meta=WeeklyScriptMeta(
                title="《拮抗中学：三年因果》",
                generated_at=time.strftime("%Y-%m-%d %H:%M:%S"),
                description="Dynamic weekly events and plot points.",
            ),
            weeks={},
        )

    def _resolve_quiz_content(self, abs_week: int, week: int, quiz_raw: QuizContent | None) -> str | None:
        if quiz_raw is None:
            return None

        if quiz_raw.kind == "direct":
            if quiz_raw.content is None:
                raise RuntimeError("Direct quiz content is missing")
            return quiz_raw.content

        if quiz_raw.subject is None or quiz_raw.topic is None:
            raise RuntimeError("Fallback quiz must include subject and topic")

        cached = self._upsert_or_read_quiz_cache(abs_week, quiz_raw.subject, quiz_raw.topic)
        if cached:
            return cached

        print(f"    [Week {week:02d}] 正在请‘判官’命题: {quiz_raw.topic}...")
        generated = self.quiz_generator(quiz_raw.subject, quiz_raw.topic)
        if not generated:
            raise RuntimeError(
                f"Quiz generation failed for week={week} subject={quiz_raw.subject} topic={quiz_raw.topic}"
            )
        return self._upsert_or_read_quiz_cache(abs_week, quiz_raw.subject, quiz_raw.topic, generated)

    def _build_week_entry(
        self,
        engine: BeingEngine,
        year: int,
        semester: int,
        week: int,
    ) -> tuple[str, WeeklyEntry]:
        logs, battle_type, quiz_raw = engine.tick(week)
        abs_week = (year - 1) * Config.WEEKS_PER_YEAR + (semester - 1) * Config.WEEKS_PER_SEMESTER + week
        quiz_final = self._resolve_quiz_content(abs_week, week, quiz_raw)
        date_key = f"G{year}S{semester}_W{week:02d}"
        entry = self._build_week_data(
            engine=engine,
            battle_type=battle_type,
            logs=logs,
            quiz_final=quiz_final,
            abs_week=abs_week,
        )
        return date_key, entry

    def _build_week_data(
        self,
        engine: BeingEngine,
        battle_type: str,
        logs: List[str],
        quiz_final: str | None,
        abs_week: int,
    ) -> WeeklyEntry:
        rankings = engine.get_rankings()
        if not rankings:
            raise RuntimeError("rankings is empty when building weekly data")
        top_student = rankings[0].name
        return WeeklyEntry(
            event=battle_type,
            date=self._get_week_date_from_db(abs_week),
            details=self._extract_key_details(logs),
            quiz=quiz_final,
            rankings=WeeklyRankings(mc_report=render_mc_report(engine.build_mc_report()), top_student=top_student),
        )
