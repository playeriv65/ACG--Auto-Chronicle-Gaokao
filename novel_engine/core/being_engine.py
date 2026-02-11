from __future__ import annotations

"""Main world simulation orchestrator."""

import random
from typing import Dict, List, Literal, Sequence, Tuple

from config import Config

from novel_engine.core.contracts import CharacterProfile, EngineState, QuizContent, SkillState, TraitType, WorldSettings
from novel_engine.core.effects import apply_effect
from novel_engine.core.engine_constants import (
    ALL_SUBJECTS_MARKER,
    CLASSMATE_ROLE,
    CORE_SUBJECTS,
    PROTAGONIST_ROLE,
    SUMMER_SEASON,
    TEACHER_ROLE,
    WINTER_SEASON,
)
from novel_engine.core.engine_io import get_curriculum_from_db
from novel_engine.core.person import Person
from novel_engine.core.view_models import MCReportDTO, StudentDetailDTO
from novel_engine.data.database import NPCData, SkillTree, Subject, get_random_event
from novel_engine.data.quiz_data import QuizDatabase

ProfileRole = Literal["protagonist", "classmate", "teacher"]

PROFILE_ROLE_TO_ENGINE_ROLE: dict[ProfileRole, str] = {
    "protagonist": PROTAGONIST_ROLE,
    "classmate": CLASSMATE_ROLE,
    "teacher": TEACHER_ROLE,
}
ENGINE_ROLE_TO_PROFILE_ROLE: dict[str, ProfileRole] = {
    engine_role: profile_role for profile_role, engine_role in PROFILE_ROLE_TO_ENGINE_ROLE.items()
}
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
        protagonist = next((s for s in self.students if s.role == PROTAGONIST_ROLE), None)
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
            engine_role = PROFILE_ROLE_TO_ENGINE_ROLE[char.role]
            person = self._create_person(
                name=char.name,
                role=engine_role,
                tags=list(char.tags),
                gender=char.gender,
                is_elite=char.is_elite,
                traits=list(char.traits),
                family=char.family,
                quirk=char.quirk,
                flaw=char.flaw,
            )
            if engine_role == TEACHER_ROLE:
                self.teachers.append(person)
            else:
                self.students.append(person)

        protagonist = next((s for s in self.students if s.role == PROTAGONIST_ROLE), None)
        if protagonist is None:
            raise ValueError("world settings does not contain protagonist")
        self.protagonist = protagonist

    def init_world(self) -> None:
        self.students = []
        self.teachers = []

        protagonist = self._create_person(
            name=Config.PROTAGONIST_NAME,
            role=PROTAGONIST_ROLE,
            tags=["做题家"],
            gender="男",
            is_elite=False,
            traits=[HARDCORE_TRAIT],
        )
        self.protagonist = protagonist
        self.students.append(protagonist)

        rival = self._create_person(
            name=Config.RIVAL_NAME,
            role=CLASSMATE_ROLE,
            tags=["天赋怪", "卷王"],
            gender="男",
            is_elite=True,
            traits=[ELITE_TRAIT, HARDCORE_TRAIT],
        )
        rival.mastery = {s: 4000.0 for s in Subject.ALL}
        self.students.append(rival)

        used = {Config.PROTAGONIST_NAME, Config.RIVAL_NAME}
        for _ in range(Config.DEFAULT_CLASSMATE_COUNT):
            is_male = random.random() < 0.5
            gender = "男" if is_male else "女"
            name = NPCData.get_name("M" if is_male else "F", "00s")
            while name in used:
                name = NPCData.get_name("M" if is_male else "F", "00s")
            used.add(name)
            archetype_name = random.choice(NPCData.ARCHETYPES).name
            is_elite = archetype_name in Config.ELITE_TAGS
            traits: List[TraitType] = [ELITE_TRAIT] if is_elite else []
            self.students.append(
                self._create_person(
                    name=name,
                    role=CLASSMATE_ROLE,
                    tags=[archetype_name],
                    gender=gender,
                    is_elite=is_elite,
                    traits=traits,
                )
            )

        for profile in NPCData.TEACHER_PROFILES:
            is_male_teacher = random.random() < 0.5
            name = NPCData.get_name("M" if is_male_teacher else "F", "70s")
            self.teachers.append(
                self._create_person(
                    name=name + "老师",
                    role=TEACHER_ROLE,
                    tags=[profile.subject],
                    gender="男" if is_male_teacher else "女",
                    is_elite=False,
                    traits=[],
                )
            )

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
            gender=student.gender,
            soul_desc=student.get_soul_desc(),
            last_week_rank=student.last_week_rank,
            total_mastery=total_mastery,
            skills=skills,
        )

    def build_character_profile(self, person: Person) -> CharacterProfile:
        if person.role not in ENGINE_ROLE_TO_PROFILE_ROLE:
            raise ValueError(f"Unsupported person role: {person.role}")
        profile_role = ENGINE_ROLE_TO_PROFILE_ROLE[person.role]
        traits: List[TraitType] = list(person.traits)
        if person.is_elite and ELITE_TRAIT not in traits:
            traits.append(ELITE_TRAIT)
        return CharacterProfile(
            name=person.name,
            gender=person.gender,
            role=profile_role,
            is_elite=person.is_elite,
            traits=traits,
            tags=list(person.tags),
            family=person.family,
            flaw=person.flaw,
            quirk=person.quirk,
        )

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
                if student.role == PROTAGONIST_ROLE
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

        scenes = [
            "监考老师祭出‘信号屏蔽仪’，全场灵气被封印。",
            "压轴导数题化作一条恶龙，盘踞在卷面上。",
            "听力广播里传来了魔音贯耳的英语听力，试图扰乱道心。",
            "隔壁班学霸开启了‘抖腿光环’，引发地震波攻击。",
            f"{top_student.name}眼神冰冷，随手丢出一招‘洛必达法则’。",
        ]
        if diff > 10:
            if not self.protagonist.skills:
                raise RuntimeError("Protagonist has no skill for dominant victory report")
            skill_name = self.protagonist.skills[-1].name
            result = f"{self.protagonist.name}使用了‘{skill_name}’，提前交卷，留下一个孤傲的背影。"
        elif diff > -20:
            result = f"{self.protagonist.name}与{top_student.name}在分数线上反复拉锯，最终险胜/惜败。"
        else:
            result = f"{self.protagonist.name}被压轴题镇压，道心破碎，看着{top_student.name}绝尘而去。"
        return f"【战报】{random.choice(scenes)} {result} (我方战力:{mc_score} vs 榜首:{rival_score})"

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

    def _create_person(
        self,
        *,
        name: str,
        role: str,
        tags: List[str],
        gender: str,
        is_elite: bool,
        traits: List[TraitType],
        family: str | None = None,
        quirk: str | None = None,
        flaw: str | None = None,
    ) -> Person:
        return Person(
            name,
            role,
            tags,
            gender,
            is_elite=is_elite,
            family=family or NPCData.get_family(),
            quirk=quirk or NPCData.get_quirk(),
            flaw=flaw or NPCData.get_flaw(),
            traits=traits,
        )
