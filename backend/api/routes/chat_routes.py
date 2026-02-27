"""
AI Chat route – proxies user messages to the LangGraph agent.
Uses lazy import to avoid native module crashes at startup.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from database.models import User
from api.auth import get_current_user

router = APIRouter(prefix="/api/chat", tags=["AI Chat"])


class ChatMessage(BaseModel):
    role: str            # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []


class ChatResponse(BaseModel):
    reply: str


@router.post("", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Send a message to the AI Receptionist LangGraph agent and get a reply.
    The user_email is injected from the JWT token so the agent can act on
    behalf of the authenticated user.
    """
    try:
        from agent.graph import caller_app  # lazy import
        messages = []
        for msg in (payload.history or []):
            messages.append({"role": msg.role, "content": msg.content})
        messages.append({
            "role": "user",
            "content": (
                f"[Context: User email is {current_user.email}, "
                f"Name is {current_user.name or 'Patient'}]\n"
                f"{payload.message}"
            ),
        })

        result = caller_app.invoke({"messages": messages})
        reply_messages = result.get("messages", [])
        if reply_messages:
            last = reply_messages[-1]
            reply_text = last.content if hasattr(last, "content") else str(last)
        else:
            reply_text = "I'm sorry, I couldn't process your request."

        return {"reply": reply_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")
