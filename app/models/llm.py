from google import genai
from google.genai import types  # Import types for configuration
import logging
from transformers import AutoModelForCausalLM, AutoTokenizer

logger = logging.getLogger(__name__)

class LLMModel:
    """Handles LLM operations using Google GenAI SDK"""
    
    def __init__(self, api_key: str, model: str, temperature: float):
        """Initialize the LLM client"""
        try:
            # FIX: Pass api_key as a keyword argument
            self.client = genai.Client(api_key=api_key)
            self.model = model
            self.temperature = temperature
            logger.info(f"✅ Initialized LLM model: {model}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            raise
    
    def generate(self, prompt: str, system_prompt: str = None) -> str:
        """
        Generate response from Gemini
        """
        try:
            # Gemini uses 'config' for temperature and 'contents' for messages
            # It also uses 'system_instruction' as a separate parameter
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
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise

# Singleton instance
_llm_model = None

def get_llm_model(config) -> LLMModel:
    """Get or create LLM model instance"""
    global _llm_model
    if _llm_model is None:
        _llm_model = LLMModel(
            api_key=config.GEMINI_API_KEY,
            model=config.GEMINI_MODEL,
            temperature=config.GEMINI_TEMPERATURE
        )
    return _llm_model