from typing import Dict, Any, List
from app.services.exam_types.base import BaseExamType

class SATExamType(BaseExamType):
    """
    SAT exam type implementation
    Flow: selecting_section -> selecting_difficulty -> taking_exam
    
    SAT has different structure:
    - Sections: Math, Reading, Writing
    - Difficulty levels: Easy, Medium, Hard
    - No year selection (uses current format)
    """
    
    def __init__(self):
        super().__init__("SAT")
    
    def get_flow_stages(self) -> List[str]:
        return ['selecting_section', 'selecting_difficulty', 'taking_exam']
    
    def get_initial_stage(self) -> str:
        return 'selecting_section'
    
    def handle_stage(self, stage: str, user_phone: str, message: str, user_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle SAT-specific stages
        """
        if stage == 'selecting_section':
            return self._handle_section_selection(user_phone, message, user_state)
        elif stage == 'selecting_difficulty':
            return self._handle_difficulty_selection(user_phone, message, user_state)
        elif stage == 'taking_exam':
            return self._handle_answer(user_phone, message, user_state)
        else:
            return {
                'response': f"Unknown stage: {stage}. Please send 'restart' to start over.",
                'next_stage': 'selecting_section',
                'state_updates': {}
            }
    
    def validate_stage_input(self, stage: str, message: str, user_state: Dict[str, Any]) -> bool:
        """
        Validate input for SAT stages
        """
        if stage == 'selecting_section':
            sections = self.get_available_sections()
            return self.parse_choice(message, sections) is not None
        elif stage == 'selecting_difficulty':
            difficulties = self.get_available_difficulties()
            return self.parse_choice(message, difficulties) is not None
        elif stage == 'taking_exam':
            return message.strip().lower() in ['a', 'b', 'c', 'd']
        return False
    
    def get_available_options(self, stage: str, user_state: Dict[str, Any]) -> List[str]:
        """
        Get available options for SAT stages
        """
        if stage == 'selecting_section':
            return self.get_available_sections()
        elif stage == 'selecting_difficulty':
            return self.get_available_difficulties()
        elif stage == 'taking_exam':
            return ['A', 'B', 'C', 'D']
        return []
    
    def get_available_sections(self) -> List[str]:
        """
        Get available SAT sections
        """
        return ['Math', 'Reading', 'Writing and Language']
    
    def get_available_difficulties(self) -> List[str]:
        """
        Get available difficulty levels
        """
        return ['Easy', 'Medium', 'Hard']
    
    def _handle_section_selection(self, user_phone: str, message: str, user_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle section selection for SAT
        """
        sections = self.get_available_sections()
        self.logger.info(f"Available sections for SAT: {sections}")
        
        selected_section = self.parse_choice(message, sections)
        
        if selected_section:
            self.logger.info(f"User {user_phone} selected section: {selected_section}")
            
            difficulties = self.get_available_difficulties()
            return {
                'response': f"✅ You selected: {selected_section}\n\n" + 
                           self.format_options_list(difficulties, "Available difficulty levels"),
                'next_stage': 'selecting_difficulty',
                'state_updates': {'section': selected_section}
            }
        else:
            return {
                'response': f"Invalid choice. Please select a number between 1 and {len(sections)}.\n\n" + 
                           self.format_options_list(sections, "Available sections"),
                'next_stage': 'selecting_section',
                'state_updates': {}
            }
    
    def _handle_difficulty_selection(self, user_phone: str, message: str, user_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle difficulty selection for SAT
        """
        section = user_state.get('section')
        if not section:
            return {
                'response': "Session error. Please send 'restart' to start over.",
                'next_stage': 'selecting_section',
                'state_updates': {}
            }
        
        difficulties = self.get_available_difficulties()
        selected_difficulty = self.parse_choice(message, difficulties)
        
        if selected_difficulty:
            self.logger.info(f"User {user_phone} selected difficulty: {selected_difficulty}")
            
            # For now, create sample questions (in real implementation, load from data)
            questions = self._generate_sample_questions(section, selected_difficulty)
            
            if not questions:
                return {
                    'response': f"Sorry, no questions available for {section} - {selected_difficulty}. Please try another difficulty.\n\n" + 
                               self.format_options_list(difficulties, "Available difficulty levels"),
                    'next_stage': 'selecting_difficulty',
                    'state_updates': {}
                }
            
            # Format first question
            first_question = self._format_question(questions[0], 1, len(questions))
            intro = f"🎯 Starting SAT {section} - {selected_difficulty} Practice\n\n"
            
            return {
                'response': intro + first_question,
                'next_stage': 'taking_exam',
                'state_updates': {
                    'difficulty': selected_difficulty,
                    'questions': questions,
                    'total_questions': len(questions),
                    'current_question_index': 0,
                    'score': 0
                }
            }
        else:
            return {
                'response': f"Invalid choice. Please select a number between 1 and {len(difficulties)}.\n\n" + 
                           self.format_options_list(difficulties, "Available difficulty levels"),
                'next_stage': 'selecting_difficulty',
                'state_updates': {}
            }
    
    def _handle_answer(self, user_phone: str, message: str, user_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle answer submission for SAT
        """
        questions = user_state.get('questions', [])
        current_index = user_state.get('current_question_index', 0)
        
        if not questions or current_index >= len(questions):
            return {
                'response': "No more questions available. Send 'start' to begin a new session.",
                'next_stage': 'completed',
                'state_updates': {}
            }
        
        current_question = questions[current_index]
        user_answer = message.strip().lower()
        
        # Validate answer format
        if user_answer not in ['a', 'b', 'c', 'd']:
            return {
                'response': "Please reply with A, B, C, or D for your answer.\n\n" + 
                           self._format_question(current_question, current_index + 1, len(questions)),
                'next_stage': 'taking_exam',
                'state_updates': {}
            }
        
        # Check if answer is correct
        correct_answer = current_question.get('correct_answer', '').lower()
        is_correct = user_answer == correct_answer
        
        # Update score
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
            response += (f"🎉 SAT Practice completed!\n\n"
                        f"Your Score: {new_score}/{len(questions)} ({percentage:.1f}%)\n\n"
                        f"Send 'start' to take another exam.")
            
            return {
                'response': response,
                'next_stage': 'completed',
                'state_updates': {'score': new_score}
            }
        else:
            # Continue with next question
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
    
    def _generate_sample_questions(self, section: str, difficulty: str) -> List[Dict[str, Any]]:
        """
        Generate sample SAT questions (in real implementation, load from database)
        """
        if section == "Math":
            return [
                {
                    "id": 1,
                    "question": f"If 2x + 3 = 11, what is the value of x? ({difficulty} level)",
                    "options": {
                        "A": "3",
                        "B": "4", 
                        "C": "5",
                        "D": "6"
                    },
                    "correct_answer": "B",
                    "explanation": "Solving: 2x + 3 = 11, so 2x = 8, therefore x = 4"
                },
                {
                    "id": 2,
                    "question": f"What is 15% of 80? ({difficulty} level)",
                    "options": {
                        "A": "10",
                        "B": "12",
                        "C": "15", 
                        "D": "20"
                    },
                    "correct_answer": "B",
                    "explanation": "15% of 80 = 0.15 × 80 = 12"
                }
            ]
        elif section == "Reading":
            return [
                {
                    "id": 1,
                    "question": f"Which word best describes the author's tone? ({difficulty} level)",
                    "options": {
                        "A": "Optimistic",
                        "B": "Pessimistic",
                        "C": "Neutral",
                        "D": "Sarcastic"
                    },
                    "correct_answer": "A",
                    "explanation": "The author uses positive language throughout the passage."
                }
            ]
        else:  # Writing and Language
            return [
                {
                    "id": 1,
                    "question": f"Choose the best revision for the underlined portion. ({difficulty} level)",
                    "options": {
                        "A": "NO CHANGE",
                        "B": "However,",
                        "C": "Therefore,",
                        "D": "Moreover,"
                    },
                    "correct_answer": "B",
                    "explanation": "The sentence shows contrast, so 'However' is appropriate."
                }
            ]
    
    def _format_question(self, question: Dict[str, Any], question_num: int, total_questions: int) -> str:
        """
        Format a SAT question for display
        """
        question_text = question.get('question', 'No question text available')
        options = question.get('options', {})
        
        formatted = f"Question {question_num}/{total_questions}:\n{question_text}\n\n"
        
        # Add options in order
        for key in ['A', 'B', 'C', 'D']:
            if key in options:
                formatted += f"{key}. {options[key]}\n"
        
        formatted += "\nReply with A, B, C, or D"
        
        return formatted