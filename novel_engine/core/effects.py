from __future__ import annotations

"""Effect parser and stat mutation helpers."""

from novel_engine.core.person import Person
from novel_engine.data.database import Subject


def apply_effect(person: Person, effect: str) -> None:
    """Apply a comma-separated effect string to a person."""
    if not effect:
        return

    for part in effect.split(","):
        effect_key = part.strip()
        if effect_key.startswith("mood+"):
            person.mood += 10
        elif effect_key.startswith("mood-"):
            person.mood -= 10
        elif effect_key.startswith("stress+"):
            person.stress += 10
        elif effect_key.startswith("stress-"):
            person.stress -= 10
        elif effect_key.startswith("fatigue+"):
            person.fatigue += 10
        elif effect_key.startswith("fatigue-"):
            person.fatigue -= 10
        elif effect_key.startswith("all_mastery+"):
            for subject in Subject.ALL:
                person.mastery[subject] = person.mastery.get(subject, 0.0) + 100.0
        elif effect_key.startswith("all_mastery-"):
            for subject in Subject.ALL:
                person.mastery[subject] = person.mastery.get(subject, 0.0) - 100.0
