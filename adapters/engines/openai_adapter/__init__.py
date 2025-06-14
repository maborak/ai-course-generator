"""OpenAI Engine implementation for AI content generation.

This module provides an implementation of the CompletionEnginePort interface
using OpenAI as the underlying language model. It handles the generation of
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
import time
from typing import Dict, List, Tuple
from openai import OpenAI
import tiktoken
from core.ports import CompletionEnginePort

# ANSI color codes
GRAY = "\033[90m"
ORANGE = "\033[33m"  # Orange color
RED = "\033[31m"    # Red color
CYAN = "\033[36m"   # Cyan color
RESET = "\033[0m"

# OpenAI specific constants
MODEL = "gpt-4"
TEMPERATURE = 0.7
MAX_TOKENS = 4096
MAX_ITERATIONS = 3
INPUT_COST_PER_1K = 0.01   # Set your own price
OUTPUT_COST_PER_1K = 0.03  # Set your own price


class OpenAIEngineError(Exception):
    """Base exception for OpenAI engine errors."""


class OpenAIPromptError(OpenAIEngineError):
    """Raised when there are issues with prompt processing."""


class OpenAIResponseError(OpenAIEngineError):
    """Raised when there are issues with the model's response."""


logger = logging.getLogger(__name__)


class OpenAIEngine(CompletionEnginePort):
    """Implementation of CompletionEnginePort using OpenAI as the backend.

    This class handles the generation of AI content using OpenAI's language
    models. It supports different expertise levels and formats the output
    according to specified templates.

    Attributes:
        level_descriptions (Dict[str, str]): Mapping of expertise levels to
            their descriptions.
        model (str): The name of the OpenAI model to use.
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
        model: str = MODEL,
        temperature: float = TEMPERATURE,
        max_tokens: int = MAX_TOKENS,
        stream: bool = True,
        category: str = "Tip",
        expertise_level: str = "Novice"
    ) -> None:
        """Initialize the OpenAIEngine.

        Args:
            model: The name of the OpenAI model to use.
            temperature: The temperature for response generation.
            max_tokens: Maximum tokens to generate.
            stream: Whether to stream the responses.
            category: The category of content to generate.
            expertise_level: The expertise level for the generated content.

        Raises:
            OpenAIEngineError: If there's an error initializing the engine.
            ValueError: If the expertise level is invalid.
        """
        logger.debug(
            "Initializing OpenAIEngine with model=%s, temperature=%s, "
            "max_tokens=%s, stream=%s",
            model,
            temperature,
            max_tokens,
            stream
        )
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
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
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            # Initialize tokenizer only if streaming is enabled
            if self.stream:
                try:
                    self.encoding = tiktoken.encoding_for_model(model)
                except KeyError:
                    logger.warning(
                        "Could not find specific tokenizer for model %s, "
                        "falling back to cl100k_base encoding",
                        model
                    )
                    self.encoding = tiktoken.get_encoding("cl100k_base")
        except Exception as exc:
            raise OpenAIEngineError(
                f"Failed to initialize OpenAI client. "
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
            titles_prompt_path = os.path.join(
                titles_prompt_dir, "openai.txt"
            )
            logger.warning(
                "Model-specific prompt template not found for %s, "
                "falling back to openai.txt",
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
            raise OpenAIPromptError(
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
            content_prompt_path = os.path.join(
                content_prompt_dir, "openai.txt"
            )
            logger.warning(
                "Model-specific content template not found for %s, "
                "falling back to openai.txt",
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
            raise OpenAIPromptError(
                f"Failed to load content prompt template from "
                f"{content_prompt_path}. Error: {str(exc)}"
            ) from exc

        self.tokens_used = {"input": 0, "output": 0}

    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text string.

        Args:
            text: The text to count tokens for.

        Returns:
            The number of tokens in the text.
        """
        if not self.stream:
            return 0  # Don't count tokens manually when not streaming
        return len(self.encoding.encode(text))

    def build_titles_prompt(self, topic: str, quantity: int) -> str:
        """Build the prompt for generating chapter titles.

        Args:
            topic: The topic to generate chapters for.
            quantity: The number of chapters to generate.

        Returns:
            The formatted prompt string.
        """
        prompt = self._prompt_titles_template
        prompt = prompt.replace("{{TOPIC}}", topic)
        prompt = prompt.replace("{{QUANTITY}}", str(quantity))
        prompt = prompt.replace("{{CATEGORY}}", self.category)
        prompt = prompt.replace("{{EXPERTISE_LEVEL}}", self.expertise_level)
        prompt = prompt.replace("{{CONTEXT_NOTE}}", self.context_note)
        return prompt

    def build_detail_prompt(
        self, topic: str, chapter_title: str, chapter_index: int,
        total_chapters: int, chapter_short_title: str, quantity: int
    ) -> str:
        """Build the prompt for generating chapter content.

        Args:
            topic: The topic to generate content for.
            chapter_title: The title of the chapter to generate content for.
            chapter_index: The index of the current chapter.
            total_chapters: The total number of chapters being generated.
            chapter_short_title: The short version of the chapter title.
            quantity: The total number of chapters requested.

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
        prompt = prompt.replace("{{QUANTITY}}", str(quantity))
        return prompt

    def generate_chapters(
        self, topic: str, quantity: int
    ) -> Tuple[List[Dict[str, str]], str]:
        """Generate a list of chapter titles for the given topic.

        Args:
            topic: The topic to generate chapters for.
            quantity: The number of chapters to generate.

        Returns:
            A tuple containing:
                - List of dictionaries with 'full' and 'short' title keys
                - Overview string of the generated chapters

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
            {
                "role": "system",
                "content": "You are a helpful AI assistant."
            },
            {"role": "user", "content": prompt}
        ]

        # Count input tokens only if streaming
        if self.stream:
            for message in messages:
                self.tokens_used["input"] += self.count_tokens(message["content"])

        content = ""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=self.stream
            )

            if self.stream:
                for chunk in response:
                    if hasattr(chunk.choices[0].delta, "content"):
                        piece = chunk.choices[0].delta.content
                        if piece:
                            print(f"{GRAY}{piece}{RESET}", end="", flush=True)
                            content += piece
                            # Count output tokens in streaming mode
                            self.tokens_used["output"] += self.count_tokens(piece)
            else:
                content = response.choices[0].message.content
                print(f"{GRAY}{content}{RESET}", end="", flush=True)
                # Use native token counts when not streaming
                if hasattr(response, "usage"):
                    self.tokens_used["input"] += response.usage.prompt_tokens
                    self.tokens_used["output"] += response.usage.completion_tokens

        except Exception as e:
            raise OpenAIResponseError(
                f"Failed to generate chapter titles. Error: {str(e)}"
            ) from e

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
            raise OpenAIResponseError(
                "Failed to generate chapter titles. The model's response did "
                "not contain the expected TITLE_BLOCK format. Please try again "
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
                # If short title is empty, use the full title
                if not short_title:
                    short_title = full_title
                chapters.append({"full": full_title, "short": short_title})

        if not chapters:
            raise OpenAIResponseError(
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
        total_chapters: int, chapter_short_title: str, quantity: int
    ) -> str:
        """Generate detailed content for a chapter.

        Args:
            topic: The main topic.
            chapter_title: The title of the chapter.
            chapter_index: The index of the chapter.
            total_chapters: Total number of chapters.
            chapter_short_title: The short version of the chapter title.
            quantity: The total number of chapters requested.

        Returns:
            The generated content as a string.

        Raises:
            OpenAIResponseError: If there's an error generating content.
        """
        prompt = self.build_detail_prompt(
            topic, chapter_title, chapter_index, total_chapters, chapter_short_title, quantity
        )
        logger.debug(
            "----Prompt BEGIN----\n"
            "%s%s%s\n"
            "----Prompt END----",
            ORANGE,
            prompt,
            RESET
        )
        max_retries = 3
        retry_delay = 2  # seconds

        print(
            f"+-----\n| Processing Chapter #{chapter_index} of "
            f"{total_chapters} (Attempt 1)\n+-----"
        )

        for attempt in range(max_retries):
            try:
                if self.stream:
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=self.temperature,
                        max_tokens=self.max_tokens,
                        stream=True
                    )
                    collected_chunks = []
                    try:
                        for chunk in response:
                            if chunk.choices[0].delta.content is not None:
                                piece = chunk.choices[0].delta.content
                                print(f"{GRAY}{piece}{RESET}", end="", flush=True)
                                collected_chunks.append(piece)
                                # Count tokens for streaming response
                                self.tokens_used["output"] += self.count_tokens(piece)
                    except Exception as stream_error:
                        if attempt < max_retries - 1:
                            logger.warning(
                                "Streaming error occurred, retrying... (Attempt %d/%d)",
                                attempt + 1,
                                max_retries
                            )
                            time.sleep(retry_delay)
                            continue
                        raise OpenAIResponseError(
                            f"Failed to stream response. Error: {str(stream_error)}"
                        ) from stream_error

                    print("\n[End of OpenAI Streaming Output]")
                    return "".join(collected_chunks)
                else:
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=self.temperature,
                        max_tokens=self.max_tokens
                    )
                    content = response.choices[0].message.content
                    print(f"{GRAY}{content}{RESET}")
                    return content

            except Exception as exc:
                if attempt < max_retries - 1:
                    logger.warning(
                        "Error occurred, retrying... (Attempt %d/%d)",
                        attempt + 1,
                        max_retries
                    )
                    time.sleep(retry_delay)
                    continue
                raise OpenAIResponseError(
                    f"Failed to generate chapter content. Error: {str(exc)}"
                ) from exc

        raise OpenAIResponseError(
            f"Failed to generate chapter content after {max_retries} attempts."
        )

    def calculate_costs(self) -> Dict[str, float]:
        """Calculate the total cost of API usage.

        Returns:
            A dictionary containing:
                - input_tokens: Number of input tokens used
                - output_tokens: Number of output tokens used
                - input_cost: Cost of input tokens
                - output_cost: Cost of output tokens
                - total_cost: Total cost of API usage
        """
        input_tokens = self.tokens_used.get("input", 0)
        output_tokens = self.tokens_used.get("output", 0)
        input_cost = (input_tokens / 1000) * INPUT_COST_PER_1K
        output_cost = (output_tokens / 1000) * OUTPUT_COST_PER_1K
        total_cost = input_cost + output_cost

        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_cost": round(input_cost, 4),
            "output_cost": round(output_cost, 4),
            "total_cost": round(total_cost, 4)
        }

    def generate(
        self, topic: str, quantity: int
    ) -> Tuple[List[Tuple[int, Dict[str, str], str]], str]:
        """Generate a complete set of chapters with their content.

        Args:
            topic: The topic to generate chapters for.
            quantity: The number of chapters to generate.

        Returns:
            A tuple containing:
                - List of tuples with (index, chapter_info, content)
                - Overview string of the generated chapters

        Note:
            This method orchestrates the generation of chapter titles and
            their detailed content.
        """
        # Reset token usage at the start of generation
        self.tokens_used = {"input": 0, "output": 0}
        chapters, overview = self.generate_chapters(topic, quantity)
        details = []
        for i, chapter in enumerate(chapters, 1):
            detail = self.generate_content(
                topic,
                chapter["full"],
                i,
                len(chapters),
                chapter["short"],
                quantity
            )
            details.append((i, chapter, detail))

        # Calculate and log costs
        costs = self.calculate_costs()
        logger.info(
            "OpenAI API Usage:\n"
            "  Input tokens: %d (Cost: $%.4f)\n"
            "  Output tokens: %d (Cost: $%.4f)\n"
            "  Total cost: $%.4f",
            costs["input_tokens"],
            costs["input_cost"],
            costs["output_tokens"],
            costs["output_cost"],
            costs["total_cost"]
        )

        return details, overview
