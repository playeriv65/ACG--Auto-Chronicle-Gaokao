from __future__ import annotations

"""Main world simulation orchestrator."""

import random
from typing import Dict, List, Sequence, Tuple

from config import Config

from novel_engine.core.contracts import (
    EngineState,
    PersonProfile,
    QuizContent,
    RoleType,
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
from novel_engine.core.engine_io import get_curriculum_from_db
from novel_engine.core.person import Person
from novel_engine.core.presenters import render_battle_report
from novel_engine.core.view_models import BattleReportDTO, MCReportDTO, StudentDetailDTO
from novel_engine.data.database import NPCData, SkillTree, Subject, get_random_event
from novel_engine.data.quiz_data import QuizDatabase

INFO_TRACK_TRAIT: TraitType = "info_track"
ELITE_TRAIT: TraitType = "elite"
HARDCORE_TRAIT: TraitType = "hardcore"


class BeingEngine:
    """Coordinates weekly simulation, events, rankings and quiz context."""

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
        self.students = []
        self.teachers = []

        if not settings.characters:
            raise ValueError("world settings must contain at least one character")

        print(f" [Engine] Initializing from settings ({len(settings.characters)} students)...")

        for char in settings.characters:
            person = self.create_person(char)
            if char.role == "teacher":
                self.teachers.append(person)
            else:
                self.students.append(person)

        protagonist = next((s for s in self.students if s.role == "protagonist"), None)
        if protagonist is None:
            raise ValueError("world settings does not contain protagonist")
        self.protagonist = protagonist

    def init_world(self) -> None:
        self.students = []
        self.teachers = []
        self._init_core_students()
        self._spawn_classmates()
        self._spawn_teachers()

    def _init_core_students(self) -> None:
        protagonist = self.create_person(self._build_protagonist_profile())
        self.protagonist = protagonist
        self.students.append(protagonist)

        rival = self.create_person(self._build_rival_profile())
        rival.mastery = {s: 4000.0 for s in Subject.ALL}
        self.students.append(rival)

    def _spawn_classmates(self) -> None:
        used = {Config.PROTAGONIST_NAME, Config.RIVAL_NAME}
        for _ in range(Config.DEFAULT_CLASSMATE_COUNT):
            is_male = random.random() < 0.5
            name = NPCData.get_name(is_male, "00s")
            while name in used:
                name = NPCData.get_name(is_male, "00s")
            used.add(name)
            archetype_name = random.choice(NPCData.ARCHETYPES).name
            profile = self._build_classmate_profile(name=name, is_male=is_male, archetype_name=archetype_name)
            self.students.append(self.create_person(profile))

    def _spawn_teachers(self) -> None:
        for profile in NPCData.TEACHER_PROFILES:
            is_male_teacher = random.random() < 0.5
            name = NPCData.get_name(is_male_teacher, "70s")
            teacher_profile = self._build_teacher_profile(name=name, is_male=is_male_teacher, subject=profile.subject)
            self.teachers.append(self.create_person(teacher_profile))

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

        return logs, battle_type, quiz_data

    def calculate_rankings(self) -> None:
        def total_score(student: Person) -> int:
            return sum(student.get_exam_score(subject) for subject in CORE_SUBJECTS)

        self.students.sort(key=total_score, reverse=True)
        self.rankings = self.students

    def get_rankings(self) -> List[Person]:
        if not self.rankings:
            self.calculate_rankings()
        return self.rankings

    def build_mc_report(self) -> MCReportDTO:
        rank_map = self._build_rank_map(self.get_rankings())
        if self.protagonist.name not in rank_map:
            raise RuntimeError(f"Protagonist not found in rankings: {self.protagonist.name}")
        latest_skill = self.protagonist.skills[-1].name if self.protagonist.skills else None
        return MCReportDTO(rank=rank_map[self.protagonist.name], latest_skill=latest_skill, stress=self.protagonist.stress)

    def build_student_detail(self, name: str) -> StudentDetailDTO:
        student = next((s for s in self.students if s.name == name), None)
        if student is None:
            raise ValueError(f"Student not found: {name}")

        total_mastery = int(sum(student.mastery.values()))
        skills = [skill.name for skill in student.skills]
        return StudentDetailDTO(
            name=student.name,
            is_male=student.is_male,
            soul_desc=student.get_soul_desc(),
            last_week_rank=student.last_week_rank,
            total_mastery=total_mastery,
            skills=skills,
        )

    def build_person_profile(self, person: Person) -> PersonProfile:
        return person.to_profile()

    def build_quiz_prompt_payload(self, quiz_result: QuizContent | None) -> str | None:
        if quiz_result is None:
            return None
        if quiz_result.kind == "direct":
            if quiz_result.content is None:
                raise ValueError("Direct quiz content is missing")
            return quiz_result.content
        if quiz_result.subject is None or quiz_result.topic is None:
            raise ValueError("Fallback quiz content requires subject and topic")
        return f"[AI_GENERATED] {quiz_result.subject} - {quiz_result.topic}"

    def _build_rank_map(self, rankings: Sequence[Person]) -> dict[str, int]:
        return {student.name: idx + 1 for idx, student in enumerate(rankings)}

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
            event = get_random_event(season)
            self.global_cooldowns[event.description] = abs_week
            apply_effect(student, event.effect)
            logs.append(f"【突发】{student.name}: {event.description}")

            unlock_prob = (
                Config.PROTAGONIST_SKILL_BREAKTHROUGH_PROB
                if student.role == "protagonist"
                else Config.NORMAL_STUDENT_SKILL_BREAKTHROUGH_PROB
            )
            if random.random() < unlock_prob:
                self._try_unlock_skill(student, logs)

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
        rank_map = self._build_rank_map(self.rankings)
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

    def _build_profile(
        self,
        *,
        name: str,
        role: RoleType,
        tags: List[str],
        is_male: bool,
        is_elite: bool = False,
        traits: List[TraitType] | None = None,
    ) -> PersonProfile:
        family, quirk, flaw = self._sample_background()
        return PersonProfile(
            name=name,
            is_male=is_male,
            role=role,
            tags=tags,
            is_elite=is_elite,
            traits=list(traits or []),
            family=family,
            quirk=quirk,
            flaw=flaw,
        )

    def _build_protagonist_profile(self) -> PersonProfile:
        return self._build_profile(
            name=Config.PROTAGONIST_NAME,
            role="protagonist",
            tags=["做题家"],
            is_male=True,
            traits=[HARDCORE_TRAIT],
        )

    def _build_rival_profile(self) -> PersonProfile:
        return self._build_profile(
            name=Config.RIVAL_NAME,
            role="classmate",
            tags=["天赋怪", "卷王"],
            is_male=True,
            is_elite=True,
            traits=[ELITE_TRAIT, HARDCORE_TRAIT],
        )

    def _build_classmate_profile(self, *, name: str, is_male: bool, archetype_name: str) -> PersonProfile:
        is_elite = archetype_name in Config.ELITE_TAGS
        traits: List[TraitType] = [ELITE_TRAIT] if is_elite else []
        return self._build_profile(
            name=name,
            role="classmate",
            tags=[archetype_name],
            is_male=is_male,
            is_elite=is_elite,
            traits=traits,
        )

    def _build_teacher_profile(self, *, name: str, is_male: bool, subject: str) -> PersonProfile:
        return self._build_profile(
            name=name,
            role="teacher",
            tags=[subject],
            is_male=is_male,
        )

    def create_person(self, profile: PersonProfile) -> Person:
        return Person.from_profile(profile)

    def _sample_background(self) -> tuple[str, str, str]:
        return NPCData.get_family(), NPCData.get_quirk(), NPCData.get_flaw()
