from collections import defaultdict
from typing import Dict, List, Optional
import os
import random

from llm_client import LLMClient
from models import Agent, ConversationRound, RoundAnalysis, MemoryEntry


class Simulation:
    def __init__(
        self,
        agents: List[Agent],
        places: List[str],
        time_slots: List[str],
        llm_client: LLMClient,
        topic_probability: float = 0.5
    ):
        self.agents = {
            agent.name: agent
            for agent in agents
        }

        self.places = places
        self.time_slots = time_slots
        self.llm_client = llm_client

        self.topic_probability = max(0.0, min(1.0, topic_probability))

        self.round_id_counter = 1
        self.rounds: List[ConversationRound] = []

    def run(
        self,
        days: int = 2,
        default_turns: int = 2
    ) -> None:
        for day in range(1, days + 1):
            print(f"\n===== Day {day} 시작 =====")

            self._make_daily_plans(day)
            self._print_daily_plans(day)

            for time_label in self.time_slots:
                place_groups = self._group_agents_by_place(time_label)

                for place, agents_at_place in place_groups.items():
                    if len(agents_at_place) < 2:
                        continue

                    turns_by_agent = {
                        agent.name: default_turns
                        for agent in agents_at_place
                    }

                    topic = self._pick_optional_topic(
                        place=place,
                        time_label=time_label,
                        participants=agents_at_place
                    )

                    self.run_conversation_round(
                        day=day,
                        time_label=time_label,
                        place=place,
                        participants=agents_at_place,
                        topic=topic,
                        turns_by_agent=turns_by_agent
                    )

    def _make_daily_plans(self, day: int) -> None:
        for agent in self.agents.values():
            agent.daily_plan = self.llm_client.make_daily_plan(
                agent=agent,
                places=self.places,
                time_slots=self.time_slots,
                day=day
            )

    def _print_daily_plans(self, day: int) -> None:
        print(f"\n[Day {day} 일정]")

        for agent in self.agents.values():
            compressed_plan = ", ".join(
                f"{time_label}:{place}"
                for time_label, place in agent.daily_plan.items()
            )

            print(f"- {agent.name}: {compressed_plan}")

    def _group_agents_by_place(
        self,
        time_label: str
    ) -> Dict[str, List[Agent]]:
        place_groups = defaultdict(list)

        for agent in self.agents.values():
            place = agent.daily_plan.get(time_label)

            if place:
                place_groups[place].append(agent)

        return dict(place_groups)

    def _pick_optional_topic(
        self,
        place: str,
        time_label: str,
        participants: List[Agent]
    ) -> Optional[str]:
        if self.topic_probability <= 0.0:
            return None

        if random.random() > self.topic_probability:
            return None

        return self._pick_random_topic(
            place=place,
            time_label=time_label,
            participants=participants
        )

    def _pick_random_topic(
        self,
        place: str,
        time_label: str,
        participants: List[Agent]
    ) -> str:
        candidates = self._get_base_topics(
            place=place,
            time_label=time_label
        )

        self._add_light_interest_topics(
            candidates=candidates,
            participants=participants
        )

        return random.choice(candidates)

    def _get_base_topics(
        self,
        place: str,
        time_label: str
    ) -> List[str]:
        topics_by_place = {
            "집": [
                "오늘 하루 계획",
                "최근 생활 패턴",
                "쉬는 시간에 하는 일",
                "집에서 집중하는 방법"
            ],
            "학교": [
                "수업과 과제",
                "시험 준비",
                "학교 생활",
                "최근 공부한 내용"
            ],
            "카페": [
                "커피 취향",
                "최근 근황",
                "작업하기 좋은 자리",
                "요즘 자주 하는 일"
            ],
            "도서관": [
                "공부 계획",
                "읽고 있는 책",
                "집중하는 방법",
                "조용한 장소에서 하는 일"
            ],
            "레스토랑": [
                "식사 메뉴",
                "하루 동안 있었던 일",
                "요즘 고민",
                "최근 가장 바빴던 일"
            ],
            "공원": [
                "산책",
                "날씨",
                "휴식과 취미",
                "기분 전환 방법"
            ]
        }

        default_topics = [
            "최근 근황",
            "오늘 일정",
            "요즘 관심사",
            "최근 기억에 남는 일"
        ]

        candidates = list(topics_by_place.get(place, default_topics))

        hour = int(time_label.split(":")[0])

        if hour in (12, 18):
            candidates.extend([
                "식사하면서 나누는 근황",
                "오늘 하루 중 가장 바빴던 일",
                "오후 일정이나 저녁 계획"
            ])

        return candidates

    def _add_light_interest_topics(
        self,
        candidates: List[str],
        participants: List[Agent]
    ) -> None:
        interests = []

        for agent in participants:
            interests.extend(agent.profile.interests[:1])

        for interest in interests:
            candidates.append(f"{interest}에 대한 가벼운 이야기")

    def run_conversation_round(
        self,
        day: int,
        time_label: str,
        place: str,
        participants: List[Agent],
        topic: Optional[str],
        turns_by_agent: Dict[str, int]
    ) -> ConversationRound:
        round_id = self.round_id_counter
        self.round_id_counter += 1

        conversation_round = ConversationRound(
            round_id=round_id,
            day=day,
            time_label=time_label,
            place=place,
            participants=[
                agent.name
                for agent in participants
            ],
            topic=topic
        )

        transcript = self.llm_client.generate_conversation(
            participants=participants,
            place=place,
            time_label=time_label,
            topic=topic,
            turns_by_agent=turns_by_agent
        )

        conversation_round.transcript = transcript
        self.rounds.append(conversation_round)

        self._print_round(conversation_round)

        self._store_meeting_history(
            conversation_round=conversation_round,
            participants=participants
        )

        analysis = self.llm_client.analyze_round(
            conversation_round=conversation_round,
            participants=participants
        )

        self._apply_round_analysis(
            conversation_round=conversation_round,
            participants=participants,
            analysis=analysis
        )

        return conversation_round

    def _store_meeting_history(
        self,
        conversation_round: ConversationRound,
        participants: List[Agent]
    ) -> None:
        for viewer in participants:
            for target in participants:
                if viewer.name == target.name:
                    continue

                viewer.mark_met(
                    target_name=target.name,
                    day=conversation_round.day,
                    time_label=conversation_round.time_label,
                    place=conversation_round.place,
                    round_id=conversation_round.round_id
                )

    def _apply_round_analysis(
        self,
        conversation_round: ConversationRound,
        participants: List[Agent],
        analysis: RoundAnalysis
    ) -> None:
        self._store_facts(
            conversation_round=conversation_round,
            participants=participants,
            facts_by_subject=analysis.facts_by_subject
        )

        self._store_reflections(
            conversation_round=conversation_round,
            participants=participants,
            reflections_by_viewer=analysis.reflections_by_viewer
        )

    def _store_facts(
        self,
        conversation_round: ConversationRound,
        participants: List[Agent],
        facts_by_subject: Dict[str, List[str]]
    ) -> None:
        for receiver in participants:
            for subject_name, facts in facts_by_subject.items():
                if receiver.name == subject_name:
                    continue

                for fact in facts:
                    receiver.add_memory(
                        subject_name=subject_name,
                        fact=fact,
                        day=conversation_round.day,
                        time_label=conversation_round.time_label,
                        round_id=conversation_round.round_id
                    )

    def _store_reflections(
        self,
        conversation_round: ConversationRound,
        participants: List[Agent],
        reflections_by_viewer: Dict[str, Dict[str, str]]
    ) -> None:
        for viewer in participants:
            viewer_reflections = reflections_by_viewer.get(viewer.name, {})

            for target in participants:
                if viewer.name == target.name:
                    continue

                summary = viewer_reflections.get(target.name, "")

                if not summary:
                    continue

                viewer.update_reflection(
                    target_name=target.name,
                    summary=summary,
                    day=conversation_round.day,
                    time_label=conversation_round.time_label,
                    round_id=conversation_round.round_id
                )

    def _print_round(
        self,
        conversation_round: ConversationRound
    ) -> None:
        print(
            f"\n[Round {conversation_round.round_id}] "
            f"Day {conversation_round.day} "
            f"{conversation_round.time_label} / {conversation_round.place}"
        )

        print(f"참여자: {', '.join(conversation_round.participants)}")

        if conversation_round.topic:
            print(f"Topic: {conversation_round.topic}")
        else:
            print("Topic: 없음")

        for turn in conversation_round.transcript:
            print(f"{turn.speaker}: {turn.text}")

    def generate_report(
        self,
        perspective_agent_name: str
    ) -> str:
        if perspective_agent_name not in self.agents:
            raise ValueError(f"존재하지 않는 Agent입니다: {perspective_agent_name}")

        perspective_agent = self.agents[perspective_agent_name]

        lines = []
        lines.append(f"# {perspective_agent_name} 기준 Agent Report")
        lines.append("")
        lines.append("## 기본 정보")
        lines.append(f"- 이름: {perspective_agent.profile.name}")
        lines.append(f"- 나이: {perspective_agent.profile.age}")
        lines.append(f"- 성별: {perspective_agent.profile.gender}")
        lines.append(f"- 직업: {perspective_agent.profile.job}")
        lines.append(f"- 성격: {perspective_agent.profile.personality}")
        lines.append(f"- 말투: {perspective_agent.profile.speech_style}")
        lines.append(f"- 관심사: {', '.join(perspective_agent.profile.interests)}")
        lines.append(f"- 목표: {perspective_agent.profile.goal}")
        lines.append(f"- 배경: {perspective_agent.profile.background}")
        lines.append(f"- 특징: {', '.join(perspective_agent.profile.quirks)}")
        lines.append("")

        for target_name in self.agents.keys():
            if target_name == perspective_agent_name:
                continue

            lines.append(f"## {target_name}")
            lines.append("")

            meeting_record = perspective_agent.meeting_map.get(target_name)

            lines.append("### 만남 기록")

            if meeting_record is None:
                lines.append("- 아직 직접 만난 적이 없다.")
            else:
                lines.append(
                    f"- 처음 만난 시점: Day {meeting_record.first_day}, "
                    f"{meeting_record.first_time_label}, "
                    f"{meeting_record.first_place}, "
                    f"Round {meeting_record.first_round_id}"
                )
                lines.append(
                    f"- 마지막 만남: Day {meeting_record.last_day}, "
                    f"{meeting_record.last_time_label}, "
                    f"{meeting_record.last_place}, "
                    f"Round {meeting_record.last_round_id}"
                )
                lines.append(f"- 총 만남 횟수: {meeting_record.meet_count}회")

            lines.append("")
            lines.append("### 알고 있는 사실")

            memory_entries = perspective_agent.memory.get(target_name, [])

            if not memory_entries:
                lines.append("- 아직 알고 있는 사실이 없다.")
            else:
                for entry in memory_entries:
                    lines.append(
                        f"- {entry.fact} "
                        f"(Day {entry.day}, {entry.time_label}, Round {entry.round_id})"
                    )

            lines.append("")
            lines.append("### 관계 관련 사실")

            relationship_entries = self._extract_relationship_memory_entries(
                memory_entries=memory_entries
            )

            if not relationship_entries:
                lines.append("- 관계 관련 사실이 없다.")
            else:
                for entry in relationship_entries:
                    lines.append(
                        f"- {entry.fact} "
                        f"(Day {entry.day}, {entry.time_label}, Round {entry.round_id})"
                    )

            lines.append("")
            lines.append("### 관계 / 마지막 Reflection")

            reflection_entry = perspective_agent.relation_map.get(target_name)

            if reflection_entry is None:
                lines.append("- 아직 관계 Reflection이 없다.")
            else:
                lines.append(f"- {reflection_entry.summary}")
                lines.append(
                    f"  - 갱신 시점: Day {reflection_entry.day}, "
                    f"{reflection_entry.time_label}, Round {reflection_entry.round_id}"
                )

            lines.append("")

        return "\n".join(lines)

    def _extract_relationship_memory_entries(
        self,
        memory_entries: List[MemoryEntry]
    ) -> List[MemoryEntry]:
        relationship_keywords = [
            "연애중",
            "연인",
            "애인",
            "사귀",
            "사귄",
            "현재 수진과",
            "현재 지훈과",
            "현재 민수와",
            "현재 하린과",
            "헤어진 연인",
            "과거에는",
            "과거 연인",
            "전 연인",
            "이별",
            "헤어",
            "어색함",
            "미련",
            "거리감",
            "조심스럽",
            "반말",
            "챙긴다",
            "배려",
            "편하게 말",
            "가까운 관계",
            "현재 관계",
            "과거 관계"
        ]

        relationship_entries = []

        for entry in memory_entries:
            if any(keyword in entry.fact for keyword in relationship_keywords):
                relationship_entries.append(entry)

        return relationship_entries

    def save_report(
        self,
        perspective_agent_name: str,
        file_path: str
    ) -> None:
        report = self.generate_report(perspective_agent_name)
        directory = os.path.dirname(file_path)

        if directory:
            os.makedirs(directory, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as file:
            file.write(report)