import json
import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import statistics

logger = logging.getLogger(__name__)

class UserAnalytics:
    """
    Service to track user performance, identify weaknesses, and provide personalized recommendations
    """
    
    def __init__(self):
        self.data_dir = "app/data/user_analytics"
        self.ensure_data_directory()
    
    def ensure_data_directory(self):
        """Ensure the analytics data directory exists"""
        os.makedirs(self.data_dir, exist_ok=True)
    
    def get_user_file_path(self, user_phone: str) -> str:
        """Get the file path for user's analytics data"""
        # Clean phone number for filename
        clean_phone = user_phone.replace('+', '').replace('-', '').replace(' ', '')
        return os.path.join(self.data_dir, f"{clean_phone}_analytics.json")
    
    def load_user_analytics(self, user_phone: str) -> Dict[str, Any]:
        """Load user's analytics data"""
        file_path = self.get_user_file_path(user_phone)
        
        if not os.path.exists(file_path):
            return self._create_initial_analytics()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading analytics for {user_phone}: {e}")
            return self._create_initial_analytics()
    
    def save_user_analytics(self, user_phone: str, analytics_data: Dict[str, Any]):
        """Save user's analytics data"""
        file_path = self.get_user_file_path(user_phone)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(analytics_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving analytics for {user_phone}: {e}")
    
    def _create_initial_analytics(self) -> Dict[str, Any]:
        """Create initial analytics structure for a new user"""
        return {
            "user_profile": {
                "first_seen": datetime.now().isoformat(),
                "last_active": datetime.now().isoformat(),
                "total_sessions": 0,
                "total_questions_answered": 0,
                "preferred_exams": [],
                "preferred_subjects": []
            },
            "performance_history": [],
            "subject_performance": {},
            "topic_performance": {},
            "weakness_areas": [],
            "strength_areas": [],
            "learning_patterns": {
                "best_time_of_day": None,
                "average_session_length": 0,
                "preferred_difficulty": "medium"
            },
            "recommendations": []
        }
    
    def record_session(self, user_phone: str, session_data: Dict[str, Any]):
        """Record a completed exam session"""
        analytics = self.load_user_analytics(user_phone)
        
        # Update user profile
        analytics["user_profile"]["last_active"] = datetime.now().isoformat()
        analytics["user_profile"]["total_sessions"] += 1
        analytics["user_profile"]["total_questions_answered"] += session_data.get("total_questions", 0)
        
        # Track preferred exams and subjects
        exam = session_data.get("exam")
        subject = session_data.get("subject")
        
        if exam and exam not in analytics["user_profile"]["preferred_exams"]:
            analytics["user_profile"]["preferred_exams"].append(exam)
        
        if subject and subject not in analytics["user_profile"]["preferred_subjects"]:
            analytics["user_profile"]["preferred_subjects"].append(subject)
        
        # Record performance history
        performance_record = {
            "timestamp": datetime.now().isoformat(),
            "exam": exam,
            "subject": subject,
            "year": session_data.get("year"),
            "total_questions": session_data.get("total_questions", 0),
            "correct_answers": session_data.get("score", 0),
            "percentage": (session_data.get("score", 0) / session_data.get("total_questions", 1)) * 100,
            "time_taken": session_data.get("time_taken", 0),
            "question_details": session_data.get("question_details", [])
        }
        
        analytics["performance_history"].append(performance_record)
        
        # Update subject performance
        self._update_subject_performance(analytics, performance_record)
        
        # Update topic performance based on individual questions
        self._update_topic_performance(analytics, performance_record)
        
        # Analyze weaknesses and strengths
        self._analyze_performance(analytics)
        
        # Generate recommendations
        self._generate_recommendations(analytics)
        
        # Save updated analytics
        self.save_user_analytics(user_phone, analytics)
        
        logger.info(f"Recorded session for {user_phone}: {exam} {subject} - {performance_record['percentage']:.1f}%")
    
    def record_question_answer(self, user_phone: str, question_data: Dict[str, Any]):
        """Record individual question answer for real-time tracking"""
        analytics = self.load_user_analytics(user_phone)
        
        # Extract question topic/category if available
        topic = self._extract_question_topic(question_data.get("question", ""))
        
        if topic:
            if topic not in analytics["topic_performance"]:
                analytics["topic_performance"][topic] = {
                    "total_attempts": 0,
                    "correct_answers": 0,
                    "recent_performance": []
                }
            
            analytics["topic_performance"][topic]["total_attempts"] += 1
            
            if question_data.get("is_correct", False):
                analytics["topic_performance"][topic]["correct_answers"] += 1
            
            # Keep recent performance (last 10 attempts)
            recent = analytics["topic_performance"][topic]["recent_performance"]
            recent.append({
                "timestamp": datetime.now().isoformat(),
                "correct": question_data.get("is_correct", False)
            })
            
            if len(recent) > 10:
                recent.pop(0)
        
        self.save_user_analytics(user_phone, analytics)
    
    def get_user_weaknesses(self, user_phone: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get user's top weakness areas"""
        analytics = self.load_user_analytics(user_phone)
        
        weaknesses = []
        
        # Analyze subject weaknesses
        for subject, performance in analytics["subject_performance"].items():
            if performance["total_attempts"] >= 3:  # Minimum attempts for reliable data
                accuracy = performance["correct_answers"] / performance["total_attempts"]
                if accuracy < 0.7:  # Less than 70% accuracy
                    weaknesses.append({
                        "type": "subject",
                        "name": subject,
                        "accuracy": accuracy,
                        "attempts": performance["total_attempts"],
                        "priority": 1.0 - accuracy  # Higher priority for lower accuracy
                    })
        
        # Analyze topic weaknesses
        for topic, performance in analytics["topic_performance"].items():
            if performance["total_attempts"] >= 2:
                accuracy = performance["correct_answers"] / performance["total_attempts"]
                if accuracy < 0.6:  # Less than 60% accuracy for topics
                    weaknesses.append({
                        "type": "topic",
                        "name": topic,
                        "accuracy": accuracy,
                        "attempts": performance["total_attempts"],
                        "priority": 1.0 - accuracy
                    })
        
        # Sort by priority and return top weaknesses
        weaknesses.sort(key=lambda x: x["priority"], reverse=True)
        return weaknesses[:limit]
    
    def get_user_strengths(self, user_phone: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Get user's top strength areas"""
        analytics = self.load_user_analytics(user_phone)
        
        strengths = []
        
        # Analyze subject strengths
        for subject, performance in analytics["subject_performance"].items():
            if performance["total_attempts"] >= 3:
                accuracy = performance["correct_answers"] / performance["total_attempts"]
                if accuracy >= 0.8:  # 80% or higher accuracy
                    strengths.append({
                        "type": "subject",
                        "name": subject,
                        "accuracy": accuracy,
                        "attempts": performance["total_attempts"]
                    })
        
        # Sort by accuracy
        strengths.sort(key=lambda x: x["accuracy"], reverse=True)
        return strengths[:limit]
    
    def get_personalized_recommendations(self, user_phone: str) -> List[str]:
        """Get personalized study recommendations"""
        analytics = self.load_user_analytics(user_phone)
        return analytics.get("recommendations", [])
    
    def get_user_progress_summary(self, user_phone: str) -> Dict[str, Any]:
        """Get comprehensive user progress summary"""
        analytics = self.load_user_analytics(user_phone)
        
        # Calculate overall statistics
        total_sessions = analytics["user_profile"]["total_sessions"]
        total_questions = analytics["user_profile"]["total_questions_answered"]
        
        if not analytics["performance_history"]:
            return {
                "total_sessions": total_sessions,
                "total_questions": total_questions,
                "overall_accuracy": 0,
                "recent_performance": "No data available",
                "improvement_trend": "No data available"
            }
        
        # Calculate overall accuracy
        recent_sessions = analytics["performance_history"][-10:]  # Last 10 sessions
        if recent_sessions:
            recent_accuracy = statistics.mean([s["percentage"] for s in recent_sessions])
        else:
            recent_accuracy = 0
        
        # Calculate improvement trend
        if len(analytics["performance_history"]) >= 5:
            early_sessions = analytics["performance_history"][:5]
            late_sessions = analytics["performance_history"][-5:]
            
            early_avg = statistics.mean([s["percentage"] for s in early_sessions])
            late_avg = statistics.mean([s["percentage"] for s in late_sessions])
            
            improvement = late_avg - early_avg
            if improvement > 5:
                trend = "Improving"
            elif improvement < -5:
                trend = "Declining"
            else:
                trend = "Stable"
        else:
            trend = "Insufficient data"
        
        return {
            "total_sessions": total_sessions,
            "total_questions": total_questions,
            "overall_accuracy": recent_accuracy,
            "recent_performance": f"{recent_accuracy:.1f}%",
            "improvement_trend": trend,
            "weaknesses": self.get_user_weaknesses(user_phone, 3),
            "strengths": self.get_user_strengths(user_phone, 2)
        }
    
    def _update_subject_performance(self, analytics: Dict[str, Any], performance_record: Dict[str, Any]):
        """Update subject-specific performance data"""
        subject = performance_record["subject"]
        if not subject:
            return
        
        if subject not in analytics["subject_performance"]:
            analytics["subject_performance"][subject] = {
                "total_attempts": 0,
                "correct_answers": 0,
                "total_questions": 0,
                "sessions": []
            }
        
        subject_perf = analytics["subject_performance"][subject]
        subject_perf["total_attempts"] += 1
        subject_perf["correct_answers"] += performance_record["correct_answers"]
        subject_perf["total_questions"] += performance_record["total_questions"]
        
        # Keep session history (last 20 sessions)
        subject_perf["sessions"].append({
            "timestamp": performance_record["timestamp"],
            "percentage": performance_record["percentage"],
            "questions": performance_record["total_questions"]
        })
        
        if len(subject_perf["sessions"]) > 20:
            subject_perf["sessions"].pop(0)
    
    def _update_topic_performance(self, analytics: Dict[str, Any], performance_record: Dict[str, Any]):
        """Update topic-specific performance based on question details"""
        question_details = performance_record.get("question_details", [])
        
        for question_detail in question_details:
            topic = self._extract_question_topic(question_detail.get("question", ""))
            if topic:
                if topic not in analytics["topic_performance"]:
                    analytics["topic_performance"][topic] = {
                        "total_attempts": 0,
                        "correct_answers": 0,
                        "recent_performance": []
                    }
                
                analytics["topic_performance"][topic]["total_attempts"] += 1
                if question_detail.get("is_correct", False):
                    analytics["topic_performance"][topic]["correct_answers"] += 1
    
    def _extract_question_topic(self, question_text: str) -> Optional[str]:
        """Extract topic/category from question text using keywords"""
        question_lower = question_text.lower()
        
        # Biology topics
        biology_topics = {
            "cell biology": ["cell", "mitochondria", "nucleus", "organelle", "membrane"],
            "genetics": ["dna", "gene", "chromosome", "heredity", "mutation"],
            "ecology": ["ecosystem", "environment", "population", "habitat"],
            "photosynthesis": ["photosynthesis", "chloroplast", "light reaction"],
            "respiration": ["respiration", "breathing", "oxygen", "carbon dioxide"],
            "reproduction": ["reproduction", "sexual", "asexual", "gamete"]
        }
        
        # Chemistry topics
        chemistry_topics = {
            "atomic structure": ["atom", "electron", "proton", "neutron", "orbital"],
            "chemical bonding": ["bond", "ionic", "covalent", "molecular"],
            "acids and bases": ["acid", "base", "ph", "alkaline"],
            "organic chemistry": ["carbon", "hydrocarbon", "alcohol", "organic"]
        }
        
        # Physics topics
        physics_topics = {
            "mechanics": ["force", "motion", "velocity", "acceleration"],
            "electricity": ["current", "voltage", "resistance", "circuit"],
            "waves": ["wave", "frequency", "amplitude", "sound"],
            "thermodynamics": ["heat", "temperature", "energy", "thermal"]
        }
        
        # Math topics
        math_topics = {
            "algebra": ["equation", "variable", "solve", "polynomial"],
            "geometry": ["triangle", "circle", "area", "volume", "angle"],
            "calculus": ["derivative", "integral", "limit", "function"]
        }
        
        all_topics = {**biology_topics, **chemistry_topics, **physics_topics, **math_topics}
        
        for topic, keywords in all_topics.items():
            if any(keyword in question_lower for keyword in keywords):
                return topic
        
        return None
    
    def _analyze_performance(self, analytics: Dict[str, Any]):
        """Analyze performance to identify weaknesses and strengths"""
        weaknesses = []
        strengths = []
        
        # Analyze subjects
        for subject, performance in analytics["subject_performance"].items():
            if performance["total_attempts"] >= 2:
                accuracy = performance["correct_answers"] / performance["total_questions"]
                
                if accuracy < 0.6:
                    weaknesses.append(f"{subject} (accuracy: {accuracy:.1%})")
                elif accuracy > 0.8:
                    strengths.append(f"{subject} (accuracy: {accuracy:.1%})")
        
        # Analyze topics
        for topic, performance in analytics["topic_performance"].items():
            if performance["total_attempts"] >= 2:
                accuracy = performance["correct_answers"] / performance["total_attempts"]
                
                if accuracy < 0.5:
                    weaknesses.append(f"{topic} (accuracy: {accuracy:.1%})")
                elif accuracy > 0.9:
                    strengths.append(f"{topic} (accuracy: {accuracy:.1%})")
        
        analytics["weakness_areas"] = weaknesses[:10]  # Top 10 weaknesses
        analytics["strength_areas"] = strengths[:5]    # Top 5 strengths
    
    def _generate_recommendations(self, analytics: Dict[str, Any]):
        """Generate personalized study recommendations"""
        recommendations = []
        
        # Recommendations based on weaknesses
        weaknesses = self.get_user_weaknesses("temp", 3)  # Get top 3 weaknesses
        
        for weakness in weaknesses:
            if weakness["type"] == "subject":
                recommendations.append(f"Focus more practice on {weakness['name']} - current accuracy: {weakness['accuracy']:.1%}")
            elif weakness["type"] == "topic":
                recommendations.append(f"Review {weakness['name']} concepts - you've struggled with this topic")
        
        # Recommendations based on performance trends
        recent_sessions = analytics["performance_history"][-5:]
        if len(recent_sessions) >= 3:
            recent_scores = [s["percentage"] for s in recent_sessions]
            avg_score = statistics.mean(recent_scores)
            
            if avg_score < 60:
                recommendations.append("Consider reviewing fundamental concepts before attempting more questions")
            elif avg_score > 85:
                recommendations.append("Great progress! Try challenging yourself with harder questions")
        
        # Session frequency recommendations
        if analytics["user_profile"]["total_sessions"] > 0:
            last_active = datetime.fromisoformat(analytics["user_profile"]["last_active"])
            days_since_last = (datetime.now() - last_active).days
            
            if days_since_last > 7:
                recommendations.append("Try to practice more regularly - consistency is key to improvement")
        
        analytics["recommendations"] = recommendations[:5]  # Keep top 5 recommendations