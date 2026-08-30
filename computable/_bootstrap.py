"""Late concrete-class linking for the Computable numeric family."""

from __future__ import annotations

from .algebraic import Algebraic
from .complex import ComputableComplex
from .core.family import NumericFamily, bind_family
from .core.promotion import ConversionRegistry, PromotionRegistry
from .gaussian_rational import GaussianRational
from .rational import Rational
from .real import ComputableReal

NUMERIC_FAMILY = NumericFamily(
    rational=Rational,
    gaussian_rational=GaussianRational,
    algebraic=Algebraic,
    real=ComputableReal,
    complex=ComputableComplex,
)

PROMOTIONS = PromotionRegistry()
CONVERSIONS = ConversionRegistry()

_BOOTSTRAPPED = False


def bootstrap() -> NumericFamily:
    """Idempotently link concrete classes after all class modules are loaded."""

    global _BOOTSTRAPPED
    if not _BOOTSTRAPPED:
        bind_family(NUMERIC_FAMILY)
        _BOOTSTRAPPED = True
    return NUMERIC_FAMILY
