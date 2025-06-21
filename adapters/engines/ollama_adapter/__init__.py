"""Ollama Engine implementation for AI content generation.

This module provides an implementation of the CompletionEnginePort interface
using Ollama as the underlying language model. It handles the generation of
AI content with different expertise levels and formats the output according to
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
from typing import Dict, List, Tuple, Optional, Callable
from ollama import Client
from ollama._types import ResponseError
from alive_progress import alive_bar
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

    This class handles the generation of AI content using Ollama's language
    models. It supports different expertise levels and formats the output
    according to specified templates.

    Attributes:
        level_descriptions (Dict[str, str]): Mapping of expertise levels to
            their descriptions.
        model (str): The name of the Ollama model to use.
        stream (bool): Whether to stream the responses.
        category (str): The category of content to generate.
        expertise_level (str): The expertise level for the generated content.
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
        host: str = None,
        stream: bool = True,
        category: str = "Tip",
        expertise_level: str = "Novice",
        think: bool = True,
        debug: bool = False,
        progress_bar: bool = False
    ) -> None:
        """Initialize the Ollama engine.

        Args:
            model: The Ollama model to use
            host: The Ollama host address
            stream: Whether to stream the response
            category: The category of content to generate
            expertise_level: The expertise level for the content
            think: Whether to show thinking process
            debug: Whether to show debug output
            progress_bar: Whether to show progress bar
        """
        self.model = model
        self.host = host
        self.stream = stream
        self.category = category
        self.progress_bar = progress_bar

        # Normalize expertise level to title case
        normalized_level = expertise_level.title()
        if normalized_level not in self.level_descriptions:
            raise ValueError(
                f"Invalid expertise level: {expertise_level}. "
                f"Must be one of: {', '.join(self.level_descriptions.keys())}"
            )
        self.expertise_level = normalized_level
        self.context_note = self.level_descriptions[self.expertise_level]

        self.think = think
        self.debug = debug
        self.tokens_used = 0
        self.quantity = 5  # Default quantity

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
        # Determine prompt directory based on category
        prompt_subdir = "course" if self.category.lower() == "course" else "common"
        # Load titles prompt template
        titles_prompt_dir = os.path.abspath(
            os.path.join(here, f"prompts/{prompt_subdir}/titles")
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
            os.path.join(here, f"prompts/{prompt_subdir}/content")
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

    def build_titles_prompt(self, topic: str) -> str:
        """Build the prompt for generating chapter titles.

        Args:
            topic: The topic to generate chapters for.

        Returns:
            The formatted prompt string.
        """
        prompt = self._prompt_titles_template
        prompt = prompt.replace("{{TOPIC}}", topic)
        prompt = prompt.replace("{{QUANTITY}}", str(self.quantity))
        prompt = prompt.replace("{{CATEGORY}}", self.category)
        prompt = prompt.replace("{{EXPERTISE_LEVEL}}", self.expertise_level)
        prompt = prompt.replace("{{CONTEXT_NOTE}}", self.context_note)
        return prompt

    def build_detail_prompt(
        self, topic: str, chapter_title: str, chapter_index: int,
        chapter_short_title: str
    ) -> str:
        """Build the prompt for generating chapter content.

        Args:
            topic: The topic to generate content for.
            chapter_title: The title of the chapter to generate content for.
            chapter_index: The index of the current chapter.
            chapter_short_title: The short version of the chapter title.

        Returns:
            The formatted prompt string.
        """
        prompt = self.prompt_detail_template
        prompt = prompt.replace("{{TOPIC}}", topic)
        prompt = prompt.replace("{{CHAPTER_TITLE}}", chapter_title)
        prompt = prompt.replace("{{CHAPTER_SHORT_TITLE}}", chapter_short_title)
        prompt = prompt.replace("{{CATEGORY}}", self.category)
        prompt = prompt.replace("{{EXPERTISE_LEVEL}}", self.expertise_level)
        prompt = prompt.replace("{{CONTEXT_NOTE}}", self.context_note)
        prompt = prompt.replace("{{CHAPTER_INDEX}}", str(chapter_index))
        prompt = prompt.replace("{{QUANTITY}}", str(self.quantity))
        return prompt

    def generate_chapters(
        self, topic: str
    ) -> Tuple[List[Dict[str, str]], str]:
        """Generate a list of chapter titles for the given topic.

        Args:
            topic: The topic to generate chapters for.

        Returns:
            A tuple containing:
                - List of dictionaries with 'full' and 'short' title keys
                - Overview string of the generated chapters

        Note:
            The output is parsed from the model's response between
            <TITLE_BLOCK> and </TITLE_BLOCK> tags.
        """
        prompt = self.build_titles_prompt(topic)
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
            chat_kwargs = {
                "model": self.model,
                "messages": messages,
                "stream": self.stream
            }
            if not self.think:
                chat_kwargs["think"] = False

            if self.stream:
                for msg in self.ollama.chat(**chat_kwargs):
                    piece = msg['message']['content']

                    # Handle think tags for display only
                    if "<think>" in piece:
                        in_think_block = True
                    if "</think>" in piece:
                        in_think_block = False

                    # Print with appropriate color
                    color = RED if in_think_block else GRAY
                    if self.debug:
                        print(f"{color}{piece}{RESET}", end="", flush=True)
                    content += piece
            else:
                response = self.ollama.chat(**chat_kwargs)
                content = response['message']['content']
                if self.debug:
                    print(f"{GRAY}{content}{RESET}")

        except ResponseError as e:
            if "does not support thinking" in str(e) and self.think:
                logger.warning(
                    "Model %s does not support thinking feature. "
                    "Retrying without thinking.",
                    self.model
                )
                # Retry without thinking
                chat_kwargs = {
                    "model": self.model,
                    "messages": messages,
                    "stream": self.stream
                }
                if self.stream:
                    for msg in self.ollama.chat(**chat_kwargs):
                        piece = msg['message']['content']
                        if self.debug:
                            print(f"{GRAY}{piece}{RESET}", end="", flush=True)
                        content += piece
                else:
                    response = self.ollama.chat(**chat_kwargs)
                    content = response['message']['content']
                    if self.debug:
                        print(f"{GRAY}{content}{RESET}")
            else:
                raise

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

        chapters = []
        overview = ""
        if not title_block_match:
            raise OllamaResponseError(
                "Failed to generate chapter titles. The model's response did not "
                "contain the expected TITLE_BLOCK format. Please try again "
                "with a different topic or model."
            )

        title_lines = title_block_match.group(1).strip().splitlines()
        for line in title_lines:
            # Match lines like: 1. Decorators for Advanced Functionality |
            # Decorators
            match = re.match(r"\s*(.*?)\s*\|\s*(.*)", line)
            if match:
                full_title = match.group(1).strip()
                short_title = match.group(2).strip()
                # If short title is empty, use the full title
                if not short_title:
                    short_title = full_title
                chapters.append({"full": full_title, "short": short_title})

        if not chapters:
            raise OllamaResponseError(
                "Failed to parse chapter titles from the model's response. "
                "The response format was not as expected. Please try again."
            )

        if not overview_match:
            logger.warning("TITLE_OVERVIEW not found in model output.")
        else:
            overview = overview_match.group(1).strip()

        # Log extracted chapters and overview
        logger.debug("Extracted chapters: %s, overview: %s", chapters, overview)
        return chapters, overview

    def generate_content(
        self, topic: str, chapter_title: str, chapter_index: int,
        total_chapters: int, chapter_short_title: str
    ) -> str:
        """Generate detailed content for a specific chapter.

        Args:
            topic: The topic to generate content for.
            chapter_title: The title of the chapter to generate content for.
            chapter_index: The index of the current chapter being generated.
            total_chapters: The total number of chapters being generated.
            chapter_short_title: The short version of the chapter title.

        Returns:
            The generated chapter content as a string.

        Note:
            The content is generated in markdown format and includes sections
            like introduction, main content, and conclusion.
        """
        prompt = self.build_detail_prompt(
            topic, chapter_title, chapter_index, chapter_short_title
        )
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
        logger.debug("Processing Chapter #%d of %d (Attempt 1)",
                    chapter_index, total_chapters)

        in_think_block = False
        try:
            chat_kwargs = {
                "model": self.model,
                "messages": messages,
                "stream": self.stream
            }
            if not self.think:
                chat_kwargs["think"] = False

            if self.stream:
                for msg in self.ollama.chat(**chat_kwargs):
                    piece = msg['message']['content']

                    # Handle think tags for display only
                    if "<think>" in piece:
                        in_think_block = True
                    if "</think>" in piece:
                        in_think_block = False

                    # Print with appropriate color
                    color = RED if in_think_block else GRAY
                    if self.debug:
                        print(f"{color}{piece}{RESET}", end="", flush=True)
                    content += piece
            else:
                response = self.ollama.chat(**chat_kwargs)
                content = response['message']['content']
                if self.debug:
                    print(f"{GRAY}{content}{RESET}")

        except ResponseError as e:
            if "does not support thinking" in str(e) and self.think:
                logger.warning(
                    "Model %s does not support thinking feature. "
                    "Retrying without thinking.",
                    self.model
                )
                # Retry without thinking
                chat_kwargs = {
                    "model": self.model,
                    "messages": messages,
                    "stream": self.stream
                }
                if self.stream:
                    for msg in self.ollama.chat(**chat_kwargs):
                        piece = msg['message']['content']
                        if self.debug:
                            print(f"{GRAY}{piece}{RESET}", end="", flush=True)
                        content += piece
                else:
                    response = self.ollama.chat(**chat_kwargs)
                    content = response['message']['content']
                    if self.debug:
                        print(f"{GRAY}{content}{RESET}")
            else:
                raise

        # Save original content for token counting
        original_content = content

        # Remove <think> tags for further processing
        content = re.sub(
            r'<think\b[^>]*>.*?</think>',
            '',
            content,
            flags=re.DOTALL | re.IGNORECASE
        )
        logger.debug("\n[End of Ollama Streaming Output]")

        # Estimate and log the token usage using the original content
        self.tokens_used += int(len(original_content.split()) * 0.75)

        return content

    def generate(
        self,
        topic: str
    ) -> Tuple[List[Tuple[int, Dict[str, str], str]], str]:
        """Generate a complete set of chapters with their content."""
        # Generate chapters
        if self.progress_bar:
            print("Generating chapter titles...")
        chapters, overview = self.generate_chapters(topic)

        details = []
        total_chapters = len(chapters)

        # Generate content for each chapter
        if self.progress_bar:
            with alive_bar(
                total_chapters,
                title="Generating content",
                bar="smooth",
                spinner="waves",
                enrich_print=False
            ) as progress:
                for i, chapter in enumerate(chapters, 1):
                    progress.text(f"Processing: {chapter['short']}")
                    detail = self.generate_content(
                        topic,
                        chapter["full"],
                        i,
                        total_chapters,
                        chapter["short"]
                    )
                    details.append((i, chapter, detail))
                    progress()   # pylint: disable=not-callable
        else:
            for i, chapter in enumerate(chapters, 1):
                detail = self.generate_content(
                    topic,
                    chapter["full"],
                    i,
                    total_chapters,
                    chapter["short"]
                )
                details.append((i, chapter, detail))

        return details, overview
