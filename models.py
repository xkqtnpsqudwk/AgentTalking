from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class AgentProfile:
    name: str
    age: int
    job: str
    personality: str


@dataclass
class MemoryEntry:
    subject_name: str
    fact: str
    day: int
    time_label: str
    round_id: int


@dataclass
class ReflectionEntry:
    target_name: str
    summary: str
    day: int
    time_label: str
    round_id: int


@dataclass
class ConversationTurn:
    speaker: str
    text: str


@dataclass
class ConversationRound:
    round_id: int
    day: int
    time_label: str
    place: str
    participants: List[str]
    topic: Optional[str]
    transcript: List[ConversationTurn] = field(default_factory=list)


@dataclass
class RoundAnalysis:
    facts_by_subject: Dict[str, List[str]]
    reflections_by_viewer: Dict[str, Dict[str, str]]


@dataclass
class Agent:
    profile: AgentProfile
    memory: Dict[str, List[MemoryEntry]] = field(default_factory=dict)
    relation_map: Dict[str, ReflectionEntry] = field(default_factory=dict)
    daily_plan: Dict[str, str] = field(default_factory=dict)

    @property
    def name(self) -> str:
        return self.profile.name

    def knows(self, target_name: str) -> bool:
        return target_name in self.memory or target_name in self.relation_map

    def add_memory(
        self,
        subject_name: str,
        fact: str,
        day: int,
        time_label: str,
        round_id: int
    ) -> None:
        if subject_name == self.name:
            return

        fact = fact.strip()

        if not fact:
            return

        if subject_name not in self.memory:
            self.memory[subject_name] = []

        existing_facts = {
            entry.fact
            for entry in self.memory[subject_name]
        }

        if fact not in existing_facts:
            self.memory[subject_name].append(
                MemoryEntry(
                    subject_name=subject_name,
                    fact=fact,
                    day=day,
                    time_label=time_label,
                    round_id=round_id
                )
            )

    def update_reflection(
        self,
        target_name: str,
        summary: str,
        day: int,
        time_label: str,
        round_id: int
    ) -> None:
        summary = summary.strip()

        if not summary:
            return

        self.relation_map[target_name] = ReflectionEntry(
            target_name=target_name,
            summary=summary,
            day=day,
            time_label=time_label,
            round_id=round_id
        )
