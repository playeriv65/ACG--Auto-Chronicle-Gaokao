from __future__ import annotations

"""Read/query helpers for engine state and DTO construction."""

from typing import TYPE_CHECKING, Sequence

from novel_engine.core.contracts import PersonProfile, QuizContent
from novel_engine.core.engine_constants import CORE_SUBJECTS
from novel_engine.core.person import Person
from novel_engine.core.view_models import MCReportDTO, StudentDetailDTO

if TYPE_CHECKING:
    from novel_engine.core.being_engine import BeingEngine


class EngineQueryService:
    """Builds rank/query projections from the current engine runtime state."""

    def __init__(self, engine: BeingEngine) -> None:
        self.engine = engine

    def calculate_rankings(self) -> None:
        def total_score(student: Person) -> int:
            return sum(student.get_exam_score(subject) for subject in CORE_SUBJECTS)

        self.engine.students.sort(key=total_score, reverse=True)
        self.engine.rankings = self.engine.students

    def get_rankings(self) -> list[Person]:
        if not self.engine.rankings:
            self.calculate_rankings()
        return self.engine.rankings

    def build_mc_report(self) -> MCReportDTO:
        rank_map = self.build_rank_map(self.get_rankings())
        if self.engine.protagonist.name not in rank_map:
            raise RuntimeError(f"Protagonist not found in rankings: {self.engine.protagonist.name}")
        latest_skill = self.engine.protagonist.skills[-1].name if self.engine.protagonist.skills else None
        return MCReportDTO(
            rank=rank_map[self.engine.protagonist.name],
            latest_skill=latest_skill,
            stress=self.engine.protagonist.stress,
        )

    def build_student_detail(self, name: str) -> StudentDetailDTO:
        student = next((s for s in self.engine.students if s.name == name), None)
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

    @staticmethod
    def build_person_profile(person: Person) -> PersonProfile:
        return person.to_profile()

    @staticmethod
    def build_quiz_prompt_payload(quiz_result: QuizContent | None) -> str | None:
        if quiz_result is None:
            return None
        if quiz_result.kind == "direct":
            if quiz_result.content is None:
                raise ValueError("Direct quiz content is missing")
            return quiz_result.content
        if quiz_result.subject is None or quiz_result.topic is None:
            raise ValueError("Fallback quiz content requires subject and topic")
        return f"[AI_GENERATED] {quiz_result.subject} - {quiz_result.topic}"

    @staticmethod
    def build_rank_map(rankings: Sequence[Person]) -> dict[str, int]:
        return {student.name: idx + 1 for idx, student in enumerate(rankings)}
