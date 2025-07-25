from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from app.services.chat_service import chat_service

router = APIRouter()

class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str

class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[ChatMessage]] = None

class ChatResponse(BaseModel):
    response: str
    success: bool
    error: Optional[str] = None

@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(request: ChatRequest):
    """Chat with AI assistant about metrics"""
    try:
        # Convert conversation history to the format expected by chat service
        history = []
        if request.conversation_history:
            history = [
                {"role": msg.role, "content": msg.content} 
                for msg in request.conversation_history
            ]
        
        # Get response from chat service
        response = await chat_service.chat_with_metrics(
            message=request.message,
            conversation_history=history
        )
        
        return ChatResponse(
            response=response,
            success=True
        )
        
    except Exception as e:
        return ChatResponse(
            response="Sorry, I encountered an error processing your request.",
            success=False,
            error=str(e)
        )