"""Pydantic models for stream events — mirrors Flink record + watermark metadata."""

from __future__ import annotations

from pydantic import BaseModel, Field


class StreamEvent(BaseModel):
    """One keyed event with event-time (not processing time)."""

    key: str
    value: float
    event_time_ms: int = Field(description="Epoch ms embedded in the record")


class WindowResult(BaseModel):
    window_start_ms: int
    window_end_ms: int
    key: str
    sum_value: float
    count: int
    on_time: bool = True  # False if emitted via allowed lateness update
