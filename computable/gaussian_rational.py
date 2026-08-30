"""Phase-1 shell for the GaussianRational exact complex regime."""

from __future__ import annotations

from typing import ClassVar

from .core.family import NumericFamily
from .core.kinds import NumericKind


class GaussianRational:
    """Placeholder for the Phase-3 Q(i) implementation."""

    _kind: ClassVar[NumericKind] = NumericKind.GAUSSIAN_RATIONAL
    _family: ClassVar[NumericFamily | None] = None

    def __new__(cls, *args, **kwargs):
        raise NotImplementedError("GaussianRational value semantics are implemented in Phase 3")
