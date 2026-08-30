"""Roadmap Phase-1 conformance tests."""

from __future__ import annotations

import importlib
import unittest

import computable
from computable import (
    Algebraic,
    ComputableComplex,
    ComputableReal,
    DecisionProcess,
    GaussianRational,
    NumericKind,
    Pending,
    Rational,
    Resolved,
)
from computable.core.promotion import ConversionRegistry, PromotionRegistry


class TestImportsAndBootstrap(unittest.TestCase):
    def test_concrete_modules_import_cleanly(self) -> None:
        names = (
            "computable.rational",
            "computable.gaussian_rational",
            "computable.algebraic.algebraic",
            "computable.real.real",
            "computable.complex.complex",
        )
        for name in names:
            with self.subTest(name=name):
                self.assertIsNotNone(importlib.import_module(name))

    def test_family_is_linked_after_bootstrap(self) -> None:
        family = computable.bootstrap()
        expected = (
            (Rational, NumericKind.RATIONAL),
            (GaussianRational, NumericKind.GAUSSIAN_RATIONAL),
            (Algebraic, NumericKind.ALGEBRAIC),
            (ComputableReal, NumericKind.COMPUTABLE_REAL),
            (ComputableComplex, NumericKind.COMPUTABLE_COMPLEX),
        )
        for cls, kind in expected:
            with self.subTest(cls=cls.__name__):
                self.assertIs(cls._family, family)
                self.assertIs(cls._kind, kind)
                self.assertIs(family.by_kind(kind), cls)

    def test_bootstrap_is_idempotent(self) -> None:
        self.assertIs(computable.bootstrap(), computable.bootstrap())

    def test_shells_do_not_fabricate_values(self) -> None:
        for cls in (Rational, GaussianRational, Algebraic, ComputableReal, ComputableComplex):
            with self.subTest(cls=cls.__name__), self.assertRaises(NotImplementedError):
                cls()


class TestPendingAndDecisionProcess(unittest.TestCase):
    def test_pending_truth_test_raises(self) -> None:
        with self.assertRaises(TypeError):
            bool(Pending())

    def test_advance_is_bounded_and_resumable(self) -> None:
        state = {"remaining": 3}

        def step():
            state["remaining"] -= 1
            if state["remaining"] == 0:
                return Resolved("done")
            return Pending()

        process = DecisionProcess(step)
        self.assertIsInstance(process.advance(work=1), Pending)
        self.assertEqual(process.transition_count, 1)
        result = process.advance(work=10)
        self.assertEqual(result, Resolved("done"))
        self.assertEqual(process.transition_count, 3)

    def test_work_zero_performs_no_transition(self) -> None:
        calls = 0

        def step():
            nonlocal calls
            calls += 1
            return Pending()

        process = DecisionProcess(step)
        self.assertIsInstance(process.advance(work=0), Pending)
        self.assertEqual(calls, 0)
        self.assertEqual(process.transition_count, 0)

    def test_resolved_result_is_stable_without_more_work(self) -> None:
        calls = 0

        def step():
            nonlocal calls
            calls += 1
            return Resolved(17)

        process = DecisionProcess(step)
        first = process.advance(work=1)
        second = process.advance(work=100)
        self.assertEqual(first, Resolved(17))
        self.assertEqual(second, first)
        self.assertEqual(calls, 1)
        self.assertEqual(process.transition_count, 1)

    def test_terminal_exception_is_stable(self) -> None:
        calls = 0

        def step():
            nonlocal calls
            calls += 1
            raise ZeroDivisionError("synthetic terminal failure")

        process = DecisionProcess(step)
        with self.assertRaises(ZeroDivisionError):
            process.advance(work=1)
        with self.assertRaises(ZeroDivisionError):
            process.advance(work=100)
        self.assertEqual(calls, 1)
        self.assertEqual(process.transition_count, 1)

    def test_resolve_returns_value(self) -> None:
        state = {"n": 0}

        def step():
            state["n"] += 1
            return Resolved(5) if state["n"] == 4 else Pending()

        process = DecisionProcess(step)
        self.assertEqual(process.resolve(), 5)
        self.assertEqual(process.transition_count, 4)

    def test_invalid_phase1_work(self) -> None:
        process = DecisionProcess(lambda: Pending())
        with self.assertRaises(TypeError):
            process.advance(work=1.5)
        with self.assertRaises(ValueError):
            process.advance(work=-1)


class TestRegistries(unittest.TestCase):
    def test_conversion_registry(self) -> None:
        registry = ConversionRegistry()
        registry.register(int, str, str)
        self.assertEqual(registry.convert(12, str), "12")
        with self.assertRaises(ValueError):
            registry.register(int, str, str)

    def test_promotion_registry(self) -> None:
        registry = PromotionRegistry()
        registry.register(int, int, lambda a, b: (a, b, int))
        self.assertEqual(registry.promote(2, 3), (2, 3, int))
        with self.assertRaises(TypeError):
            registry.promote(2, 3.0)


if __name__ == "__main__":
    unittest.main()
