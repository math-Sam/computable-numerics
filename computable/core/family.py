"""Numeric-family linking without concrete-class imports."""

from __future__ import annotations

from dataclasses import dataclass

from .kinds import NumericKind


@dataclass(frozen=True, slots=True)
class NumericFamily:
    """The five concrete classes belonging to one Computable family."""

    rational: type
    gaussian_rational: type
    algebraic: type
    real: type
    complex: type

    def by_kind(self, kind: NumericKind) -> type:
        """Return the concrete class registered for *kind*."""

        if not isinstance(kind, NumericKind):
            raise TypeError(f"Expected NumericKind, got {type(kind).__name__}")
        mapping = {
            NumericKind.RATIONAL: self.rational,
            NumericKind.GAUSSIAN_RATIONAL: self.gaussian_rational,
            NumericKind.ALGEBRAIC: self.algebraic,
            NumericKind.COMPUTABLE_REAL: self.real,
            NumericKind.COMPUTABLE_COMPLEX: self.complex,
        }
        return mapping[kind]


def bind_family(family: NumericFamily) -> None:
    """Attach *family* to its five classes after all concrete imports finish.

    The function verifies each class's declared ``_kind`` before mutating any
    class.  This keeps bootstrap failure transactional with respect to family
    linking and avoids concrete imports inside :mod:`computable.core`.
    """

    expected = (
        (family.rational, NumericKind.RATIONAL),
        (family.gaussian_rational, NumericKind.GAUSSIAN_RATIONAL),
        (family.algebraic, NumericKind.ALGEBRAIC),
        (family.real, NumericKind.COMPUTABLE_REAL),
        (family.complex, NumericKind.COMPUTABLE_COMPLEX),
    )
    for cls, kind in expected:
        if getattr(cls, "_kind", None) is not kind:
            raise TypeError(
                f"{getattr(cls, '__name__', cls)!r} does not declare expected kind {kind.name}"
            )
    for cls, _ in expected:
        cls._family = family
