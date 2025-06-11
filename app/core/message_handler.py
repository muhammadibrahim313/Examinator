from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class MessageHandler(ABC):
    """
    Abstract base class for handling different types of messages
    """
    
    @abstractmethod
    def can_handle(self, message: str, user_state: Dict[str, Any]) -> bool:
        """Check if this handler can process the message"""
        pass
    
    @abstractmethod
    def handle(self, user_phone: str, message: str, user_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle the message and return response data
        Returns: {
            'response': str,
            'state_updates': Dict[str, Any],
            'next_handler': Optional[str]
        }
        """
        pass

class GlobalCommandHandler(MessageHandler):
    """
    Handles global commands that work from any state
    """
    
    def __init__(self, state_manager, exam_registry):
        self.state_manager = state_manager
        self.exam_registry = exam_registry
    
    def can_handle(self, message: str, user_state: Dict[str, Any]) -> bool:
        return message.lower().strip() in ['start', 'restart', 'exit', 'help']
    
    def handle(self, user_phone: str, message: str, user_state: Dict[str, Any]) -> Dict[str, Any]:
        command = message.lower().strip()
        
        if command in ['start', 'restart']:
            return self._handle_start(user_phone)
        elif command == 'exit':
            return self._handle_exit(user_phone)
        elif command == 'help':
            return self._handle_help()
        
        return {'response': 'Unknown command', 'state_updates': {}, 'next_handler': None}
    
    def _handle_start(self, user_phone: str) -> Dict[str, Any]:
        """Handle start/restart command"""
        logger.info(f"Starting new session for {user_phone}")
        
        # Get available exams
        exams = self.exam_registry.get_available_exams()
        if not exams:
            return {
                'response': "Sorry, no exams are currently available. Please contact support.",
                'state_updates': {'stage': 'error'},
                'next_handler': None
            }
        
        # Format exam list
        exam_list = "\n".join([f"{i+1}. {exam.upper()}" for i, exam in enumerate(exams)])
        response = (f"🎓 Welcome to the Exam Practice Bot!\n\n"
                   f"Available exams:\n{exam_list}\n\n"
                   f"Please reply with the number of your choice (e.g., '1' for {exams[0].upper()}).")
        
        return {
            'response': response,
            'state_updates': {
                'stage': 'selecting_exam',
                'exam': None,
                'subject': None,
                'year': None,
                'section': None,
                'difficulty': None,
                'current_question_index': 0,
                'score': 0,
                'total_questions': 0,
                'questions': []
            },
            'next_handler': 'exam_selection'
        }
    
    def _handle_exit(self, user_phone: str) -> Dict[str, Any]:
        """Handle exit command"""
        logger.info(f"User {user_phone} exiting")
        return {
            'response': "Thanks for using the Exam Practice Bot! Send 'start' to begin a new session.",
            'state_updates': {'stage': 'initial'},
            'next_handler': None
        }
    
    def _handle_help(self) -> Dict[str, Any]:
        """Handle help command"""
        return {
            'response': ("Available commands:\n"
                        "• 'start' - Begin a new exam session\n"
                        "• 'restart' - Restart current session\n"
                        "• 'exit' - End current session\n"
                        "• 'help' - Show this help message"),
            'state_updates': {},
            'next_handler': None
        }

class ExamSelectionHandler(MessageHandler):
    """
    Handles exam selection stage
    """
    
    def __init__(self, state_manager, exam_registry):
        self.state_manager = state_manager
        self.exam_registry = exam_registry
    
    def can_handle(self, message: str, user_state: Dict[str, Any]) -> bool:
        return user_state.get('stage') == 'selecting_exam'
    
    def handle(self, user_phone: str, message: str, user_state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Processing exam selection for {user_phone}: {message}")
        
        exams = self.exam_registry.get_available_exams()
        if not exams:
            return {
                'response': "Sorry, no exams are currently available. Please contact support.",
                'state_updates': {'stage': 'error'},
                'next_handler': None
            }
        
        try:
            choice = int(message.strip()) - 1
            logger.info(f"Parsed choice: {choice} from message: '{message}'")
            
            if 0 <= choice < len(exams):
                selected_exam = exams[choice]
                logger.info(f"Selected exam: {selected_exam}")
                
                try:
                    # Get exam type implementation
                    exam_type = self.exam_registry.get_exam_type(selected_exam)
                    initial_stage = exam_type.get_initial_stage()
                    
                    # Get initial options for the first stage
                    options = exam_type.get_available_options(initial_stage, user_state)
                    
                    if not options:
                        return {
                            'response': f"Sorry, no options available for {selected_exam.upper()}. Please try another exam.",
                            'state_updates': {},
                            'next_handler': 'exam_selection'
                        }
                    
                    # Format the response based on the stage
                    stage_name = initial_stage.replace('selecting_', '').replace('_', ' ').title()
                    options_text = exam_type.format_options_list(options, f"Available {stage_name}s")
                    
                    return {
                        'response': f"✅ You selected: {selected_exam.upper()}\n\n{options_text}",
                        'state_updates': {
                            'exam': selected_exam,
                            'stage': initial_stage
                        },
                        'next_handler': f'{selected_exam}_handler'
                    }
                    
                except ValueError as e:
                    logger.error(f"Error getting exam type for {selected_exam}: {e}")
                    return {
                        'response': f"Sorry, {selected_exam.upper()} is not yet supported. Please try another exam.",
                        'state_updates': {},
                        'next_handler': 'exam_selection'
                    }
            else:
                return {
                    'response': f"Invalid choice. Please select a number between 1 and {len(exams)}.",
                    'state_updates': {},
                    'next_handler': 'exam_selection'
                }
                
        except ValueError:
            logger.warning(f"Invalid input for exam selection: '{message}'")
            return {
                'response': f"Please enter a valid number between 1 and {len(exams)}.",
                'state_updates': {},
                'next_handler': 'exam_selection'
            }

class ExamTypeHandler(MessageHandler):
    """
    Handles exam-specific stages using the exam type implementations
    """
    
    def __init__(self, state_manager, exam_registry):
        self.state_manager = state_manager
        self.exam_registry = exam_registry
    
    def can_handle(self, message: str, user_state: Dict[str, Any]) -> bool:
        stage = user_state.get('stage', '')
        exam = user_state.get('exam')
        
        # Handle if we have an exam and are not in initial stages
        return (exam is not None and 
                stage not in ['initial', 'selecting_exam'] and
                self.exam_registry.is_exam_supported(exam))
    
    def handle(self, user_phone: str, message: str, user_state: Dict[str, Any]) -> Dict[str, Any]:
        exam = user_state.get('exam')
        stage = user_state.get('stage')
        
        logger.info(f"Handling {exam} stage {stage} for {user_phone}: {message}")
        
        if not exam or not stage:
            return {
                'response': "Session error. Please send 'start' to begin again.",
                'state_updates': {'stage': 'initial'},
                'next_handler': None
            }
        
        try:
            # Get exam type implementation
            exam_type = self.exam_registry.get_exam_type(exam)
            
            # Handle the current stage
            result = exam_type.handle_stage(stage, user_phone, message, user_state)
            
            # Convert exam type result to our handler format
            return {
                'response': result.get('response', 'No response generated.'),
                'state_updates': result.get('state_updates', {}),
                'next_handler': f'{exam}_handler' if result.get('next_stage') != 'completed' else None
            }
            
        except ValueError as e:
            logger.error(f"Exam type error for {exam}: {e}")
            return {
                'response': f"Sorry, {exam.upper()} is not supported yet. Please send 'start' to try another exam.",
                'state_updates': {'stage': 'initial'},
                'next_handler': None
            }
        except Exception as e:
            logger.error(f"Error in exam type handler: {str(e)}", exc_info=True)
            return {
                'response': "Sorry, something went wrong. Please try again or send 'restart' to start over.",
                'state_updates': {},
                'next_handler': f'{exam}_handler'
            }

class FallbackHandler(MessageHandler):
    """
    Fallback handler for unrecognized states or messages
    """
    
    def can_handle(self, message: str, user_state: Dict[str, Any]) -> bool:
        return True  # Always can handle as fallback
    
    def handle(self, user_phone: str, message: str, user_state: Dict[str, Any]) -> Dict[str, Any]:
        stage = user_state.get('stage', 'unknown')
        logger.warning(f"Fallback handler triggered for {user_phone} in stage {stage}")
        
        if stage == 'initial':
            return {
                'response': "Welcome! Send 'start' to begin practicing exams.",
                'state_updates': {},
                'next_handler': None
            }
        else:
            return {
                'response': "I didn't understand that. Send 'help' for available commands or 'restart' to start over.",
                'state_updates': {},
                'next_handler': None
            }