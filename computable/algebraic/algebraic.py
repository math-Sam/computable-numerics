"""Phase-1 shell for the unified Algebraic exact numeric regime."""

from __future__ import annotations

from typing import ClassVar

from ..core.family import NumericFamily
from ..core.kinds import NumericKind


class Algebraic:
    """Placeholder for the Phase-5 algebraic-number implementation."""

    _kind: ClassVar[NumericKind] = NumericKind.ALGEBRAIC
    _family: ClassVar[NumericFamily | None] = None

    def __new__(cls, *args, **kwargs):
        raise NotImplementedError("Algebraic value semantics are implemented in Phase 5")
