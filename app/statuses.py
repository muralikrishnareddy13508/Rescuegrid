"""All donation statuses in one place (no other imports, so rules can use it easily)."""

from enum import StrEnum


class DonationStatus(StrEnum):
    registered = "registered"          # first state (set only for an instant)
    safety_review = "safety_review"    # blocked: a person must review food-safety info
    safety_cleared = "safety_cleared"  # rules passed or a reviewer approved: may be matched
    matched = "matched"
    accepted = "accepted"
    picked_up = "picked_up"
    completed = "completed"            # the ONLY status that counts as confirmed redistribution
    rejected_unsafe = "rejected_unsafe"
    cancelled = "cancelled"
    expired = "expired"
