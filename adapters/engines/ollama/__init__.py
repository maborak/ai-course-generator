import os
import re
import logging
from core.ports import CompletionEnginePort
from ollama import Client

logger = logging.getLogger(__name__)
MAX_ITERATIONS = 3

class OllamaEngine(CompletionEnginePort):
    def __init__(self, model, host=None, stream=False):
        logger.debug(f"Initializing OllamaEngine with model={model}, host={host}, stream={stream}")
        self.model = model
        self.stream = stream

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

    def build_titles_prompt(self, topic, quantity):
        prompt = self.prompt_titles_template.replace("{{TOPIC}}", topic)
        prompt = prompt.replace("{{NUMBER_OF_TIPS}}", str(quantity))
        return prompt

    def build_detail_prompt(self, topic, tip_title):
        prompt = self.prompt_detail_template.replace("{{TOPIC}}", topic)
        prompt = prompt.replace("{{TIP_TITLE}}", tip_title)
        return prompt

    def generate_tip_titles(self, topic, quantity):
        """
        Returns a list of tip titles by parsing the TIP_BLOCK section.
        """
        prompt = self.build_titles_prompt(topic, quantity)
        messages = [{"role": "user", "content": prompt}]
        content = ""
        for msg in self.ollama.chat(
            model=self.model,
            messages=messages,
            stream=True
        ):
            piece = msg['message']['content']
            # Remove <think> tags and any content between them from the response
            piece = re.sub(r'<think>.*?</think>', '', piece, flags=re.DOTALL | re.IGNORECASE)
            print(piece, end="", flush=True)
            content += piece
        # Extract everything inside <TIP_BLOCK>...</TIP_BLOCK>
        match = re.search(r"<TIP_BLOCK>(.*?)</TIP_BLOCK>", content, re.DOTALL | re.IGNORECASE)
        tips = []
        if match:
            block = match.group(1)
            for line in block.strip().splitlines():
                if ':' in line:
                    tips.append(line.split(":", 1)[1].strip())
        logger.debug(f"Extracted tips: {tips}")
        return tips

    def generate_tip_detail(self, topic, tip_title, tip_index, total_tips):
        """
        Generates a full expert tip (markdown) for the given tip title.
        """
        prompt = self.build_detail_prompt(topic, tip_title)
        messages = [{"role": "user", "content": prompt}]
        content = ""
        print(f"+-----\n| Processing Tip #{tip_index} of {total_tips}\n+-----")
        for msg in self.ollama.chat(
            model=self.model,
            messages=messages,
            stream=True
        ):
            piece = msg['message']['content']
            # Remove <think> tags and any content between them from the response
            piece = re.sub(r'<think>.*?</think>', '', piece, flags=re.DOTALL | re.IGNORECASE)
            print(piece, end="", flush=True)
            content += piece
        print("\n[End of Ollama Streaming Output]")
        logger.debug(f"Received tip detail response: {content}")
        return content

    def generate(self, topic, quantity):
        """
        Returns a list of tuples: (tip_index, tip_title, tip_detail)
        """
        tips = self.generate_tip_titles(topic, quantity)
        details = []
        for i, tip_title in enumerate(tips, 1):
            detail = self.generate_tip_detail(topic, tip_title, i, len(tips))
            details.append((i, tip_title, detail))
        return details