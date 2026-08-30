"""Core enums used for numeric routing and semantic relations.

This module deliberately imports no concrete numeric class.  That acyclic
boundary is a Phase-1 invariant of the Computable architecture.
"""

from __future__ import annotations

from enum import Enum


class NumericKind(Enum):
    """Routing identifier for the five scalar numeric regimes."""

    RATIONAL = "rational"
    GAUSSIAN_RATIONAL = "gaussian_rational"
    ALGEBRAIC = "algebraic"
    COMPUTABLE_REAL = "computable_real"
    COMPUTABLE_COMPLEX = "computable_complex"


class Order(Enum):
    """Exact trichotomy result for real-valued comparisons."""

    LESS = -1
    EQUAL = 0
    GREATER = 1


class Relation(Enum):
    """Public relation family over real order trichotomy.

    Complex-valued APIs will later restrict this enum to EQUAL/NOT_EQUAL.
    """

    LESS = frozenset({Order.LESS})
    LESS_EQUAL = frozenset({Order.LESS, Order.EQUAL})
    EQUAL = frozenset({Order.EQUAL})
    NOT_EQUAL = frozenset({Order.LESS, Order.GREATER})
    GREATER_EQUAL = frozenset({Order.EQUAL, Order.GREATER})
    GREATER = frozenset({Order.GREATER})

    def contains(self, order: Order) -> bool:
        """Return whether *order* belongs to this relation cell union."""

        return order in self.value
