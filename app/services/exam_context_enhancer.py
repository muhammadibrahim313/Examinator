import logging
from typing import Dict, Any, Optional, List
from app.utils.helpers import load_exam_data

logger = logging.getLogger(__name__)

class ExamContextEnhancer:
    """
    Service to enhance LLM responses with exam-specific context and knowledge
    """
    
    def __init__(self):
        self.exam_knowledge_cache = {}
    
    def get_exam_context(self, user_state: Dict[str, Any]) -> str:
        """
        Generate contextual information about the user's current exam session
        """
        context_parts = []
        
        exam = user_state.get('exam')
        subject = user_state.get('subject')
        year = user_state.get('year')
        stage = user_state.get('stage')
        
        if exam:
            context_parts.append(f"The user is practicing for the {exam.upper()} exam.")
        
        if subject:
            context_parts.append(f"They are studying {subject}.")
        
        if year:
            context_parts.append(f"The exam year is {year}.")
        
        if stage:
            stage_description = self._get_stage_description(stage)
            context_parts.append(f"Current stage: {stage_description}")
        
        # Add current question context if in exam
        if stage == 'taking_exam':
            current_q = user_state.get('current_question_index', 0)
            total_q = user_state.get('total_questions', 0)
            score = user_state.get('score', 0)
            
            if total_q > 0:
                context_parts.append(f"Question {current_q + 1} of {total_q}, current score: {score}/{current_q + 1}")
        
        return " ".join(context_parts) if context_parts else "User is starting their exam practice session."
    
    def get_current_question_context(self, user_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get the current question being answered
        """
        questions = user_state.get('questions', [])
        current_index = user_state.get('current_question_index', 0)
        
        if questions and 0 <= current_index < len(questions):
            return questions[current_index]
        
        return None
    
    def get_subject_knowledge(self, exam: str, subject: str) -> str:
        """
        Get general knowledge about a subject for the exam
        """
        cache_key = f"{exam}_{subject}"
        
        if cache_key in self.exam_knowledge_cache:
            return self.exam_knowledge_cache[cache_key]
        
        # Generate subject-specific knowledge
        knowledge = self._generate_subject_knowledge(exam, subject)
        self.exam_knowledge_cache[cache_key] = knowledge
        
        return knowledge
    
    def _get_stage_description(self, stage: str) -> str:
        """
        Get human-readable description of the current stage
        """
        stage_descriptions = {
            'initial': 'Starting the bot',
            'selecting_exam': 'Choosing which exam to practice',
            'selecting_subject': 'Choosing a subject',
            'selecting_year': 'Choosing an exam year',
            'selecting_section': 'Choosing an exam section',
            'selecting_difficulty': 'Choosing difficulty level',
            'taking_exam': 'Currently taking the practice exam',
            'completed': 'Exam session completed'
        }
        
        return stage_descriptions.get(stage, f'In stage: {stage}')
    
    def _generate_subject_knowledge(self, exam: str, subject: str) -> str:
        """
        Generate subject-specific knowledge for better LLM responses
        """
        knowledge_base = {
            'jamb': {
                'biology': "JAMB Biology covers topics like cell biology, genetics, ecology, evolution, plant and animal physiology, and human anatomy. Focus on understanding concepts rather than memorization.",
                'chemistry': "JAMB Chemistry includes atomic structure, chemical bonding, acids and bases, organic chemistry, and chemical calculations. Practice balancing equations and understanding chemical reactions.",
                'physics': "JAMB Physics covers mechanics, waves, electricity, magnetism, and modern physics. Focus on understanding formulas and their applications.",
                'mathematics': "JAMB Mathematics includes algebra, geometry, trigonometry, calculus, and statistics. Practice problem-solving techniques and formula applications."
            },
            'sat': {
                'math': "SAT Math covers algebra, geometry, trigonometry, and data analysis. Focus on problem-solving strategies and time management.",
                'reading': "SAT Reading tests comprehension, analysis, and reasoning skills with passages from literature, history, and science.",
                'writing': "SAT Writing and Language focuses on grammar, usage, and rhetorical skills in context."
            }
        }
        
        exam_subjects = knowledge_base.get(exam.lower(), {})
        return exam_subjects.get(subject.lower(), f"General knowledge for {exam.upper()} {subject} exam preparation.")
    
    def enhance_question_explanation(self, question: Dict[str, Any], user_answer: str, is_correct: bool) -> str:
        """
        Enhance question explanations with additional context
        """
        base_explanation = question.get('explanation', 'No explanation available.')
        
        if not is_correct:
            enhancement = f"\n\n💡 Study Tip: {self._get_study_tip_for_question(question)}"
            return base_explanation + enhancement
        
        return base_explanation
    
    def _get_study_tip_for_question(self, question: Dict[str, Any]) -> str:
        """
        Generate study tips based on question content
        """
        question_text = question.get('question', '').lower()
        
        # Basic keyword-based tips
        if 'cell' in question_text or 'mitochondria' in question_text:
            return "Review cell structure and organelle functions. Draw diagrams to help memorize."
        elif 'equation' in question_text or 'solve' in question_text:
            return "Practice similar problems and review the step-by-step solution method."
        elif 'definition' in question_text or 'meaning' in question_text:
            return "Create flashcards for key terms and their definitions."
        else:
            return "Review the related topic in your textbook and practice similar questions."