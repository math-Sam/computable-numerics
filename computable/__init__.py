"""Computable exact numerical runtime.

The current implementation checkpoint is Roadmap Phase 2: the Rational exact
substrate is implemented while later numeric regimes remain deliberate shells.
"""

from ._bootstrap import CONVERSIONS, NUMERIC_FAMILY, PROMOTIONS, bootstrap
from .algebraic import Algebraic
from .complex import ComputableComplex
from .core import (
    AppendOnlyKnowledgeStore,
    ComputableError,
    ConversionRegistry,
    DecisionProcess,
    InconsistentKnowledgeError,
    InvalidCertificateError,
    KnowledgeRecord,
    NumericFamily,
    NumericKind,
    Order,
    Pending,
    PromotionRegistry,
    ProvenanceKind,
    Relation,
    Resolved,
    UnresolvedDomainError,
)
from .gaussian_rational import GaussianRational
from .rational import Rational
from .real import ComputableReal

bootstrap()

__all__ = [
    "CONVERSIONS",
    "NUMERIC_FAMILY",
    "PROMOTIONS",
    "Algebraic",
    "AppendOnlyKnowledgeStore",
    "ComputableComplex",
    "ComputableError",
    "ComputableReal",
    "ConversionRegistry",
    "DecisionProcess",
    "GaussianRational",
    "InconsistentKnowledgeError",
    "InvalidCertificateError",
    "KnowledgeRecord",
    "NumericFamily",
    "NumericKind",
    "Order",
    "Pending",
    "PromotionRegistry",
    "ProvenanceKind",
    "Rational",
    "Relation",
    "Resolved",
    "UnresolvedDomainError",
    "bootstrap",
]
