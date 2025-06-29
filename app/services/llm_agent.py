import os
import asyncio
import logging
from typing import Dict, Any, Optional
from langchain_core.messages import HumanMessage
from app.agent_reflection.RAG_reflection import agent
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class LLMAgentService:
    """
    Service to handle LLM agent interactions for the WhatsApp bot
    """
    
    def __init__(self):
        self.agent = agent
        self.config = {"recursion_limit": 50}
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
        Process a message using the LLM agent
        
        Args:
            user_phone: User's phone number
            message: User's message
            context: Optional context about the user's exam session
            
        Returns:
            Agent's response
        """
        try:
            logger.info(f"Processing LLM message from {user_phone}: {message}")
            
            # Enhance the message with context if available
            enhanced_message = self._enhance_message_with_context(message, context)
            
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
            
            # Clean and format the response for WhatsApp
            formatted_response = self._format_response_for_whatsapp(full_response)
            
            logger.info(f"LLM response for {user_phone}: {formatted_response[:100]}...")
            return formatted_response
            
        except Exception as e:
            logger.error(f"Error processing LLM message from {user_phone}: {str(e)}", exc_info=True)
            return "I'm sorry, I encountered an error while processing your request. Please try again or contact support."
    
    def _enhance_message_with_context(self, message: str, context: Optional[Dict[str, Any]]) -> str:
        """
        Enhance the user message with exam context if available
        """
        if not context:
            return message
        
        # Add exam context to help the agent understand the user's situation
        context_parts = []
        
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
        
        if context_parts:
            context_info = " | ".join(context_parts)
            enhanced_message = f"[EXAM CONTEXT: {context_info}]\n\nUser message: {message}"
            return enhanced_message
        
        return message
    
    def _format_response_for_whatsapp(self, response: str) -> str:
        """
        Format the agent response for WhatsApp delivery
        """
        # Remove excessive formatting that doesn't work well in WhatsApp
        formatted = response.strip()
        
        # Limit response length for WhatsApp (max ~1600 characters)
        max_length = 1500
        if len(formatted) > max_length:
            formatted = formatted[:max_length] + "...\n\n(Response truncated. Ask me to continue for more details.)"
        
        # Clean up any problematic characters or formatting
        formatted = formatted.replace('```', '').replace('**', '*')
        
        return formatted
    
    def is_exam_related_query(self, message: str) -> bool:
        """
        Check if the message is related to exam practice
        """
        exam_keywords = [
            'exam', 'test', 'question', 'answer', 'jamb', 'sat', 'waec',
            'biology', 'chemistry', 'physics', 'math', 'english',
            'practice', 'study', 'score', 'result'
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in exam_keywords)