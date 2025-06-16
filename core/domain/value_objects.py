"""Value objects for the AI Knowledge Generator.

This module contains value objects that represent immutable concepts in the domain.
These objects are used to ensure type safety and domain constraints.
"""

from enum import Enum
from typing import Dict


class ExpertiseLevel(str, Enum):
    """Represents the expertise level of the content."""
    NOVICE = "Novice"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"
    EXPERT = "Expert"

    @classmethod
    def get_description(cls, level: str) -> str:
        """Get the description for an expertise level.
        
        Args:
            level: The expertise level to get the description for
            
        Returns:
            A string describing the expertise level
        """
        descriptions: Dict[str, str] = {
            cls.NOVICE: "You are new to this topic and need clear, simple guidance.",
            cls.INTERMEDIATE: "You have some experience and are ready for more depth.",
            cls.ADVANCED: "You are comfortable with the topic and want sophisticated techniques.",
            cls.EXPERT: "You are deeply experienced and need highly technical, optimized solutions."
        }
        return descriptions.get(level, descriptions[cls.NOVICE])


class Category(str, Enum):
    """Represents the category of the content."""
    TIP = "Tip"
    GUIDE = "Guide"
    TUTORIAL = "Tutorial"
    HOW_TO = "How-to"
    BEST_PRACTICES = "Best Practices"
    COURSE = "Course"

    @classmethod
    def get_description(cls, category: str) -> str:
        """Get the description for a category.
        
        Args:
            category: The category to get the description for
            
        Returns:
            A string describing the category
        """
        descriptions: Dict[str, str] = {
            cls.TIP: "Quick, actionable advice or insight",
            cls.GUIDE: "Comprehensive overview and instructions",
            cls.TUTORIAL: "Step-by-step learning experience",
            cls.HOW_TO: "Specific task or problem solution",
            cls.BEST_PRACTICES: "Recommended approaches and patterns",
            cls.COURSE: "Structured learning material"
        }
        return descriptions.get(category, descriptions[cls.TIP]) 