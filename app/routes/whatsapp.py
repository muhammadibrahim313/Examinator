from fastapi import APIRouter, Form, Request
from fastapi.responses import Response
from twilio.twiml.messaging_response import MessagingResponse
from app.services.enhanced_state import EnhancedUserStateManager
from app.services.exam_registry import ExamRegistry
from app.core.enhanced_smart_processor import EnhancedSmartMessageProcessor
import logging
import asyncio

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize enhanced components
state_manager = EnhancedUserStateManager()
exam_registry = ExamRegistry()
smart_message_processor = EnhancedSmartMessageProcessor(state_manager, exam_registry)

@router.post("/whatsapp")
async def whatsapp_webhook(
    request: Request,
    From: str = Form(...),
    Body: str = Form(...),
    To: str = Form(...)
):
    """
    Enhanced WhatsApp webhook handler with async question loading support
    """
    logger.info(f"Received message from {From}: {Body}")
    
    # Create Twilio response
    response = MessagingResponse()
    msg = response.message()
    
    # Extract user phone number
    user_phone = From.replace('whatsapp:', '')
    message_body = Body.strip()
    
    try:
        # FIXED: Check if user is in async loading state and trigger loading
        user_state = state_manager.get_user_state(user_phone)
        current_stage = user_state.get('stage', 'initial')
        
        if current_stage == 'async_loading':
            logger.info(f"🔄 ASYNC TRIGGER: User {user_phone} in async_loading stage, triggering question fetch")
            
            # Trigger async loading immediately
            response_text = await smart_message_processor._handle_async_loading(user_phone, user_state)
            msg.body(response_text)
            
        else:
            # Process the message using our enhanced smart processor
            response_text = await smart_message_processor.process_message(user_phone, message_body)
            msg.body(response_text)
            
            # FIXED: If response indicates async loading started, trigger it immediately
            updated_state = state_manager.get_user_state(user_phone)
            if updated_state.get('stage') == 'async_loading':
                logger.info(f"🔄 IMMEDIATE ASYNC: Triggering immediate async loading for {user_phone}")
                
                # Wait a moment for state to settle, then trigger loading
                await asyncio.sleep(0.1)
                
                # Trigger the async loading
                loading_response = await smart_message_processor._handle_async_loading(user_phone, updated_state)
                
                # Send the loading response as a follow-up message
                # Note: In a real implementation, you might want to use Twilio's API to send this as a separate message
                # For now, we'll replace the original response
                msg.body(loading_response)
        
    except Exception as e:
        logger.error(f"Error processing message from {user_phone}: {str(e)}", exc_info=True)
        msg.body("Sorry, something went wrong. Please try again or send 'restart' to start over.")
    
    return Response(content=str(response), media_type="application/xml")

@router.get("/whatsapp")
async def whatsapp_webhook_verify():
    """
    Webhook verification endpoint
    """
    return {"message": "WhatsApp webhook endpoint is ready with enhanced personalized learning and async question loading"}

@router.get("/analytics/{user_phone}")
async def get_user_analytics(user_phone: str):
    """
    API endpoint to get user analytics (for debugging/admin purposes)
    """
    try:
        # Clean phone number
        clean_phone = user_phone.replace('+', '').replace('-', '').replace(' ', '')
        
        # Get user performance summary
        performance_summary = state_manager.get_user_performance_summary(clean_phone)
        
        return {
            "user_phone": user_phone,
            "performance_summary": performance_summary,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Error getting analytics for {user_phone}: {e}")
        return {
            "user_phone": user_phone,
            "error": str(e),
            "status": "error"
        }

@router.post("/trigger-loading/{user_phone}")
async def trigger_async_loading(user_phone: str):
    """
    Manual endpoint to trigger async loading for testing
    """
    try:
        clean_phone = user_phone.replace('+', '').replace('-', '').replace(' ', '')
        user_state = state_manager.get_user_state(clean_phone)
        
        if user_state.get('stage') == 'async_loading':
            response_text = await smart_message_processor._handle_async_loading(clean_phone, user_state)
            return {
                "user_phone": user_phone,
                "response": response_text,
                "status": "success"
            }
        else:
            return {
                "user_phone": user_phone,
                "error": f"User not in async_loading stage. Current stage: {user_state.get('stage')}",
                "status": "error"
            }
    except Exception as e:
        logger.error(f"Error triggering async loading for {user_phone}: {e}")
        return {
            "user_phone": user_phone,
            "error": str(e),
            "status": "error"
        }