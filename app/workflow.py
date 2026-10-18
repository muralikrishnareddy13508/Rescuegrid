"""Which status changes are allowed. Pure rules, easy to read and test."""

from app.statuses import DonationStatus as S

TRANSITIONS = {
    S.registered: set(),
    S.safety_review: {S.safety_cleared, S.rejected_unsafe},   # human decision only
    S.safety_cleared: {S.matched, S.cancelled, S.expired},
    S.matched: {S.accepted, S.safety_cleared, S.cancelled},   # back to cleared = declined
    S.accepted: {S.picked_up, S.cancelled},
    S.picked_up: {S.completed},
    S.completed: set(),
    S.rejected_unsafe: set(),
    S.cancelled: set(),
    S.expired: set(),
}

# A reviewer must explain these decisions.
REASON_REQUIRED = {
    (S.safety_review, S.safety_cleared),
    (S.safety_review, S.rejected_unsafe),
}

# 'matched' may only be set by the matching step (added in a later milestone).
MATCHING_ONLY = {S.matched}


class WorkflowError(Exception):
    """Base class for all status-change problems."""


class InvalidTransition(WorkflowError):
    """That change is not allowed from the current status."""


class ReasonRequired(WorkflowError):
    """A written reason is needed for this decision."""


class NotAllowedHere(WorkflowError):
    """That status cannot be set through this route."""


def check_transition(current, new, reason, internal: bool = False) -> None:
    """Raise a WorkflowError if the change is not allowed; return None if it is."""
    current, new = S(current), S(new)
    if new in MATCHING_ONLY and not internal:
        raise NotAllowedHere("'matched' can only be set by the matching step")
    if new not in TRANSITIONS[current]:
        raise InvalidTransition(f"Cannot change status from '{current}' to '{new}'")
    if (current, new) in REASON_REQUIRED and not (reason and reason.strip()):
        raise ReasonRequired("A reason is required for this safety decision")
