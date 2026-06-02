from google import genai
from google.genai import types
from groq import Groq
import logging

logger = logging.getLogger(__name__)


class LLMModel:
    """Handles LLM operations using Gemini or Groq"""

    def __init__(
        self,
        provider: str,
        api_key: str,
        model: str,
        temperature: float
    ):
        self.provider = provider.lower()
        self.model = model
        self.temperature = temperature

        try:
            if self.provider == "gemini":
                self.client = genai.Client(api_key=api_key)

            elif self.provider == "groq":
                self.client = Groq(api_key=api_key)

            else:
                raise ValueError(
                    f"Unsupported provider: {self.provider}"
                )

            logger.info(
                f"✅ Initialized {self.provider} model: {model}"
            )

        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            raise

    def generate(
        self,
        prompt: str,
        system_prompt: str = None
    ) -> str:
        try:

            if self.provider == "gemini":

                model_id = self.model.replace("models/", "")

                response = self.client.models.generate_content(
                    model=model_id,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=self.temperature,
                    ),
                )

                return response.text

            elif self.provider == "groq":

                messages = []

                if system_prompt:
                    messages.append({
                        "role": "system",
                        "content": system_prompt
                    })

                messages.append({
                    "role": "user",
                    "content": prompt
                })

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                )

                return response.choices[0].message.content

        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise


# Singleton instance
_llm_model = None


def get_llm_model(config) -> LLMModel:
    global _llm_model

    if _llm_model is None:

        provider = getattr(config, "LLM_PROVIDER", "gemini")

        if provider == "groq":

            _llm_model = LLMModel(
                provider="groq",
                api_key=config.GROQ_API_KEY,
                model=config.GROQ_MODEL,
                temperature=config.GROQ_TEMPERATURE
            )

        else:

            _llm_model = LLMModel(
                provider="gemini",
                api_key=config.GEMINI_API_KEY,
                model=config.GEMINI_MODEL,
                temperature=config.GEMINI_TEMPERATURE
            )

    return _llm_model