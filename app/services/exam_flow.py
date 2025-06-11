from app.services.state import UserStateManager
from app.services.exam_registry import ExamRegistry
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class ExamFlowManager:
    """
    Manages the exam flow logic using pluggable exam types
    """
    
    def __init__(self):
        self.state_manager = UserStateManager()
        self.exam_registry = ExamRegistry()
    
    def start_conversation(self, user_phone: str) -> str:
        """
        Start a new conversation with the user
        """
        logger.info(f"Starting new conversation for user {user_phone}")
        
        # Reset user state to ensure clean start
        self.state_manager.reset_user_state(user_phone)
        
        # Update state to exam selection stage
        self.state_manager.update_user_state(user_phone, {'stage': 'selecting_exam'})
        
        # Verify state was updated (access directly, don't call get_user_state again)
        current_state = self.state_manager.user_states.get(user_phone, {})
        logger.info(f"State after start_conversation: {current_state.get('stage')}")
        
        # Get available exams
        exams = self.exam_registry.get_available_exams()
        logger.info(f"Available exams: {exams}")
        
        if not exams:
            return "Sorry, no exams are currently available. Please contact support."
        
        # Format exam list with proper capitalization
        exam_list = "\n".join([f"{i+1}. {exam.upper()}" for i, exam in enumerate(exams)])
        
        return (f"🎓 Welcome to the Exam Practice Bot!\n\n"
                f"Available exams:\n{exam_list}\n\n"
                f"Please reply with the number of your choice (e.g., '1' for {exams[0].upper()}).")
    
    def handle_exam_selection(self, user_phone: str, message: str) -> str:
        """
        Handle exam selection
        """
        logger.info(f"Handling exam selection for {user_phone}: {message}")
        
        # Verify we're in the right state (access directly)
        user_state = self.state_manager.user_states.get(user_phone, {})
        current_stage = user_state.get('stage')
        
        if current_stage != 'selecting_exam':
            logger.warning(f"User {user_phone} not in selecting_exam stage (current: {current_stage})")
            return "Session error. Please send 'start' to begin again."
        
        exams = self.exam_registry.get_available_exams()
        
        if not exams:
            return "Sorry, no exams are currently available. Please contact support."
        
        try:
            choice = int(message.strip()) - 1
            logger.info(f"Parsed choice: {choice} from message: '{message}'")
            
            if 0 <= choice < len(exams):
                selected_exam = exams[choice]
                logger.info(f"Selected exam: {selected_exam}")
                
                # Get exam type implementation
                try:
                    exam_type = self.exam_registry.get_exam_type(selected_exam)
                    initial_stage = exam_type.get_initial_stage()
                    
                    # Update user state with exam and initial stage
                    state_updates = {
                        'exam': selected_exam,
                        'stage': initial_stage
                    }
                    
                    self.state_manager.update_user_state(user_phone, state_updates)
                    
                    # Verify state update (access directly)
                    updated_state = self.state_manager.user_states.get(user_phone, {})
                    logger.info(f"State after exam selection: exam={updated_state.get('exam')}, stage={updated_state.get('stage')}")
                    
                    # Get initial options for the first stage
                    options = exam_type.get_available_options(initial_stage, updated_state)
                    
                    if not options:
                        return f"Sorry, no options available for {selected_exam.upper()}. Please try another exam."
                    
                    # Format the response based on the stage
                    stage_name = initial_stage.replace('selecting_', '').replace('_', ' ').title()
                    options_text = exam_type.format_options_list(options, f"Available {stage_name}s")
                    
                    return f"✅ You selected: {selected_exam.upper()}\n\n{options_text}"
                    
                except ValueError as e:
                    logger.error(f"Error getting exam type for {selected_exam}: {e}")
                    return f"Sorry, {selected_exam.upper()} is not yet supported. Please try another exam."
                
            else:
                return f"Invalid choice. Please select a number between 1 and {len(exams)}."
                
        except ValueError:
            logger.warning(f"Invalid input for exam selection: '{message}'")
            return f"Please enter a valid number between 1 and {len(exams)}."
        except Exception as e:
            logger.error(f"Error in exam selection: {str(e)}")
            return "Sorry, something went wrong. Please try again."
    
    def handle_stage_flow(self, user_phone: str, message: str) -> str:
        """
        Handle stage-specific flow using exam type implementations
        """
        # Access state directly to avoid recreation
        user_state = self.state_manager.user_states.get(user_phone, {})
        exam = user_state.get('exam')
        stage = user_state.get('stage')
        
        logger.info(f"Handling stage flow for {user_phone}: exam={exam}, stage={stage}, message={message}")
        
        if not exam:
            logger.error(f"No exam found in state for {user_phone}")
            return "Session expired. Please send 'start' to begin again."
        
        if not stage:
            logger.error(f"No stage found in state for {user_phone}")
            return "Session error. Please send 'restart' to start over."
        
        try:
            # Get exam type implementation
            exam_type = self.exam_registry.get_exam_type(exam)
            
            # Handle the current stage
            result = exam_type.handle_stage(stage, user_phone, message, user_state)
            
            # Apply state updates if provided
            if result.get('state_updates'):
                self.state_manager.update_user_state(user_phone, result['state_updates'])
                logger.info(f"Applied state updates for {user_phone}: {result['state_updates']}")
            
            # Update stage if changed
            if result.get('next_stage') and result['next_stage'] != stage:
                self.state_manager.update_user_state(user_phone, {'stage': result['next_stage']})
                logger.info(f"Stage transition for {user_phone}: {stage} -> {result['next_stage']}")
            
            # Reset state if exam is completed
            if result.get('next_stage') == 'completed':
                self.state_manager.reset_user_state(user_phone)
                logger.info(f"Exam completed for {user_phone}, state reset")
            
            return result.get('response', 'No response generated.')
            
        except ValueError as e:
            logger.error(f"Exam type error for {exam}: {e}")
            return f"Sorry, {exam.upper()} is not supported yet. Please send 'start' to try another exam."
        except Exception as e:
            logger.error(f"Error in stage flow: {str(e)}", exc_info=True)
            return "Sorry, something went wrong. Please try again or send 'restart' to start over."