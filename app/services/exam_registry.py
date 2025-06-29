from typing import Dict, Type
from app.services.exam_types.base import BaseExamType
from app.services.exam_types.flexible_jamb import FlexibleJAMBExamType
from app.services.exam_types.flexible_sat import FlexibleSATExamType
from app.services.exam_types.flexible_neet import FlexibleNEETExamType
import logging

logger = logging.getLogger(__name__)

class ExamRegistry:
    """
    Registry for different exam types with flexible practice support (topics OR years)
    """
    
    def __init__(self):
        self._exam_types: Dict[str, BaseExamType] = {}
        self._register_default_exams()
    
    def _register_default_exams(self):
        """
        Register flexible exam types supporting both topic and year-based practice
        """
        try:
            self.register_exam('jamb', FlexibleJAMBExamType())
            self.register_exam('sat', FlexibleSATExamType())
            self.register_exam('neet', FlexibleNEETExamType())
            logger.info("Successfully registered all exam types: JAMB, SAT, NEET")
        except Exception as e:
            logger.error(f"Error registering exam types: {e}")
            # Fallback registration
            try:
                from app.services.exam_types.jamb import JAMBExamType
                from app.services.exam_types.sat import SATExamType
                from app.services.exam_types.neet import NEETExamType
                
                self.register_exam('jamb', JAMBExamType())
                self.register_exam('sat', SATExamType())
                self.register_exam('neet', NEETExamType())
                logger.info("Registered fallback exam types: JAMB, SAT, NEET")
            except Exception as fallback_error:
                logger.error(f"Error with fallback registration: {fallback_error}")
    
    def register_exam(self, exam_name: str, exam_type: BaseExamType):
        """Register a new exam type"""
        self._exam_types[exam_name.lower()] = exam_type
        logger.info(f"Registered exam type: {exam_name}")
    
    def get_exam_type(self, exam_name: str) -> BaseExamType:
        """Get exam type implementation"""
        exam_key = exam_name.lower()
        if exam_key not in self._exam_types:
            raise ValueError(f"Unknown exam type: {exam_name}")
        return self._exam_types[exam_key]
    
    def get_available_exams(self) -> list[str]:
        """Get list of available exam names"""
        available = list(self._exam_types.keys())
        logger.info(f"Available exams: {available}")
        return available
    
    def is_exam_supported(self, exam_name: str) -> bool:
        """Check if an exam type is supported"""
        return exam_name.lower() in self._exam_types
    
    def get_exam_info(self, exam_name: str) -> Dict[str, any]:
        """Get comprehensive exam information"""
        try:
            exam_type = self.get_exam_type(exam_name)
            if hasattr(exam_type, 'question_fetcher'):
                return exam_type.question_fetcher.get_exam_info(exam_name)
            return {}
        except Exception as e:
            logger.error(f"Error getting exam info for {exam_name}: {e}")
            return {}