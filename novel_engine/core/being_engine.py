from __future__ import annotations

"""Main world simulation orchestrator."""

import random
from typing import Dict, List, Sequence, Tuple

from config import Config
from novel_engine.core.contracts import CharacterProfile, EngineState, WorldSettings
from novel_engine.core.effects import apply_effect
from novel_engine.core.engine_constants import (
    ALL_SUBJECTS_MARKER,
    CLASSMATE_ROLE,
    CORE_SUBJECTS,
    INFO_TRACK_TAG,
    PROTAGONIST_ROLE,
    SUMMER_SEASON,
    TEACHER_ROLE,
    WINTER_SEASON,
)
from novel_engine.core.engine_io import get_curriculum_from_db
from novel_engine.core.person import Person
from novel_engine.core.view_models import MCReportDTO, StudentDetailDTO
from novel_engine.data.database import NPCData, SkillTree, Subject, get_random_event
from novel_engine.data.quiz_data import AIQuizFallbackModel, QuizDatabase, QuizResult


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
            role = PROTAGONIST_ROLE if char.name == Config.PROTAGONIST_NAME else CLASSMATE_ROLE
            person = Person(char.name, role, list(char.tags), gender=char.gender)
            self._restore_character_background(person, char.background)
            self.students.append(person)

        protagonist = next((s for s in self.students if s.role == PROTAGONIST_ROLE), None)
        if protagonist is None:
            raise ValueError("world settings does not contain protagonist")
        self.protagonist = protagonist

        for profile in NPCData.TEACHER_PROFILES:
            is_male_teacher = random.random() < 0.5
            name = NPCData.get_name("M" if is_male_teacher else "F", "70s")
            self.teachers.append(Person(name + "老师", TEACHER_ROLE, [profile.subject]))

    def init_world(self) -> None:
        self.students = []
        self.teachers = []

        protagonist = Person(Config.PROTAGONIST_NAME, PROTAGONIST_ROLE, ["做题家"], gender="男")
        self.protagonist = protagonist
        self.students.append(protagonist)

        rival = Person(Config.RIVAL_NAME, CLASSMATE_ROLE, ["天赋怪", "卷王"], gender="男")
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
            self.students.append(Person(name, CLASSMATE_ROLE, [archetype_name], gender=gender))

        for profile in NPCData.TEACHER_PROFILES:
            is_male_teacher = random.random() < 0.5
            name = NPCData.get_name("M" if is_male_teacher else "F", "70s")
            self.teachers.append(Person(name + "老师", TEACHER_ROLE, [profile.subject]))

    def tick(self, week_idx: int) -> Tuple[List[str], str, QuizResult | None]:
        abs_week = (self.year - 1) * Config.WEEKS_PER_YEAR + (self.semester - 1) * Config.WEEKS_PER_SEMESTER + week_idx
        curriculum = get_curriculum_from_db(self.db_path, abs_week)

        logs: List[str] = []
        is_exam_week = week_idx % Config.MONTHLY_EXAM_INTERVAL == 0
        season = SUMMER_SEASON if (week_idx % Config.WEEKS_PER_SEMESTER) < (Config.WEEKS_PER_SEMESTER // 2) else WINTER_SEASON

        if is_exam_week:
            battle_type = "【全科月考】"
            battle_subjects: List[str] = [ALL_SUBJECTS_MARKER]
        else:
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
            battle_type = f"【周考·{'/'.join(battle_subjects)}】"

        if abs_week == Config.INFO_OLYMPIAD_UNLOCK_ABS_WEEK and self.year == 1:
            self.protagonist.tags.append(INFO_TRACK_TAG)
            logs.append("开启信奥。")

        if INFO_TRACK_TAG in self.protagonist.tags and random.random() < Config.INFO_OLYMPIAD_CONFLICT_PROB:
            choices = [
                f"放弃{battle_type}复习，潜入机房备战信奥集训。林清北嘲笑主角是逃兵。",
                f"一边应付{battle_type}，一边在草稿纸上推导信奥集训算法。双线操作，神魂枯竭。",
                f"在{battle_type}的考场上，把作文写成了代码，震惊阅卷长老。",
            ]
            logs.append(f"【道心抉择】{random.choice(choices)}")

        for student in self.students:
            student.plan_week(is_exam_week, abs_week, battle_subjects)
            student.execute_week()

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
                target_subj = random.choice(Subject.ALL)
                mastery_val = student.mastery[target_subj]
                skill_data = SkillTree.get_skill_by_subject(target_subj, mastery_val)
                if skill_data.name not in [sk[0] for sk in student.skills]:
                    student.skills.append((skill_data.name, skill_data.level, skill_data.description))
                    logs.append(f"【突破】{student.name}领悟绝学「{skill_data.name}」")

        self.calculate_rankings()

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
            skill_name = self.protagonist.skills[-1][0] if self.protagonist.skills else "基础解题法"
            result = f"{self.protagonist.name}使用了‘{skill_name}’，提前交卷，留下一个孤傲的背影。"
        elif diff > -20:
            result = f"{self.protagonist.name}与{top_student.name}在分数线上反复拉锯，最终险胜/惜败。"
        else:
            result = f"{self.protagonist.name}被压轴题镇压，道心破碎，看着{top_student.name}绝尘而去。"
        logs.append(f"【战报】{random.choice(scenes)} {result} (我方战力:{mc_score} vs 榜首:{rival_score})")

        for student in self.students:
            try:
                student.last_week_rank = self.rankings.index(student) + 1
            except ValueError:
                student.last_week_rank = Config.FALLBACK_RANK

        quiz_data: QuizResult | None = None
        if not is_exam_week and self.year == 1 and battle_subjects and ALL_SUBJECTS_MARKER not in battle_subjects:
            subject = battle_subjects[0]
            topic = curriculum.subjects[subject]
            quiz_data = QuizDatabase.get_quiz(subject, topic)

        return logs, battle_type, quiz_data

    def _restore_character_background(self, person: Person, background: str) -> None:
        if not (background.startswith("[") and background.endswith("]")):
            raise ValueError(f"Invalid background format for {person.name}: {background}")

        parts = [item.strip() for item in background[1:-1].split(",")]
        if len(parts) < 3:
            raise ValueError(f"Invalid background parts for {person.name}: {background}")

        person.family = parts[0]
        person.flaw = parts[1]
        person.quirk = parts[2].replace("喜欢", "")

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
        ranks = self.get_rankings()
        rank = next((idx + 1 for idx, s in enumerate(ranks) if s.name == self.protagonist.name), Config.FALLBACK_RANK)
        skill = self.protagonist.skills[-1][0] if self.protagonist.skills else "无"
        return MCReportDTO(rank=rank, skill=skill, stress=self.protagonist.stress)

    def build_student_detail(self, name: str) -> StudentDetailDTO:
        student = next((s for s in self.students if s.name == name), None)
        if student is None:
            raise ValueError(f"Student not found: {name}")

        total_mastery = int(sum(student.mastery.values()))
        skills = [skill[0] for skill in student.skills]
        return StudentDetailDTO(
            name=student.name,
            gender=student.gender,
            soul_desc=student.get_soul_desc(),
            last_week_rank=student.last_week_rank,
            total_mastery=total_mastery,
            skills=skills,
        )

    def build_character_profile(self, person: Person) -> CharacterProfile:
        return CharacterProfile(
            name=person.name,
            gender=person.gender,
            background=person.get_soul_desc(),
            tags=list(person.tags),
        )

    def build_quiz_prompt_payload(self, quiz_result: QuizResult | None) -> str | None:
        if quiz_result is None:
            return None
        if isinstance(quiz_result, AIQuizFallbackModel):
            return f"[{quiz_result.type}] {quiz_result.subject} - {quiz_result.topic}"
        return quiz_result.content
