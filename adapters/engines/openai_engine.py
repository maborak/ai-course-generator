import os
import logging
from core.ports import CompletionEnginePort

logger = logging.getLogger(__name__)

class OpenAIEngine(CompletionEnginePort):
    def __init__(self, model, temperature, max_tokens):
        from openai import OpenAI
        logger.debug(f"Initializing OpenAIEngine with model={model}, temperature={temperature}, max_tokens={max_tokens}")
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def generate(self, prompt, quantity):
        logger.debug(f"Generating tips with OpenAIEngine. Prompt: {prompt[:100]}..., Quantity: {quantity}")
        messages = [{"role": "user", "content": prompt}]
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        result = response.choices[0].message.content
        logger.debug(f"OpenAIEngine response: {result[:100]}...")
        return result