# Agent Talking

여러 Agent가 하루 일정을 만들고, 같은 장소에서 만나면 자동으로 대화하는 시뮬레이션 프로젝트다.

대화가 끝나면 LLM이 대화에서 나온 사실(Fact)과 관계 요약(Reflection)을 분석해서 각 Agent의 Memory와 Relation Map에 저장한다.  
마지막에는 특정 Agent 기준으로 리포트를 파일로 저장한다.

LLM은 다음 순서로 사용된다.

```text
OpenAI → Ollama(qwen3:8b) → RuleBasedLLM
```

OpenAI 키가 없거나 Ollama 모델이 없어도 RuleBasedLLM으로 실행되도록 했다.

---

## 1. 설치

```powershell
python -m pip install -r requirements.txt
```

필요 패키지는 다음과 같다.

```text
openai
ollama
python-dotenv
```

---

## 2. 환경 변수 설정

`.env.example`을 복사해서 `.env` 파일을 만든다.

```powershell
copy .env.example .env
```

예시:

```env
# OpenAI 사용 여부
USE_OPENAI=true
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL_NAME=gpt-5.5
OPENAI_MAX_OUTPUT_TOKENS=1024

# Ollama 사용 여부
USE_OLLAMA=true
OLLAMA_MODEL_NAME=qwen3:8b
OLLAMA_NUM_CTX=2048
OLLAMA_NUM_PREDICT=256

# 시뮬레이션 설정
START_HOUR=8
END_HOUR=22
SIMULATION_DAYS=2
DEFAULT_TURNS=2

# 상대별 최근 Memory 몇 개까지 사용할지
MAX_MEMORY_PER_TARGET=3

# 랜덤 topic 적용 확률
# 0.0 = 사용 안 함, 1.0 = 항상 사용
TOPIC_PROBABILITY=0.5

# 리포트 설정
REPORT_AGENT_NAME=지훈
REPORT_FILE_PATH=reports/final_jihoon_report.md
```

---

## 3. 실행

```powershell
python main.py
```

실행이 끝나면 설정된 경로에 리포트가 저장된다.

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
```

가장 빠른 테스트용으로 RuleBasedLLM만 쓰려면:

```env
USE_OPENAI=false
USE_OLLAMA=false
```

---

## 5. 파일 구조

```text
main.py                → 실행 시작점
config.py              → .env 설정 로딩
models.py              → Agent, Memory, Relation, Meeting 데이터 구조
simulation.py          → 시뮬레이션 진행 로직
llm_client.py          → LLM 공통 인터페이스
prompt_llm_base.py     → LLM 공통 프롬프트 / JSON 파싱
openai_llm.py          → OpenAI 연결
ollama_llm.py          → Ollama 연결
rule_based_llm.py      → LLM 없이 실행하는 fallback
cascade_llm_client.py  → OpenAI → Ollama → RuleBasedLLM 순서 처리
utils.py               → 시간 슬롯 생성, 초기 Memory/관계 주입
```

---

## 6. Agent 구조

Agent는 기본적으로 다음 정보를 가진다.

```text
이름
나이
성별
직업
성격
말투
관심사
목표
배경
특징
```

예시:

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
    quirks=[
        "대화 중 예시를 들어 설명하려 함",
        "처음에는 조심스럽지만 익숙해지면 질문이 많아짐"
    ]
)
```

말투, 관심사, 목표, 배경, 특징을 넣어서 Agent마다 대화 스타일이 다르게 나오도록 했다.

---

## 7. Memory / Relation / Meeting

Agent는 세 가지 상태를 가진다.

```text
Memory       → 상대에 대해 알고 있는 사실
Relation Map → 상대에 대한 관계 요약
Meeting Map  → 실제로 만난 적이 있는지 기록
```

`meeting_map`을 따로 둔 이유는 이미 만난 상대에게 계속 자기소개를 반복하지 않게 하기 위해서다.

---

## 8. 초기 관계 설정

초기 Memory는 이렇게 넣는다.

```python
inject_initial_memory(
    receiver=agent_map["지훈"],
    subject_name="민수",
    fact="민수는 예전에 지훈과 같은 동네에 살았다."
)
```

초기 관계는 이렇게 넣는다.

```python
inject_initial_relationship(
    agent_a=agent_map["지훈"],
    agent_b=agent_map["하린"],
    relationship_name="연애중"
)

inject_initial_relationship(
    agent_a=agent_map["민수"],
    agent_b=agent_map["수진"],
    relationship_name="연애중"
)
```

현재 초기 관계는 다음과 같다.

```text
지훈 ↔ 하린: 연애중
민수 ↔ 수진: 연애중
```

초기 관계 주입은 Memory, Relation Map, Meeting Map을 같이 설정한다.  
그래서 연애중인 Agent들은 처음부터 이미 만난 사이로 처리된다.

---

## 9. 대화 시스템

같은 시간에 같은 장소에 2명 이상의 Agent가 있으면 자동으로 대화한다.

대화에는 다음 정보가 들어간다.

```text
Agent 기본 정보
말투와 성격
관심사와 목표
Memory
Relation
Meeting 기록
topic
발언 횟수
```

처음 만나는 상대에게는 자기소개를 하고, 이미 만난 상대에게는 자기소개를 반복하지 않도록 했다.

---

## 10. 랜덤 Topic

topic은 확률적으로 들어간다.

```env
TOPIC_PROBABILITY=0.5
```

값의 의미는 다음과 같다.

```text
0.0 → topic 사용 안 함
0.5 → 50% 확률로 사용
1.0 → 항상 사용
```

topic은 장소, 시간, 참여자의 관심사, 관계 상태를 참고해서 고른다.

예시:

```text
카페 → 커피 취향, 최근 관심사
도서관 → 공부 계획, 읽고 있는 책
레스토랑 → 식사 메뉴, 하루 동안 있었던 일
연애중 관계 포함 → 서로의 최근 컨디션
```

---

## 11. 발언 횟수

자동 시뮬레이션에서는 모든 참여자에게 `DEFAULT_TURNS`가 적용된다.

```env
DEFAULT_TURNS=2
```

이면 Agent 한 명당 기본 2번씩 말한다.

구조적으로는 Agent별 발언 횟수를 따로 설정할 수도 있다.

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

---

## 12. Fact / Reflection 분석

대화가 끝나면 `analyze_round()`에서 Fact와 Reflection을 한 번에 분석한다.

```text
대화 로그
→ Fact 추출
→ Reflection 갱신
```

Fact는 해당 Agent를 제외한 나머지 참여자의 Memory에 저장된다.  
Reflection은 `viewer → target` 방향으로 저장된다.

기존처럼 Agent 쌍마다 LLM을 호출하지 않고, 한 번에 분석하도록 해서 호출 횟수를 줄였다.

---

## 13. 리포트

시뮬레이션 종료 후 특정 Agent 기준 리포트를 만든다.

```python
report = simulation.generate_report(REPORT_AGENT_NAME)
```

리포트는 상대방별로 다음 순서로 나온다.

```text
만남 기록
알고 있는 사실
관계 / Reflection
```