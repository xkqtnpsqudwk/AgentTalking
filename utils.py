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
    relationship_name: str
) -> None:
    """
    두 Agent 사이에 초기 관계를 주입한다.
    예: 연애중, 가족, 친구, 직장 동료 등

    이 함수는 세 가지를 동시에 처리한다.

    1. 서로 이미 만난 사이로 기록
    2. 서로의 Memory에 관계 Fact 저장
    3. 서로의 Relation Map에 관계 요약 저장
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

    # 2. 서로의 Memory에 객관적 관계 Fact 저장
    agent_a.add_memory(
        subject_name=agent_b.name,
        fact=f"{agent_b.name}은 {agent_a.name}과 {relationship_name} 관계이다.",
        day=0,
        time_label="초기 설정",
        round_id=0
    )

    agent_b.add_memory(
        subject_name=agent_a.name,
        fact=f"{agent_a.name}은 {agent_b.name}과 {relationship_name} 관계이다.",
        day=0,
        time_label="초기 설정",
        round_id=0
    )

    # 3. 서로의 Relation Map에 관계 요약 저장
    agent_a.update_reflection(
        target_name=agent_b.name,
        summary=(
            f"{agent_b.name}은 {agent_a.name}의 {relationship_name} 상대이며, "
            f"이미 서로를 잘 알고 있는 가까운 관계다."
        ),
        day=0,
        time_label="초기 설정",
        round_id=0
    )

    agent_b.update_reflection(
        target_name=agent_a.name,
        summary=(
            f"{agent_a.name}은 {agent_b.name}의 {relationship_name} 상대이며, "
            f"이미 서로를 잘 알고 있는 가까운 관계다."
        ),
        day=0,
        time_label="초기 설정",
        round_id=0
    )