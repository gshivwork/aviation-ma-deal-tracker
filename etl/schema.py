"""Pydantic schema for validating the deal seed dataset before it is loaded into SQLite."""

from datetime import date
from enum import Enum

from pydantic import BaseModel, field_validator


class DealType(str, Enum):
    ACQUISITION = "Acquisition"
    JOINT_VENTURE = "Joint Venture"
    CODESHARE = "Codeshare"
    EQUITY_STAKE = "Equity Stake"
    TECH_PARTNERSHIP = "Tech Partnership"


class BuildBuyPartner(str, Enum):
    BUILD = "Build"
    BUY = "Buy"
    PARTNER = "Partner"


class DealStatus(str, Enum):
    COMPLETED = "Completed"
    PENDING = "Pending"
    BLOCKED = "Blocked"
    UNWOUND = "Unwound"
    EXPLORED = "Explored"


class Deal(BaseModel):
    deal_id: str
    announced_date: date
    deal_name: str
    acquirer: str
    target_or_partner: str
    deal_type: DealType
    capability_area: str
    region: str
    deal_value_usd_m: float
    deal_value_disclosed: bool
    strategic_rationale: str
    build_buy_partner: BuildBuyPartner
    source_name: str
    source_url: str
    status: DealStatus

    @field_validator("strategic_rationale")
    @classmethod
    def rationale_not_trivial(cls, v: str) -> str:
        if len(v.strip()) < 20:
            raise ValueError("strategic_rationale must be a substantive sentence, not a placeholder")
        return v.strip()

    @field_validator("deal_value_usd_m")
    @classmethod
    def value_non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("deal_value_usd_m cannot be negative")
        return v
