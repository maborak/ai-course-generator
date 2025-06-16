"""
Port interfaces for AI Tips Generator.

Defines abstract base classes for completion engines and file converters.
"""

import logging
from abc import ABC, abstractmethod
from typing import Tuple, List, Dict, Optional, Callable


logger = logging.getLogger(__name__)


class ProgressCallback:
    """Class to handle progress updates."""
    def __init__(self, total: int, title: str = "Processing"):
        self.total = total
        self.current = 0
        self.title = title
        self.callback: Optional[Callable[[int, str], None]] = None

    def update(self, increment: int = 1, text: str = "") -> None:
        """Update progress and call the callback if set."""
        self.current += increment
        if self.callback:
            self.callback(self.current, text)

    def set_callback(self, callback: Callable[[int, str], None]) -> None:
        """Set the callback function for progress updates."""
        self.callback = callback


class CompletionEnginePort(ABC):
    """Abstract base class for completion engine implementations."""
    @abstractmethod
    def generate(
        self, 
        topic: str,
        progress_callback: Optional[ProgressCallback] = None
    ) -> Tuple[List[Tuple[int, Dict[str, str], str]], str]:
        """Generate content for a given topic.

        Args:
            topic (str): The topic to generate content for.
            progress_callback (Optional[ProgressCallback]): Callback for progress updates.

        Returns:
            Tuple[List[Tuple[int, Dict[str, str], str]], str]: A tuple containing:
                - List of tuples with (index, chapter_info, content)
                - Overview string of the generated chapters
        """
        # Abstract method, do not implement

    @abstractmethod
    def set_progress_callback(self, callback: Callable[[int, str], None]) -> None:
        """Set the callback function for progress updates.
        
        Args:
            callback (Callable[[int, str], None]): Function to call with progress updates.
                Takes current progress (int) and status text (str) as arguments.
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
