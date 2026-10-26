"""
Bronze → silver → gold pipeline with validation and incremental merge.

Production: Airflow + Spark/dbt on S3. Here: in-memory tables + pydantic validation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, ValidationError as PydanticValidationError


class ValidationError(Exception):
    pass


class RawOrder(BaseModel):
    order_id: str
    user_id: str
    amount_cents: int = Field(ge=0)
    updated_at: datetime


class SilverOrder(BaseModel):
    order_id: str
    user_id: str
    amount_usd: float
    updated_at: datetime


@dataclass
class PipelineConfig:
    min_rows: int = 1
    max_null_user_rate: float = 0.0


@dataclass
class EtlPipeline:
    """In-memory medallion store."""

    config: PipelineConfig = field(default_factory=PipelineConfig)
    bronze: list[dict[str, Any]] = field(default_factory=list)
    silver: dict[str, SilverOrder] = field(default_factory=dict)
    gold_revenue_usd: float = 0.0
    _last_watermark: datetime | None = None

    def ingest_bronze(self, rows: list[dict[str, Any]]) -> int:
        self.bronze.extend(rows)
        return len(rows)

    def bronze_to_silver(self) -> int:
        if len(self.bronze) < self.config.min_rows:
            raise ValidationError(f"bronze row count {len(self.bronze)} < min_rows")
        null_users = sum(1 for r in self.bronze if not r.get("user_id"))
        if null_users / max(len(self.bronze), 1) > self.config.max_null_user_rate:
            raise ValidationError("too many null user_id in bronze")

        merged = 0
        for raw in self.bronze:
            try:
                ro = RawOrder.model_validate(raw)
            except PydanticValidationError as e:
                raise ValidationError(str(e)) from e
            if self._last_watermark and ro.updated_at <= self._last_watermark:
                continue
            silver = SilverOrder(
                order_id=ro.order_id,
                user_id=ro.user_id,
                amount_usd=ro.amount_cents / 100.0,
                updated_at=ro.updated_at,
            )
            self.silver[ro.order_id] = silver
            merged += 1
            if self._last_watermark is None or ro.updated_at > self._last_watermark:
                self._last_watermark = ro.updated_at
        return merged

    def silver_to_gold(self) -> float:
        self.gold_revenue_usd = sum(o.amount_usd for o in self.silver.values())
        return self.gold_revenue_usd

    def run_incremental(self, new_bronze: list[dict[str, Any]]) -> dict[str, Any]:
        self.ingest_bronze(new_bronze)
        n = self.bronze_to_silver()
        rev = self.silver_to_gold()
        return {"silver_upserts": n, "gold_revenue_usd": rev, "silver_rows": len(self.silver)}
