#!/usr/bin/env python3
# pylint: disable=invalid-name,too-many-arguments,too-many-locals
# pylint: disable=too-many-branches,too-many-statements,line-too-long
"""
AI Knowledge Generator Core Module.

This module provides the core functionality for generating AI knowledge content using
various language models and converting them to different formats.

Example:
    generator = AIKnowledgeGenerator(engine, converter)
    generator.generate_tips("python", 5, "output.md")
"""

import logging
import time
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class AIKnowledgeGenerator:
    """Generator class for creating AI knowledge content with various engines and converters.

    This class handles the generation of content using different AI engines and
    converts the output to various formats using the provided converter.

    Attributes:
        engine: The AI engine to use for generating content
        converter: The converter to use for output formatting
        tokens_used: Counter for tokens used in generation
    """

    def __init__(self, engine: Any, converter: Any) -> None:
        """Initialize the AIKnowledgeGenerator.

        Args:
            engine: The AI engine to use for generating content
            converter: The converter to use for output formatting
        """
        logger.debug(
            "Initializing AIKnowledgeGenerator with engine=%s, converter=%s",
            engine.__class__.__name__,
            converter.__class__.__name__
        )
        self.engine = engine
        self.converter = converter
        self.tokens_used = 0

    def run(
        self,
        topic: str,
        quantity: int,
        output_md: str,
        force: bool = False,  # pylint: disable=unused-argument
    ) -> None:
        """Run the knowledge generation process.

        This is the main execution method that orchestrates the entire generation process,
        from content creation to file output.

        Args:
            topic: The topic to generate content for
            quantity: Number of items to generate
            output_md: Path to save the markdown output
            force: Whether to force overwrite existing files
        """
        logger.debug(
            "Running generation process for %d items on topic '%s'",
            quantity,
            topic
        )

        # Start timing
        start_time = time.time()

        # Get current timestamp
        now = datetime.now()
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")

        # Get category and expertise level from engine
        category = self.engine.category
        expertise_level = self.engine.expertise_level
        model = (
            self.engine.model
            if hasattr(self.engine, "model")
            else "unknown"
        )

        # Generate content
        self.engine.quantity = quantity
        details, overview = self.engine.generate(topic)
        tokens_used = (
            self.engine.tokens_used
            if hasattr(self.engine, "tokens_used")
            else 0
        )

        # Calculate elapsed time
        elapsed = time.time() - start_time

        # Calculate reading time from the content
        content = ""
        if overview:
            content += overview + "\n"
        for _, _, detail in details:
            content += detail + "\n"
        reading_time = self.calculate_reading_time(content)

        # Create header with metadata
        header = (
            f"# {topic} ({category})\n\n"
            f"---\n\n"
            f"## Document Info\n\n"
            f"- **Expertise Level:** {expertise_level}\n"
            f"- **Category:** {category}\n"
            f"- **Model Used:** {model}\n"
            f"- **Total Tokens Used:** {tokens_used}\n"
            f"- **Generated on:** {now_str}\n"
            f"- **Generated in:** {self.format_elapsed(elapsed)}\n"
            f"- **Reading Time:** {reading_time}\n\n"
            "---\n\n")
        # Write the content to the markdown file
        with open(output_md, "w", encoding="utf-8") as file:
            file.write(header)
            if overview:
                file.write(overview + "\n\n")
            for _, _, detail in details:
                file.write(detail.strip() + "\n\n")

        # Convert to other formats
        metadata = {
            "title": f"{topic} ({category}, {expertise_level})",
            "category": category,
            "author": "AI Knowledge Generator",
            "date": now_str,
            "model": model,
            "tokens": str(tokens_used),
            "reading-time": reading_time
        }
        self.converter.convert(output_md, metadata, force)

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

    def calculate_reading_time(self, content: str) -> str:
        """Calculate estimated reading time for the content.

        Args:
            content: The text content to calculate reading time for

        Returns:
            str: Formatted reading time string
        """
        # Average reading speed: 200-250 words per minute
        words = len(content.split())
        minutes = max(1, round(words / 200))  # Using 200 words per minute as baseline
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
