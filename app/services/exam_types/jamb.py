from typing import Dict, Any, List
from app.services.exam_types.base import BaseExamType
from app.utils.helpers import get_available_subjects, get_available_years, load_exam_data
import random

class JAMBExamType(BaseExamType):
    """
    JAMB exam type implementation (fallback)
    Flow: selecting_subject -> selecting_year -> taking_exam
    """
    
    def __init__(self):
        super().__init__("JAMB")
    
    def get_flow_stages(self) -> List[str]:
        return ['selecting_subject', 'selecting_year', 'taking_exam']
    
    def get_initial_stage(self) -> str:
        return 'selecting_subject'
    
    def handle_stage(self, stage: str, user_phone: str, message: str, user_state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle JAMB-specific stages"""
        if stage == 'selecting_subject':
            return self._handle_subject_selection(user_phone, message, user_state)
        elif stage == 'selecting_year':
            return self._handle_year_selection(user_phone, message, user_state)
        elif stage == 'taking_exam':
            return self._handle_answer(user_phone, message, user_state)
        else:
            return {
                'response': f"Unknown stage: {stage}. Please send 'restart' to start over.",
                'next_stage': 'selecting_subject',
                'state_updates': {'stage': 'selecting_subject'}
            }
    
    def validate_stage_input(self, stage: str, message: str, user_state: Dict[str, Any]) -> bool:
        return True  # Basic validation
    
    def get_available_options(self, stage: str, user_state: Dict[str, Any]) -> List[str]:
        if stage == 'selecting_subject':
            return ['Biology', 'Chemistry', 'Physics', 'Mathematics', 'English Language']
        return []
    
    def _handle_subject_selection(self, user_phone: str, message: str, user_state: Dict[str, Any]) -> Dict[str, Any]:
        subjects = ['Biology', 'Chemistry', 'Physics', 'Mathematics', 'English Language']
        
        try:
            choice = int(message.strip()) - 1
            if 0 <= choice < len(subjects):
                selected_subject = subjects[choice]
                
                return {
                    'response': f"✅ You selected: {selected_subject}\n\nChoose a year:\n1. 2023\n2. 2022\n3. 2021",
                    'next_stage': 'selecting_year',
                    'state_updates': {'subject': selected_subject, 'stage': 'selecting_year'}
                }
            else:
                return {
                    'response': f"Invalid choice. Please select 1-{len(subjects)}.",
                    'next_stage': 'selecting_subject',
                    'state_updates': {}
                }
        except ValueError:
            return {
                'response': f"Please enter a number 1-{len(subjects)}.",
                'next_stage': 'selecting_subject',
                'state_updates': {}
            }
    
    def _handle_year_selection(self, user_phone: str, message: str, user_state: Dict[str, Any]) -> Dict[str, Any]:
        years = ['2023', '2022', '2021']
        
        try:
            choice = int(message.strip()) - 1
            if 0 <= choice < len(years):
                selected_year = years[choice]
                
                # Generate sample questions
                questions = self._generate_sample_questions(user_state.get('subject'), selected_year)
                
                first_question = self._format_question(questions[0], 1, len(questions))
                
                return {
                    'response': f"🎯 Starting JAMB {user_state.get('subject')} {selected_year}\n\n{first_question}",
                    'next_stage': 'taking_exam',
                    'state_updates': {
                        'year': selected_year,
                        'stage': 'taking_exam',
                        'questions': questions,
                        'total_questions': len(questions),
                        'current_question_index': 0,
                        'score': 0
                    }
                }
            else:
                return {
                    'response': f"Invalid choice. Please select 1-{len(years)}.",
                    'next_stage': 'selecting_year',
                    'state_updates': {}
                }
        except ValueError:
            return {
                'response': f"Please enter a number 1-{len(years)}.",
                'next_stage': 'selecting_year',
                'state_updates': {}
            }
    
    def _handle_answer(self, user_phone: str, message: str, user_state: Dict[str, Any]) -> Dict[str, Any]:
        questions = user_state.get('questions', [])
        current_index = user_state.get('current_question_index', 0)
        
        if not questions or current_index >= len(questions):
            return {
                'response': "Practice completed! Send 'start' for another session.",
                'next_stage': 'completed',
                'state_updates': {'stage': 'completed'}
            }
        
        current_question = questions[current_index]
        user_answer = message.strip().lower()
        
        if user_answer not in ['a', 'b', 'c', 'd']:
            return {
                'response': "Please reply with A, B, C, or D.\n\n" + 
                           self._format_question(current_question, current_index + 1, len(questions)),
                'next_stage': 'taking_exam',
                'state_updates': {}
            }
        
        correct_answer = current_question.get('correct_answer', '').lower()
        is_correct = user_answer == correct_answer
        new_score = user_state.get('score', 0) + (1 if is_correct else 0)
        next_index = current_index + 1
        
        response = f"{'✅ Correct!' if is_correct else '❌ Wrong!'} Answer: {correct_answer.upper()}\n\n"
        
        if next_index >= len(questions):
            percentage = (new_score / len(questions)) * 100
            response += f"🎉 JAMB Practice Complete!\nScore: {new_score}/{len(questions)} ({percentage:.1f}%)\n\nSend 'start' for another session."
            
            return {
                'response': response,
                'next_stage': 'completed',
                'state_updates': {'score': new_score, 'stage': 'completed'}
            }
        else:
            next_question = questions[next_index]
            response += self._format_question(next_question, next_index + 1, len(questions))
            
            return {
                'response': response,
                'next_stage': 'taking_exam',
                'state_updates': {
                    'current_question_index': next_index,
                    'score': new_score
                }
            }
    
    def _generate_sample_questions(self, subject: str, year: str) -> List[Dict[str, Any]]:
        """Generate sample questions"""
        return [
            {
                "id": 1,
                "question": f"Sample {subject} question from {year}",
                "options": {"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"},
                "correct_answer": "B",
                "explanation": f"This is a sample {subject} question."
            },
            {
                "id": 2,
                "question": f"Another {subject} question from {year}",
                "options": {"A": "Choice A", "B": "Choice B", "C": "Choice C", "D": "Choice D"},
                "correct_answer": "A",
                "explanation": f"Another sample {subject} question."
            }
        ]
    
    def _format_question(self, question: Dict[str, Any], question_num: int, total_questions: int) -> str:
        """Format a question for display"""
        question_text = question.get('question', 'No question text available')
        options = question.get('options', {})
        
        formatted = f"Question {question_num}/{total_questions}:\n{question_text}\n\n"
        
        for key in ['A', 'B', 'C', 'D']:
            if key in options:
                formatted += f"{key}. {options[key]}\n"
        
        formatted += "\nReply with A, B, C, or D"
        return formatted