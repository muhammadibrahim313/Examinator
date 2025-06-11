from app.services.state import UserStateManager
from app.utils.helpers import load_exam_data, get_available_exams, get_available_subjects, get_available_years
import random
from typing import List, Dict, Any
import logging

# Set up logging
logger = logging.getLogger(__name__)

class ExamFlowManager:
    """
    Manages the exam flow logic and question handling
    """
    
    def __init__(self):
        self.state_manager = UserStateManager()
    
    def start_conversation(self, user_phone: str) -> str:
        """
        Start a new conversation with the user
        """
        logger.info(f"Starting conversation for {user_phone}")
        
        # Reset user state
        self.state_manager.reset_user_state(user_phone)
        
        # Update state to exam selection - this is crucial!
        self.state_manager.update_user_state(user_phone, {'stage': 'selecting_exam'})
        
        # Verify the state was updated
        current_state = self.state_manager.get_user_state(user_phone)
        logger.info(f"State after starting conversation: {current_state}")
        
        # Get available exams
        exams = get_available_exams()
        
        if not exams:
            return "Sorry, no exams are currently available. Please contact support."
        
        exam_list = "\n".join([f"{i+1}. {exam.upper()}" for i, exam in enumerate(exams)])
        
        return (f"🎓 Welcome to the Exam Practice Bot!\n\n"
                f"Available exams:\n{exam_list}\n\n"
                f"Please reply with the number of your choice (e.g., '1' for {exams[0].upper()}).")
    
    def handle_exam_selection(self, user_phone: str, message: str) -> str:
        """
        Handle exam selection
        """
        logger.info(f"Handling exam selection for {user_phone}: '{message}'")
        
        # Get current state to verify we're in the right stage
        current_state = self.state_manager.get_user_state(user_phone)
        logger.info(f"Current state before exam selection: {current_state}")
        
        exams = get_available_exams()
        
        if not exams:
            return "Sorry, no exams are currently available. Please contact support."
        
        try:
            choice = int(message.strip()) - 1
            logger.info(f"User choice: {choice}, Available exams: {exams}")
            
            if 0 <= choice < len(exams):
                selected_exam = exams[choice]
                logger.info(f"Selected exam: {selected_exam}")
                
                # Update user state to subject selection
                self.state_manager.update_user_state(user_phone, {
                    'exam': selected_exam,
                    'stage': 'selecting_subject'
                })
                
                # Verify state was updated
                updated_state = self.state_manager.get_user_state(user_phone)
                logger.info(f"State after exam selection: {updated_state}")
                
                # Get available subjects for this exam
                subjects = get_available_subjects(selected_exam)
                logger.info(f"Available subjects for {selected_exam}: {subjects}")
                
                if not subjects:
                    # Reset to exam selection if no subjects
                    self.state_manager.update_user_state(user_phone, {'stage': 'selecting_exam'})
                    return f"Sorry, no subjects available for {selected_exam.upper()}. Please try another exam."
                
                subject_list = "\n".join([f"{i+1}. {subject}" for i, subject in enumerate(subjects)])
                
                return (f"✅ You selected: {selected_exam.upper()}\n\n"
                        f"Available subjects:\n{subject_list}\n\n"
                        f"Please reply with the number of your choice.")
            else:
                return f"Invalid choice. Please select a number between 1 and {len(exams)}."
                
        except ValueError:
            logger.warning(f"Invalid input for exam selection: '{message}'")
            return f"Please enter a valid number between 1 and {len(exams)}."
        except Exception as e:
            logger.error(f"Error in exam selection: {str(e)}")
            return "Sorry, something went wrong. Please try again."
    
    def handle_subject_selection(self, user_phone: str, message: str) -> str:
        """
        Handle subject selection
        """
        logger.info(f"Handling subject selection for {user_phone}: '{message}'")
        
        user_state = self.state_manager.get_user_state(user_phone)
        logger.info(f"Current state before subject selection: {user_state}")
        
        exam = user_state.get('exam')
        
        if not exam:
            logger.error(f"No exam found in state for {user_phone}")
            # Reset to start
            self.state_manager.update_user_state(user_phone, {'stage': 'selecting_exam'})
            return "Session expired. Please send 'start' to begin again."
        
        subjects = get_available_subjects(exam)
        logger.info(f"Available subjects for {exam}: {subjects}")
        
        if not subjects:
            # Reset to exam selection
            self.state_manager.update_user_state(user_phone, {'stage': 'selecting_exam'})
            return f"Sorry, no subjects available for {exam.upper()}. Please send 'start' to try again."
        
        try:
            choice = int(message.strip()) - 1
            logger.info(f"User choice: {choice}, Available subjects: {subjects}")
            
            if 0 <= choice < len(subjects):
                selected_subject = subjects[choice]
                logger.info(f"Selected subject: {selected_subject}")
                
                # Update user state to year selection
                self.state_manager.update_user_state(user_phone, {
                    'subject': selected_subject,
                    'stage': 'selecting_year'
                })
                
                # Verify state was updated
                updated_state = self.state_manager.get_user_state(user_phone)
                logger.info(f"State after subject selection: {updated_state}")
                
                # Get available years for this exam/subject
                years = get_available_years(exam, selected_subject)
                logger.info(f"Available years for {exam} {selected_subject}: {years}")
                
                if not years:
                    # Reset to subject selection if no years
                    self.state_manager.update_user_state(user_phone, {'stage': 'selecting_subject'})
                    return f"Sorry, no years available for {exam.upper()} {selected_subject}. Please try another subject."
                
                year_list = "\n".join([f"{i+1}. {year}" for i, year in enumerate(years)])
                
                return (f"✅ You selected: {selected_subject}\n\n"
                        f"Available years:\n{year_list}\n\n"
                        f"Please reply with the number of your choice.")
            else:
                return f"Invalid choice. Please select a number between 1 and {len(subjects)}."
                
        except ValueError:
            logger.warning(f"Invalid input for subject selection: '{message}'")
            return f"Please enter a valid number between 1 and {len(subjects)}."
        except Exception as e:
            logger.error(f"Error in subject selection: {str(e)}")
            return "Sorry, something went wrong. Please try again."
    
    def handle_year_selection(self, user_phone: str, message: str) -> str:
        """
        Handle year selection and start the exam
        """
        logger.info(f"Handling year selection for {user_phone}: '{message}'")
        
        user_state = self.state_manager.get_user_state(user_phone)
        logger.info(f"Current state before year selection: {user_state}")
        
        exam = user_state.get('exam')
        subject = user_state.get('subject')
        
        if not exam or not subject:
            logger.error(f"Missing exam or subject in state for {user_phone}")
            self.state_manager.update_user_state(user_phone, {'stage': 'selecting_exam'})
            return "Session expired. Please send 'start' to begin again."
        
        years = get_available_years(exam, subject)
        logger.info(f"Available years for {exam} {subject}: {years}")
        
        if not years:
            # Reset to subject selection
            self.state_manager.update_user_state(user_phone, {'stage': 'selecting_subject'})
            return f"Sorry, no years available for {exam.upper()} {subject}. Please send 'start' to try again."
        
        try:
            choice = int(message.strip()) - 1
            logger.info(f"User choice: {choice}, Available years: {years}")
            
            if 0 <= choice < len(years):
                selected_year = years[choice]
                logger.info(f"Selected year: {selected_year}")
                
                # Load questions for this exam/subject/year
                questions = load_exam_data(exam, subject, selected_year)
                logger.info(f"Loaded {len(questions)} questions for {exam} {subject} {selected_year}")
                
                if not questions:
                    # Reset to year selection if no questions
                    self.state_manager.update_user_state(user_phone, {'stage': 'selecting_year'})
                    return f"Sorry, no questions available for {exam.upper()} {subject} {selected_year}. Please try another year."
                
                # Shuffle questions for variety
                random.shuffle(questions)
                
                # Update user state to taking exam
                self.state_manager.update_user_state(user_phone, {
                    'year': selected_year,
                    'stage': 'taking_exam',
                    'questions': questions,
                    'total_questions': len(questions),
                    'current_question_index': 0,
                    'score': 0
                })
                
                # Verify state was updated
                updated_state = self.state_manager.get_user_state(user_phone)
                logger.info(f"Final state after year selection: {updated_state}")
                
                # Send first question
                return self._send_current_question(user_phone)
            else:
                return f"Invalid choice. Please select a number between 1 and {len(years)}."
                
        except ValueError:
            logger.warning(f"Invalid input for year selection: '{message}'")
            return f"Please enter a valid number between 1 and {len(years)}."
        except Exception as e:
            logger.error(f"Error in year selection: {str(e)}")
            return "Sorry, something went wrong. Please try again."
    
    def handle_answer(self, user_phone: str, message: str) -> str:
        """
        Handle user's answer to a question
        """
        logger.info(f"Handling answer for {user_phone}: '{message}'")
        
        user_state = self.state_manager.get_user_state(user_phone)
        questions = user_state.get('questions', [])
        current_index = user_state.get('current_question_index', 0)
        
        if not questions or current_index >= len(questions):
            logger.error(f"No questions or invalid index for {user_phone}")
            return "No more questions available. Send 'start' to begin a new session."
        
        current_question = questions[current_index]
        
        # Validate answer format
        valid_answers = ['a', 'b', 'c', 'd']
        user_answer = message.strip().lower()
        
        if user_answer not in valid_answers:
            return ("Please reply with A, B, C, or D for your answer.\n\n" + 
                   self._format_question(current_question, current_index + 1, len(questions)))
        
        # Check if answer is correct
        correct_answer = current_question.get('correct_answer', '').lower()
        is_correct = user_answer == correct_answer
        
        # Update score if correct
        new_score = user_state.get('score', 0)
        if is_correct:
            new_score += 1
        
        # Move to next question
        next_index = current_index + 1
        
        # Prepare response with explanation
        explanation = current_question.get('explanation', 'No explanation available.')
        response = f"{'✅ Correct!' if is_correct else '❌ Wrong!'} The correct answer is {correct_answer.upper()}.\n\n"
        response += f"💡 {explanation}\n\n"
        
        if next_index >= len(questions):
            # End of exam
            percentage = (new_score / len(questions)) * 100
            self.state_manager.reset_user_state(user_phone)
            
            return (f"{response}🎉 Exam completed!\n\n"
                   f"Your Score: {new_score}/{len(questions)} ({percentage:.1f}%)\n\n"
                   f"Send 'start' to take another exam.")
        else:
            # Update state and send next question
            self.state_manager.update_user_state(user_phone, {
                'current_question_index': next_index,
                'score': new_score
            })
            
            next_question = questions[next_index]
            response += self._format_question(next_question, next_index + 1, len(questions))
        
        return response
    
    def _send_current_question(self, user_phone: str) -> str:
        """
        Send the current question to the user
        """
        user_state = self.state_manager.get_user_state(user_phone)
        questions = user_state.get('questions', [])
        current_index = user_state.get('current_question_index', 0)
        
        if current_index >= len(questions):
            return "No questions available."
        
        current_question = questions[current_index]
        exam = user_state.get('exam', '').upper()
        subject = user_state.get('subject', '')
        year = user_state.get('year', '')
        
        intro = f"🎯 Starting {exam} {subject} {year} Practice\n\n"
        question_text = self._format_question(current_question, current_index + 1, len(questions))
        
        return intro + question_text
    
    def _format_question(self, question: Dict[str, Any], question_num: int, total_questions: int) -> str:
        """
        Format a question for display
        """
        question_text = question.get('question', 'No question text available')
        options = question.get('options', {})
        image_ref = question.get('image_ref')
        
        formatted = f"Question {question_num}/{total_questions}:\n{question_text}\n\n"
        
        # Add image reference if available
        if image_ref:
            formatted += f"📷 Image: {image_ref}\n\n"
        
        # Add options in order
        for key in ['A', 'B', 'C', 'D']:
            if key in options:
                formatted += f"{key}. {options[key]}\n"
        
        formatted += "\nReply with A, B, C, or D"
        
        return formatted