"""Ollama Engine implementation for AI tips generation.

This module provides an implementation of the CompletionEnginePort interface
using Ollama as the underlying language model. It handles the generation of
AI tips with different expertise levels and formats the output according to
specified templates.

The engine supports:
- Different expertise levels (Novice to Expert)
- Customizable prompts based on model type
- Streaming responses
- Token usage tracking
"""

import os
import re
import logging
from typing import Dict, List, Tuple, Optional
from ollama import Client
from core.ports import CompletionEnginePort

# ANSI color codes
GRAY = "\033[90m"
ORANGE = "\033[33m"  # Orange color
RED = "\033[31m"    # Red color
CYAN = "\033[36m"   # Cyan color
RESET = "\033[0m"


class OllamaEngineError(Exception):
    """Base exception for Ollama engine errors."""


class OllamaPromptError(OllamaEngineError):
    """Raised when there are issues with prompt processing."""


class OllamaResponseError(OllamaEngineError):
    """Raised when there are issues with the model's response."""


logger = logging.getLogger(__name__)
MAX_ITERATIONS = 3


class OllamaEngine(CompletionEnginePort):
    """Implementation of CompletionEnginePort using Ollama as the backend.

    This class handles the generation of AI tips using Ollama's language
    models. It supports different expertise levels and formats the output
    according to specified templates.

    Attributes:
        level_descriptions (Dict[str, str]): Mapping of expertise levels to
            their descriptions.
        model (str): The name of the Ollama model to use.
        stream (bool): Whether to stream the responses.
        category (str): The category of tips to generate.
        expertise_level (str): The expertise level for the generated tips.
        context_note (str): The context note based on expertise level.
        tokens_used (int): Counter for tokens used in generation.
    """

    level_descriptions: Dict[str, str] = {
        "Novice": "You are new to this topic and need clear, simple guidance.",
        "Intermediate": (
            "You have some experience and are ready for more depth."
        ),
        "Advanced": (
            "You are comfortable with the topic and want sophisticated "
            "techniques."
        ),
        "Expert": (
            "You are deeply experienced and need highly technical, "
            "optimized solutions."
        )
    }

    def __init__(
        self,
        model: str,
        host: Optional[str] = None,
        stream: bool = False,
        category: str = "Tip",
        expertise_level: str = "Novice"
    ) -> None:
        """Initialize the OllamaEngine.

        Args:
            model: The name of the Ollama model to use.
            host: Optional host URL for the Ollama server.
            stream: Whether to stream the responses.
            category: The category of tips to generate.
            expertise_level: The expertise level for the generated tips.

        Raises:
            OllamaEngineError: If there's an error initializing the engine.
            ValueError: If the expertise level is invalid.
        """
        logger.debug(
            "Initializing OllamaEngine with model=%s, host=%s, stream=%s",
            model,
            host,
            stream
        )
        self.model = model
        self.stream = stream
        self.category = category

        # Normalize expertise_level to title case for matching
        normalized_level = expertise_level.strip().title()
        if normalized_level not in self.level_descriptions:
            valid_levels = ", ".join(self.level_descriptions.keys())
            raise ValueError(
                f"Invalid expertise level: '{expertise_level}'. "
                f"Please choose from: {valid_levels}"
            )

        self.expertise_level = normalized_level
        self.context_note = self.level_descriptions[self.expertise_level]

        try:
            # Create a custom Ollama client with the specified host
            self.ollama = Client(host=host) if host else Client()
        except Exception as exc:
            raise OllamaEngineError(
                f"Failed to connect to Ollama server at {host or 'default'}. "
                f"Please ensure the server is running and accessible. "
                f"Error: {str(exc)}"
            ) from exc

        here = os.path.dirname(__file__)

        # Load prompt templates based on model
        base_model = self.model.split(":")[0].split(".")[0].lower()
        # Load titles prompt template
        titles_prompt_dir = os.path.abspath(
            os.path.join(here, "prompts/titles")
        )
        titles_prompt_path = os.path.join(
            titles_prompt_dir, f"{base_model}.txt"
        )
        if not os.path.exists(titles_prompt_path):
            titles_prompt_path = os.path.join(titles_prompt_dir, "llama.txt")
            logger.warning(
                "Model-specific prompt template not found for %s, "
                "falling back to llama.txt",
                base_model
            )

        logger.debug(
            "%sUsing titles prompt file: %s%s",
            CYAN,
            titles_prompt_path,
            RESET
        )
        try:
            with open(titles_prompt_path, encoding="utf-8") as file:
                self._prompt_titles_template = file.read()
        except Exception as exc:
            raise OllamaPromptError(
                f"Failed to load titles prompt template from "
                f"{titles_prompt_path}. Error: {str(exc)}"
            ) from exc

        # Load content prompt template
        content_prompt_dir = os.path.abspath(
            os.path.join(here, "prompts/content")
        )
        content_prompt_path = os.path.join(
            content_prompt_dir, f"{base_model}.txt"
        )
        if not os.path.exists(content_prompt_path):
            content_prompt_path = os.path.join(content_prompt_dir, "llama.txt")
            logger.warning(
                "Model-specific content template not found for %s, "
                "falling back to llama.txt",
                base_model
            )

        logger.debug(
            "%sUsing content prompt file: %s%s",
            CYAN,
            content_prompt_path,
            RESET
        )
        try:
            with open(content_prompt_path, encoding="utf-8") as file:
                self.prompt_detail_template = file.read()
        except Exception as exc:
            raise OllamaPromptError(
                f"Failed to load content prompt template from "
                f"{content_prompt_path}. Error: {str(exc)}"
            ) from exc

        self.tokens_used = 0

    def build_titles_prompt(self, topic: str, quantity: int) -> str:
        """Build the prompt for generating tip titles.

        Args:
            topic: The topic to generate tips for.
            quantity: The number of tips to generate.

        Returns:
            The formatted prompt string.
        """
        prompt = self._prompt_titles_template.replace("{{TOPIC}}", topic)
        prompt = prompt.replace("{{NUMBER_OF_TIPS}}", str(quantity))
        prompt = prompt.replace("{{CATEGORY}}", self.category)
        prompt = prompt.replace("{{EXPERTISE_LEVEL}}", self.expertise_level)
        prompt = prompt.replace("{{CONTEXT_NOTE}}", self.context_note)
        return prompt

    def build_detail_prompt(self, topic: str, tip_title: str, tip_index: int) -> str:
        """Build the prompt for generating tip details.

        Args:
            topic: The topic to generate tips for.
            tip_title: The title of the tip to generate details for.
            tip_index: The index of the tip to generate details for.
        Returns:
            The formatted prompt string.
        """
        prompt = self.prompt_detail_template.replace("{{TOPIC}}", topic)
        prompt = prompt.replace("{{TIP_TITLE}}", tip_title)
        prompt = prompt.replace("{{CATEGORY}}", self.category)
        prompt = prompt.replace("{{EXPERTISE_LEVEL}}", self.expertise_level)
        prompt = prompt.replace("{{CONTEXT_NOTE}}", self.context_note)
        prompt = prompt.replace("{{TIP_INDEX}}", str(tip_index))
        return prompt

    def generate_tip_titles(
        self, topic: str, quantity: int
    ) -> Tuple[List[Dict[str, str]], str]:
        """Generate a list of tip titles for the given topic.

        Args:
            topic: The topic to generate tips for.
            quantity: The number of tips to generate.

        Returns:
            A tuple containing:
                - List of dictionaries with 'full' and 'short' title keys
                - Overview string of the generated tips

        Note:
            The output is parsed from the model's response between
            <TITLE_BLOCK> and </TITLE_BLOCK> tags.
        """
        prompt = self.build_titles_prompt(topic, quantity)
        logger.debug(
            "----Prompt BEGIN----\n"
            "%s%s%s\n"
            "----Prompt END----",
            ORANGE,
            prompt,
            RESET
        )
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": prompt}
        ]

        content = ""
        in_think_block = False
        try:
            for msg in self.ollama.chat(
                model=self.model,
                messages=messages,
                stream=True
            ):
                piece = msg['message']['content']

                # Handle think tags for display only
                if "<think>" in piece:
                    in_think_block = True
                if "</think>" in piece:
                    in_think_block = False

                # Print with appropriate color
                color = RED if in_think_block else GRAY
                print(f"{color}{piece}{RESET}", end="", flush=True)
                content += piece
        except KeyboardInterrupt:
            print("\n[Interrupted] Partial session discarded.")
            return [], ""

        original_content = content
        # Remove <think> tags for further processing
        content = re.sub(
            r'<think\b[^>]*>.*?</think>',
            '',
            content,
            flags=re.DOTALL | re.IGNORECASE
        )
        self.tokens_used += int(len(original_content.split()) * 0.75)

        # Ensure </TITLE_OVERVIEW> is present for consistent parsing
        if ("<TITLE_OVERVIEW>" in content and
                "</TITLE_OVERVIEW>" not in content):
            content += "</TITLE_OVERVIEW>"

        # Extract title block and overview using regex
        title_block_match = re.search(
            r"<TITLE_BLOCK>(.*?)</TITLE_BLOCK>",
            content,
            re.DOTALL | re.IGNORECASE
        )
        overview_match = re.search(
            r"<TITLE_OVERVIEW>(.*?)</TITLE_OVERVIEW>",
            content,
            re.DOTALL | re.IGNORECASE
        )

        logger.debug("Content after all regex and tag fixes:\n%s", content)

        tips = []
        overview = ""
        if not title_block_match:
            raise OllamaResponseError(
                "Failed to generate tip titles. The model's response did not "
                "contain the expected TITLE_BLOCK format. Please try again "
                "with a different topic or model."
            )

        title_lines = title_block_match.group(1).strip().splitlines()
        for line in title_lines:
            # Match lines like: 1. Decorators for Advanced Functionality |
            # Decorators
            match = re.match(r"\d+\.\s*(.*?)\s*\|\s*(.*)", line)
            if match:
                full_title = match.group(1).strip()
                short_title = match.group(2).strip()
                tips.append({"full": full_title, "short": short_title})

        if not tips:
            raise OllamaResponseError(
                "Failed to parse tip titles from the model's response. "
                "The response format was not as expected. Please try again."
            )

        if not overview_match:
            logger.warning("TITLE_OVERVIEW not found in model output.")
        else:
            overview = overview_match.group(1).strip()

        # Log extracted tips and overview
        logger.debug("Extracted tips: %s, overview: %s", tips, overview)
        return tips, overview

    def generate_tip_detail(
        self, topic: str, tip_title: str, tip_index: int, total_tips: int
    ) -> str:
        """Generate detailed content for a specific tip.

        Args:
            topic: The topic to generate tips for.
            tip_title: The title of the tip to generate details for.
            tip_index: The index of the current tip being generated.
            total_tips: The total number of tips being generated.

        Returns:
            The generated tip content as a string.

        Note:
            The content is generated in markdown format and includes sections
            like introduction, main content, and conclusion.
        """
        prompt = self.build_detail_prompt(topic, tip_title, tip_index)
        logger.debug(
            "----Prompt BEGIN----\n"
            "%s%s%s\n"
            "----Prompt END----",
            ORANGE,
            prompt,
            RESET
        )
        messages = [{"role": "user", "content": prompt}]
        content = ""
        print(
            f"+-----\n| Processing Tip #{tip_index} of {total_tips} "
            f"(Attempt 1)\n+-----"
        )

        in_think_block = False
        for msg in self.ollama.chat(
            model=self.model,
            messages=messages,
            stream=True
        ):
            piece = msg['message']['content']

            # Handle think tags for display only
            if "<think>" in piece:
                in_think_block = True
            if "</think>" in piece:
                in_think_block = False

            # Print with appropriate color
            color = RED if in_think_block else GRAY
            print(f"{color}{piece}{RESET}", end="", flush=True)
            content += piece

        # Save original content for token counting
        original_content = content

        # Remove <think> tags for further processing
        content = re.sub(
            r'<think\b[^>]*>.*?</think>',
            '',
            content,
            flags=re.DOTALL | re.IGNORECASE
        )
        print("\n[End of Ollama Streaming Output]")
        # logger.debug("Received tip detail response:\n%s", content)

        # Estimate and log the token usage using the original content
        self.tokens_used += int(len(original_content.split()) * 0.75)

        return content

    def generate(
        self, topic: str, quantity: int
    ) -> Tuple[List[Tuple[int, Dict[str, str], str]], str]:
        """Generate a complete set of tips for the given topic.

        Args:
            topic: The topic to generate tips for.
            quantity: The number of tips to generate.

        Returns:
            A tuple containing:
                - List of tuples with (tip_index, tip_dict, tip_detail)
                - Overview string of all generated tips

        Note:
            This method orchestrates the generation of both tip titles and
            their detailed content.
        """
        tips, overview = self.generate_tip_titles(topic, quantity)
        details = []
        for i, tip in enumerate(tips, 1):
            detail = self.generate_tip_detail(
                topic,
                tip["full"],
                i,
                len(tips)
            )
            details.append((i, tip, detail))
        return details, overview
