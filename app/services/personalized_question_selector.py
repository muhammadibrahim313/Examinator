import random
import logging
from typing import Dict, Any, List, Optional
from app.utils.helpers import load_exam_data, get_available_subjects, get_available_years
from app.services.user_analytics import UserAnalytics

logger = logging.getLogger(__name__)

class PersonalizedQuestionSelector:
    """
    Service to select questions based on user's performance history and weaknesses
    """
    
    def __init__(self):
        self.analytics = UserAnalytics()
    
    def get_personalized_questions(self, user_phone: str, exam: str, subject: str, 
                                 year: str, num_questions: int = 10) -> List[Dict[str, Any]]:
        """
        Get personalized questions based on user's performance history
        """
        logger.info(f"Getting personalized questions for {user_phone}: {exam} {subject} {year}")
        
        # Load all available questions
        all_questions = load_exam_data(exam, subject, year)
        if not all_questions:
            logger.warning(f"No questions found for {exam} {subject} {year}")
            return []
        
        # Get user's weaknesses
        user_weaknesses = self.analytics.get_user_weaknesses(user_phone)
        
        # Categorize questions by topics
        categorized_questions = self._categorize_questions(all_questions)
        
        # Select questions based on weaknesses and performance
        selected_questions = self._select_targeted_questions(
            categorized_questions, user_weaknesses, num_questions
        )
        
        # If we don't have enough targeted questions, fill with random ones
        if len(selected_questions) < num_questions:
            remaining_questions = [q for q in all_questions if q not in selected_questions]
            random.shuffle(remaining_questions)
            needed = num_questions - len(selected_questions)
            selected_questions.extend(remaining_questions[:needed])
        
        # Shuffle the final selection to avoid predictable patterns
        random.shuffle(selected_questions)
        
        logger.info(f"Selected {len(selected_questions)} personalized questions for {user_phone}")
        return selected_questions[:num_questions]
    
    def get_adaptive_questions(self, user_phone: str, exam: str, subject: str, 
                             current_performance: float) -> List[Dict[str, Any]]:
        """
        Get adaptive questions based on current session performance
        """
        # Get available years for this subject
        years = get_available_years(exam, subject)
        if not years:
            return []
        
        all_questions = []
        for year in years:
            questions = load_exam_data(exam, subject, year)
            all_questions.extend(questions)
        
        if not all_questions:
            return []
        
        # Adjust difficulty based on current performance
        if current_performance >= 0.8:  # 80% or higher - give harder questions
            selected_questions = self._select_challenging_questions(all_questions, 5)
        elif current_performance <= 0.4:  # 40% or lower - give easier questions
            selected_questions = self._select_foundational_questions(all_questions, 5)
        else:  # Medium performance - balanced selection
            selected_questions = self._select_balanced_questions(all_questions, 5)
        
        return selected_questions
    
    def _categorize_questions(self, questions: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Categorize questions by topic/concept
        """
        categorized = {}
        
        for question in questions:
            topic = self._extract_question_topic(question.get("question", ""))
            if topic:
                if topic not in categorized:
                    categorized[topic] = []
                categorized[topic].append(question)
            else:
                # Uncategorized questions
                if "general" not in categorized:
                    categorized["general"] = []
                categorized["general"].append(question)
        
        return categorized
    
    def _select_targeted_questions(self, categorized_questions: Dict[str, List[Dict[str, Any]]], 
                                 user_weaknesses: List[Dict[str, Any]], 
                                 num_questions: int) -> List[Dict[str, Any]]:
        """
        Select questions targeting user's weaknesses
        """
        selected = []
        
        # Calculate how many questions to allocate to each weakness
        if user_weaknesses:
            questions_per_weakness = max(1, num_questions // len(user_weaknesses))
        else:
            questions_per_weakness = 0
        
        # Select questions for each weakness area
        for weakness in user_weaknesses:
            weakness_name = weakness["name"]
            
            # Find matching topic in categorized questions
            matching_questions = []
            for topic, questions in categorized_questions.items():
                if weakness_name.lower() in topic.lower() or topic.lower() in weakness_name.lower():
                    matching_questions.extend(questions)
            
            # Select questions for this weakness
            if matching_questions:
                random.shuffle(matching_questions)
                selected.extend(matching_questions[:questions_per_weakness])
        
        return selected
    
    def _select_challenging_questions(self, questions: List[Dict[str, Any]], 
                                    num_questions: int) -> List[Dict[str, Any]]:
        """
        Select more challenging questions for high-performing users
        """
        # For now, we'll use a simple heuristic - longer questions or those with more complex language
        challenging_questions = []
        
        for question in questions:
            question_text = question.get("question", "")
            # Consider questions with more words as potentially more challenging
            if len(question_text.split()) > 20:
                challenging_questions.append(question)
        
        # If we don't have enough "challenging" questions, use all questions
        if len(challenging_questions) < num_questions:
            challenging_questions = questions.copy()
        
        random.shuffle(challenging_questions)
        return challenging_questions[:num_questions]
    
    def _select_foundational_questions(self, questions: List[Dict[str, Any]], 
                                     num_questions: int) -> List[Dict[str, Any]]:
        """
        Select foundational/easier questions for struggling users
        """
        # For now, we'll use a simple heuristic - shorter questions or those with basic concepts
        foundational_questions = []
        
        for question in questions:
            question_text = question.get("question", "").lower()
            # Look for basic concept keywords
            basic_keywords = ["what is", "define", "which of the following", "basic", "simple"]
            if any(keyword in question_text for keyword in basic_keywords):
                foundational_questions.append(question)
        
        # If we don't have enough "foundational" questions, use all questions
        if len(foundational_questions) < num_questions:
            foundational_questions = questions.copy()
        
        random.shuffle(foundational_questions)
        return foundational_questions[:num_questions]
    
    def _select_balanced_questions(self, questions: List[Dict[str, Any]], 
                                 num_questions: int) -> List[Dict[str, Any]]:
        """
        Select a balanced mix of questions
        """
        random.shuffle(questions)
        return questions[:num_questions]
    
    def _extract_question_topic(self, question_text: str) -> Optional[str]:
        """
        Extract topic/category from question text using keywords
        """
        question_lower = question_text.lower()
        
        # Biology topics
        biology_topics = {
            "cell biology": ["cell", "mitochondria", "nucleus", "organelle", "membrane", "cytoplasm"],
            "genetics": ["dna", "gene", "chromosome", "heredity", "mutation", "allele"],
            "ecology": ["ecosystem", "environment", "population", "habitat", "biodiversity"],
            "photosynthesis": ["photosynthesis", "chloroplast", "light reaction", "calvin cycle"],
            "respiration": ["respiration", "breathing", "oxygen", "carbon dioxide", "atp"],
            "reproduction": ["reproduction", "sexual", "asexual", "gamete", "fertilization"],
            "evolution": ["evolution", "natural selection", "adaptation", "species"],
            "anatomy": ["anatomy", "organ", "system", "tissue", "body"]
        }
        
        # Chemistry topics
        chemistry_topics = {
            "atomic structure": ["atom", "electron", "proton", "neutron", "orbital", "shell"],
            "chemical bonding": ["bond", "ionic", "covalent", "molecular", "valence"],
            "acids and bases": ["acid", "base", "ph", "alkaline", "neutral"],
            "organic chemistry": ["carbon", "hydrocarbon", "alcohol", "organic", "compound"],
            "stoichiometry": ["mole", "molecular weight", "equation", "balance"],
            "thermodynamics": ["enthalpy", "entropy", "energy", "heat", "temperature"]
        }
        
        # Physics topics
        physics_topics = {
            "mechanics": ["force", "motion", "velocity", "acceleration", "momentum"],
            "electricity": ["current", "voltage", "resistance", "circuit", "ohm"],
            "waves": ["wave", "frequency", "amplitude", "sound", "light"],
            "thermodynamics": ["heat", "temperature", "energy", "thermal", "gas"],
            "optics": ["lens", "mirror", "reflection", "refraction", "light"]
        }
        
        # Math topics
        math_topics = {
            "algebra": ["equation", "variable", "solve", "polynomial", "linear"],
            "geometry": ["triangle", "circle", "area", "volume", "angle", "polygon"],
            "calculus": ["derivative", "integral", "limit", "function", "rate"],
            "statistics": ["mean", "median", "mode", "probability", "data"],
            "trigonometry": ["sine", "cosine", "tangent", "angle", "triangle"]
        }
        
        all_topics = {**biology_topics, **chemistry_topics, **physics_topics, **math_topics}
        
        for topic, keywords in all_topics.items():
            if any(keyword in question_lower for keyword in keywords):
                return topic
        
        return "general"
    
    def suggest_study_areas(self, user_phone: str) -> List[str]:
        """
        Suggest study areas based on user's performance
        """
        user_weaknesses = self.analytics.get_user_weaknesses(user_phone, 5)
        suggestions = []
        
        for weakness in user_weaknesses:
            if weakness["type"] == "subject":
                suggestions.append(f"Practice more {weakness['name']} questions")
            elif weakness["type"] == "topic":
                suggestions.append(f"Review {weakness['name']} concepts and practice related questions")
        
        if not suggestions:
            suggestions.append("Continue practicing regularly to maintain your performance")
        
        return suggestions