import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def get_bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in ("1", "true", "yes", "y", "on")


def get_int_env(name: str, default: int) -> int:
    value = os.getenv(name)

    if value is None:
        return default

    try:
        return int(value)
    except ValueError:
        return default


def get_str_env(name: str, default: str) -> str:
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip()


USE_OPENAI = get_bool_env("USE_OPENAI", True)
OPENAI_API_KEY = get_str_env("OPENAI_API_KEY", "")
OPENAI_MODEL_NAME = get_str_env("OPENAI_MODEL_NAME", "gpt-5.5")
OPENAI_MAX_OUTPUT_TOKENS = get_int_env("OPENAI_MAX_OUTPUT_TOKENS", 512)

USE_OLLAMA = get_bool_env("USE_OLLAMA", True)
OLLAMA_MODEL_NAME = get_str_env("OLLAMA_MODEL_NAME", "qwen3:8b")
OLLAMA_NUM_CTX = get_int_env("OLLAMA_NUM_CTX", 2048)
OLLAMA_NUM_PREDICT = get_int_env("OLLAMA_NUM_PREDICT", 192)

START_HOUR = get_int_env("START_HOUR", 8)
END_HOUR = get_int_env("END_HOUR", 22)
SIMULATION_DAYS = get_int_env("SIMULATION_DAYS", 2)
DEFAULT_TURNS = get_int_env("DEFAULT_TURNS", 2)

MAX_MEMORY_PER_TARGET = get_int_env("MAX_MEMORY_PER_TARGET", 5)

REPORT_AGENT_NAME = get_str_env("REPORT_AGENT_NAME", "지훈")
REPORT_FILE_PATH = get_str_env("REPORT_FILE_PATH", "reports/final_jihoon_report.md")
