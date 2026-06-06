from typing import List

from models import Agent


def make_time_slots(
    start_hour: int,
    end_hour: int
) -> List[str]:
    return [
        f"{hour:02d}:00"
        for hour in range(start_hour, end_hour + 1)
    ]


def inject_initial_memory(
    receiver: Agent,
    subject_name: str,
    fact: str
) -> None:
    """
    특정 Agent에게 초기 Memory를 주입한다.

    예:
    지훈이 민수에 대해 알고 있는 사실을 넣고 싶을 때 사용한다.
    """

    receiver.add_memory(
        subject_name=subject_name,
        fact=fact,
        day=0,
        time_label="초기 설정",
        round_id=0
    )


def inject_initial_relationship(
    agent_a: Agent,
    agent_b: Agent,
    relationship_name: str,
    emotional_context: str = ""
) -> None:
    """
    두 Agent 사이에 초기 관계를 주입한다.

    예:
    - 연애중
    - 헤어진 연인
    - 친구
    - 가족
    - 직장 동료

    이 함수는 세 가지를 동시에 처리한다.

    1. Meeting Map에 이미 만난 사이로 기록
    2. Memory에 관계 Fact 저장
    3. Relation Map에 관계 요약 저장
    """

    # 1. 서로 이미 만난 사이로 기록
    agent_a.mark_met(
        target_name=agent_b.name,
        day=0,
        time_label="초기 설정",
        place="초기 설정",
        round_id=0
    )

    agent_b.mark_met(
        target_name=agent_a.name,
        day=0,
        time_label="초기 설정",
        place="초기 설정",
        round_id=0
    )

    # 2. 서로의 Memory에 관계 Fact 저장
    context_suffix = f" {emotional_context}" if emotional_context else ""

    agent_a.add_memory(
        subject_name=agent_b.name,
        fact=(
            f"{agent_b.name}은 {agent_a.name}과 "
            f"{relationship_name} 관계이다.{context_suffix}"
        ),
        day=0,
        time_label="초기 설정",
        round_id=0
    )

    agent_b.add_memory(
        subject_name=agent_a.name,
        fact=(
            f"{agent_a.name}은 {agent_b.name}과 "
            f"{relationship_name} 관계이다.{context_suffix}"
        ),
        day=0,
        time_label="초기 설정",
        round_id=0
    )

    # 3. 서로의 Relation Map에 관계 요약 저장
    if emotional_context:
        agent_a_summary = (
            f"{agent_b.name}은 {agent_a.name}의 {relationship_name} 상대다. "
            f"{emotional_context}"
        )

        agent_b_summary = (
            f"{agent_a.name}은 {agent_b.name}의 {relationship_name} 상대다. "
            f"{emotional_context}"
        )
    else:
        agent_a_summary = (
            f"{agent_b.name}은 {agent_a.name}의 {relationship_name} 상대이며, "
            f"서로에게 의미 있는 관계다."
        )

        agent_b_summary = (
            f"{agent_a.name}은 {agent_b.name}의 {relationship_name} 상대이며, "
            f"서로에게 의미 있는 관계다."
        )

    agent_a.update_reflection(
        target_name=agent_b.name,
        summary=agent_a_summary,
        day=0,
        time_label="초기 설정",
        round_id=0
    )

    agent_b.update_reflection(
        target_name=agent_a.name,
        summary=agent_b_summary,
        day=0,
        time_label="초기 설정",
        round_id=0
    )


def inject_public_fact(
    agents: List[Agent],
    subject_name: str,
    fact: str
) -> None:
    """
    모든 Agent에게 공개 사실을 주입한다.

    예:
    모든 인물이 지훈의 현재 관계나 과거 관계를 알고 있는 상태로 만들고 싶을 때 사용한다.

    subject_name에 해당하는 인물 본인에게는 저장하지 않고,
    나머지 Agent들의 Memory에만 저장한다.
    """

    for agent in agents:
        if agent.name == subject_name:
            continue

        agent.add_memory(
            subject_name=subject_name,
            fact=fact,
            day=0,
            time_label="초기 설정",
            round_id=0
        )