# Phase 1 implementation checkpoint

This checkpoint implements Roadmap **Phase 1 — Core package skeleton** only.

Implemented:

- `computable/core/{kinds,family,promotion,decision,certificates,knowledge,errors}.py`;
- five public numeric-regime shells;
- late `_bootstrap.py` family linking;
- empty promotion/conversion registries ready for later phases;
- `Pending`, `Resolved`, resumable `DecisionProcess` with bounded cooperative transitions and terminal-state caching;
- provenance enum and minimal knowledge-store interfaces;
- v1 custom error classes fixed by the semantic specification;
- Phase-1 conformance tests.

Deliberately **not** implemented early:

- Rational value semantics (Phase 2);
- GaussianRational field semantics (Phase 3);
- Polynomial/Algebraic semantics (Phases 4–5);
- geometry-first knowledge logic (Phase 6+);
- the complete shared exact integer-valued recognizer for `DecisionProcess.work` (later registry/subdomain-recognition work).

The five numeric shells therefore reject construction with `NotImplementedError` rather than create objects without a mathematical denotation.
