from fastapi import APIRouter, HTTPException
from app.models.schemas import ChatRequest, ChatResponse
from app.chatbot.agent import ChatbotAgent

router = APIRouter()
_agent = None

def get_agent():
    global _agent
    if _agent is None:
        _agent = ChatbotAgent()
    return _agent

@router.get("/health")
def health_check():
    return {"status": "ok"}

@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    try:
        agent = get_agent()
        response = agent.generate_response(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
