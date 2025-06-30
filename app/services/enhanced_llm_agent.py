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
    Enhanced LLM agent service with FIXED response processing
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
        Process a message using the enhanced LLM agent with FIXED response handling
        """
        try:
            logger.info(f"Processing enhanced LLM message from {user_phone}: {message}")
            
            # Get user's performance data
            user_summary = self.analytics.get_user_progress_summary(user_phone)
            user_weaknesses = self.analytics.get_user_weaknesses(user_phone, 3)
            user_recommendations = self.analytics.get_personalized_recommendations(user_phone)
            
            # Enhance the message with comprehensive context including FAQ capabilities
            enhanced_message = self._enhance_message_with_full_context(
                message, context, user_summary, user_weaknesses, user_recommendations
            )
            
            # Create the input for the agent
            agent_input = {"messages": [HumanMessage(content=enhanced_message)]}
            
            # FIXED: Process with the agent and collect ALL response content
            response_chunks = []
            final_messages = []
            
            logger.info(f"🤖 Starting LLM agent processing for: {message}")
            
            async for chunk in self.agent.astream(agent_input, config=self.config):
                logger.debug(f"📦 Agent chunk received: {list(chunk.keys())}")
                
                # Collect messages from different possible locations
                if 'messages' in chunk:
                    for msg in chunk['messages']:
                        if hasattr(msg, 'content') and msg.content:
                            logger.debug(f"✅ Found message content: {msg.content[:100]}...")
                            response_chunks.append(msg.content)
                            final_messages.append(msg)
                
                # Also check for agent-specific message format
                if 'agent' in chunk and 'messages' in chunk['agent']:
                    for msg in chunk['agent']['messages']:
                        if hasattr(msg, 'content') and msg.content:
                            logger.debug(f"✅ Found agent message content: {msg.content[:100]}...")
                            response_chunks.append(msg.content)
                            final_messages.append(msg)
            
            logger.info(f"📝 LLM agent processing complete: {len(response_chunks)} response chunks collected")
            
            # FIXED: Process the final response properly
            if response_chunks:
                # Get the last meaningful response (usually the final answer)
                final_response = response_chunks[-1] if response_chunks else ""
                
                # Log what we got
                logger.info(f"📤 Final LLM response length: {len(final_response)} characters")
                logger.info(f"📤 Final LLM response preview: {final_response[:200]}...")
                
                # FIXED: Don't apply word limits or truncation to LLM responses
                # The LLM should handle its own response length
                formatted_response = self._format_response_for_whatsapp(final_response)
                
                logger.info(f"✅ Enhanced LLM response for {user_phone}: SUCCESS")
                return formatted_response
            
            else:
                logger.error(f"❌ LLM AGENT FAILED: No response chunks collected for {user_phone}")
                return self._get_fallback_response(message, context)
            
        except Exception as e:
            logger.error(f"❌ Error processing enhanced LLM message from {user_phone}: {str(e)}", exc_info=True)
            
            # Check hybrid model status for better error messages
            stats = hybrid_manager.get_stats()
            logger.info(f"🤖 Hybrid model stats during error: {stats}")
            
            return self._get_fallback_response(message, context)
    
    def _enhance_message_with_full_context(self, message: str, context: Optional[Dict[str, Any]], 
                                         user_summary: Dict[str, Any], user_weaknesses: list, 
                                         user_recommendations: list) -> str:
        """
        Enhance the user message with comprehensive context
        """
        context_parts = []
        
        # Determine message type for appropriate system prompt
        message_type = self._classify_message_type(message, context)
        
        # Get appropriate system prompt based on message type
        system_prompt = self._get_system_prompt_for_type(message_type)
        
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
            
            # Add stage context for better help
            stage = context.get('stage', 'initial')
            context_parts.append(f"Current stage: {stage}")
        
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
            enhanced_message = f"{system_prompt}\n\n[USER CONTEXT: {context_info}]\n\nUser message: {message}"
            return enhanced_message
        
        return f"{system_prompt}\n\nUser message: {message}"
    
    def _classify_message_type(self, message: str, context: Optional[Dict[str, Any]]) -> str:
        """Classify the type of message for appropriate handling"""
        message_lower = message.lower().strip()
        
        # FAQ and help requests
        if any(word in message_lower for word in ['help', 'faq', 'how', 'what', 'why', 'explain']):
            return 'faq_help'
        
        # Navigation requests
        if any(word in message_lower for word in ['back', 'previous', 'return', 'go back']):
            return 'navigation'
        
        # Performance queries
        if any(word in message_lower for word in ['performance', 'score', 'progress', 'stats']):
            return 'performance'
        
        # Test control
        if any(word in message_lower for word in ['stop', 'quit', 'submit', 'exit']):
            return 'test_control'
        
        # Greetings
        if context and context.get('is_greeting'):
            return 'greeting'
        
        # General queries during exam
        if context and context.get('stage') == 'taking_exam':
            return 'exam_query'
        
        return 'general'
    
    def _get_system_prompt_for_type(self, message_type: str) -> str:
        """Get appropriate system prompt based on message type"""
        base_rules = """
You are a helpful exam practice assistant specializing in JAMB, SAT, and NEET exams.

RESPONSE GUIDELINES:
- Be helpful, informative, and encouraging
- Provide practical advice and explanations
- Use emojis appropriately to make responses friendly
- Focus on exam practice and study guidance
- Keep responses conversational but informative
"""
        
        if message_type == 'faq_help':
            return f"""
{base_rules}

HELP SPECIALIZATION:
- Provide clear, step-by-step guidance
- Explain available commands and features
- Help with navigation and exam practice
- Answer questions about JAMB, SAT, NEET exams
- Explain practice modes (topic, year, mixed, weak areas)
- Give study tips and strategies
"""
        
        elif message_type == 'performance':
            return f"""
{base_rules}

PERFORMANCE SPECIALIZATION:
- Analyze user performance data
- Provide encouraging feedback
- Suggest improvement strategies
- Highlight strengths and weaknesses
- Give personalized study recommendations
"""
        
        elif message_type == 'exam_query':
            return f"""
{base_rules}

EXAM ASSISTANCE:
- Answer questions about current exam content
- Provide study tips and explanations
- Help with exam strategies
- Encourage continued practice
- Explain difficult concepts
"""
        
        elif message_type == 'greeting':
            return f"""
{base_rules}

GREETING SPECIALIZATION:
- Be warm and welcoming
- Mention available exams: JAMB, SAT, NEET
- Provide clear next steps
- Keep it conversational and encouraging
"""
        
        else:  # general
            return f"""
{base_rules}

GENERAL ASSISTANCE:
- Be direct and helpful
- Focus on exam practice guidance
- Provide clear next steps
- Answer questions about the platform
- Give study advice when appropriate
"""
    
    def _get_fallback_response(self, message: str, context: Optional[Dict[str, Any]]) -> str:
        """Get fallback response when LLM fails"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['hello', 'hi', 'hey']):
            return "Hello! 👋 I'm your Exam Practice Bot. Send 'start' to begin practicing for JAMB, SAT, or NEET exams!"
        
        elif any(word in message_lower for word in ['help', 'faq']):
            return self._get_fallback_help_response(context)
        
        elif any(word in message_lower for word in ['duplicate', 'repeat', 'same']):
            return "📚 About duplicate questions:\n\nSometimes you might see similar questions because:\n• Real exams often test the same concepts\n• Questions come from multiple years\n• Important topics appear frequently\n\nThis helps reinforce learning! 💪"
        
        elif context and context.get('exam'):
            exam_name = context.get('exam', '').upper()
            return f"I'm having trouble processing that request about {exam_name}. Send 'help' for available commands or try rephrasing your question."
        
        else:
            return "I'm having a technical issue right now. Please send 'help' for available commands or try again in a moment."
    
    def _get_fallback_help_response(self, context: Optional[Dict[str, Any]]) -> str:
        """Get fallback help response when LLM fails"""
        stage = context.get('stage', 'initial') if context else 'initial'
        
        response = "🆘 **Help**\n\n"
        
        if stage == 'taking_exam':
            response += "📝 **During Exam:**\n"
            response += "• A, B, C, D - Answer questions\n"
            response += "• 'stop' - Stop test\n"
            response += "• 'submit' - Submit progress\n"
        else:
            response += "🔧 **Commands:**\n"
            response += "• 'start' - Begin practice\n"
            response += "• 'back' - Previous step\n"
            response += "• 'restart' - Start over\n"
        
        response += "\n💡 Ask me anything about exam practice!"
        return response
    
    def _format_response_for_whatsapp(self, response: str) -> str:
        """
        Format the agent response for WhatsApp delivery - FIXED: No truncation
        """
        # Remove excessive formatting that doesn't work well in WhatsApp
        formatted = response.strip()
        
        # Clean up any problematic characters or formatting
        formatted = formatted.replace('```', '').replace('**', '*')
        
        # FIXED: Don't truncate LLM responses - let them be full length
        # The LLM should handle appropriate response length
        
        return formatted
    
    def is_exam_related_query(self, message: str) -> bool:
        """
        Check if the message is related to exam practice
        """
        exam_keywords = [
            'exam', 'test', 'question', 'answer', 'jamb', 'sat', 'neet',
            'biology', 'chemistry', 'physics', 'math', 'english',
            'practice', 'study', 'score', 'result', 'performance',
            'weakness', 'strength', 'improve', 'help', 'faq', 'duplicate'
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