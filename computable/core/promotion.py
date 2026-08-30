"""Acyclic registries for finite promotion and exact conversion routing.

Phase 1 only establishes registration/lookup mechanics.  Numeric conversion
algorithms and downgrade-first promotion rules are added in later phases.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeAlias

ConversionFunction: TypeAlias = Callable[[Any], Any]
PromotionFunction: TypeAlias = Callable[[Any, Any], tuple[Any, Any, type]]


class ConversionRegistry:
    """Registry of guaranteed-finite exact source-to-target conversions."""

    __slots__ = ("_conversions",)

    def __init__(self) -> None:
        self._conversions: dict[tuple[type, type], ConversionFunction] = {}

    def register(
        self,
        source: type,
        target: type,
        function: ConversionFunction,
        *,
        replace: bool = False,
    ) -> None:
        if not isinstance(source, type) or not isinstance(target, type):
            raise TypeError("source and target must be classes")
        if not callable(function):
            raise TypeError("conversion function must be callable")
        key = (source, target)
        if key in self._conversions and not replace:
            raise ValueError(f"conversion already registered: {source.__name__} -> {target.__name__}")
        self._conversions[key] = function

    def get(self, source: type, target: type) -> ConversionFunction | None:
        return self._conversions.get((source, target))

    def convert(self, value: Any, target: type) -> Any:
        function = self.get(type(value), target)
        if function is None:
            raise TypeError(
                f"no guaranteed-finite exact conversion registered: "
                f"{type(value).__name__} -> {getattr(target, '__name__', target)!s}"
            )
        return function(value)

    def __contains__(self, key: object) -> bool:
        return key in self._conversions

    def __len__(self) -> int:
        return len(self._conversions)


class PromotionRegistry:
    """Registry for pair-promotion strategies.

    A strategy is keyed by the post-downgrade concrete operand classes.  The
    strategy itself is intentionally left generic in Phase 1 so later phases
    can implement the specification's mathematical-value-first routing.
    """

    __slots__ = ("_promotions",)

    def __init__(self) -> None:
        self._promotions: dict[tuple[type, type], PromotionFunction] = {}

    def register(
        self,
        left: type,
        right: type,
        function: PromotionFunction,
        *,
        replace: bool = False,
    ) -> None:
        if not isinstance(left, type) or not isinstance(right, type):
            raise TypeError("left and right must be classes")
        if not callable(function):
            raise TypeError("promotion function must be callable")
        key = (left, right)
        if key in self._promotions and not replace:
            raise ValueError(f"promotion already registered: {left.__name__}, {right.__name__}")
        self._promotions[key] = function

    def get(self, left: type, right: type) -> PromotionFunction | None:
        return self._promotions.get((left, right))

    def promote(self, left: Any, right: Any) -> tuple[Any, Any, type]:
        function = self.get(type(left), type(right))
        if function is None:
            raise TypeError(
                f"no pair promotion registered: {type(left).__name__}, {type(right).__name__}"
            )
        return function(left, right)

    def __contains__(self, key: object) -> bool:
        return key in self._promotions

    def __len__(self) -> int:
        return len(self._promotions)
