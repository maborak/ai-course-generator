"""
Port interfaces for AI Tips Generator.

Defines abstract base classes for completion engines and file converters.
"""

import logging
from abc import ABC, abstractmethod
from typing import Tuple, List, Dict, Optional, Callable


logger = logging.getLogger(__name__)


class CompletionEnginePort(ABC):
    """Abstract base class for completion engine implementations."""
    @abstractmethod
    def generate(
        self, 
        topic: str
    ) -> Tuple[List[Tuple[int, Dict[str, str], str]], str]:
        """Generate content for a given topic.

        Args:
            topic (str): The topic to generate content for.

        Returns:
            Tuple[List[Tuple[int, Dict[str, str], str]], str]: A tuple containing:
                - List of tuples with (index, chapter_info, content)
                - Overview string of the generated chapters
        """
        # Abstract method, do not implement

class FileConverterPort(ABC):
    """Abstract base class for file converter implementations."""
    @abstractmethod
    def convert(self, md_file: str):
        """Convert a markdown file to other formats.

        Args:
            md_file (str): Path to the markdown file to convert.
        """
        # Abstract method, do not implement
