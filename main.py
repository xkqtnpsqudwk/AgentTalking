from typing import List

from cascade_llm_client import CascadeLLMClient
from config import (
    USE_OPENAI,
    OPENAI_API_KEY,
    OPENAI_MODEL_NAME,
    OPENAI_MAX_OUTPUT_TOKENS,
    USE_OLLAMA,
    OLLAMA_MODEL_NAME,
    OLLAMA_NUM_CTX,
    OLLAMA_NUM_PREDICT,
    START_HOUR,
    END_HOUR,
    SIMULATION_DAYS,
    DEFAULT_TURNS,
    MAX_MEMORY_PER_TARGET,
    TOPIC_PROBABILITY,
    REPORT_AGENT_NAME,
    REPORT_FILE_PATH,
)
from llm_client import LLMClient
from models import Agent, AgentProfile
from ollama_llm import OllamaLLM
from openai_llm import OpenAILLM
from rule_based_llm import RuleBasedLLM
from simulation import Simulation
from utils import (
    inject_initial_memory,
    inject_initial_relationship,
    inject_public_fact,
    make_time_slots
)


def create_llm_client() -> LLMClient:
    clients: List[LLMClient] = []

    if USE_OPENAI:
        try:
            openai_llm = OpenAILLM(
                api_key=OPENAI_API_KEY,
                model_name=OPENAI_MODEL_NAME,
                max_output_tokens=OPENAI_MAX_OUTPUT_TOKENS,
                max_memory_per_target=MAX_MEMORY_PER_TARGET
            )

            clients.append(openai_llm)
            print(f"[LLM] OpenAI 후보 등록: {OPENAI_MODEL_NAME}")

        except Exception as error:
            print(f"[LLM] OpenAI 사용 불가 → 생략: {error}")
    else:
        print("[LLM] USE_OPENAI=false → OpenAI 생략")

    if USE_OLLAMA:
        try:
            ollama_llm = OllamaLLM(
                model_name=OLLAMA_MODEL_NAME,
                num_ctx=OLLAMA_NUM_CTX,
                num_predict=OLLAMA_NUM_PREDICT,
                max_memory_per_target=MAX_MEMORY_PER_TARGET
            )

            clients.append(ollama_llm)
            print(
                f"[LLM] Ollama 후보 등록: {OLLAMA_MODEL_NAME} "
                f"(ctx={OLLAMA_NUM_CTX}, predict={OLLAMA_NUM_PREDICT})"
            )

        except Exception as error:
            print(f"[LLM] Ollama 사용 불가 → 생략: {error}")
    else:
        print("[LLM] USE_OLLAMA=false → Ollama 생략")

    clients.append(RuleBasedLLM())
    print("[LLM] RuleBasedLLM 후보 등록")

    return CascadeLLMClient(clients)


def create_agents() -> List[Agent]:
    agents = [
        Agent(
            profile=AgentProfile(
                name="지훈",
                age=24,
                gender="남성",
                job="대학생",
                personality="조용하고 계획적임",
                speech_style="짧고 신중하게 말하며, 생각을 정리한 뒤 답하는 편",
                interests=["프로그래밍", "게임 개발", "도서관 공부"],
                goal="학교 프로젝트를 완성하고 게임 개발 역량을 키우는 것",
                background="컴퓨터공학을 공부하며 게임 시스템 설계에 관심이 많다.",
                quirks=[
                    "대화 중 예시를 들어 설명하려 함",
                    "처음에는 조심스럽지만 익숙해지면 질문이 많아짐"
                ]
            )
        ),
        Agent(
            profile=AgentProfile(
                name="민수",
                age=22,
                gender="남성",
                job="카페 직원",
                personality="밝고 사교적임",
                speech_style="가볍고 친근하게 말하며, 먼저 분위기를 풀어주는 편",
                interests=["커피", "음악", "동네 사람들과 대화하기"],
                goal="카페에서 단골들과 좋은 관계를 만들고, 언젠가 작은 카페를 여는 것",
                background="동네 카페에서 일하며 사람들과 자주 대화한다.",
                quirks=[
                    "상대의 기분을 먼저 살핌",
                    "대화 중 농담을 조금 섞음"
                ]
            )
        ),
        Agent(
            profile=AgentProfile(
                name="수진",
                age=25,
                gender="여성",
                job="디자이너",
                personality="차분하고 섬세함",
                speech_style="부드럽지만 관찰이 날카롭고, 감각적인 표현을 자주 사용함",
                interests=["브랜딩", "전시", "조용한 카페", "스케치"],
                goal="개인 포트폴리오를 완성하고 독립 프로젝트를 시작하는 것",
                background="프리랜서 디자인 작업을 준비하며 여러 장소에서 작업한다.",
                quirks=[
                    "사람의 말투나 표정을 잘 관찰함",
                    "생각을 바로 말하기보다 한 번 정리해서 표현함"
                ]
            )
        ),
        Agent(
            profile=AgentProfile(
                name="하린",
                age=27,
                gender="여성",
                job="프로그래머",
                personality="논리적이고 신중함",
                speech_style="정확하고 담백하게 말하며, 문제를 구조적으로 정리하는 편",
                interests=["알고리즘", "자동화", "SF 소설", "조용한 작업 공간"],
                goal="복잡한 문제를 단순한 시스템으로 정리하는 능력을 더 키우는 것",
                background="소프트웨어 개발자로 일하며 혼자 집중하는 시간을 중요하게 여긴다.",
                quirks=[
                    "대화를 구조화해서 이해하려 함",
                    "불확실한 내용은 단정하지 않음"
                ]
            )
        ),
    ]

    agent_map = {
        agent.name: agent
        for agent in agents
    }

    # 초기 관계 설정
    inject_initial_relationship(
        agent_a=agent_map["지훈"],
        agent_b=agent_map["수진"],
        relationship_name="연애중",
        emotional_context=(
            "현재 연애중인 연인 관계다."
            "서로를 애인으로 대한다."
            "둘만 있을 때는 반말을 쓰고 편하게 챙긴다."
            "사소한 말투에서 익숙함과 애정이 드러난다."
            "공개적으로 과하게 표현하지는 않지만 자연스럽게 서로를 챙긴다."
        )
    )

    inject_initial_relationship(
        agent_a=agent_map["민수"],
        agent_b=agent_map["하린"],
        relationship_name="연애중",
        emotional_context=(
            "현재 연애중인 연인 관계다."
            "서로를 애인으로 대한다."
            "둘만 있을 때는 반말을 쓰고 편하게 챙긴다."
            "사소한 말투에서 익숙함과 애정이 드러난다."
            "공개적으로 과하게 표현하지는 않지만 자연스럽게 서로를 챙긴다."
        )
    )

    # 사각 관계 정보를 모두가 어느 정도 알고 있는 상태로 시작한다.
    inject_public_fact(
        agents=agents,
        subject_name="지훈",
        fact="지훈은 현재 수진과 연애중이다."
    )

    inject_public_fact(
        agents=agents,
        subject_name="하린",
        fact="하린은 현재 민수와 연애중이다."
    )

    inject_public_fact(
        agents=agents,
        subject_name="민수",
        fact="민수는 현재 하린과 연애중이다."
    )

    inject_public_fact(
        agents=agents,
        subject_name="수진",
        fact="수진은 현재 지훈과 연애중이다."
    )

    return agents


def main() -> None:
    agents = create_agents()

    places = [
        "집",
        "학교",
        "카페",
        "도서관",
        "레스토랑",
        "공원"
    ]

    time_slots = make_time_slots(
        start_hour=START_HOUR,
        end_hour=END_HOUR
    )

    llm_client = create_llm_client()

    simulation = Simulation(
        agents=agents,
        places=places,
        time_slots=time_slots,
        llm_client=llm_client,
        topic_probability=TOPIC_PROBABILITY
    )

    simulation.run(
        days=SIMULATION_DAYS,
        default_turns=DEFAULT_TURNS
    )

    report = simulation.generate_report(REPORT_AGENT_NAME)

    print("\n\n===== 최종 리포트 =====")
    print(report)

    simulation.save_report(
        perspective_agent_name=REPORT_AGENT_NAME,
        file_path=REPORT_FILE_PATH
    )

    print(f"\n리포트 저장 완료: {REPORT_FILE_PATH}")


if __name__ == "__main__":
    main()
