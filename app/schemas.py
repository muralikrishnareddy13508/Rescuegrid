"""Data shapes (and validation rules) for the API."""

from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.statuses import DonationStatus  # noqa: F401  (re-exported for other modules)


class FoodCategory(StrEnum):
    cooked_meal = "cooked_meal"
    produce = "produce"
    bakery = "bakery"
    dairy = "dairy"
    packaged = "packaged"
    beverage = "beverage"
    other = "other"


class QuantityUnit(StrEnum):
    kg = "kg"
    portions = "portions"
    items = "items"


class DonationCreate(BaseModel):
    """What a donor sends to POST /donations."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    donor_name: str = Field(min_length=1, max_length=100)
    donor_phone: str = Field(min_length=5, max_length=30)
    food_name: str = Field(min_length=1, max_length=100)
    category: FoodCategory
    quantity: float = Field(gt=0, le=100000)
    unit: QuantityUnit
    prepared_on: date | None = None
    expiry_at: datetime
    pickup_address: str = Field(min_length=1, max_length=200)
    pickup_at: datetime
    # None means "not provided": the safety rules send that to review.
    temperature_controlled: bool | None = None
    packaging_intact: bool | None = None
    notes: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def pickup_must_be_before_expiry(self):
        if (self.pickup_at.tzinfo is None) != (self.expiry_at.tzinfo is None):
            raise ValueError("pickup_at and expiry_at must both include a timezone or both omit it")
        if self.pickup_at >= self.expiry_at:
            raise ValueError("pickup_at must be before expiry_at")
        return self


class DonationOut(DonationCreate):
    """What the API sends back: the donation plus server-created fields."""

    id: int
    status: DonationStatus
    safety_note: str | None = None
    created_at: str


class StatusUpdate(BaseModel):
    """Body of PATCH /donations/{id}/status."""

    model_config = ConfigDict(extra="forbid")

    status: DonationStatus
    reason: str | None = Field(default=None, max_length=300)
