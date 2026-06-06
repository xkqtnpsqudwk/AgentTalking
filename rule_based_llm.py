from typing import Dict, List, Optional

from models import Agent, ConversationRound, ConversationTurn, RoundAnalysis


class RuleBasedLLM:
    name = "RuleBasedLLM"

    def make_daily_plan(
        self,
        agent: Agent,
        places: List[str],
        time_slots: List[str],
        day: int
    ) -> Dict[str, str]:
        plan = {}

        for time_label in time_slots:
            hour = int(time_label.split(":")[0])
            plan[time_label] = self._decide_place(agent, places, hour, day)

        return plan

    def _decide_place(
        self,
        agent: Agent,
        places: List[str],
        hour: int,
        day: int
    ) -> str:
        job = agent.profile.job

        if hour < 9 or hour >= 21:
            return self._pick_place(places, ["집"], day)

        if hour in (12, 18):
            return self._pick_place(places, ["레스토랑", "카페", "공원"], day + hour)

        if "학생" in job or "대학생" in job:
            if 9 <= hour <= 15:
                return self._pick_place(places, ["학교", "도서관"], day + hour)

            return self._pick_place(places, ["도서관", "카페", "공원"], day + hour)

        if "카페" in job:
            if 9 <= hour <= 17:
                return self._pick_place(places, ["카페"], day)

            return self._pick_place(places, ["집", "레스토랑", "공원"], day + hour)

        if "디자이너" in job:
            if 10 <= hour <= 17:
                return self._pick_place(places, ["카페", "도서관", "학교"], day + hour)

            return self._pick_place(places, ["집", "레스토랑", "공원"], day + hour)

        if "프로그래머" in job:
            if 10 <= hour <= 18:
                return self._pick_place(places, ["도서관", "카페", "학교"], day + hour)

            return self._pick_place(places, ["집", "레스토랑"], day + hour)

        return self._pick_place(places, ["집", "카페", "레스토랑"], day + hour)

    def _pick_place(
        self,
        places: List[str],
        candidates: List[str],
        offset: int
    ) -> str:
        valid_candidates = [
            place
            for place in candidates
            if place in places
        ]

        if not valid_candidates:
            return places[0]

        return valid_candidates[offset % len(valid_candidates)]

    def generate_conversation(
        self,
        participants: List[Agent],
        place: str,
        time_label: str,
        topic: Optional[str],
        turns_by_agent: Dict[str, int]
    ) -> List[ConversationTurn]:
        transcript = []
        remaining_turns = dict(turns_by_agent)
        turn_index = 0

        while any(count > 0 for count in remaining_turns.values()):
            for speaker in participants:
                if remaining_turns.get(speaker.name, 0) <= 0:
                    continue

                text = self._make_line(
                    speaker=speaker,
                    participants=participants,
                    place=place,
                    time_label=time_label,
                    topic=topic,
                    turn_index=turn_index
                )

                transcript.append(
                    ConversationTurn(
                        speaker=speaker.name,
                        text=text
                    )
                )

                remaining_turns[speaker.name] -= 1
                turn_index += 1

        return transcript

    def _make_line(
        self,
        speaker: Agent,
        participants: List[Agent],
        place: str,
        time_label: str,
        topic: Optional[str],
        turn_index: int
    ) -> str:
        others = [
            agent
            for agent in participants
            if agent.name != speaker.name
        ]

        first_meeting_targets = [
            agent
            for agent in others
            if not speaker.has_met(agent.name)
        ]

        if first_meeting_targets and turn_index < len(participants):
            return (
                f"안녕하세요. 저는 {speaker.name}입니다. "
                f"{speaker.profile.age}살 {speaker.profile.gender}이고, "
                f"{speaker.profile.job}입니다. "
                f"{self._short_trait_sentence(speaker)}"
            )

        if topic:
            return (
                f"{topic}에 대해 말하자면, 저는 {speaker.profile.personality} "
                f"성격이라서 제 방식대로 생각하는 편입니다."
            )

        known_agents = [
            agent
            for agent in others
            if speaker.memory.get(agent.name)
        ]

        if known_agents:
            target = known_agents[0]
            latest_memory = speaker.memory[target.name][-1].fact
            interest = self._first_interest(speaker)

            return (
                f"{target.name}님, 지난번에 '{latest_memory}'라고 들었던 게 기억나요. "
                f"저는 요즘 {interest} 쪽에 관심이 많아서 그런 이야기도 해보고 싶네요."
            )

        if others:
            target = others[0]
            interest = self._first_interest(speaker)

            return (
                f"{target.name}님, 오늘 {place}에서 또 보네요. "
                f"저는 요즘 {interest}에 관심이 있어요."
            )

        return f"오늘 {place}에 와 있습니다."

    def _first_interest(self, agent: Agent) -> str:
        if agent.profile.interests:
            return agent.profile.interests[0]

        return "일상적인 일"

    def _short_trait_sentence(self, agent: Agent) -> str:
        if agent.profile.speech_style:
            return f"저는 {agent.profile.speech_style}입니다."

        return f"저는 {agent.profile.personality} 성격입니다."

    def analyze_round(
        self,
        conversation_round: ConversationRound,
        participants: List[Agent]
    ) -> RoundAnalysis:
        facts_by_subject = {}
        reflections_by_viewer = {}

        for subject in participants:
            name = subject.name
            profile = subject.profile

            facts_by_subject[name] = [
                f"{name}은 {profile.age}살이다.",
                f"{name}의 성별은 {profile.gender}이다.",
                f"{name}의 직업은 {profile.job}이다.",
                f"{name}의 성격은 {profile.personality}이다.",
                f"{name}의 말투 특징은 {profile.speech_style}이다.",
                f"{name}의 관심사는 {', '.join(profile.interests)}이다.",
                f"{name}의 목표는 {profile.goal}이다.",
                (
                    f"{name}은 Day {conversation_round.day} "
                    f"{conversation_round.time_label}에 "
                    f"{conversation_round.place}에 있었다."
                )
            ]

        for viewer in participants:
            reflections_by_viewer[viewer.name] = {}

            for target in participants:
                if viewer.name == target.name:
                    continue

                old_reflection = viewer.relation_map.get(target.name)
                meeting_record = viewer.meeting_map.get(target.name)

                if old_reflection is None:
                    summary = (
                        f"{target.name}은 {target.profile.job}이며, "
                        f"{target.profile.personality} 성향과 "
                        f"'{target.profile.speech_style}' 말투를 가진 사람으로 보인다. "
                        f"{conversation_round.place}에서 대화했고 관계는 초기 단계다."
                    )
                else:
                    meet_count = meeting_record.meet_count if meeting_record else 1

                    summary = (
                        f"{target.name}에 대한 기존 인상은 유지된다. "
                        f"이번 대화까지 총 {meet_count}회 만났으며, "
                        f"{target.profile.interests[0] if target.profile.interests else '일상'}에 대한 관심을 가진 상대로 더 익숙하게 인식된다."
                    )

                reflections_by_viewer[viewer.name][target.name] = summary

        return RoundAnalysis(
            facts_by_subject=facts_by_subject,
            reflections_by_viewer=reflections_by_viewer
        )