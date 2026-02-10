from __future__ import annotations

"""Main world simulation orchestrator."""

import ast
import random
from typing import Any, Dict, List, Optional, Sequence, Tuple

from config import Config
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
from novel_engine.data.database import NPCData, SkillTree, Subject, get_random_event
from novel_engine.data.quiz_data import QuizDatabase, QuizResult



class BeingEngine:
    """Coordinates weekly simulation, events, rankings and quiz context."""

    def __init__(self):
        self.db_path: str = "background/curriculum.db"
        self.students: List[Person] = []
        self.teachers: List[Person] = []
        self.protagonist: Optional[Person] = None
        self.rankings: List[Person] = []
        self.global_cooldowns: Dict[str, int] = {}
        self.year: int = 1
        self.semester: int = 1
        self.last_battle_subjects: List[str] = []
        self.init_world()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize engine state for save/resume."""
        return {
            "students": [s.to_dict() for s in self.students],
            "teachers": [t.to_dict() for t in self.teachers],
            "global_cooldowns": self.global_cooldowns,
            "year": self.year,
            "semester": self.semester,
            "last_battle_subjects": self.last_battle_subjects,
        }

    def from_dict(self, data: Dict[str, Any]) -> None:
        """Restore engine state from serialized dictionary."""
        self.students = [Person.from_dict(s) for s in data["students"]]
        self.teachers = [Person.from_dict(t) for t in data["teachers"]]
        self.protagonist = self._find_protagonist()
        self.global_cooldowns = data.get("global_cooldowns", {})
        self.year = data.get("year", 1)
        self.semester = data.get("semester", 1)
        self.last_battle_subjects = data.get("last_battle_subjects", [])

    def init_from_settings(self, settings_data: Dict[str, Any]) -> None:
        """Initialize world using pre-generated character settings."""
        # Rebuild runtime actors from serialized character settings without changing simulation rules.
        self.students = []
        self.teachers = []

        char_list = settings_data.get("characters", [])
        if not char_list:
            self.init_world()
            return

        print(f" [Engine] Initializing from settings ({len(char_list)} students)...")

        for c in char_list:
            if not isinstance(c, dict):
                continue

            name = c["name"]
            gender = c["gender"]
            tags = self._parse_tags(c["tags"])
            role = PROTAGONIST_ROLE if name == Config.PROTAGONIST_NAME else CLASSMATE_ROLE

            p = Person(name, role, tags, gender=gender)
            self._restore_character_background(p, c["background"])

            self.students.append(p)

        self.protagonist = self._find_protagonist()

        for subj, _desc in NPCData.TEACHER_PROFILES:
            self.teachers.append(self._build_teacher(subj))

    def init_world(self) -> None:
        """Initialize default world when no external settings are present."""
        # Bootstrap protagonist/rival first, then fill remaining classmates and teachers.
        self.protagonist = Person(Config.PROTAGONIST_NAME, PROTAGONIST_ROLE, ["做题家"], gender="男")
        self.students.append(self.protagonist)

        nemesis = Person(Config.RIVAL_NAME, CLASSMATE_ROLE, ["天赋怪", "卷王"], gender="男")
        nemesis.mastery = {s: 4000.0 for s in Subject.ALL}
        self.students.append(nemesis)

        used = {Config.PROTAGONIST_NAME, Config.RIVAL_NAME}
        for _ in range(Config.DEFAULT_CLASSMATE_COUNT):
            is_male = random.random() < 0.5
            gender = "男" if is_male else "女"
            name = NPCData.get_name("M" if is_male else "F", "00s")
            while name in used:
                name = NPCData.get_name("M" if is_male else "F", "00s")
            used.add(name)

            archetype_data = random.choice(NPCData.ARCHETYPES)
            archetype_name = archetype_data[0]
            self.students.append(Person(name, CLASSMATE_ROLE, [archetype_name], gender=gender))

        for subj, _desc in NPCData.TEACHER_PROFILES:
            self.teachers.append(self._build_teacher(subj))

    def tick(self, week_idx: int) -> Tuple[List[str], str, Optional[QuizResult]]:
        """Advance one in-game week and return logs/battle/quiz payload."""
        # Keep this method as the canonical weekly pipeline: plan -> progress -> events -> rankings -> quiz payload.
        abs_week = self._to_abs_week(week_idx)
        curriculum = get_curriculum_from_db(self.db_path, abs_week)

        logs: List[str] = []
        is_exam_week = week_idx % Config.MONTHLY_EXAM_INTERVAL == 0
        season = SUMMER_SEASON if (week_idx % Config.WEEKS_PER_SEMESTER) < (Config.WEEKS_PER_SEMESTER // 2) else WINTER_SEASON

        battle_type, battle_subjects = self._resolve_battle_plan(is_exam_week)
        self._try_open_info_olympiad(abs_week, logs)
        self._try_resolve_conflict(battle_type, logs)

        self._advance_all_students(is_exam_week, abs_week, battle_subjects)
        self._trigger_random_events(abs_week, season, logs)

        self.calculate_rankings()
        self._append_battle_report(logs, battle_type, battle_subjects)
        self._update_last_week_rankings()

        quiz_data = self._build_quiz_data(is_exam_week, battle_subjects, curriculum)
        return logs, battle_type, quiz_data

    def _to_abs_week(self, week_idx: int) -> int:
        return (self.year - 1) * Config.WEEKS_PER_YEAR + (self.semester - 1) * Config.WEEKS_PER_SEMESTER + week_idx

    # todo: remove those helper. Use explicit main charactor instance.
    def _find_protagonist(self) -> Optional[Person]:
        return next((student for student in self.students if student.role == PROTAGONIST_ROLE), self.students[0] if self.students else None)

    # todo: Use json format to forbid parse logics.
    def _parse_tags(self, raw_tags: str) -> List[str]:
        parsed_tags = ast.literal_eval(raw_tags)
        return parsed_tags if isinstance(parsed_tags, list) else []

    # todo: Use OOP. Person base, derive Student and Teacher.
    def _build_teacher(self, subject: str) -> Person:
        is_male_teacher = random.random() < 0.5
        name = NPCData.get_name("M" if is_male_teacher else "F", "70s")
        return Person(name + "老师", TEACHER_ROLE, [subject])

    def _restore_character_background(self, person: Person, background: str) -> None:
        if not background.startswith("[") or not background.endswith("]"):
            return

        parts = [item.strip() for item in background[1:-1].split(",")]
        if len(parts) < 3:
            return

        person.family = parts[0]
        person.flaw = parts[1]
        person.quirk = parts[2].replace("喜欢", "")

    def _resolve_battle_plan(self, is_exam_week: bool) -> Tuple[str, List[str]]:
        """Build weekly battle type and subject scope."""
        # Rotate or expand battle subjects by school year while preserving exam-week override.
        battle_type = ""
        battle_subjects: List[str] = []

        if is_exam_week:
            battle_type = "【全科月考】"
            battle_subjects = [ALL_SUBJECTS_MARKER]
        else:
            if self.year == 1:
                candidates = [c for c in CORE_SUBJECTS if c not in self.last_battle_subjects]
                battle_subjects = [random.choice(candidates)]
            elif self.year == 2:
                battle_subjects = [Subject.PHYS, Subject.CHEM, Subject.BIO]
            else:
                battle_subjects = list(CORE_SUBJECTS)

            self.last_battle_subjects = list(battle_subjects)
            battle_type = f"【周考·{'/'.join(battle_subjects)}】"

        return battle_type, battle_subjects

    # todo: more complex olympiad intro logic. Should add a new part into background prompt.
    def _try_open_info_olympiad(self, abs_week: int, logs: List[str]) -> None:
        if abs_week == Config.INFO_OLYMPIAD_UNLOCK_ABS_WEEK and self.year == 1:
            if self.protagonist:
                self.protagonist.tags.append(INFO_TRACK_TAG)
            logs.append("开启信奥。")

    def _try_resolve_conflict(self, battle_type: str, logs: List[str]) -> None:
        if self.protagonist and INFO_TRACK_TAG in self.protagonist.tags and random.random() < Config.INFO_OLYMPIAD_CONFLICT_PROB:
            logs.append(self._resolve_conflict(battle_type, "信奥集训"))

    def _advance_all_students(self, is_exam_week: bool, abs_week: int, battle_subjects: Sequence[str]) -> None:
        for student in self.students:
            student.plan_week(is_exam_week, abs_week, battle_subjects)
            student.execute_week()

    def _pick_focus_students(self) -> List[Person]:
        focus_count = min(Config.RANDOM_EVENT_FOCUS_COUNT, len(self.students))
        focus = random.sample(self.students, focus_count)
        if self.protagonist and self.protagonist not in focus:
            focus[0] = self.protagonist
        return focus

    def _try_unlock_skill(self, student: Person, logs: List[str]) -> None:
        # Skill unlock chance depends on actor role; unlocked skills are deduplicated by name.
        unlock_prob = (
            Config.PROTAGONIST_SKILL_BREAKTHROUGH_PROB
            if student.role == PROTAGONIST_ROLE
            else Config.NORMAL_STUDENT_SKILL_BREAKTHROUGH_PROB
        )
        if random.random() >= unlock_prob:
            return

        target_subj = random.choice(Subject.ALL)
        mastery_val = student.mastery.get(target_subj, 0.0)
        skill_data = SkillTree.get_skill_by_subject(target_subj, mastery_val)
        if skill_data and skill_data[0] not in [sk[0] for sk in student.skills]:
            student.skills.append(skill_data)
            logs.append(f"【突破】{student.name}领悟绝学「{skill_data[0]}」")

    def _trigger_random_events(self, abs_week: int, season: str, logs: List[str]) -> None:
        """Apply random events to focus students and append event logs."""
        for student in self._pick_focus_students():
            desc, effect = get_random_event(season)
            self.global_cooldowns[desc] = abs_week
            apply_effect(student, effect)
            logs.append(f"【突发】{student.name}: {desc}")
            self._try_unlock_skill(student, logs)

    def _append_battle_report(self, logs: List[str], battle_type: str, battle_subjects: Sequence[str]) -> None:
        """Append battle narrative based on current ranking head-to-head."""
        mc = self.protagonist
        if not mc or not self.rankings:
            return

        score_subjects = self._resolve_score_subjects(battle_subjects)
        mc_score = sum(mc.get_exam_score(s) for s in score_subjects)
        rival_score = sum(self.rankings[0].get_exam_score(s) for s in score_subjects)

        battle_log = self._battle_narrative(mc, self.rankings[0], battle_type, mc_score, rival_score)
        logs.append(battle_log)

    def _resolve_score_subjects(self, battle_subjects: Sequence[str]) -> List[str]:
        if ALL_SUBJECTS_MARKER in battle_subjects:
            return list(CORE_SUBJECTS)
        return list(battle_subjects)

    def _update_last_week_rankings(self) -> None:
        for student in self.students:
            try:
                student.last_week_rank = self.rankings.index(student) + 1
            except ValueError:
                student.last_week_rank = Config.FALLBACK_RANK

    def _build_quiz_data(
        self,
        is_exam_week: bool,
        battle_subjects: Sequence[str],
        curriculum: Optional[Dict[str, str]],
    ) -> Optional[QuizResult]:
        # Quiz payload is only produced for year-1 non-exam single-subject weeks.
        if is_exam_week or self.year != 1 or not battle_subjects or ALL_SUBJECTS_MARKER in battle_subjects:
            return None

        subject = battle_subjects[0]
        topic = "复习"
        if curriculum:
            topic = curriculum.get(subject, "复习")
        return QuizDatabase.get_quiz(subject, topic)

    def _resolve_conflict(self, main: str, sub: str) -> str:
        choices = [
            f"放弃{main}复习，潜入机房备战{sub}。林清北嘲笑主角是逃兵。",
            f"一边应付{main}，一边在草稿纸上推导{sub}算法。双线操作，神魂枯竭。",
            f"在{main}的考场上，把作文写成了代码，震惊阅卷长老。",
        ]
        return f"【道心抉择】{random.choice(choices)}"

    def _battle_narrative(self, mc: Person, rival: Person, event: str, mc_score: int, rival_score: int) -> str:
        # Narrative branch is score-difference driven to keep deterministic tone buckets.
        diff = mc_score - rival_score
        scenes = [
            "监考老师祭出‘信号屏蔽仪’，全场灵气被封印。",
            "压轴导数题化作一条恶龙，盘踞在卷面上。",
            "听力广播里传来了魔音贯耳的英语听力，试图扰乱道心。",
            "隔壁班学霸开启了‘抖腿光环’，引发地震波攻击。",
            f"{rival.name}眼神冰冷，随手丢出一招‘洛必达法则’。",
        ]

        if diff > 10:
            skill_name = mc.skills[-1][0] if mc.skills else "基础解题法"
            res = f"{mc.name}使用了‘{skill_name}’，提前交卷，留下一个孤傲的背影。"
        elif diff > -20:
            res = f"{mc.name}与{rival.name}在分数线上反复拉锯，最终险胜/惜败。"
        else:
            res = f"{mc.name}被压轴题镇压，道心破碎，看着{rival.name}绝尘而去。"

        return f"【战报】{random.choice(scenes)} {res} (我方战力:{mc_score} vs 榜首:{rival_score})"

    def calculate_rankings(self) -> None:
        """Refresh class ranking by core-subject total score."""
        def total_score(s: Person) -> int:
            return sum(s.get_exam_score(sub) for sub in CORE_SUBJECTS)

        self.students.sort(key=total_score, reverse=True)
        self.rankings = self.students

    def get_rankings(self) -> List[Person]:
        if not self.rankings:
            self.calculate_rankings()
        return self.rankings

    def get_mc_report(self) -> str:
        """Return compact protagonist status line used in prompts."""
        p = self.protagonist
        if not p:
            return "主角未初始化"

        ranks = self.get_rankings()
        my_rank = -1
        for i, s in enumerate(ranks):
            if s.name == p.name:
                my_rank = i + 1
                break

        skill = p.skills[-1][0] if p.skills else "无"
        return f"排名:{my_rank} | 技能:{skill} | 压力:{p.stress}"

    def get_student_detail(self, name: str) -> str:
        """Return prompt-friendly summary for a specific student."""
        s = next((x for x in self.students if x.name == name), None)
        if not s:
            return ""

        skill_list = " | ".join(sk[0] for sk in s.skills) if s.skills else "无"
        sum_val = sum(v for v in s.mastery.values() if isinstance(v, (int, float)))
        return f"{s.name}({s.gender}) | {s.get_soul_desc()} | 排名:{s.last_week_rank} | 修为:{int(sum_val)} | 技能:{skill_list}"
