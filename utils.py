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
