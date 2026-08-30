"""Phase-1 shell for the Rational exact numeric regime."""

from __future__ import annotations

from typing import ClassVar

from .core.family import NumericFamily
from .core.kinds import NumericKind


class Rational:
    """Placeholder for the Phase-2 exact rational implementation."""

    _kind: ClassVar[NumericKind] = NumericKind.RATIONAL
    _family: ClassVar[NumericFamily | None] = None

    def __new__(cls, *args, **kwargs):
        raise NotImplementedError("Rational value semantics are implemented in Phase 2")
