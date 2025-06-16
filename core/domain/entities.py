"""Domain entities for the AI Knowledge Generator.

This module contains the core domain entities that represent the business objects
in the system. These entities are independent of any external frameworks or
technologies.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class Chapter:
    """Represents a chapter in the generated content.
    
    Attributes:
        title: The full title of the chapter
        short_title: A shorter version of the title
        content: The chapter's content
        index: The chapter's position in the sequence
    """
    title: str
    short_title: str
    content: str
    index: int


@dataclass
class Content:
    """Represents the complete generated content.
    
    Attributes:
        topic: The main topic of the content
        category: The category (e.g., Guide, Tutorial)
        expertise_level: The target expertise level
        chapters: List of chapters in the content
        overview: Optional overview of the content
        generated_at: When the content was generated
        model: The AI model used for generation
        tokens_used: Number of tokens used in generation
    """
    topic: str
    category: str
    expertise_level: str
    chapters: List[Chapter]
    overview: Optional[str] = None
    generated_at: datetime = datetime.now()
    model: str = "unknown"
    tokens_used: int = 0

    @property
    def reading_time(self) -> str:
        """Calculate and return the estimated reading time.
        
        Returns:
            A string representing the estimated reading time.
        """
        # Average reading speed: 200 words per minute
        words = sum(len(chapter.content.split()) for chapter in self.chapters)
        if self.overview:
            words += len(self.overview.split())
        
        minutes = words // 200
        if minutes < 1:
            return "Less than 1 minute"
        if minutes == 1:
            return "1 minute"
        return f"{minutes} minutes"

    def to_markdown(self) -> str:
        """Convert the content to markdown format.
        
        Returns:
            A string containing the content in markdown format.
        """
        # Create header with metadata
        header = f"""# {self.topic} ({self.category}, {self.expertise_level})

Generated on: {self.generated_at.strftime("%Y-%m-%d %H:%M:%S")}
Model: {self.model}
Tokens used: {self.tokens_used}
Reading Time: {self.reading_time}

---

"""
        # Add overview if available
        content = header
        if self.overview:
            content += f"{self.overview}\n\n"

        # Add chapters
        for chapter in self.chapters:
            content += f"## {chapter.title}\n\n{chapter.content}\n\n"

        return content 