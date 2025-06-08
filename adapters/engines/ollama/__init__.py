import os
import re
import logging
import json
import yaml
from core.ports import CompletionEnginePort
from ollama import Client

logger = logging.getLogger(__name__)
MAX_ITERATIONS = 3

class OllamaEngine(CompletionEnginePort):
    level_descriptions = {
        "Novice": "You are new to this topic and need clear, simple guidance.",
        "Intermediate": "You have some experience and are ready for more depth.",
        "Advanced": "You are comfortable with the topic and want sophisticated techniques.",
        "Expert": "You are deeply experienced and need highly technical, optimized solutions."
    }

    def __init__(self, model, host=None, stream=False, category="Tip", expertise_level="Novice"):
        logger.debug(f"Initializing OllamaEngine with model={model}, host={host}, stream={stream}")
        self.model = model
        self.stream = stream
        self.category = category

        # Normalize expertise_level to title case for matching
        normalized_level = expertise_level.strip().title()
        if normalized_level not in self.level_descriptions:
            raise ValueError(f"Invalid expertise level: {expertise_level}")

        self.expertise_level = normalized_level
        self.context_note = self.level_descriptions[self.expertise_level]

        # Create a custom Ollama client with the specified host
        if host:
            self.ollama = Client(host=host)
        else:
            self.ollama = Client()

        here = os.path.dirname(__file__)

        # --- Load prompt_titles_template based on model ---
        # Extract base model name (e.g., "llama" from "llama3.2")
        base_model = self.model.split(":")[0].split(".")[0].lower()
        prompt_dir = os.path.abspath(os.path.join(here, "prompts/titles"))
        prompt_path = os.path.join(prompt_dir, f"{base_model}.txt")
        if not os.path.exists(prompt_path):
            # Fallback to llama.txt if specific model prompt does not exist
            prompt_path = os.path.join(prompt_dir, "llama.txt")
        with open(prompt_path, encoding="utf-8") as f:
            self._prompt_titles_template = f.read()  # protected

        # --- Load prompt_detail_template as before ---
        with open(os.path.join(here, "prompt.txt"), encoding="utf-8") as f:
            self.prompt_detail_template = f.read()

        self.tokens_used = 0

    def build_titles_prompt(self, topic, quantity):
        prompt = self._prompt_titles_template.replace("{{TOPIC}}", topic)
        prompt = prompt.replace("{{NUMBER_OF_TIPS}}", str(quantity))
        prompt = prompt.replace("{{CATEGORY}}", self.category)
        prompt = prompt.replace("{{EXPERTISE_LEVEL}}", self.expertise_level)
        prompt = prompt.replace("{{CONTEXT_NOTE}}", self.context_note)
        return prompt

    def build_detail_prompt(self, topic, tip_title):
        prompt = self.prompt_detail_template.replace("{{TOPIC}}", topic)
        prompt = prompt.replace("{{TIP_TITLE}}", tip_title)
        prompt = prompt.replace("{{CATEGORY}}", self.category)
        prompt = prompt.replace("{{EXPERTISE_LEVEL}}", self.expertise_level)
        prompt = prompt.replace("{{CONTEXT_NOTE}}", self.context_note)
        return prompt

    def generate_tip_titles(self, topic, quantity):
        """
        Returns a list of tip titles by parsing the model output between <TITLE_BLOCK_START> and <TITLE_BLOCK_END>.
        """
        prompt = self.build_titles_prompt(topic, quantity)
        logger.debug(f"----Prompt BEGIN----\n{prompt}\n----Prompt END----")
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": prompt}
        ]

        content = ""
        try:
            for msg in self.ollama.chat(
                model=self.model,
                messages=messages,
                stream=True
            ):
                piece = msg['message']['content']
                print(piece, end="", flush=True)
                content += piece
        except KeyboardInterrupt:
            print("\n[Interrupted] Partial session discarded.")
            return [], ""

        original_content = content
        # Remove <think> tags for further processing
        content = re.sub(r'<think\b[^>]*>.*?</think>', '', content, flags=re.DOTALL | re.IGNORECASE)
        logger.debug(f"Content after <think> removal:\n{content}")
        self.tokens_used += int(len(original_content.split()) * 0.75)

        # Extract title block and overview using regex
        title_block_match = re.search(
            r"<TITLE_BLOCK_START>(.*?)</TITLE_BLOCK_END>", content, re.DOTALL | re.IGNORECASE
        )
        overview_match = re.search(
            r"<TITLE_OVERVIEW>(.*?)</TITLE_OVERVIEW>", content, re.DOTALL | re.IGNORECASE
        )

        tips = []
        overview = ""
        if title_block_match:
            title_lines = title_block_match.group(1).strip().splitlines()
            for line in title_lines:
                # Match lines like: 1. Decorators for Advanced Functionality | Decorators
                m = re.match(r"\d+\.\s*(.*?)\s*\|\s*(.*)", line)
                if m:
                    full_title = m.group(1).strip()
                    short_title = m.group(2).strip()
                    tips.append({"full": full_title, "short": short_title})
        else:
            logger.error("TITLE_BLOCK not found in model output.")

        if overview_match:
            overview = overview_match.group(1).strip()
        else:
            logger.error("TITLE_OVERVIEW not found in model output.")

        #logger.debug(f"Extracted tips: {tips}, overview: {overview}")
        return tips, overview

    def generate_tip_detail(self, topic, tip_title, tip_index, total_tips):
        """
        Generates a full expert tip (markdown) for the given tip title.
        Only makes a single request, does not retry if '### Conclusion' is missing.
        """
        prompt = self.build_detail_prompt(topic, tip_title)
        logger.debug(f"----Prompt BEGIN----\n{prompt}\n----Prompt END----")
        messages = [{"role": "user", "content": prompt}]
        content = ""
        print(f"+-----\n| Processing Tip #{tip_index} of {total_tips} (Attempt 1)\n+-----")
        for msg in self.ollama.chat(
            model=self.model,
            messages=messages,
            stream=True
        ):
            piece = msg['message']['content']
            print(piece, end="", flush=True)
            content += piece

        # Save original content for token counting
        original_content = content

        # Remove <think> tags for further processing
        content = re.sub(r'<think\b[^>]*>.*?</think>', '', content, flags=re.DOTALL | re.IGNORECASE)
        print("\n[End of Ollama Streaming Output]")
        logger.debug(f"Received tip detail response:\n{content}")

        # Estimate and log the token usage using the original content
        self.tokens_used += int(len(original_content.split()) * 0.75)

        return content

    def generate(self, topic, quantity):
        """
        Returns a list of tuples: (tip_index, tip_dict, tip_detail), and overview
        """
        tips, overview = self.generate_tip_titles(topic, quantity)
        details = []
        for i, tip in enumerate(tips, 1):
            detail = self.generate_tip_detail(topic, tip["full"], i, len(tips))
            details.append((i, tip, detail))  # pass the whole tip dict
        return details, overview