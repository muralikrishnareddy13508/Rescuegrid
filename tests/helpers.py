"""Shared test data."""

from datetime import datetime, timedelta


def future(hours: int) -> str:
    """A date-time string `hours` from now (negative = in the past)."""
    return (datetime.now() + timedelta(hours=hours)).replace(microsecond=0).isoformat()


VALID = {
    "donor_name": "Demo Bakery (synthetic)",
    "donor_phone": "555-0100",
    "food_name": "Day-old bread",
    "category": "bakery",
    "quantity": 12.5,
    "unit": "kg",
    "expiry_at": future(48),
    "pickup_address": "12 Example Street",
    "pickup_at": future(24),
    "temperature_controlled": True,
    "packaging_intact": True,
}
