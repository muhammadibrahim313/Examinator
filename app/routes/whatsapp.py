from fastapi import APIRouter, Form, Request
from fastapi.responses import Response
from twilio.twiml.messaging_response import MessagingResponse
from app.services.state import UserStateManager
from app.services.exam_registry import ExamRegistry
from app.core.message_processor import MessageProcessor
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize components
state_manager = UserStateManager()
exam_registry = ExamRegistry()
message_processor = MessageProcessor(state_manager, exam_registry)

@router.post("/whatsapp")
async def whatsapp_webhook(
    request: Request,
    From: str = Form(...),
    Body: str = Form(...),
    To: str = Form(...)
):
    """
    Clean WhatsApp webhook handler
    """
    logger.info(f"Received message from {From}: {Body}")
    
    # Create Twilio response
    response = MessagingResponse()
    msg = response.message()
    
    # Extract user phone number
    user_phone = From.replace('whatsapp:', '')
    message_body = Body.strip()
    
    try:
        # Process the message using our clean architecture
        response_text = message_processor.process_message(user_phone, message_body)
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
    return {"message": "WhatsApp webhook endpoint is ready"}