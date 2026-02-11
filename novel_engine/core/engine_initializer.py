from __future__ import annotations

"""World initialization and person/profile construction helpers."""

import random
from typing import TYPE_CHECKING, List

from config import Config
from novel_engine.core.contracts import PersonProfile, RoleType, TraitType, WorldSettings
from novel_engine.core.person import Person
from novel_engine.data.database import NPCData, Subject

if TYPE_CHECKING:
    from novel_engine.core.being_engine import BeingEngine

ELITE_TRAIT: TraitType = "elite"
HARDCORE_TRAIT: TraitType = "hardcore"


class EngineInitializer:
    """Builds initial world state and converts profiles into runtime persons."""

    def __init__(self, engine: BeingEngine) -> None:
        self.engine = engine

    def init_from_settings(self, settings: WorldSettings) -> None:
        self.engine.students = []
        self.engine.teachers = []

        if not settings.characters:
            raise ValueError("world settings must contain at least one character")

        print(f" [Engine] Initializing from settings ({len(settings.characters)} students)...")

        for char in settings.characters:
            person = self.create_person(char)
            if char.role == "teacher":
                self.engine.teachers.append(person)
            else:
                self.engine.students.append(person)

        protagonist = next((s for s in self.engine.students if s.role == "protagonist"), None)
        if protagonist is None:
            raise ValueError("world settings does not contain protagonist")
        self.engine.protagonist = protagonist

    def init_world(self) -> None:
        self.engine.students = []
        self.engine.teachers = []
        self._init_core_students()
        self._spawn_classmates()
        self._spawn_teachers()

    def create_person(self, profile: PersonProfile) -> Person:
        return Person.from_profile(profile)

    def _init_core_students(self) -> None:
        protagonist = self.create_person(self._build_protagonist_profile())
        self.engine.protagonist = protagonist
        self.engine.students.append(protagonist)

        rival = self.create_person(self._build_rival_profile())
        rival.mastery = {s: 4000.0 for s in Subject.ALL}
        self.engine.students.append(rival)

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
            self.engine.students.append(self.create_person(profile))

    def _spawn_teachers(self) -> None:
        for profile in NPCData.TEACHER_PROFILES:
            is_male_teacher = random.random() < 0.5
            name = NPCData.get_name(is_male_teacher, "70s")
            teacher_profile = self._build_teacher_profile(name=name, is_male=is_male_teacher, subject=profile.subject)
            self.engine.teachers.append(self.create_person(teacher_profile))

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

    def _sample_background(self) -> tuple[str, str, str]:
        return NPCData.get_family(), NPCData.get_quirk(), NPCData.get_flaw()
