import os
import logging
from core.ports import CompletionEnginePort

logger = logging.getLogger(__name__)

MODEL = "gpt-4.1"
TEMPERATURE = 0.7
MAX_TOKENS = 4096
MAX_ITERATIONS = 8
INPUT_COST_PER_1K = 0.01   # Set your own price
OUTPUT_COST_PER_1K = 0.03  # Set your own price

class OpenAIEngine(CompletionEnginePort):
    def __init__(self, model=MODEL, temperature=TEMPERATURE, max_tokens=MAX_TOKENS):
        from openai import OpenAI
        logger.debug(f"Initializing OpenAIEngine with model={model}, temperature={temperature}, max_tokens={max_tokens}")
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        # Load the prompt template from this directory
        here = os.path.dirname(__file__)
        prompt_file = os.path.join(here, "prompt.txt")
        with open(prompt_file, encoding="utf-8") as f:
            self.prompt_template = f.read()

    def build_prompt(self, topic, quantity):
        prompt = self.prompt_template.replace("{{TOPIC}}", topic)
        prompt = prompt.replace("{{NUMBER_OF_TIPS}}", str(quantity))
        return prompt

    def generate(self, topic, quantity):
        prompt = self.build_prompt(topic, quantity)
        messages = [{"role": "user", "content": prompt}]
        full_response = ""
        iteration = 0
        total_prompt_tokens = 0
        total_completion_tokens = 0

        while True:
            iteration += 1
            logger.debug(f"--- Requesting chunk {iteration} ---")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            chunk = response.choices[0].message.content
            finish_reason = response.choices[0].finish_reason
            logger.debug(f"Finish reason: {finish_reason}")
            logger.debug(f"Chunk length: {len(chunk)} characters")

            usage = response.usage
            total_prompt_tokens += usage.prompt_tokens
            total_completion_tokens += usage.completion_tokens

            full_response += chunk

            if finish_reason == "stop":
                if (f"Tip #{quantity}" in chunk or f"Tip {quantity}" in chunk) or iteration > MAX_ITERATIONS:
                    logger.debug("Completed successfully.")
                    break
                else:
                    logger.debug(f"Detected incomplete Tip #{quantity}, requesting continuation...")
                    messages.append({"role": "assistant", "content": chunk})
                    messages.append({"role": "user", "content": "Please continue from where you left off."})
                    continue
            elif finish_reason == "length":
                logger.debug("Output truncated, requesting continuation...")
                messages.append({"role": "assistant", "content": chunk})
                messages.append({"role": "user", "content": "Please continue from where you left off."})
            else:
                logger.warning(f"Unexpected finish_reason: {finish_reason}")
                break

        input_cost = (total_prompt_tokens / 1000) * INPUT_COST_PER_1K
        output_cost = (total_completion_tokens / 1000) * OUTPUT_COST_PER_1K
        total_cost = input_cost + output_cost

        logger.info(f"Total prompt tokens used: {total_prompt_tokens}")
        logger.info(f"Total completion tokens used: {total_completion_tokens}")
        logger.info(f"Input cost: ${input_cost:.4f}")
        logger.info(f"Output cost: ${output_cost:.4f}")
        logger.info(f"Total cost: ${total_cost:.4f}")

        return full_response