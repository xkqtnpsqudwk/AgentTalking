from __future__ import annotations

from typing import Any, Dict, List, Optional
import json
import re

from models import Agent, ConversationRound, ConversationTurn, RoundAnalysis


class PromptLLMBase:
    name = "PromptLLMBase"

    def __init__(self, max_memory_per_target: int = 5):
        self.max_memory_per_target = max_memory_per_target

    def _ask(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.4
    ) -> str:
        raise NotImplementedError

    def health_check(self) -> None:
        result = self._ask(
            system_prompt="너는 테스트 도우미다.",
            user_prompt="정상 작동 중이면 OK만 출력해라.",
            temperature=0.1
        )

        if not result.strip():
            raise RuntimeError("health_check 응답이 비어 있습니다.")

    def _remove_think_tags(self, text: str) -> str:
        return re.sub(
            r"<think>.*?</think>",
            "",
            text,
            flags=re.DOTALL
        ).strip()

    def _extract_json(self, text: str) -> Any:
        text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        fenced_blocks = re.findall(
            r"```(?:json)?\s*(.*?)```",
            text,
            flags=re.DOTALL
        )

        for block in fenced_blocks:
            block = block.strip()

            try:
                return json.loads(block)
            except json.JSONDecodeError:
                pass

        for candidate in self._balanced_json_candidates(text):
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue

        raise ValueError(f"JSON 파싱 실패:\n{text}")

    def _balanced_json_candidates(self, text: str) -> List[str]:
        candidates = []

        for start_index, start_char in enumerate(text):
            if start_char not in "{[":
                continue

            stack = []
            in_string = False
            escape = False

            for index in range(start_index, len(text)):
                char = text[index]

                if in_string:
                    if escape:
                        escape = False
                    elif char == "\\":
                        escape = True
                    elif char == '"':
                        in_string = False

                    continue

                if char == '"':
                    in_string = True
                    continue

                if char in "{[":
                    stack.append(char)
                    continue

                if char in "}]":
                    if not stack:
                        break

                    open_char = stack.pop()

                    if open_char == "{" and char != "}":
                        break

                    if open_char == "[" and char != "]":
                        break

                    if not stack:
                        candidates.append(text[start_index:index + 1])
                        break

        return candidates

    def _ask_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2
    ) -> Any:
        last_error = None

        for _ in range(2):
            text = self._ask(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=temperature
            )

            try:
                return self._extract_json(text)
            except Exception as error:
                last_error = error
                user_prompt = f"""
이전 응답은 JSON 파싱에 실패했다.
반드시 순수 JSON만 다시 출력해라.
마크다운, 설명, 코드블록, 주석은 금지한다.

원래 요청:
{user_prompt}
"""

        raise ValueError(f"JSON 재시도 실패: {last_error}")

    def _extract_relationship_facts(
        self,
        agent: Agent,
        target_name: str
    ) -> List[str]:
        """
        일반 Memory는 최근 몇 개만 프롬프트에 넣지만,
        관계 관련 Memory는 오래된 내용이어도 항상 넣기 위해 따로 추출한다.
        """

        relationship_keywords = [
            "연애중",
            "연인",
            "애인",
            "사귀",
            "사귄",
            "현재 수진과",
            "현재 지훈과",
            "현재 민수와",
            "현재 하린과",
            "헤어진 연인",
            "과거에는",
            "과거 연인",
            "전 연인",
            "이별",
            "헤어",
            "어색함",
            "미련",
            "거리감",
            "조심스럽",
            "반말",
            "챙긴다",
            "배려",
            "편하게 말",
            "가까운 관계",
            "현재 관계",
            "과거 관계"
        ]

        relationship_facts = []

        for entry in agent.memory.get(target_name, []):
            if any(keyword in entry.fact for keyword in relationship_keywords):
                relationship_facts.append(entry.fact)

        return relationship_facts

    def make_daily_plan(
        self,
        agent: Agent,
        places: List[str],
        time_slots: List[str],
        day: int
    ) -> Dict[str, str]:
        system_prompt = """
너는 가상 인물 시뮬레이션의 일정 생성기다.
반드시 JSON 객체만 출력해라.
설명, 마크다운, 코드블록은 출력하지 마라.
"""

        user_prompt = f"""
다음 Agent의 하루 장소 계획을 만들어라.

Day: {day}

Agent 정보:
- 이름: {agent.name}
- 나이: {agent.profile.age}
- 성별: {agent.profile.gender}
- 직업: {agent.profile.job}
- 성격: {agent.profile.personality}
- 말투: {agent.profile.speech_style}
- 관심사: {json.dumps(agent.profile.interests, ensure_ascii=False)}
- 목표: {agent.profile.goal}
- 배경: {agent.profile.background}
- 특징: {json.dumps(agent.profile.quirks, ensure_ascii=False)}

사용 가능한 장소:
{json.dumps(places, ensure_ascii=False)}

시간 슬롯:
{json.dumps(time_slots, ensure_ascii=False)}

규칙:
- 각 시간 슬롯마다 반드시 장소 하나를 배정한다.
- 장소는 반드시 사용 가능한 장소 목록 안에서만 고른다.
- 직업, 성격, 목표, 관심사에 어울리는 자연스러운 하루 계획을 만든다.
- 성별은 인물 정보로만 참고하고, 성별 고정관념에 따라 장소를 결정하지 않는다.
- 출력은 JSON 객체만 사용한다.

출력 예시:
{{
  "08:00": "집",
  "09:00": "학교"
}}
"""

        raw_plan = self._ask_json(system_prompt, user_prompt)
        fixed_plan = {}

        if not isinstance(raw_plan, dict):
            raw_plan = {}

        for time_label in time_slots:
            place = raw_plan.get(time_label)

            if place not in places:
                place = places[0]

            fixed_plan[time_label] = place

        return fixed_plan

    def generate_conversation(
        self,
        participants: List[Agent],
        place: str,
        time_label: str,
        topic: Optional[str],
        turns_by_agent: Dict[str, int]
    ) -> List[ConversationTurn]:
        participant_info = []

        for agent in participants:
            known_info = {}
            relations = {}
            meetings = {}
            relationship_states = {}

            for other in participants:
                if other.name == agent.name:
                    continue

                recent_memory = agent.memory.get(other.name, [])[-self.max_memory_per_target:]
                relationship_facts = self._extract_relationship_facts(
                    agent=agent,
                    target_name=other.name
                )

                meeting_record = agent.meeting_map.get(other.name)

                known_info[other.name] = {
                    "has_met_before": agent.has_met(other.name),
                    "meet_count": meeting_record.meet_count if meeting_record else 0,
                    "facts": [
                        entry.fact
                        for entry in recent_memory
                    ],
                    "relationship_facts": relationship_facts
                }

                meetings[other.name] = {
                    "has_met_before": agent.has_met(other.name),
                    "meet_count": meeting_record.meet_count if meeting_record else 0,
                    "last_met": (
                        {
                            "day": meeting_record.last_day,
                            "time": meeting_record.last_time_label,
                            "place": meeting_record.last_place,
                            "round_id": meeting_record.last_round_id
                        }
                        if meeting_record
                        else None
                    )
                }

                relation_entry = agent.relation_map.get(other.name)
                relation_summary = (
                    relation_entry.summary
                    if relation_entry
                    else ""
                )

                relations[other.name] = (
                    relation_summary
                    if relation_summary
                    else None
                )

                all_memory_text = " ".join(
                    entry.fact
                    for entry in agent.memory.get(other.name, [])
                )

                relationship_facts_text = " ".join(relationship_facts)

                combined_relationship_text = (
                    f"{relation_summary} "
                    f"{all_memory_text} "
                    f"{relationship_facts_text}"
                )

                relationship_states[other.name] = {
                    "is_current_partner": "연애중" in combined_relationship_text,
                    "is_ex_partner": "헤어진 연인" in combined_relationship_text,
                    "relationship_facts": relationship_facts
                }

            # 대화에서는 goal/background를 뺀다.
            # 이유: 이 값이 강하면 관계 중심 일상 대화가 아니라 직업/목표 이야기로 흐르기 쉽다.
            participant_info.append({
                "name": agent.name,
                "age": agent.profile.age,
                "gender": agent.profile.gender,
                "job": agent.profile.job,
                "personality": agent.profile.personality,
                "speech_style": agent.profile.speech_style,
                "interests": agent.profile.interests[:2],
                "quirks": agent.profile.quirks,
                "known_info": known_info,
                "relations": relations,
                "meetings": meetings,
                "relationship_states": relationship_states
            })

        system_prompt = """
너는 가상 인물 시뮬레이션의 대화 생성기다.
반드시 JSON 배열만 출력해라.
설명, 마크다운, 코드블록은 출력하지 마라.
"""

        user_prompt = f"""
다음 조건에 맞는 자연스러운 대화를 생성해라.

장소: {place}
시간: {time_label}
주제: {topic if topic else "없음"}

참여 Agent 정보:
{json.dumps(participant_info, ensure_ascii=False, indent=2)}

Agent별 발언 횟수:
{json.dumps(turns_by_agent, ensure_ascii=False, indent=2)}

대화 규칙:
- 각 Agent는 지정된 발언 횟수만큼 말한다.
- 처음 만나는 상대인지 여부는 known_info 안의 has_met_before 값을 기준으로 판단한다.
- has_met_before가 false인 상대와는 각 Agent의 첫 발언에서만 인사와 자기소개를 한다.
- has_met_before가 true인 상대에게는 이름, 나이, 직업을 다시 소개하지 않는다.
- 같은 라운드 안에서 자기소개를 반복하지 않는다.

topic 처리 규칙:
- topic이 있으면 그 topic을 대화의 표면적인 주제로 사용한다.
- topic을 관계 갈등, 감정 고백, 연애 문제 주제로 바꾸지 않는다.
- topic은 커피, 식사, 공부, 날씨, 근황 같은 일상 대화의 소재로 유지한다.
- 관계 정보는 topic 자체를 바꾸는 것이 아니라 말투, 반응, 거리감, 배려, 어색함에만 영향을 준다.

관계 말투 규칙:
- relationship_states에서 is_current_partner가 true인 상대는 현재 연인으로 취급한다.
- relationship_states에서 relationship_facts가 있으면 그 내용을 반드시 참고한다.
- 현재 연인끼리는 서로에게 편한 말투나 반말을 사용할 수 있다.
- 현재 연인끼리만 대화하는 상황이면 말투를 더 편하게 해도 된다.
- 현재 연인끼리는 평범한 topic을 말하더라도 가벼운 배려, 익숙함, 자연스러운 챙김이 드러나게 한다.
- 현재 연인끼리는 상대의 컨디션, 식사, 피곤함, 일정 같은 사소한 부분을 자연스럽게 챙길 수 있다.
- 여러 사람이 함께 있는 상황에서는 연인 관계를 과하게 드러내지 말고, 짧은 챙김이나 눈치 보는 반응 정도로만 표현한다.
- relationship_states에서 is_ex_partner가 true인 상대는 헤어진 연인으로 취급한다.
- 헤어진 연인끼리는 반말을 쓸 수도 있지만, 어색해서 존댓말이나 거리감 있는 표현이 섞일 수 있다.
- 헤어진 연인끼리는 평범한 topic을 말하더라도 말 고르기, 짧은 반응, 괜히 조심하는 태도가 드러날 수 있다.
- 전 연인과 현재 연인이 같은 대화에 포함되어도 topic은 일상적으로 유지하고, 긴장감은 말투와 반응으로만 표현한다.
- “우리는 연애중이니까”, “우리는 헤어진 사이니까” 같은 직접 설명은 피한다.
- 감정을 직접 해설하지 말고 말투, 돌려 말하기, 짧은 대답, 상대를 살피는 표현으로 드러낸다.
- 관계를 매 발언마다 직접 언급하지 않는다.

인물 표현 규칙:
- speech_style과 personality는 말투에 자연스럽게 반영한다.
- interests는 대화가 끊길 때 보조 소재로만 사용한다.
- goal과 background는 직접적인 주제가 되지 않는 한 대화에서 언급하지 않는다.
- 관계가 있는 상대와 대화할 때도 직업/목표 이야기보다 일상 topic에 대한 반응과 분위기를 우선한다.
- quirks는 과하지 않게 아주 가끔만 반영한다.
- 성별은 인물 정보로만 참고하고, 성별 고정관념에 따라 말투나 행동을 과장하지 않는다.
- 모든 Agent가 똑같은 말투로 말하지 않게 한다.
- 모든 발언을 감정적으로 만들지는 말고, 일상 대화 안에 은근히 섞는다.
- 각 발언은 1~2문장으로 짧게 한다.
- 출력은 JSON 배열만 사용한다.

출력 형식:
[
  {{
    "speaker": "이름",
    "text": "발언 내용"
  }}
]
"""

        raw_turns = self._ask_json(system_prompt, user_prompt)

        if not isinstance(raw_turns, list):
            raise ValueError("대화 생성 결과가 JSON 배열이 아닙니다.")

        valid_speakers = {
            agent.name
            for agent in participants
        }

        generated_counts = {
            agent.name: 0
            for agent in participants
        }

        turns = []

        for item in raw_turns:
            if not isinstance(item, dict):
                continue

            speaker = str(item.get("speaker", "")).strip()
            text = str(item.get("text", "")).strip()

            if speaker not in valid_speakers:
                continue

            if not text:
                continue

            if generated_counts[speaker] >= turns_by_agent.get(speaker, 0):
                continue

            turns.append(
                ConversationTurn(
                    speaker=speaker,
                    text=text
                )
            )

            generated_counts[speaker] += 1

        if not turns:
            raise ValueError("유효한 대화 발언이 생성되지 않았습니다.")

        return turns

    def analyze_round(
        self,
        conversation_round: ConversationRound,
        participants: List[Agent]
    ) -> RoundAnalysis:
        transcript_text = "\n".join(
            f"{turn.speaker}: {turn.text}"
            for turn in conversation_round.transcript
        )

        participant_names = [
            agent.name
            for agent in participants
        ]

        analysis_context = {}

        for viewer in participants:
            analysis_context[viewer.name] = {}

            for target in participants:
                if viewer.name == target.name:
                    continue

                recent_memory = viewer.memory.get(target.name, [])[-self.max_memory_per_target:]
                relationship_facts = self._extract_relationship_facts(
                    agent=viewer,
                    target_name=target.name
                )

                relation_entry = viewer.relation_map.get(target.name)
                meeting_record = viewer.meeting_map.get(target.name)

                analysis_context[viewer.name][target.name] = {
                    "has_met_before": viewer.has_met(target.name),
                    "meet_count": meeting_record.meet_count if meeting_record else 0,
                    "known_facts": [
                        entry.fact
                        for entry in recent_memory
                    ],
                    "relationship_facts": relationship_facts,
                    "old_reflection": (
                        relation_entry.summary
                        if relation_entry
                        else None
                    )
                }

        system_prompt = """
너는 대화 로그를 분석하는 Agent 시뮬레이션 분석기다.
반드시 JSON 객체만 출력해라.
설명, 마크다운, 코드블록은 출력하지 마라.
"""

        user_prompt = f"""
다음 대화 라운드를 분석해라.

라운드 정보:
- Round ID: {conversation_round.round_id}
- Day: {conversation_round.day}
- 시간: {conversation_round.time_label}
- 장소: {conversation_round.place}

참여자:
{json.dumps(participant_names, ensure_ascii=False)}

참여자 기본 정보:
{json.dumps([
    {
        "name": agent.name,
        "age": agent.profile.age,
        "gender": agent.profile.gender,
        "job": agent.profile.job,
        "personality": agent.profile.personality,
        "speech_style": agent.profile.speech_style,
        "interests": agent.profile.interests,
        "goal": agent.profile.goal,
        "background": agent.profile.background,
        "quirks": agent.profile.quirks
    }
    for agent in participants
], ensure_ascii=False, indent=2)}

기존 Memory / Reflection / Meeting 요약:
{json.dumps(analysis_context, ensure_ascii=False, indent=2)}

대화 로그:
{transcript_text}

작업:
1. facts_by_subject:
   - 각 인물에 대해 대화에서 명시적으로 드러난 객관적 사실만 추출한다.
   - 나이, 성별, 직업, 취미, 일정, 선호, 소속, 경험, 장소 방문 사실 등이 가능하다.
   - 추측, 감정 평가, 관계 평가는 Fact에 넣지 않는다.
   - 사실이 없으면 빈 배열을 사용한다.

2. reflections_by_viewer:
   - 각 관찰자(viewer)가 각 대상(target)을 어떻게 인식하는지 갱신한다.
   - viewer 자신에 대한 reflection은 만들지 않는다.
   - 기존 Reflection, known_facts, relationship_facts, meet_count, 이번 대화를 함께 고려한다.
   - 대상의 성격, 말투, 관심사, 목표, 특징이 관계 인식에 영향을 줄 수 있다.
   - 헤어진 연인, 연애중, 과거 연인 관계가 있으면 감정선과 긴장감을 반영한다.
   - 너무 과장하지 않고 1~2문장으로 작성한다.

출력 형식:
{{
  "facts_by_subject": {{
    "지훈": ["지훈은 대학생이다."],
    "민수": ["민수는 카페에서 일한다."]
  }},
  "reflections_by_viewer": {{
    "지훈": {{
      "민수": "지훈은 민수를 밝고 사교적인 사람으로 인식한다."
    }},
    "민수": {{
      "지훈": "민수는 지훈을 조용하지만 예의 있는 사람으로 인식한다."
    }}
  }}
}}
"""

        raw_analysis = self._ask_json(system_prompt, user_prompt)

        if not isinstance(raw_analysis, dict):
            raise ValueError("라운드 분석 결과가 JSON 객체가 아닙니다.")

        raw_facts = raw_analysis.get("facts_by_subject", {})
        raw_reflections = raw_analysis.get("reflections_by_viewer", {})

        facts_by_subject = {}
        reflections_by_viewer = {}

        for name in participant_names:
            facts = raw_facts.get(name, [])

            if isinstance(facts, list):
                facts_by_subject[name] = [
                    str(fact).strip()
                    for fact in facts
                    if str(fact).strip()
                ]
            else:
                facts_by_subject[name] = []

        for viewer in participants:
            viewer_data = raw_reflections.get(viewer.name, {})
            reflections_by_viewer[viewer.name] = {}

            if not isinstance(viewer_data, dict):
                viewer_data = {}

            for target in participants:
                if viewer.name == target.name:
                    continue

                summary = str(viewer_data.get(target.name, "")).strip()

                if summary:
                    reflections_by_viewer[viewer.name][target.name] = summary

        return RoundAnalysis(
            facts_by_subject=facts_by_subject,
            reflections_by_viewer=reflections_by_viewer
        )