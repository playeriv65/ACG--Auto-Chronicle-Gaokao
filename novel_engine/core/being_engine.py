from __future__ import annotations

"""Main world simulation orchestrator."""

import json
import random
import time
from typing import Dict, List, Sequence, Tuple

from config import Config
from novel_engine.core.contracts import (
    EngineState,
    PersonProfile,
    QuizContent,
    SkillState,
    TraitType,
    WorldSettings,
)
from novel_engine.core.effects import apply_effect
from novel_engine.core.engine_constants import (
    ALL_SUBJECTS_MARKER,
    CORE_SUBJECTS,
    SUMMER_SEASON,
    WINTER_SEASON,
)
from novel_engine.core.engine_initializer import EngineInitializer
from novel_engine.core.engine_io import get_curriculum_from_db
from novel_engine.core.engine_queries import EngineQueryService
from novel_engine.core.person import Person
from novel_engine.core.presenters import render_battle_report
from novel_engine.core.view_models import BattleReportDTO, MCReportDTO, StudentDetailDTO
from novel_engine.data.database import SkillTree, Subject, get_random_event
from novel_engine.data.quiz_data import QuizDatabase

INFO_TRACK_TRAIT: TraitType = "info_track"


class BeingEngine:
    """Coordinates weekly simulation, world initialization and query DTO building."""

    def __init__(self) -> None:
        self.db_path: str = Config.PATHS["COURSE_DB"]
        self.students: List[Person] = []
        self.teachers: List[Person] = []
        self.protagonist: Person
        self.rankings: List[Person] = []
        self.global_cooldowns: Dict[str, int] = {}
        self.year: int = 1
        self.semester: int = 1
        self.last_battle_subjects: List[str] = []
        self.simulation_source: str = "runtime"
        self.simulation_log_path: str = Config.PATHS["SIMULATION_LOG"]

        self.initializer = EngineInitializer(self)
        self.queries = EngineQueryService(self)
        self.init_world()

    def to_state(self) -> EngineState:
        return EngineState(
            students=[s.to_state() for s in self.students],
            teachers=[t.to_state() for t in self.teachers],
            global_cooldowns=self.global_cooldowns,
            year=self.year,
            semester=self.semester,
            last_battle_subjects=self.last_battle_subjects,
        )

    def from_state(self, state: EngineState) -> None:
        self.students = [Person.from_state(s) for s in state.students]
        self.teachers = [Person.from_state(t) for t in state.teachers]
        protagonist = next((s for s in self.students if s.role == "protagonist"), None)
        if protagonist is None:
            raise ValueError("Invalid engine state: protagonist not found")
        self.protagonist = protagonist

        self.global_cooldowns = dict(state.global_cooldowns)
        self.year = state.year
        self.semester = state.semester
        self.last_battle_subjects = list(state.last_battle_subjects)

    def init_from_settings(self, settings: WorldSettings) -> None:
        self.initializer.init_from_settings(settings)

    def init_world(self) -> None:
        self.initializer.init_world()

    def tick(self, week_idx: int) -> Tuple[List[str], str, QuizContent | None]:
        abs_week = (self.year - 1) * Config.WEEKS_PER_YEAR + (self.semester - 1) * Config.WEEKS_PER_SEMESTER + week_idx
        curriculum = get_curriculum_from_db(self.db_path, abs_week)

        logs: List[str] = []
        is_exam_week = week_idx % Config.MONTHLY_EXAM_INTERVAL == 0
        season = SUMMER_SEASON if (week_idx % Config.WEEKS_PER_SEMESTER) < (Config.WEEKS_PER_SEMESTER // 2) else WINTER_SEASON
        battle_type, battle_subjects = self._resolve_battle_context(is_exam_week)
        self._append_info_track_logs(abs_week, battle_type, logs)
        self._run_students_week(is_exam_week, abs_week, battle_subjects)
        self._run_events_and_breakthroughs(abs_week, season, logs)

        self.calculate_rankings()
        logs.append(self._compose_battle_report(battle_subjects))
        self._update_week_ranks()
        quiz_data = self._resolve_week_quiz(is_exam_week, battle_subjects, curriculum.subjects)
        self._append_simulation_log(
            week_idx=week_idx,
            abs_week=abs_week,
            battle_type=battle_type,
            battle_subjects=battle_subjects,
            logs=logs,
            quiz_data=quiz_data,
        )

        return logs, battle_type, quiz_data

    def calculate_rankings(self) -> None:
        self.queries.calculate_rankings()

    def get_rankings(self) -> List[Person]:
        return self.queries.get_rankings()

    def build_mc_report(self) -> MCReportDTO:
        return self.queries.build_mc_report()

    def build_student_detail(self, name: str) -> StudentDetailDTO:
        return self.queries.build_student_detail(name)

    def build_person_profile(self, person: Person) -> PersonProfile:
        return self.queries.build_person_profile(person)

    def build_quiz_prompt_payload(self, quiz_result: QuizContent | None) -> str | None:
        return self.queries.build_quiz_prompt_payload(quiz_result)

    def _resolve_battle_context(self, is_exam_week: bool) -> tuple[str, List[str]]:
        if is_exam_week:
            return "【全科月考】", [ALL_SUBJECTS_MARKER]

        if self.year == 1:
            candidates = [s for s in CORE_SUBJECTS if s not in self.last_battle_subjects]
            if not candidates:
                raise RuntimeError("No available core subjects for year-1 weekly battle")
            battle_subjects = [random.choice(candidates)]
        elif self.year == 2:
            battle_subjects = [Subject.PHYS, Subject.CHEM, Subject.BIO]
        else:
            battle_subjects = list(CORE_SUBJECTS)

        self.last_battle_subjects = list(battle_subjects)
        return f"【周考·{'/'.join(battle_subjects)}】", battle_subjects

    def _append_info_track_logs(self, abs_week: int, battle_type: str, logs: List[str]) -> None:
        if abs_week == Config.INFO_OLYMPIAD_UNLOCK_ABS_WEEK and self.year == 1:
            if not self.protagonist.has_trait(INFO_TRACK_TRAIT):
                self.protagonist.traits.append(INFO_TRACK_TRAIT)
            logs.append("开启信奥。")

        if not self.protagonist.has_trait(INFO_TRACK_TRAIT):
            return
        if random.random() >= Config.INFO_OLYMPIAD_CONFLICT_PROB:
            return

        choices = [
            f"放弃{battle_type}复习，潜入机房备战信奥集训。林清北嘲笑主角是逃兵。",
            f"一边应付{battle_type}，一边在草稿纸上推导信奥集训算法。双线操作，神魂枯竭。",
            f"在{battle_type}的考场上，把作文写成了代码，震惊阅卷长老。",
        ]
        logs.append(f"【道心抉择】{random.choice(choices)}")

    def _run_students_week(self, is_exam_week: bool, abs_week: int, battle_subjects: Sequence[str]) -> None:
        for student in self.students:
            student.plan_week(is_exam_week, abs_week, battle_subjects)
            student.execute_week()

    def _run_events_and_breakthroughs(self, abs_week: int, season: str, logs: List[str]) -> None:
        focus_count = min(Config.RANDOM_EVENT_FOCUS_COUNT, len(self.students))
        focus_students = random.sample(self.students, focus_count)
        if self.protagonist not in focus_students and focus_students:
            focus_students[0] = self.protagonist

        for student in focus_students:
            placeholders = self._build_event_placeholders(student)
            event = get_random_event(season, placeholders=placeholders)
            self.global_cooldowns[event.description] = abs_week
            apply_effect(student, event.effect)
            logs.append(f"【突发】{event.description}")

            unlock_prob = (
                Config.PROTAGONIST_SKILL_BREAKTHROUGH_PROB
                if student.role == "protagonist"
                else Config.NORMAL_STUDENT_SKILL_BREAKTHROUGH_PROB
            )
            if random.random() < unlock_prob:
                self._try_unlock_skill(student, logs)

    def _build_event_placeholders(self, student: Person) -> Dict[str, str]:
        candidates = [p.name for p in (self.students + self.teachers) if p.name != student.name]
        random.shuffle(candidates)
        picked = [student.name] + candidates[:3]
        while len(picked) < 4:
            picked.append(student.name)
        return {f"p{i + 1}": picked[i] for i in range(4)}

    def _try_unlock_skill(self, student: Person, logs: List[str]) -> None:
        target_subj = random.choice(CORE_SUBJECTS)
        mastery_val = student.mastery[target_subj]
        skill_data = SkillTree.get_skill_by_subject(target_subj, mastery_val)
        if skill_data.name in [sk.name for sk in student.skills]:
            return
        student.skills.append(SkillState(name=skill_data.name, level=skill_data.level, description=skill_data.description))
        logs.append(f"【突破】{student.name}领悟绝学「{skill_data.name}」")

    def _compose_battle_report(self, battle_subjects: Sequence[str]) -> str:
        score_subjects = list(CORE_SUBJECTS) if ALL_SUBJECTS_MARKER in battle_subjects else list(battle_subjects)
        mc_score = sum(self.protagonist.get_exam_score(s) for s in score_subjects)
        top_student = self.rankings[0]
        rival_score = sum(top_student.get_exam_score(s) for s in score_subjects)
        diff = mc_score - rival_score
        latest_skill = self.protagonist.skills[-1].name if self.protagonist.skills else None

        scenes = [
            "监考老师祭出‘信号屏蔽仪’，全场灵气被封印。",
            "压轴导数题化作一条恶龙，盘踞在卷面上。",
            "听力广播里传来了魔音贯耳的英语听力，试图扰乱道心。",
            "隔壁班学霸开启了‘抖腿光环’，引发地震波攻击。",
            f"{top_student.name}眼神冰冷，随手丢出一招‘洛必达法则’。",
        ]
        if diff > 10 and latest_skill is None:
            raise RuntimeError("Protagonist has no skill for dominant victory report")

        dto = BattleReportDTO(
            scene=random.choice(scenes),
            protagonist_name=self.protagonist.name,
            top_student_name=top_student.name,
            mc_score=mc_score,
            rival_score=rival_score,
            diff=diff,
            latest_skill=latest_skill,
        )
        return render_battle_report(dto)

    def _update_week_ranks(self) -> None:
        rank_map = self.queries.build_rank_map(self.rankings)
        for student in self.students:
            if student.name not in rank_map:
                raise RuntimeError(f"Ranking missing student: {student.name}")
            student.last_week_rank = rank_map[student.name]

    def _resolve_week_quiz(
        self,
        is_exam_week: bool,
        battle_subjects: Sequence[str],
        curriculum_subjects: Dict[str, str],
    ) -> QuizContent | None:
        if is_exam_week or self.year != 1 or not battle_subjects or ALL_SUBJECTS_MARKER in battle_subjects:
            return None
        subject = battle_subjects[0]
        topic = curriculum_subjects[subject]
        return QuizDatabase.get_quiz(subject, topic)

    def create_person(self, profile: PersonProfile) -> Person:
        return self.initializer.create_person(profile)

    def _append_simulation_log(
        self,
        *,
        week_idx: int,
        abs_week: int,
        battle_type: str,
        battle_subjects: Sequence[str],
        logs: Sequence[str],
        quiz_data: QuizContent | None,
    ) -> None:
        quiz_payload = quiz_data.model_dump(mode="json") if quiz_data is not None else None
        rank_map = self.queries.build_rank_map(self.rankings)
        record = {
            "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
            "source": self.simulation_source,
            "year": self.year,
            "semester": self.semester,
            "week": week_idx,
            "abs_week": abs_week,
            "battle_type": battle_type,
            "battle_subjects": list(battle_subjects),
            "quiz": quiz_payload,
            "logs": list(logs),
            "protagonist": {
                "name": self.protagonist.name,
                "rank": rank_map.get(self.protagonist.name),
                "stress": self.protagonist.stress,
                "fatigue": self.protagonist.fatigue,
                "focus_subjects": list(self.protagonist.focus_subjects),
            },
            "engine_state": self.to_state().model_dump(mode="json"),
        }
        with open(self.simulation_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False, indent=2))
            f.write("\n")
