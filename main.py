from fastapi import FastAPI
from app.routes.whatsapp import router as whatsapp_router

app = FastAPI(
    title="WhatsApp Exam Chatbot",
    description="A chatbot for practicing computer-based exams via WhatsApp",
    version="1.0.0"
)

# Include WhatsApp webhook route
app.include_router(whatsapp_router, prefix="/webhook")

@app.get("/")
async def root():
    return {"message": "WhatsApp Exam Chatbot API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)