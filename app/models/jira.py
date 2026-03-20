from __future__ import annotations

from pydantic import BaseModel, Field


class JiraTicket(BaseModel):
    key: str
    summary: str
    description: str = ""
    status_name: str | None = None
    status_category: str | None = None
    labels: list[str] = Field(default_factory=list)
    url: str


class NotificationMessage(BaseModel):
    subject: str
    body: str
    ticket_key: str
    ticket_url: str
    brief_description: str


class IndexedTicket(BaseModel):
    ticket_key: str
    title: str
    description: str
    status_name: str
    labels: list[str] = Field(default_factory=list)
    url: str
    searchable_text: str
    embedding: list[float] = Field(default_factory=list)

