"""Status-change rules: plain logic, no web server needed."""

from app.statuses import DonationStatus as S
from app.workflow import (
    TRANSITIONS,
    InvalidTransition,
    NotAllowedHere,
    ReasonRequired,
    check_transition,
)


def expect_error(error_type, *args, **kwargs):
    try:
        check_transition(*args, **kwargs)
    except error_type:
        return
    raise AssertionError(f"{error_type.__name__} was not raised")


def test_review_decision_needs_a_reason():
    expect_error(ReasonRequired, "safety_review", "safety_cleared", None)
    expect_error(ReasonRequired, "safety_review", "rejected_unsafe", "   ")


def test_review_decision_with_reason_is_allowed():
    assert check_transition("safety_review", "safety_cleared", "Checked by coordinator") is None


def test_matched_cannot_be_set_directly():
    expect_error(NotAllowedHere, "safety_cleared", "matched", None)


def test_matching_step_may_set_matched():
    assert check_transition("safety_cleared", "matched", None, internal=True) is None


def test_invalid_jump_is_rejected():
    expect_error(InvalidTransition, "safety_cleared", "completed", None)


def test_unsafe_donation_cannot_skip_review():
    expect_error(InvalidTransition, "safety_review", "accepted", None)
    expect_error(InvalidTransition, "safety_review", "matched", None, internal=True)


def test_final_statuses_have_no_exits():
    for final in (S.completed, S.rejected_unsafe, S.cancelled, S.expired):
        assert TRANSITIONS[final] == set()
