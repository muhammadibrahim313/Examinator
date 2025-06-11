from typing import Dict, Type
from app.services.exam_types.base import BaseExamType
from app.services.exam_types.jamb import JAMBExamType
from app.services.exam_types.sat import SATExamType
import logging

logger = logging.getLogger(__name__)

class ExamRegistry:
    """
    Registry for different exam types
    Manages available exam types and their implementations
    """
    
    def __init__(self):
        self._exam_types: Dict[str, BaseExamType] = {}
        self._register_default_exams()
    
    def _register_default_exams(self):
        """
        Register default exam types
        """
        self.register_exam('jamb', JAMBExamType())
        self.register_exam('sat', SATExamType())
        logger.info("Registered default exam types: JAMB, SAT")
    
    def register_exam(self, exam_name: str, exam_type: BaseExamType):
        """
        Register a new exam type
        """
        self._exam_types[exam_name.lower()] = exam_type
        logger.info(f"Registered exam type: {exam_name}")
    
    def get_exam_type(self, exam_name: str) -> BaseExamType:
        """
        Get exam type implementation
        """
        exam_key = exam_name.lower()
        if exam_key not in self._exam_types:
            raise ValueError(f"Unknown exam type: {exam_name}")
        return self._exam_types[exam_key]
    
    def get_available_exams(self) -> list[str]:
        """
        Get list of available exam names
        """
        return list(self._exam_types.keys())
    
    def is_exam_supported(self, exam_name: str) -> bool:
        """
        Check if an exam type is supported
        """
        return exam_name.lower() in self._exam_types