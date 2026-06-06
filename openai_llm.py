from typing import Any

from prompt_llm_base import PromptLLMBase


try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class OpenAILLM(PromptLLMBase):
    name = "OpenAILLM"

    def __init__(
        self,
        api_key: str,
        model_name: str,
        max_output_tokens: int,
        max_memory_per_target: int = 5
    ):
        super().__init__(max_memory_per_target=max_memory_per_target)

        if OpenAI is None:
            raise RuntimeError("openai 패키지가 설치되어 있지 않습니다.")

        if not api_key:
            raise RuntimeError("OPENAI_API_KEY가 비어 있습니다.")

        self.client = OpenAI(api_key=api_key)
        self.model_name = model_name
        self.max_output_tokens = max_output_tokens

    def _ask(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.4
    ) -> str:
        kwargs = {
            "model": self.model_name,
            "input": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            "max_output_tokens": self.max_output_tokens
        }

        try:
            response = self.client.responses.create(
                **kwargs,
                temperature=temperature
            )
        except Exception as error:
            message = str(error).lower()

            if "temperature" not in message:
                raise

            response = self.client.responses.create(**kwargs)

        text = self._get_output_text(response)
        return self._remove_think_tags(text).strip()

    def _get_output_text(self, response: Any) -> str:
        if hasattr(response, "output_text"):
            return str(response.output_text)

        if hasattr(response, "output"):
            parts = []

            for item in response.output:
                content = getattr(item, "content", None)

                if not content:
                    continue

                for block in content:
                    text = getattr(block, "text", None)

                    if text:
                        parts.append(str(text))

            if parts:
                return "\n".join(parts)

        return str(response)
