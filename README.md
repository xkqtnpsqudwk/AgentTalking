# Agent Talking

여러 Agent가 하루 계획을 세우고, 시간 순서대로 장소를 이동하며, 같은 장소에 있는 Agent끼리 자동으로 대화하는 시뮬레이션 프로젝트다.

대화가 끝나면 LLM이 대화 내용을 분석해서 각 Agent의 Memory와 Relation Map을 갱신한다.  
마지막에는 특정 Agent 기준으로 상대방별 알고 있는 사실과 관계 요약을 리포트 파일로 저장한다.

LLM은 다음 순서로 사용한다.

```text
OpenAI → Ollama(qwen3:8b) → RuleBasedLLM
```

즉 OpenAI 키가 없거나, Ollama 모델이 없어도 마지막에는 RuleBasedLLM으로 실행된다.

---

## 1. 설치

```powershell
python -m pip install -r requirements.txt
```

필요 패키지:

```text
openai
ollama
python-dotenv
```

---

## 2. 환경 변수 설정

`.env.example`을 복사해서 `.env`를 만든다.

```powershell
copy .env.example .env
```

예시:

```env
# =========================
# OpenAI
# =========================

# OpenAI 사용 여부
USE_OPENAI=true

# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here

# 사용할 OpenAI 모델
OPENAI_MODEL_NAME=gpt-5.5

# OpenAI 응답 최대 출력 토큰 수
# 값이 너무 작으면 JSON이 중간에 잘릴 수 있음
OPENAI_MAX_OUTPUT_TOKENS=1024


# =========================
# Ollama
# =========================

# Ollama 사용 여부
USE_OLLAMA=true

# 사용할 로컬 모델 이름
OLLAMA_MODEL_NAME=qwen3:8b

# Ollama context 크기
# 클수록 더 많이 기억하지만 느려질 수 있음
OLLAMA_NUM_CTX=2048

# Ollama 최대 출력 토큰 수
OLLAMA_NUM_PREDICT=256


# =========================
# Simulation
# =========================

# 하루 시작 시간
START_HOUR=8

# 하루 종료 시간
END_HOUR=22

# 시뮬레이션할 날짜 수
SIMULATION_DAYS=2

# Agent 한 명당 기본 발언 횟수
DEFAULT_TURNS=2

# 상대별 최근 Memory 몇 개까지 프롬프트에 넣을지
MAX_MEMORY_PER_TARGET=3

# 리포트 기준 Agent
REPORT_AGENT_NAME=지훈

# 리포트 저장 경로
REPORT_FILE_PATH=reports/final_jihoon_report.md
```

---

## 3. 실행

```powershell
python main.py
```

실행이 끝나면 설정된 경로에 리포트가 저장된다.

기본 저장 위치:

```text
reports/final_jihoon_report.md
```

---

## 4. 실행 모드

OpenAI를 사용하려면:

```env
USE_OPENAI=true
USE_OLLAMA=true
```

OpenAI 비용 없이 Ollama만 쓰려면:

```env
USE_OPENAI=false
USE_OLLAMA=true
OLLAMA_MODEL_NAME=qwen3:8b
```

가장 빠른 테스트용으로 RuleBasedLLM만 쓰려면:

```env
USE_OPENAI=false
USE_OLLAMA=false
```

---

## 5. 프로젝트 구조

```text
models.py              → Agent, Memory, Reflection 데이터 모델
llm_client.py          → LLM 공통 인터페이스
rule_based_llm.py      → LLM이 없을 때 쓰는 fallback
prompt_llm_base.py     → OpenAI/Ollama 공통 프롬프트와 JSON 파싱
openai_llm.py          → OpenAI API 연결
ollama_llm.py          → Ollama 로컬 모델 연결
cascade_llm_client.py  → OpenAI → Ollama → RuleBasedLLM 순차 fallback
simulation.py          → 시뮬레이션 진행 로직
utils.py               → 시간 슬롯 생성, 초기 Memory 주입
config.py              → .env 설정 로딩
main.py                → 실행 시작점
```

---

## 6. 과제 요구사항 반영

이 프로젝트는 다음 요구사항을 반영한다.

```text
Agent는 이름, 나이, 직업, 성격 정보를 가진다.
Agent는 Memory를 가진다.
Agent는 Relation Map을 가진다.
초기 Memory 주입이 가능하다.
2명 이상의 Agent가 한 라운드에서 대화할 수 있다.
시간대와 장소에 따라 같은 장소의 Agent끼리 자동으로 대화한다.
대화 후 Fact와 Reflection을 분석한다.
Fact는 해당 Agent를 제외한 나머지 참여자의 Memory에 저장된다.
Reflection은 Agent 쌍별로 viewer → target 방향으로 저장된다.
가상의 이틀이 지난 후 특정 Agent 기준 리포트를 파일로 저장한다.
```

---

## 7. 발언 횟수 설정

자동 시뮬레이션에서는 기본적으로 모든 참여자에게 `DEFAULT_TURNS`가 적용된다.

```python
turns_by_agent = {
    agent.name: default_turns
    for agent in agents_at_place
}
```

그래서 `.env`에서 다음처럼 설정하면:

```env
DEFAULT_TURNS=2
```

Agent 한 명당 기본 2번씩 발언한다.

다만 구조적으로는 Agent별 발언 횟수를 따로 설정할 수 있다.  
`run_conversation_round()`가 `turns_by_agent`를 직접 받기 때문이다.

```python
simulation.run_conversation_round(
    day=1,
    time_label="12:00",
    place="카페",
    participants=[
        simulation.agents["지훈"],
        simulation.agents["민수"],
        simulation.agents["수진"]
    ],
    topic="점심시간 근황",
    turns_by_agent={
        "지훈": 2,
        "민수": 1,
        "수진": 3
    }
)
```

이 경우 발언 횟수는 다음처럼 달라진다.

```text
지훈: 2회
민수: 1회
수진: 3회
```

즉 자동 실행에서는 기본값을 쓰지만, 라운드별·Agent별 발언 횟수 개별 설정도 가능하다.

---

# 8. 모델 별 차이
 
확실히 OpenAI 모델 사용시 가장 좋은 품질의 결과를 얻을 수는 있지만, 비용이 소모된다.

---

## 9. 추가 변경 사항

최근 버전에서 다음 기능을 추가했다.

```text
1. Agent에 성별 정보 추가
2. Agent별 말투, 관심사, 목표, 배경, 특징 설정 추가
3. 실제 만남 여부를 저장하는 meeting_map 추가
4. 처음 만난 상대와 이미 만난 상대를 구분하도록 수정
5. 이미 만난 상대에게 자기소개를 반복하지 않도록 수정
6. 리포트에 만남 기록 추가
```

Agent 기본 정보는 기존보다 조금 더 세분화되었다.

```python
AgentProfile(
    name="지훈",
    age=24,
    gender="남성",
    job="대학생",
    personality="조용하고 계획적임",
    speech_style="짧고 신중하게 말하며, 생각을 정리한 뒤 답하는 편",
    interests=["프로그래밍", "게임 개발", "도서관 공부"],
    goal="학교 프로젝트를 완성하고 게임 개발 역량을 키우는 것",
    background="컴퓨터공학을 공부하며 게임 시스템 설계에 관심이 많다.",
    quirks=["대화 중 예시를 들어 설명하려 함", "처음에는 조심스럽지만 익숙해지면 질문이 많아짐"]
)
```

이번 수정으로 Agent는 단순히 이름, 나이, 직업, 성격만 가지는 것이 아니라 말투와 관심사까지 반영해서 대화할 수 있다.

또한 기존에는 Memory나 Relation을 기준으로 처음 만난 상대인지 판단했지만, 이제는 `meeting_map`을 따로 사용한다.

```text
Memory       → 상대에 대해 알고 있는 사실
Relation Map → 상대에 대한 관계 요약
Meeting Map  → 실제로 만난 적이 있는지 기록
```

따라서 이미 한 번 만난 상대에게 매번 자기소개를 반복하는 문제를 없

리포트에도 상대방별 만남 기록이 추가된다.

```text
만남 기록
→ 알고 있는 사실
→ 관계 / Reflection
```