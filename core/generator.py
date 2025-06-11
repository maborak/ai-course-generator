#!/usr/bin/env python3
# pylint: disable=invalid-name,too-many-arguments,too-many-locals
# pylint: disable=too-many-branches,too-many-statements,line-too-long
"""
AI Tips Generator Core Module.

This module provides the core functionality for generating AI tips using
various language models and converting them to different formats.

Example:
    generator = AITipsGenerator(engine, converter)
    generator.generate_tips("python", 5, "output.md")
"""

import logging
import time
from datetime import datetime
from typing import Any, List, Tuple

logger = logging.getLogger(__name__)


class AITipsGenerator:
    """Generator class for creating AI tips with various engines and converters.

    This class handles the generation of tips using different AI engines and
    converts the output to various formats using the provided converter.

    Attributes:
        engine: The AI engine to use for generating tips
        converter: The converter to use for output formatting
        tokens_used: Counter for tokens used in generation
    """

    def __init__(self, engine: Any, converter: Any) -> None:
        """Initialize the AITipsGenerator.

        Args:
            engine: The AI engine to use for generating tips
            converter: The converter to use for output formatting
        """
        logger.debug(
            "Initializing AITipsGenerator with engine=%s, converter=%s",
            engine.__class__.__name__,
            converter.__class__.__name__
        )
        self.engine = engine
        self.converter = converter
        self.tokens_used = 0

    def generate_tips(
        self,
        topic: str,
        quantity: int,
        output_md: str,
        force: bool = False  # pylint: disable=unused-argument
    ) -> None:
        """Generate tips and save them to a markdown file.

        Args:
            topic: The topic to generate tips for
            quantity: Number of tips to generate
            output_md: Path to the output markdown file
            force: Whether to overwrite existing file (unused)
        """
        start_time = time.time()
        logger.info("Generating %d tips for topic '%s'", quantity, topic)
        details, overview = self.engine.generate(topic, quantity)
        elapsed = time.time() - start_time

        # Add metadata to the markdown
        expertise_level = getattr(self.engine, "expertise_level", "Unknown")
        category = getattr(self.engine, "category", "Unknown")
        model = getattr(self.engine, "model", "Unknown")
        tokens_used = getattr(self.engine, "tokens_used", "Unknown")
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        header = (
            f"# {topic} ({category})\n\n"
            f"---\n\n"
            f"## Document Info\n\n"
            f"- **Expertise Level:** {expertise_level}\n"
            f"- **Category:** {category}\n"
            f"- **Model Used:** {model}\n"
            f"- **Total Tokens Used:** {tokens_used}\n"
            f"- **Generated on:** {now_str}\n"
            f"- **Generated in:** {self.format_elapsed(elapsed)}\n\n"
            "---\n\n"
        )

        with open(output_md, "w", encoding="utf-8") as file:
            file.write(header)
            if overview:
                file.write(f"## Overview\n\n{overview}\n\n---\n\n")
            for _, _, detail in details:  # pylint: disable=unused-variable
                file.write(detail.strip() + "\n\n---\n\n")
        logger.info("Markdown saved as %s", output_md)
        logger.info("Total tokens used: %s", tokens_used)

        # Prepare metadata for embedding
        metadata = {
            "title": topic,
            "author": "Maborak",
            "category": category,
            "expertise_level": expertise_level,
            "model": model,
            "tokens_used": tokens_used,
            "generated_on": now_str,
            "language": "en",
            "date": now_str,
            "description": f"{topic} ({category}, {expertise_level})",
        }
        # Add short title from first tip if available
        if details:
            metadata["shorttitle"] = details[0][1]["short"]

        self.converter.convert(output_md, metadata=metadata)

    def format_tips_to_markdown(self, tips_list: List[Tuple[int, str, str]]) -> str:
        """Format a list of tips into markdown format.

        Args:
            tips_list: List of tuples containing (index, title, detail)

        Returns:
            str: Formatted markdown string
        """
        markdown = ""
        for idx, tip_title, tip_detail in tips_list:
            markdown += f"### Tip #{idx}: {tip_title}\n\n{tip_detail}\n\n***\n"
        return markdown

    def format_elapsed(self, seconds: float) -> str:
        """Format elapsed time into a human-readable string.

        Args:
            seconds: Number of seconds elapsed

        Returns:
            str: Formatted time string (e.g., "2 hours, 30 minutes, 15 seconds")
        """
        seconds_int = int(seconds)
        hours, remainder = divmod(seconds_int, 3600)
        minutes, seconds_int = divmod(remainder, 60)
        parts = []
        if hours:
            parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if minutes:
            parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
        if seconds_int or not parts:
            parts.append(f"{seconds_int} second{'s' if seconds_int != 1 else ''}")
        return ", ".join(parts)
