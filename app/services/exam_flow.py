from app.services.state import UserStateManager
from app.utils.helpers import load_exam_data, get_available_exams, get_available_subjects, get_available_years
import random
from typing import List, Dict, Any

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
        # Reset user state
        self.state_manager.reset_user_state(user_phone)
        
        # Update state to exam selection
        self.state_manager.update_user_state(user_phone, {'stage': 'selecting_exam'})
        
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
        exams = get_available_exams()
        
        try:
            choice = int(message) - 1
            if 0 <= choice < len(exams):
                selected_exam = exams[choice]
                
                # Update user state
                self.state_manager.update_user_state(user_phone, {
                    'exam': selected_exam,
                    'stage': 'selecting_subject'
                })
                
                # Get available subjects for this exam
                subjects = get_available_subjects(selected_exam)
                
                if not subjects:
                    return f"Sorry, no subjects available for {selected_exam.upper()}. Please try another exam."
                
                subject_list = "\n".join([f"{i+1}. {subject}" for i, subject in enumerate(subjects)])
                
                return (f"✅ You selected: {selected_exam.upper()}\n\n"
                        f"Available subjects:\n{subject_list}\n\n"
                        f"Please reply with the number of your choice.")
            else:
                return f"Invalid choice. Please select a number between 1 and {len(exams)}."
                
        except ValueError:
            return f"Please enter a valid number between 1 and {len(exams)}."
    
    def handle_subject_selection(self, user_phone: str, message: str) -> str:
        """
        Handle subject selection
        """
        user_state = self.state_manager.get_user_state(user_phone)
        exam = user_state.get('exam')
        
        subjects = get_available_subjects(exam)
        
        try:
            choice = int(message) - 1
            if 0 <= choice < len(subjects):
                selected_subject = subjects[choice]
                
                # Update user state
                self.state_manager.update_user_state(user_phone, {
                    'subject': selected_subject,
                    'stage': 'selecting_year'
                })
                
                # Get available years for this exam/subject
                years = get_available_years(exam, selected_subject)
                
                if not years:
                    return f"Sorry, no years available for {exam.upper()} {selected_subject}. Please try another subject."
                
                year_list = "\n".join([f"{i+1}. {year}" for i, year in enumerate(years)])
                
                return (f"✅ You selected: {selected_subject}\n\n"
                        f"Available years:\n{year_list}\n\n"
                        f"Please reply with the number of your choice.")
            else:
                return f"Invalid choice. Please select a number between 1 and {len(subjects)}."
                
        except ValueError:
            return f"Please enter a valid number between 1 and {len(subjects)}."
    
    def handle_year_selection(self, user_phone: str, message: str) -> str:
        """
        Handle year selection and start the exam
        """
        user_state = self.state_manager.get_user_state(user_phone)
        exam = user_state.get('exam')
        subject = user_state.get('subject')
        
        years = get_available_years(exam, subject)
        
        try:
            choice = int(message) - 1
            if 0 <= choice < len(years):
                selected_year = years[choice]
                
                # Load questions for this exam/subject/year
                questions = load_exam_data(exam, subject, selected_year)
                
                if not questions:
                    return f"Sorry, no questions available for {exam.upper()} {subject} {selected_year}. Please try another combination."
                
                # Shuffle questions for variety
                random.shuffle(questions)
                
                # Update user state
                self.state_manager.update_user_state(user_phone, {
                    'year': selected_year,
                    'stage': 'taking_exam',
                    'questions': questions,
                    'total_questions': len(questions),
                    'current_question_index': 0,
                    'score': 0
                })
                
                # Send first question
                return self._send_current_question(user_phone)
            else:
                return f"Invalid choice. Please select a number between 1 and {len(years)}."
                
        except ValueError:
            return f"Please enter a valid number between 1 and {len(years)}."
    
    def handle_answer(self, user_phone: str, message: str) -> str:
        """
        Handle user's answer to a question
        """
        user_state = self.state_manager.get_user_state(user_phone)
        questions = user_state.get('questions', [])
        current_index = user_state.get('current_question_index', 0)
        
        if current_index >= len(questions):
            return "No more questions available. Send 'start' to begin a new session."
        
        current_question = questions[current_index]
        
        # Validate answer format
        valid_answers = ['a', 'b', 'c', 'd']
        if message not in valid_answers:
            return ("Please reply with A, B, C, or D for your answer.\n\n" + 
                   self._format_question(current_question, current_index + 1, len(questions)))
        
        # Check if answer is correct
        correct_answer = current_question.get('correct_answer', '').lower()
        is_correct = message == correct_answer
        
        # Update score if correct
        new_score = user_state.get('score', 0)
        if is_correct:
            new_score += 1
        
        # Move to next question
        next_index = current_index + 1
        
        # Prepare response
        response = f"{'✅ Correct!' if is_correct else '❌ Wrong!'} The correct answer is {correct_answer.upper()}.\n\n"
        
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
        
        # Add options
        for key in ['A', 'B', 'C', 'D']:
            if key in options:
                formatted += f"{key}. {options[key]}\n"
        
        formatted += "\nReply with A, B, C, or D"
        
        return formatted