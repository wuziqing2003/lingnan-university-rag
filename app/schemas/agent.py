from pydantic import BaseModel, Field


class AgentRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)