"""Phase-1 shell for the general ComputableComplex semantic regime."""

from __future__ import annotations

from typing import ClassVar

from ..core.family import NumericFamily
from ..core.kinds import NumericKind


class ComputableComplex:
    """Placeholder for the general computable-complex runtime."""

    _kind: ClassVar[NumericKind] = NumericKind.COMPUTABLE_COMPLEX
    _family: ClassVar[NumericFamily | None] = None

    def __new__(cls, *args, **kwargs):
        raise NotImplementedError("ComputableComplex value semantics are implemented in later phases")
