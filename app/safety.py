"""Food-safety eligibility rules.

Plain if/else rules written by people. NO AI model is used to decide safety.
Missing or failed critical information sends a donation to 'safety_review',
where matching is blocked until a person reviews it.
"""

from datetime import datetime

from app.statuses import DonationStatus


def evaluate(
    temperature_controlled: bool | None,
    packaging_intact: bool | None,
    expiry_at: datetime,
    now: datetime | None = None,
) -> tuple[DonationStatus, str | None]:
    """Return (status, note). note explains every problem found, or None if all is fine."""
    if now is None:
        now = datetime.now(expiry_at.tzinfo) if expiry_at.tzinfo else datetime.now()

    problems = []
    checks = (
        (temperature_controlled, "safe temperature"),
        (packaging_intact, "intact packaging"),
    )
    for answer, label in checks:
        if answer is None:
            problems.append(f"Missing answer: {label}.")
        elif answer is False:
            problems.append(f'Answered "No": {label}.')
    if expiry_at <= now:
        problems.append("Expiry time has already passed.")

    if problems:
        return DonationStatus.safety_review, " ".join(problems)
    return DonationStatus.safety_cleared, None
