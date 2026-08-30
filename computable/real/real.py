"""Phase-1 shell for the general ComputableReal semantic regime."""

from __future__ import annotations

from typing import ClassVar

from ..core.family import NumericFamily
from ..core.kinds import NumericKind


class ComputableReal:
    """Placeholder for the general computable-real runtime."""

    _kind: ClassVar[NumericKind] = NumericKind.COMPUTABLE_REAL
    _family: ClassVar[NumericFamily | None] = None

    def __new__(cls, *args, **kwargs):
        raise NotImplementedError("ComputableReal value semantics are implemented in later phases")
