from __future__ import annotations
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, Literal, Protocol, Union


@dataclass
class TokenEvent:
    delta : str
    type : Literal["token"] = "token"
    def payload(self) -> dict:
        return {"delta":self.delta}

@dataclass
class ActionEvent:
    round : int
    name : str
    args : dict
    id : str
    type : Literal["action"] = "action"
    def payload(self) -> dict:
        return {
            "round":self.round,
            "name":self.name,
            "args":self.args,
            "id":self.id
        }

@dataclass
class ObservationEvent:
    round : int
    name : str
    id : str
    content : str
    type : Literal["observation"] = "observation"
    def payload(self) -> dict:
        return {
            "round":self.round,
            "name":self.name,
            "id":self.id,
            "content":self.content
        }

@dataclass
class SourcesEvent:
    items : list
    type : Literal["sources"] = "sources"
    def payload(self) -> dict:
        return {
            "items":self.items
        }


@dataclass
class ErrorEvent:
    message : str
    type : Literal["error"] = "error"
    def payload(self) -> dict:
        return {
            "message":self.message
        }

@dataclass
class DoneEvent:
    type : Literal["done"] = "done"
    def payload(self) -> dict:
        return {}

@dataclass
class ThoughtEvent:
    delta: str
    skipped: bool = False
    type: Literal["thought"] = "thought"

    def payload(self) -> dict:
        return {"delta": self.delta, "skipped": self.skipped}


AgentEvent = Union[TokenEvent, ActionEvent,ThoughtEvent, ObservationEvent, SourcesEvent, ErrorEvent, DoneEvent]


class AgentRunner(Protocol):
    def run(
        self,
        question : str,
        thread_id :str | None = None,
    ) -> AsyncIterator[AgentEvent]: ...




