from __future__ import annotations

import re
from typing import Dict, List, Literal

from pydantic import BaseModel, ConfigDict, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


TraitType = Literal["elite", "info_track", "hardcore"]


class SkillState(StrictModel):
    name: str
    level: int
    description: str


class CharacterProfile(StrictModel):
    name: str
    gender: Literal["男", "女"] | str
    role: Literal["protagonist", "classmate", "teacher"]
    is_elite: bool
    traits: List[TraitType]
    tags: List[str]
    family: str
    flaw: str
    quirk: str


class SystemPrompt(StrictModel):
    role: str
    style: str
    background: str
    requirements: str


class WorldSettingsMeta(StrictModel):
    title: str
    generated_at: str
    description: str
    system_prompt: SystemPrompt


class WorldSettings(StrictModel):
    meta: WorldSettingsMeta
    characters: List[CharacterProfile]


class WeeklyScriptMeta(StrictModel):
    title: str
    generated_at: str
    description: str


class WeeklyRankings(StrictModel):
    mc_report: str
    top_student: str


class WeeklyEntry(StrictModel):
    event: str
    date: str
    details: List[str]
    quiz: str | None
    rankings: WeeklyRankings


class WeeklyScript(StrictModel):
    meta: WeeklyScriptMeta
    weeks: Dict[str, WeeklyEntry]

    @model_validator(mode="after")
    def _validate_week_keys(self) -> "WeeklyScript":
        for key in self.weeks:
            if not re.fullmatch(r"G\d+S\d+_W\d{2}", key):
                raise ValueError(f"Invalid week key: {key}")
        return self


class CurriculumWeek(StrictModel):
    abs_week: int
    subjects: Dict[str, str]


class ChatMessage(StrictModel):
    role: Literal["system", "user", "assistant"]
    content: str


class ChatRequest(StrictModel):
    messages: List[ChatMessage]
    max_tokens: int


class ChatResponse(StrictModel):
    content: str


class QuizContent(StrictModel):
    kind: Literal["direct", "fallback"]
    subject: str | None = None
    topic: str | None = None
    content: str | None = None


class PersonState(StrictModel):
    name: str
    role: str
    tags: List[str]
    traits: List[TraitType]
    is_elite: bool
    gender: str
    family: str
    quirk: str
    flaw: str
    talent: Dict[str, int]
    mastery: Dict[str, float]
    last_mastery: Dict[str, float]
    skills: List[SkillState]
    mood: int
    stress: int
    fatigue: int
    focus_subjects: List[str]
    last_week_rank: int


class EngineState(StrictModel):
    students: List[PersonState]
    teachers: List[PersonState]
    global_cooldowns: Dict[str, int]
    year: int
    semester: int
    last_battle_subjects: List[str]


class RuntimeState(StrictModel):
    total_chars: int
    chapter_count: int
    year: int
    semester: int
    week: int
    engine_state: EngineState
