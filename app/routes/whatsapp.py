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
    Enhanced WhatsApp webhook handler with personalized learning capabilities
    """
    logger.info(f"Received message from {From}: {Body}")
    
    # Create Twilio response
    response = MessagingResponse()
    msg = response.message()
    
    # Extract user phone number
    user_phone = From.replace('whatsapp:', '')
    message_body = Body.strip()
    
    try:
        # Process the message using our enhanced smart processor
        response_text = await smart_message_processor.process_message(user_phone, message_body)
        msg.body(response_text)
        
    except Exception as e:
        logger.error(f"Error processing message from {user_phone}: {str(e)}", exc_info=True)
        msg.body("Sorry, something went wrong. Please try again or send 'restart' to start over.")
    
    return Response(content=str(response), media_type="application/xml")

@router.get("/whatsapp")
async def whatsapp_webhook_verify():
    """
    Webhook verification endpoint
    """
    return {"message": "WhatsApp webhook endpoint is ready with enhanced personalized learning"}

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