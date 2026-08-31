"""Resumable explicit computation boundary for potentially divergent work.

Phase 2 keeps the Phase-1 state machine and finite-step contract, while wiring
``work`` through the shared guaranteed-finite exact integer-valued recognizer.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic, TypeVar

from .promotion import SUBDOMAINS

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


def _shared_work_recognizer(value: object) -> int:
    """Recognize ``work`` by exact mathematical integer value, finitely."""

    result = SUBDOMAINS.recognize_integer_value(value)
    if result is None:
        raise TypeError(
            "work must be a guaranteed-finite exact integer-valued numeric input"
        )
    return result


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
        self._work_recognizer = work_recognizer or _shared_work_recognizer
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
        if not isinstance(amount, int) or isinstance(amount, bool):
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
