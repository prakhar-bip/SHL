from pydantic import BaseModel, Field
from typing import List

class Message(BaseModel):
    role: str = Field(..., description="Role of the message author: 'user' or 'assistant'.")
    content: str = Field(..., description="The content of the message.")

class ChatRequest(BaseModel):
    messages: List[Message] = Field(..., description="List of the messages in the conversation history.")

class Recommendation(BaseModel):
    name: str = Field(..., description="Name of the recommended SHL assessment.")
    url: str = Field(..., description="Official URL of the SHL assessment.")
    test_type: str = Field(..., description="Test type abbreviation code (e.g. K, P, A, S, etc.).")

class ChatResponse(BaseModel):
    reply: str = Field(..., description="Conversational reply text, including markdown table if recommendations are committed.")
    recommendations: List[Recommendation] = Field(..., description="Shortlist of 1-10 recommended assessments, or empty.")
    end_of_conversation: bool = Field(..., description="Flag indicating if the conversation has concluded.")
