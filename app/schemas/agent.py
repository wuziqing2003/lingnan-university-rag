from pydantic import BaseModel, Field
from uuid import UUID

class AgentRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    thread_id : UUID