"""Resumable explicit computation boundary for potentially divergent work.

Phase 1 implements the state machine and finite-step contract.  The complete
cross-regime ExactIntegerInput recognizer is wired in a later phase; callers
may already inject a finite work recognizer without importing concrete classes
here.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")
WorkRecognizer = Callable[[object], int]
Transition = Callable[[], "Pending | Resolved[T]"]


@dataclass(frozen=True, slots=True)
class Pending:
    """The final process question has not yet resolved."""

    def __bool__(self) -> bool:
        raise TypeError("Pending has no Boolean truth value")


@dataclass(frozen=True, slots=True)
class Resolved(Generic[T]):
    """Terminal successful result of a DecisionProcess."""

    value: T


def _phase1_work_recognizer(value: object) -> int:
    """Bootstrap work recognizer used until the shared exact recognizer exists.

    Python ``bool`` is intentionally accepted through the Python ``int`` rule.
    This function is finite and does not inspect concrete numeric classes.
    """

    if not isinstance(value, int):
        raise TypeError(
            "Phase-1 DecisionProcess work accepts Python integer values; "
            "the shared exact integer-valued numeric recognizer is installed in a later phase"
        )
    return int(value)


class DecisionProcess(Generic[T]):
    """Mutable resumable process composed of cooperative finite transitions.

    ``advance(work=N)`` performs at most ``N`` transitions.  ``resolve()`` is
    the explicit unbounded boundary and **may not terminate**.

    The transition callable must itself be guaranteed finite for one call and
    return either :class:`Pending` or :class:`Resolved`.
    """

    __slots__ = (
        "_resolved",
        "_terminal_exception",
        "_transition",
        "_transition_count",
        "_work_recognizer",
    )

    def __init__(
        self,
        transition: Transition[T],
        *,
        work_recognizer: WorkRecognizer | None = None,
    ) -> None:
        if not callable(transition):
            raise TypeError("transition must be callable")
        if work_recognizer is not None and not callable(work_recognizer):
            raise TypeError("work_recognizer must be callable")
        self._transition = transition
        self._work_recognizer = work_recognizer or _phase1_work_recognizer
        self._resolved: Resolved[T] | None = None
        self._terminal_exception: BaseException | None = None
        self._transition_count = 0

    @property
    def transition_count(self) -> int:
        """Number of cooperative transitions actually executed."""

        return self._transition_count

    @property
    def is_resolved(self) -> bool:
        return self._resolved is not None

    @property
    def is_failed(self) -> bool:
        return self._terminal_exception is not None

    def _report_terminal_or_pending(self) -> Pending | Resolved[T]:
        if self._terminal_exception is not None:
            raise self._terminal_exception
        if self._resolved is not None:
            return self._resolved
        return Pending()

    def advance(self, work: object = 1) -> Pending | Resolved[T]:
        """Advance by at most ``work`` cooperative finite transitions."""

        amount = self._work_recognizer(work)
        if not isinstance(amount, int):
            raise TypeError("work recognizer must return an ordinary Python int")
        if amount < 0:
            raise ValueError(f"work must be non-negative, got {amount}")

        if self._terminal_exception is not None or self._resolved is not None or amount == 0:
            return self._report_terminal_or_pending()

        for _ in range(amount):
            self._transition_count += 1
            try:
                outcome = self._transition()
            except Exception as exc:
                self._terminal_exception = exc
                raise
            if isinstance(outcome, Resolved):
                self._resolved = outcome
                return outcome
            if not isinstance(outcome, Pending):
                exc = TypeError(
                    "DecisionProcess transition must return Pending or Resolved"
                )
                self._terminal_exception = exc
                raise exc
        return Pending()

    def resolve(self) -> T:
        """Run until resolved and return the result; **may not terminate**."""

        while True:
            outcome = self.advance(work=1)
            if isinstance(outcome, Resolved):
                return outcome.value
