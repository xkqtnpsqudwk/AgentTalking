from collections import defaultdict
from typing import Dict, List, Optional
import os

from llm_client import LLMClient
from models import Agent, ConversationRound, RoundAnalysis


class Simulation:
    def __init__(
        self,
        agents: List[Agent],
        places: List[str],
        time_slots: List[str],
        llm_client: LLMClient
    ):
        self.agents = {
            agent.name: agent
            for agent in agents
        }

        self.places = places
        self.time_slots = time_slots
        self.llm_client = llm_client

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

                    self.run_conversation_round(
                        day=day,
                        time_label=time_label,
                        place=place,
                        participants=agents_at_place,
                        topic=None,
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
        lines.append(f"- 직업: {perspective_agent.profile.job}")
        lines.append(f"- 성격: {perspective_agent.profile.personality}")
        lines.append("")

        for target_name in self.agents.keys():
            if target_name == perspective_agent_name:
                continue

            lines.append(f"## {target_name}")
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
            lines.append("### 관계 / Reflection")

            reflection_entry = perspective_agent.relation_map.get(target_name)

            if reflection_entry is None:
                lines.append("- 아직 관계 Reflection이 없다.")
            else:
                lines.append(f"- {reflection_entry.summary}")

            lines.append("")

        return "\n".join(lines)

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
