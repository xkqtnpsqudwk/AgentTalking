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
    REPORT_AGENT_NAME,
    REPORT_FILE_PATH,
)
from llm_client import LLMClient
from models import Agent, AgentProfile
from ollama_llm import OllamaLLM
from openai_llm import OpenAILLM
from rule_based_llm import RuleBasedLLM
from simulation import Simulation
from utils import inject_initial_memory, make_time_slots


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
                job="대학생",
                personality="조용하고 계획적임"
            )
        ),
        Agent(
            profile=AgentProfile(
                name="민수",
                age=22,
                job="카페 직원",
                personality="밝고 사교적임"
            )
        ),
        Agent(
            profile=AgentProfile(
                name="수진",
                age=25,
                job="디자이너",
                personality="차분하고 섬세함"
            )
        ),
        Agent(
            profile=AgentProfile(
                name="하린",
                age=27,
                job="프로그래머",
                personality="논리적이고 신중함"
            )
        ),
    ]

    agent_map = {
        agent.name: agent
        for agent in agents
    }

    inject_initial_memory(
        receiver=agent_map["지훈"],
        subject_name="민수",
        fact="민수는 예전에 지훈과 같은 동네에 살았다."
    )

    inject_initial_memory(
        receiver=agent_map["민수"],
        subject_name="지훈",
        fact="지훈은 예전에 민수와 같은 동네에 살았다."
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
        llm_client=llm_client
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
