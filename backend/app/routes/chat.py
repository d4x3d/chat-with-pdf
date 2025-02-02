from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from services.chat_service import get_chat_response
from typing import Optional, List

router = APIRouter()

class ChatMessage(BaseModel):
    message: str
    documentId: str

class Source(BaseModel):
    text: str
    page: int

class ChatResponse(BaseModel):
    message: str
    sources: Optional[List[Source]] = None

@router.post("/chat")
async def chat(message: ChatMessage) -> ChatResponse:
    """
    Process a chat message and return a response
    """
    try:
        response = await get_chat_response(message.message, message.documentId)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/ws/chat/{document_id}")
async def websocket_endpoint(websocket: WebSocket, document_id: str):
    """
    WebSocket endpoint for real-time chat
    """
    await websocket.accept()
    try:
        while True:
            # Receive message from client
            message = await websocket.receive_text()
            
            # Get response from chat service
            response = await get_chat_response(message, document_id)
            
            # Send response back to client
            await websocket.send_json(response.dict())
            
    except WebSocketDisconnect:
        # Handle client disconnect
        pass
    except Exception as e:
        # Send error message to client
        await websocket.send_json({
            "error": str(e)
        }) 