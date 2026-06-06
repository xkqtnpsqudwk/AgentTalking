from typing import Dict, List, Optional

from llm_client import LLMClient
from models import Agent, ConversationRound, ConversationTurn


class SafeLLMClient:
    def __init__(
        self,
        primary: Optional[LLMClient],
        fallback: LLMClient
    ):
        self.primary = primary
        self.fallback = fallback

    def make_daily_plan(
        self,
        agent: Agent,
        places: List[str],
        time_slots: List[str],
        day: int
    ) -> Dict[str, str]:
        try:
            if self.primary:
                return self.primary.make_daily_plan(agent, places, time_slots, day)
        except Exception as error:
            print(f"[Fallback] 일정 생성 실패 → RuleBasedLLM 사용: {error}")

        return self.fallback.make_daily_plan(agent, places, time_slots, day)

    def generate_conversation(
        self,
        participants: List[Agent],
        place: str,
        time_label: str,
        topic: Optional[str],
        turns_by_agent: Dict[str, int]
    ) -> List[ConversationTurn]:
        try:
            if self.primary:
                return self.primary.generate_conversation(
                    participants,
                    place,
                    time_label,
                    topic,
                    turns_by_agent
                )
        except Exception as error:
            print(f"[Fallback] 대화 생성 실패 → RuleBasedLLM 사용: {error}")

        return self.fallback.generate_conversation(
            participants,
            place,
            time_label,
            topic,
            turns_by_agent
        )

    def extract_facts(
        self,
        conversation_round: ConversationRound,
        participants: List[Agent]
    ) -> Dict[str, List[str]]:
        try:
            if self.primary:
                return self.primary.extract_facts(conversation_round, participants)
        except Exception as error:
            print(f"[Fallback] Fact 추출 실패 → RuleBasedLLM 사용: {error}")

        return self.fallback.extract_facts(conversation_round, participants)

    def update_reflection(
        self,
        viewer: Agent,
        target: Agent,
        conversation_round: ConversationRound,
        known_facts: List[str],
        old_reflection: Optional[str]
    ) -> str:
        try:
            if self.primary:
                return self.primary.update_reflection(
                    viewer,
                    target,
                    conversation_round,
                    known_facts,
                    old_reflection
                )
        except Exception as error:
            print(f"[Fallback] Reflection 생성 실패 → RuleBasedLLM 사용: {error}")

        return self.fallback.update_reflection(
            viewer,
            target,
            conversation_round,
            known_facts,
            old_reflection
        )