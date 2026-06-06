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

        unfamiliar_agents = [
            agent
            for agent in others
            if not speaker.knows(agent.name)
        ]

        if unfamiliar_agents and turn_index < len(participants):
            return (
                f"안녕하세요. 저는 {speaker.name}입니다. "
                f"{speaker.profile.age}살이고, {speaker.profile.job}입니다."
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

            return (
                f"{target.name}님, 지난번에 '{latest_memory}'라고 들었던 게 기억나요. "
                f"오늘 {time_label}에 {place}에서 다시 보네요."
            )

        return (
            f"오늘 {place}에 오니 사람들을 만나게 되네요. "
            f"저는 {speaker.profile.personality} 성격에 가까워요."
        )

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
                f"{name}의 직업은 {profile.job}이다.",
                f"{name}의 성격은 {profile.personality}이다.",
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

                if old_reflection is None:
                    summary = (
                        f"{target.name}은 {target.profile.job}이며, "
                        f"{target.profile.personality} 성향의 사람으로 보인다. "
                        f"{conversation_round.place}에서 대화했고 관계는 초기 단계다."
                    )
                else:
                    summary = (
                        f"{target.name}에 대한 기존 인상은 유지된다. "
                        f"Day {conversation_round.day} {conversation_round.time_label}에 "
                        f"{conversation_round.place}에서 다시 대화하면서 "
                        f"이전보다 더 익숙한 상대로 인식된다."
                    )

                reflections_by_viewer[viewer.name][target.name] = summary

        return RoundAnalysis(
            facts_by_subject=facts_by_subject,
            reflections_by_viewer=reflections_by_viewer
        )
