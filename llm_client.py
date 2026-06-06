from typing import Dict, List, Optional, Protocol

from models import Agent, ConversationRound, ConversationTurn, RoundAnalysis


class LLMClient(Protocol):
    def make_daily_plan(
        self,
        agent: Agent,
        places: List[str],
        time_slots: List[str],
        day: int
    ) -> Dict[str, str]:
        ...

    def generate_conversation(
        self,
        participants: List[Agent],
        place: str,
        time_label: str,
        topic: Optional[str],
        turns_by_agent: Dict[str, int]
    ) -> List[ConversationTurn]:
        ...

    def analyze_round(
        self,
        conversation_round: ConversationRound,
        participants: List[Agent]
    ) -> RoundAnalysis:
        ...
