from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class AgentProfile:
    name: str
    age: int
    gender: str
    job: str
    personality: str
    speech_style: str = "자연스럽고 평범한 말투"
    interests: List[str] = field(default_factory=list)
    goal: str = "특별한 목표 없음"
    background: str = "특별한 배경 없음"
    quirks: List[str] = field(default_factory=list)


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
class MeetingRecord:
    target_name: str

    first_day: int
    first_time_label: str
    first_place: str
    first_round_id: int

    last_day: int
    last_time_label: str
    last_place: str
    last_round_id: int

    meet_count: int = 1


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
    meeting_map: Dict[str, MeetingRecord] = field(default_factory=dict)
    daily_plan: Dict[str, str] = field(default_factory=dict)

    @property
    def name(self) -> str:
        return self.profile.name

    def knows(self, target_name: str) -> bool:
        """
        상대에 대해 알고 있는 정보가 있는지 확인한다.
        이것은 '실제로 만난 적 있는가'와는 다르다.
        """
        return target_name in self.memory or target_name in self.relation_map

    def has_met(self, target_name: str) -> bool:
        """
        실제로 대화 라운드에서 만난 적 있는지 확인한다.
        처음 만남 / 재만남 판단은 이 메서드를 기준으로 한다.
        """
        return target_name in self.meeting_map

    def mark_met(
        self,
        target_name: str,
        day: int,
        time_label: str,
        place: str,
        round_id: int
    ) -> None:
        """
        target_name과 실제로 만났다는 기록을 저장한다.
        이미 만난 적 있으면 마지막 만남 정보와 만남 횟수만 갱신한다.
        """
        if target_name == self.name:
            return

        if target_name not in self.meeting_map:
            self.meeting_map[target_name] = MeetingRecord(
                target_name=target_name,
                first_day=day,
                first_time_label=time_label,
                first_place=place,
                first_round_id=round_id,
                last_day=day,
                last_time_label=time_label,
                last_place=place,
                last_round_id=round_id,
                meet_count=1
            )
            return

        record = self.meeting_map[target_name]
        record.last_day = day
        record.last_time_label = time_label
        record.last_place = place
        record.last_round_id = round_id
        record.meet_count += 1

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