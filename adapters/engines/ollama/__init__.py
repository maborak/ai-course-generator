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
        # Load prompt templates
        with open(os.path.join(here, "prompt_slot.txt"), encoding="utf-8") as f:
            self.prompt_titles_template = f.read()
        with open(os.path.join(here, "prompt.txt"), encoding="utf-8") as f:
            self.prompt_detail_template = f.read()

        self.tokens_used = 0

    def build_titles_prompt(self, topic, quantity):
        prompt = self.prompt_titles_template.replace("{{TOPIC}}", topic)
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
        Returns a list of tip titles by parsing the YAML output from the model.
        """
        prompt = self.build_titles_prompt(topic, quantity)
        logger.debug(f"Prompt: {prompt}")

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
        logger.debug(f"Content after <think> removal: {content}")
        self.tokens_used += int(len(original_content.split()) * 0.75)

        try:
            # Parse YAML output
            data = yaml.safe_load(content)
            tips = []
            for item in data.get("title_block", []):
                tips.append({
                    "full": item.get("full_title", ""),
                    "short": item.get("short_title", "")
                })
            overview = data.get("overview", "")
            logger.debug(f"Extracted tips: {tips}, overview: {overview}")
            return tips, overview
        except Exception as e:
            logger.error(f"Failed to parse YAML from model output: {e}")
            return [], ""

    def generate_tip_detail(self, topic, tip_title, tip_index, total_tips):
        """
        Generates a full expert tip (markdown) for the given tip title.
        Only makes a single request, does not retry if '### Conclusion' is missing.
        """
        prompt = self.build_detail_prompt(topic, tip_title)
        logger.debug(f"Prompt: {prompt} (Attempt 1)")
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
        logger.debug(f"Received tip detail response: {content}")

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