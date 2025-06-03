import os
import re
import logging
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
        Returns a list of tip titles by parsing the TITLE_BLOCK section.
        """
        import re
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
            return []

        # Save original content for token counting
        original_content = content

        # Remove <think> tags (if any) for parsing
        content = re.sub(r'<think\b[^>]*>.*?</think>', '', content, flags=re.DOTALL | re.IGNORECASE)

        # Extract TITLE_BLOCK
        match = re.search(r"<TITLE_BLOCK_START>\s*(.*?)\s*</TITLE_BLOCK_END>", content, re.DOTALL | re.IGNORECASE)
        tips = []

        if match:
            block = match.group(1)
            for line in block.strip().splitlines():
                if line.strip().startswith("#") and '|' in line:
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        title_block = parts[1].strip()
                        full, short = map(str.strip, title_block.split("|", 1))
                        tips.append({"full": full, "short": short})

        # Estimate and log the token usage using the original content
        self.tokens_used += int(len(original_content.split()) * 0.75)
        logger.debug(f"Extracted tips: {tips}")
        return tips

    def generate_tip_detail(self, topic, tip_title, tip_index, total_tips):
        """
        Generates a full expert tip (markdown) for the given tip title.
        Continues the chat if '### Conclusion' is not found in the response, up to 3 times.
        """
        max_retries = 3
        attempt = 0
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

        while "### Conclusion" not in content and attempt < max_retries - 1:
            attempt += 1
            logger.warning(f"'### Conclusion' not found in response for tip #{tip_index}. Sending 'Please continue.' (Attempt {attempt+1})")
            followup_messages = [
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": content},
                {"role": "user", "content": "Please continue."}
            ]
            new_content = ""
            for msg in self.ollama.chat(
                model=self.model,
                messages=followup_messages,
                stream=True
            ):
                piece = msg['message']['content']
                print(piece, end="", flush=True)
                new_content += piece

            # Save original new_content for token counting
            original_content += new_content

            new_content = re.sub(r'<think\b[^>]*>.*?</think>', '', new_content, flags=re.DOTALL | re.IGNORECASE)
            print("\n[End of Ollama Streaming Output]")
            logger.debug(f"Received tip detail response (continued): {new_content}")
            content += new_content

        # Estimate and log the token usage using the original content (all responses)
        self.tokens_used += int(len(original_content.split()) * 0.75)

        if "### Conclusion" in content:
            return content
        else:
            logger.error(f"Failed to get complete tip detail for tip #{tip_index} after {max_retries} attempts.")
            return content  # Return the last attempt's content even if incomplete

    def generate(self, topic, quantity):
        """
        Returns a list of tuples: (tip_index, tip_title, tip_detail)
        """
        tips = self.generate_tip_titles(topic, quantity)
        #exit(0)
        details = []
        for i, tip in enumerate(tips, 1):
            detail = self.generate_tip_detail(topic, tip["full"], i, len(tips))
            details.append((i, tip["full"], detail))
        return details