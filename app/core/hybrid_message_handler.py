from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
import logging
from app.services.llm_agent import LLMAgentService

logger = logging.getLogger(__name__)

class HybridMessageHandler(ABC):
    """
    Hybrid message handler that can use both structured bot logic and LLM agent
    """
    
    def __init__(self, state_manager, exam_registry):
        self.state_manager = state_manager
        self.exam_registry = exam_registry
        self.llm_agent = LLMAgentService()
    
    @abstractmethod
    def can_handle(self, message: str, user_state: Dict[str, Any]) -> bool:
        """Check if this handler can process the message"""
        pass
    
    @abstractmethod
    def should_use_llm(self, message: str, user_state: Dict[str, Any]) -> bool:
        """Decide whether to use LLM agent or structured logic"""
        pass
    
    async def handle(self, user_phone: str, message: str, user_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle the message using either LLM agent or structured logic
        """
        try:
            if self.should_use_llm(message, user_state):
                return await self._handle_with_llm(user_phone, message, user_state)
            else:
                return self._handle_with_logic(user_phone, message, user_state)
        except Exception as e:
            logger.error(f"Error in hybrid handler: {str(e)}", exc_info=True)
            return {
                'response': "Sorry, something went wrong. Please try again or send 'restart'.",
                'state_updates': {},
                'next_handler': None
            }
    
    async def _handle_with_llm(self, user_phone: str, message: str, user_state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle using LLM agent"""
        logger.info(f"Using LLM agent for {user_phone}")
        
        # Create context for the LLM
        context = {
            'exam': user_state.get('exam'),
            'subject': user_state.get('subject'),
            'year': user_state.get('year'),
            'current_question_index': user_state.get('current_question_index'),
            'total_questions': user_state.get('total_questions'),
            'score': user_state.get('score'),
            'stage': user_state.get('stage')
        }
        
        # Get LLM response
        response = await self.llm_agent.process_message(user_phone, message, context)
        
        return {
            'response': response,
            'state_updates': {},  # LLM doesn't modify state directly
            'next_handler': None
        }
    
    @abstractmethod
    def _handle_with_logic(self, user_phone: str, message: str, user_state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle using structured bot logic"""
        pass

class SmartGlobalCommandHandler(HybridMessageHandler):
    """
    Enhanced global command handler with LLM capabilities
    """
    
    def can_handle(self, message: str, user_state: Dict[str, Any]) -> bool:
        command = message.lower().strip()
        return command in ['start', 'restart', 'exit', 'help'] or self._is_general_query(message)
    
    def should_use_llm(self, message: str, user_state: Dict[str, Any]) -> bool:
        """Use LLM for general queries, structured logic for specific commands"""
        command = message.lower().strip()
        specific_commands = ['start', 'restart', 'exit']
        
        if command in specific_commands:
            return False
        
        # Use LLM for help requests and general queries
        return True
    
    def _is_general_query(self, message: str) -> bool:
        """Check if this is a general query that should be handled by LLM"""
        general_keywords = [
            'help', 'how', 'what', 'why', 'when', 'where', 'explain',
            'tell me', 'can you', 'do you', 'about', 'info'
        ]
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in general_keywords)
    
    def _handle_with_logic(self, user_phone: str, message: str, user_state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle specific commands with structured logic"""
        command = message.lower().strip()
        
        if command in ['start', 'restart']:
            return self._handle_start(user_phone)
        elif command == 'exit':
            return self._handle_exit(user_phone)
        
        return {'response': 'Unknown command', 'state_updates': {}, 'next_handler': None}
    
    def _handle_start(self, user_phone: str) -> Dict[str, Any]:
        """Handle start/restart command"""
        logger.info(f"Starting new session for {user_phone}")
        
        exams = self.exam_registry.get_available_exams()
        if not exams:
            return {
                'response': "Sorry, no exams are currently available. Please contact support.",
                'state_updates': {'stage': 'error'},
                'next_handler': None
            }
        
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

class SmartExamSelectionHandler(HybridMessageHandler):
    """
    Enhanced exam selection handler with LLM capabilities
    """
    
    def can_handle(self, message: str, user_state: Dict[str, Any]) -> bool:
        return user_state.get('stage') == 'selecting_exam'
    
    def should_use_llm(self, message: str, user_state: Dict[str, Any]) -> bool:
        """FIXED: Use structured logic for number selections, LLM for other queries"""
        message_clean = message.strip()
        
        # Check if it's a valid number selection
        try:
            choice = int(message_clean)
            exams = self.exam_registry.get_available_exams()
            if 1 <= choice <= len(exams):
                logger.info(f"📊 EXAM SELECTION: Valid number choice {choice} detected - using structured logic")
                return False  # Use structured logic for valid numbers
        except ValueError:
            pass
        
        # Check if it's an invalid number
        try:
            int(message_clean)
            logger.info(f"📊 EXAM SELECTION: Invalid number detected - using structured logic for error handling")
            return False  # Use structured logic to handle invalid numbers
        except ValueError:
            pass
        
        # For non-numeric input, use LLM
        logger.info(f"📊 EXAM SELECTION: Non-numeric input '{message}' - using LLM agent")
        return True
    
    def _handle_with_logic(self, user_phone: str, message: str, user_state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle exam selection with structured logic"""
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
            
            if 0 <= choice < len(exams):
                selected_exam = exams[choice]
                logger.info(f"Selected exam: {selected_exam}")
                
                try:
                    exam_type = self.exam_registry.get_exam_type(selected_exam)
                    initial_stage = exam_type.get_initial_stage()
                    options = exam_type.get_available_options(initial_stage, user_state)
                    
                    if not options:
                        return {
                            'response': f"Sorry, no options available for {selected_exam.upper()}. Please try another exam.",
                            'state_updates': {},
                            'next_handler': 'exam_selection'
                        }
                    
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
                # Invalid number range
                exam_list = "\n".join([f"{i+1}. {exam.upper()}" for i, exam in enumerate(exams)])
                return {
                    'response': f"❌ Invalid choice. Please select a number between 1 and {len(exams)}.\n\n🎓 Available exams:\n{exam_list}\n\nPlease reply with the number of your choice.",
                    'state_updates': {},
                    'next_handler': 'exam_selection'
                }
                
        except ValueError:
            # Not a number at all
            logger.warning(f"Invalid input for exam selection: '{message}'")
            exam_list = "\n".join([f"{i+1}. {exam.upper()}" for i, exam in enumerate(exams)])
            return {
                'response': f"❌ Please enter a valid number between 1 and {len(exams)}.\n\n🎓 Available exams:\n{exam_list}\n\nPlease reply with the number of your choice.",
                'state_updates': {},
                'next_handler': 'exam_selection'
            }

class SmartExamTypeHandler(HybridMessageHandler):
    """
    Enhanced exam type handler with LLM capabilities for questions and explanations
    """
    
    def can_handle(self, message: str, user_state: Dict[str, Any]) -> bool:
        stage = user_state.get('stage', '')
        exam = user_state.get('exam')
        
        return (exam is not None and 
                stage not in ['initial', 'selecting_exam'] and
                self.exam_registry.is_exam_supported(exam))
    
    def should_use_llm(self, message: str, user_state: Dict[str, Any]) -> bool:
        """Use LLM when taking exams for explanations, structured logic for selections"""
        stage = user_state.get('stage', '')
        
        if stage == 'taking_exam':
            # For exam answers, use structured logic for A,B,C,D but LLM for explanations
            answer = message.strip().lower()
            if answer in ['a', 'b', 'c', 'd']:
                return False  # Use structured logic for answer processing
            else:
                return True  # Use LLM for questions about the exam
        
        # For selection stages, use structured logic for numbers, LLM for queries
        try:
            int(message.strip())
            return False
        except ValueError:
            return True
    
    def _handle_with_logic(self, user_phone: str, message: str, user_state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle with structured exam logic"""
        exam = user_state.get('exam')
        stage = user_state.get('stage')
        
        logger.info(f"Handling {exam} stage {stage} for {user_phone} with message '{message}'")
        
        if not exam or not stage:
            return {
                'response': "Session error. Please send 'start' to begin again.",
                'state_updates': {'stage': 'initial'},
                'next_handler': None
            }
        
        try:
            exam_type = self.exam_registry.get_exam_type(exam)
            result = exam_type.handle_stage(stage, user_phone, message, user_state)
            
            state_updates = result.get('state_updates', {})
            next_stage = result.get('next_stage')
            
            if next_stage and next_stage != stage:
                state_updates['stage'] = next_stage
                logger.info(f"Stage transition for {user_phone}: {stage} -> {next_stage}")
            
            return {
                'response': result.get('response', 'No response generated.'),
                'state_updates': state_updates,
                'next_handler': f'{exam}_handler' if next_stage != 'completed' else None
            }
            
        except Exception as e:
            logger.error(f"Error in exam type handler: {str(e)}", exc_info=True)
            return {
                'response': "Sorry, something went wrong. Please try again or send 'restart' to start over.",
                'state_updates': {},
                'next_handler': f'{exam}_handler'
            }

class SmartFallbackHandler(HybridMessageHandler):
    """
    Enhanced fallback handler that always uses LLM for unrecognized inputs
    """
    
    def can_handle(self, message: str, user_state: Dict[str, Any]) -> bool:
        return True  # Always can handle as fallback
    
    def should_use_llm(self, message: str, user_state: Dict[str, Any]) -> bool:
        return True  # Always use LLM for fallback
    
    def _handle_with_logic(self, user_phone: str, message: str, user_state: Dict[str, Any]) -> Dict[str, Any]:
        """This shouldn't be called since we always use LLM"""
        stage = user_state.get('stage', 'unknown')
        logger.warning(f"Fallback logic handler triggered for {user_phone} in stage {stage}")
        
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