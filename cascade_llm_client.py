from typing import Dict, List, Optional

from llm_client import LLMClient
from models import Agent, ConversationRound, ConversationTurn, RoundAnalysis


class CascadeLLMClient:
    """
    OpenAI → Ollama → RuleBasedLLM 순서로 시도한다.
    특정 메서드에서 실패하면 다음 LLM으로 내려간다.
    """

    def __init__(self, clients: List[LLMClient]):
        if not clients:
            raise ValueError("LLM client가 하나 이상 필요합니다.")

        self.clients = clients

    def _client_name(self, client: LLMClient) -> str:
        return getattr(client, "name", client.__class__.__name__)

    def make_daily_plan(
        self,
        agent: Agent,
        places: List[str],
        time_slots: List[str],
        day: int
    ) -> Dict[str, str]:
        last_error = None

        for client in self.clients:
            try:
                return client.make_daily_plan(agent, places, time_slots, day)
            except Exception as error:
                last_error = error
                print(
                    f"[Fallback] {self._client_name(client)} 일정 생성 실패: {error}"
                )

        raise RuntimeError(f"모든 LLM 일정 생성 실패: {last_error}")

    def generate_conversation(
        self,
        participants: List[Agent],
        place: str,
        time_label: str,
        topic: Optional[str],
        turns_by_agent: Dict[str, int]
    ) -> List[ConversationTurn]:
        last_error = None

        for client in self.clients:
            try:
                return client.generate_conversation(
                    participants=participants,
                    place=place,
                    time_label=time_label,
                    topic=topic,
                    turns_by_agent=turns_by_agent
                )
            except Exception as error:
                last_error = error
                print(
                    f"[Fallback] {self._client_name(client)} 대화 생성 실패: {error}"
                )

        raise RuntimeError(f"모든 LLM 대화 생성 실패: {last_error}")

    def analyze_round(
        self,
        conversation_round: ConversationRound,
        participants: List[Agent]
    ) -> RoundAnalysis:
        last_error = None

        for client in self.clients:
            try:
                return client.analyze_round(conversation_round, participants)
            except Exception as error:
                last_error = error
                print(
                    f"[Fallback] {self._client_name(client)} 라운드 분석 실패: {error}"
                )

        raise RuntimeError(f"모든 LLM 라운드 분석 실패: {last_error}")
