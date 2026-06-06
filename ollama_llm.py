from typing import Any

from prompt_llm_base import PromptLLMBase


try:
    from ollama import chat as ollama_chat
except ImportError:
    ollama_chat = None


class OllamaLLM(PromptLLMBase):
    name = "OllamaLLM"

    def __init__(
        self,
        model_name: str,
        num_ctx: int,
        num_predict: int,
        max_memory_per_target: int = 5
    ):
        super().__init__(max_memory_per_target=max_memory_per_target)

        if ollama_chat is None:
            raise RuntimeError("ollama 패키지가 설치되어 있지 않습니다.")

        self.model_name = model_name
        self.num_ctx = num_ctx
        self.num_predict = num_predict

    def _ask(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.4
    ) -> str:
        kwargs = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            "options": {
                "temperature": temperature,
                "num_ctx": self.num_ctx,
                "num_predict": self.num_predict
            },
            "stream": False
        }

        try:
            response = ollama_chat(
                **kwargs,
                think=False
            )
        except TypeError:
            response = ollama_chat(**kwargs)

        text = self._get_response_text(response)
        return self._remove_think_tags(text).strip()

    def _get_response_text(self, response: Any) -> str:
        if hasattr(response, "message") and hasattr(response.message, "content"):
            return str(response.message.content)

        if isinstance(response, dict):
            message = response.get("message", {})

            if isinstance(message, dict):
                return str(message.get("content", ""))

        return str(response)
