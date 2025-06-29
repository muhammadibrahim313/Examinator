from typing import Dict, Any, List
from app.services.exam_types.base import BaseExamType
from app.services.question_fetcher import QuestionFetcher
import logging

logger = logging.getLogger(__name__)

class NEETExamType(BaseExamType):
    """
    NEET exam type with real past questions
    """
    
    def __init__(self):
        super().__init__("NEET")
        self.question_fetcher = QuestionFetcher()
    
    def get_flow_stages(self) -> List[str]:
        return ['selecting_subject', 'taking_exam']
    
    def get_initial_stage(self) -> str:
        return 'selecting_subject'
    
    def handle_stage(self, stage: str, user_phone: str, message: str, user_state: Dict[str, Any]) -> Dict[str, Any]:
        if stage == 'selecting_subject':
            return self._handle_subject_selection(user_phone, message, user_state)
        elif stage == 'taking_exam':
            return self._handle_answer(user_phone, message, user_state)
        else:
            return {
                'response': f"Unknown stage: {stage}. Please send 'restart' to start over.",
                'next_stage': 'selecting_subject',
                'state_updates': {'stage': 'selecting_subject'}
            }
    
    def validate_stage_input(self, stage: str, message: str, user_state: Dict[str, Any]) -> bool:
        if stage == 'selecting_subject':
            subjects = self.question_fetcher.get_available_subjects('neet')
            return self.parse_choice(message, subjects) is not None
        elif stage == 'taking_exam':
            return message.strip().lower() in ['a', 'b', 'c', 'd']
        return False
    
    def get_available_options(self, stage: str, user_state: Dict[str, Any]) -> List[str]:
        if stage == 'selecting_subject':
            return self.question_fetcher.get_available_subjects('neet')
        elif stage == 'taking_exam':
            return ['A', 'B', 'C', 'D']
        return []
    
    def _handle_subject_selection(self, user_phone: str, message: str, user_state: Dict[str, Any]) -> Dict[str, Any]:
        subjects = self.question_fetcher.get_available_subjects('neet')
        
        if not subjects:
            return {
                'response': "Sorry, no subjects available for NEET. Please contact support.",
                'next_stage': 'selecting_subject',
                'state_updates': {}
            }
        
        selected_subject = self.parse_choice(message, subjects)
        
        if selected_subject:
            num_questions = self.question_fetcher.get_questions_per_exam('neet', selected_subject)
            
            return {
                'response': f"✅ You selected: {selected_subject}\n\n🔍 Fetching {num_questions} real NEET past questions...\n\nThis may take a moment as we search for authentic past questions.",
                'next_stage': 'loading_questions',
                'state_updates': {
                    'subject': selected_subject,
                    'stage': 'loading_questions',
                    'questions_needed': num_questions
                }
            }
        else:
            return {
                'response': f"Invalid choice. Please select a number between 1 and {len(subjects)}.\n\n" + 
                           self.format_options_list(subjects, "Available NEET subjects"),
                'next_stage': 'selecting_subject',
                'state_updates': {}
            }
    
    async def load_questions_async(self, user_phone: str, user_state: Dict[str, Any]) -> Dict[str, Any]:
        subject = user_state.get('subject')
        num_questions = user_state.get('questions_needed', 50)
        
        try:
            questions = await self.question_fetcher.fetch_questions('neet', subject, num_questions)
            
            if not questions:
                return {
                    'response': f"Sorry, could not fetch questions for {subject}. Please try again.",
                    'next_stage': 'selecting_subject',
                    'state_updates': {'stage': 'selecting_subject'}
                }
            
            first_question = self._format_question(questions[0], 1, len(questions))
            intro = f"🎯 Starting NEET {subject} Practice\n"
            intro += f"📚 {len(questions)} real past questions\n"
            intro += f"⏱️ Standard NEET format\n\n"
            
            return {
                'response': intro + first_question,
                'next_stage': 'taking_exam',
                'state_updates': {
                    'stage': 'taking_exam',
                    'questions': questions,
                    'total_questions': len(questions),
                    'current_question_index': 0,
                    'score': 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error loading NEET questions: {e}")
            return {
                'response': f"Sorry, there was an error loading questions. Please try again.",
                'next_stage': 'selecting_subject',
                'state_updates': {'stage': 'selecting_subject'}
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
        
        year = current_question.get('year', 'Unknown')
        explanation = current_question.get('explanation', 'No explanation available.')
        
        response = f"{'✅ Correct!' if is_correct else '❌ Wrong!'} Answer: {correct_answer.upper()}\n\n"
        response += f"📅 Source: NEET {year}\n"
        response += f"💡 {explanation}\n\n"
        
        if next_index >= len(questions):
            percentage = (new_score / len(questions)) * 100
            response += f"🎉 NEET {user_state.get('subject')} Complete!\n"
            response += f"📈 Score: {new_score}/{len(questions)} ({percentage:.1f}%)\n\n"
            response += "Send 'start' to practice another subject."
            
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
    
    def _format_question(self, question: Dict[str, Any], question_num: int, total_questions: int) -> str:
        question_text = question.get('question', 'No question text available')
        options = question.get('options', {})
        year = question.get('year', 'Unknown')
        
        formatted = f"Question {question_num}/{total_questions} (NEET {year}):\n{question_text}\n\n"
        
        for key in ['A', 'B', 'C', 'D']:
            if key in options:
                formatted += f"{key}. {options[key]}\n"
        
        formatted += "\nReply with A, B, C, or D"
        return formatted