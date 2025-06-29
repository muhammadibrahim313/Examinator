import os
import asyncio
import logging
from typing import Dict, Any, Optional
from langchain_core.messages import HumanMessage
from app.agent_reflection.RAG_reflection import agent, hybrid_manager
from app.services.user_analytics import UserAnalytics
from app.services.personalized_question_selector import PersonalizedQuestionSelector
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class EnhancedLLMAgentService:
    """
    Enhanced LLM agent service with personalized learning capabilities
    """
    
    def __init__(self):
        self.agent = agent
        self.config = {"recursion_limit": 50}
        self.analytics = UserAnalytics()
        self.question_selector = PersonalizedQuestionSelector()
        self._validate_environment()
    
    def _validate_environment(self):
        """Validate that required environment variables are set"""
        required_vars = ['GOOGLE_API_KEY']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            logger.warning(f"Missing environment variables: {missing_vars}")
            logger.warning("LLM agent may not function properly without these variables")
    
    async def process_message(self, user_phone: str, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Process a message using the enhanced LLM agent with personalization
        """
        try:
            logger.info(f"Processing enhanced LLM message from {user_phone}: {message}")
            
            # Get user's performance data
            user_summary = self.analytics.get_user_progress_summary(user_phone)
            user_weaknesses = self.analytics.get_user_weaknesses(user_phone, 3)
            user_recommendations = self.analytics.get_personalized_recommendations(user_phone)
            
            # Enhance the message with comprehensive context
            enhanced_message = self._enhance_message_with_full_context(
                message, context, user_summary, user_weaknesses, user_recommendations
            )
            
            # Create the input for the agent
            agent_input = {"messages": [HumanMessage(content=enhanced_message)]}
            
            # Process with the agent
            response_chunks = []
            async for chunk in self.agent.astream(agent_input, config=self.config):
                if 'messages' in chunk:
                    for msg in chunk['messages']:
                        if hasattr(msg, 'content') and msg.content:
                            response_chunks.append(msg.content)
                            logger.debug(f"Agent chunk: {msg.content[:100]}...")
            
            # Combine all response chunks
            full_response = '\n'.join(response_chunks) if response_chunks else "I'm sorry, I couldn't process your request right now."
            
            # Enhance response with personalized recommendations if appropriate
            enhanced_response = self._enhance_response_with_personalization(
                full_response, message, user_phone, context
            )
            
            # Clean and format the response for WhatsApp
            formatted_response = self._format_response_for_whatsapp(enhanced_response)
            
            logger.info(f"Enhanced LLM response for {user_phone}: {formatted_response[:100]}...")
            return formatted_response
            
        except Exception as e:
            logger.error(f"Error processing enhanced LLM message from {user_phone}: {str(e)}", exc_info=True)
            
            # Check hybrid model status for better error messages
            stats = hybrid_manager.get_stats()
            logger.info(f"Hybrid model stats during error: {stats}")
            
            # Provide more helpful error responses based on the context
            if "hello" in message.lower() or "hi" in message.lower():
                return "Hello! 👋 I'm your personalized Exam Practice Bot. Send 'start' to begin practicing with AI-powered question selection!"
            elif context and context.get('exam'):
                exam_name = context.get('exam', '').upper()
                return f"I'm having trouble processing that request. You're practicing for {exam_name}. Send 'restart' to start over or try a different approach."
            else:
                return "I'm experiencing technical difficulties right now. Please send 'start' to begin exam practice or try again in a moment."
    
    def _enhance_message_with_full_context(self, message: str, context: Optional[Dict[str, Any]], 
                                         user_summary: Dict[str, Any], user_weaknesses: list, 
                                         user_recommendations: list) -> str:
        """
        Enhance the user message with comprehensive context including performance data and greeting handling
        """
        context_parts = []
        
        # Special handling for greetings
        if context and context.get('is_greeting'):
            context_parts.append(f"GREETING CONTEXT: {context.get('greeting_context', 'General greeting')}")
            context_parts.append(f"Bot Role: {context.get('bot_role', 'exam practice assistant')}")
            context_parts.append(f"Available Exams: {', '.join(context.get('available_exams', []))}")
            
            # Current user stage context for greetings
            stage = context.get('user_stage', 'initial')
            if stage == 'initial':
                context_parts.append("USER STATUS: New user - encourage them to start practicing")
            elif stage == 'selecting_exam':
                context_parts.append("USER STATUS: Currently selecting an exam - provide help")
            elif context.get('exam'):
                exam = context.get('exam', '').upper()
                context_parts.append(f"USER STATUS: Practicing for {exam} - provide supportive encouragement")
        
        # Basic exam context
        if context:
            if context.get('exam'):
                context_parts.append(f"User is practicing for {context['exam'].upper()} exam")
            
            if context.get('subject'):
                context_parts.append(f"Subject: {context['subject']}")
            
            if context.get('year'):
                context_parts.append(f"Year: {context['year']}")
            
            if context.get('current_question_index') is not None and context.get('total_questions'):
                current = context['current_question_index'] + 1
                total = context['total_questions']
                context_parts.append(f"Currently on question {current} of {total}")
            
            if context.get('score') is not None:
                context_parts.append(f"Current score: {context['score']}")
        
        # Performance context
        if user_summary.get('total_sessions', 0) > 0:
            context_parts.append(f"User has completed {user_summary['total_sessions']} practice sessions")
            context_parts.append(f"Overall accuracy: {user_summary['recent_performance']}")
            context_parts.append(f"Performance trend: {user_summary['improvement_trend']}")
        
        # Weakness context
        if user_weaknesses:
            weakness_names = [w['name'] for w in user_weaknesses[:3]]
            context_parts.append(f"User's main weakness areas: {', '.join(weakness_names)}")
        
        # Recommendations context
        if user_recommendations:
            context_parts.append(f"Current recommendations: {'; '.join(user_recommendations[:2])}")
        
        if context_parts:
            context_info = " | ".join(context_parts)
            
            # Special system prompt for greetings
            if context and context.get('is_greeting'):
                system_prompt = """
You are a friendly exam practice assistant! 🎓 

CRITICAL RESPONSE RULES:
- MAXIMUM 50 WORDS per response
- Be warm and encouraging
- Use 1-2 emojis maximum
- Mention available exams: JAMB, SAT, NEET
- Provide ONE clear next step
- Keep it conversational and brief

WORD LIMIT: Your response must be under 50 words total!
"""
                enhanced_message = f"{system_prompt}\n\n[USER CONTEXT: {context_info}]\n\nUser message: {message}"
            else:
                # General system prompt for non-greeting queries
                general_prompt = """
You are a helpful exam practice assistant. 

CRITICAL RESPONSE RULES:
- MAXIMUM 50 WORDS per response
- Be direct and helpful
- Use 1-2 emojis if appropriate
- Keep responses brief and actionable
- Focus on exam practice for JAMB, SAT, NEET

WORD LIMIT: Your response must be under 50 words total!
"""
                enhanced_message = f"{general_prompt}\n\n[USER CONTEXT: {context_info}]\n\nUser message: {message}"
            
            return enhanced_message
        
        return message
    
    def _enhance_response_with_personalization(self, response: str, original_message: str, 
                                             user_phone: str, context: Optional[Dict[str, Any]]) -> str:
        """
        Enhance the response with personalized recommendations and study tips
        """
        # Check if user is asking for help or study advice
        help_keywords = ['help', 'study', 'improve', 'practice', 'recommend', 'suggest', 'tips']
        if any(keyword in original_message.lower() for keyword in help_keywords):
            
            # Add personalized study suggestions
            study_suggestions = self.question_selector.suggest_study_areas(user_phone)
            if study_suggestions:
                response += f"\n\n📚 Personalized Study Suggestions:\n"
                for i, suggestion in enumerate(study_suggestions[:3], 1):
                    response += f"{i}. {suggestion}\n"
        
        # If user is in an exam session, provide performance-based encouragement
        if context and context.get('stage') == 'taking_exam':
            current_score = context.get('score', 0)
            current_question = context.get('current_question_index', 0) + 1
            
            if current_question > 3:  # After a few questions
                accuracy = current_score / current_question
                if accuracy >= 0.8:
                    response += f"\n\n🎉 Excellent work! You're scoring {accuracy:.1%} so far!"
                elif accuracy >= 0.6:
                    response += f"\n\n👍 Good progress! Current accuracy: {accuracy:.1%}"
                else:
                    response += f"\n\n💪 Keep going! Remember to review the explanations carefully."
        
        return response
    
    def _format_response_for_whatsapp(self, response: str) -> str:
        """
        Format the agent response for WhatsApp delivery with 50-word limit
        """
        # Remove excessive formatting that doesn't work well in WhatsApp
        formatted = response.strip()
        
        # Clean up any problematic characters or formatting
        formatted = formatted.replace('```', '').replace('**', '*')
        
        # Enforce 50-word limit
        formatted = self._enforce_word_limit(formatted, 50)
        
        return formatted
    
    def _enforce_word_limit(self, text: str, max_words: int) -> str:
        """
        Enforce word limit on response text
        """
        words = text.split()
        word_count = len(words)
        
        if word_count <= max_words:
            return text
        
        # Truncate to word limit and add indicator
        truncated_words = words[:max_words-2]  # Save space for "..."
        truncated_text = ' '.join(truncated_words) + "..."
        
        logger.info(f"Response truncated from {word_count} to {len(truncated_words)} words")
        return truncated_text
    
    def _count_words(self, text: str) -> int:
        """
        Count words in text (excluding emojis)
        """
        # Remove emojis and special characters for accurate word count
        import re
        clean_text = re.sub(r'[^\w\s]', ' ', text)
        words = clean_text.split()
        return len(words)
    
    def is_exam_related_query(self, message: str) -> bool:
        """
        Check if the message is related to exam practice
        """
        exam_keywords = [
            'exam', 'test', 'question', 'answer', 'jamb', 'sat', 'waec',
            'biology', 'chemistry', 'physics', 'math', 'english',
            'practice', 'study', 'score', 'result', 'performance',
            'weakness', 'strength', 'improve', 'help'
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in exam_keywords)
    
    async def get_performance_summary(self, user_phone: str) -> str:
        """
        Generate a comprehensive performance summary for the user
        """
        try:
            user_summary = self.analytics.get_user_progress_summary(user_phone)
            
            if user_summary['total_sessions'] == 0:
                return "You haven't completed any practice sessions yet. Send 'start' to begin your first exam practice!"
            
            summary_text = f"📊 Your Performance Summary:\n\n"
            summary_text += f"• Total Sessions: {user_summary['total_sessions']}\n"
            summary_text += f"• Questions Answered: {user_summary['total_questions']}\n"
            summary_text += f"• Recent Accuracy: {user_summary['recent_performance']}\n"
            summary_text += f"• Trend: {user_summary['improvement_trend']}\n\n"
            
            if user_summary.get('weaknesses'):
                summary_text += "🎯 Areas to Focus On:\n"
                for weakness in user_summary['weaknesses'][:3]:
                    summary_text += f"• {weakness['name']} ({weakness['accuracy']:.1%} accuracy)\n"
                summary_text += "\n"
            
            if user_summary.get('strengths'):
                summary_text += "💪 Your Strengths:\n"
                for strength in user_summary['strengths'][:2]:
                    summary_text += f"• {strength['name']} ({strength['accuracy']:.1%} accuracy)\n"
                summary_text += "\n"
            
            recommendations = self.analytics.get_personalized_recommendations(user_phone)
            if recommendations:
                summary_text += "📚 Recommendations:\n"
                for i, rec in enumerate(recommendations[:3], 1):
                    summary_text += f"{i}. {rec}\n"
            
            return summary_text
            
        except Exception as e:
            logger.error(f"Error generating performance summary for {user_phone}: {e}")
            return "Sorry, I couldn't generate your performance summary right now. Please try again later."