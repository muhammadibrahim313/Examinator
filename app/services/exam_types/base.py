from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class BaseExamType(ABC):
    """
    Abstract base class for different exam types
    Each exam type can have its own flow and structure
    """
    
    def __init__(self, exam_name: str):
        self.exam_name = exam_name
        self.logger = logging.getLogger(f"{__name__}.{exam_name}")
    
    @abstractmethod
    def get_flow_stages(self) -> List[str]:
        """
        Return the list of stages for this exam type
        e.g., ['selecting_subject', 'selecting_year', 'taking_exam']
        """
        pass
    
    @abstractmethod
    def get_initial_stage(self) -> str:
        """
        Return the first stage after exam selection
        """
        pass
    
    @abstractmethod
    async def handle_stage(self, stage: str, user_phone: str, message: str, user_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a specific stage for this exam type (NOW ASYNC)
        Returns: {
            'response': str,  # Message to send to user
            'next_stage': str,  # Next stage to transition to
            'state_updates': Dict[str, Any]  # Updates to apply to user state
        }
        """
        pass
    
    @abstractmethod
    def validate_stage_input(self, stage: str, message: str, user_state: Dict[str, Any]) -> bool:
        """
        Validate user input for a specific stage
        """
        pass
    
    @abstractmethod
    def get_available_options(self, stage: str, user_state: Dict[str, Any]) -> List[str]:
        """
        Get available options for a specific stage
        """
        pass
    
    def format_options_list(self, options: List[str], title: str) -> str:
        """
        Helper method to format options list
        """
        if not options:
            return f"No {title.lower()} available."
        
        options_text = "\n".join([f"{i+1}. {option}" for i, option in enumerate(options)])
        return f"{title}:\n{options_text}\n\nPlease reply with the number of your choice."
    
    def parse_choice(self, message: str, options: List[str]) -> Optional[str]:
        """
        Helper method to parse user choice
        """
        try:
            choice = int(message.strip()) - 1
            if 0 <= choice < len(options):
                return options[choice]
            return None
        except (ValueError, IndexError):
            return None