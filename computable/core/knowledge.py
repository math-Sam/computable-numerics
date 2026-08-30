"""Interfaces for monotone persistent certified knowledge.

The geometry-first carriers, residual semantics, recoverable-floor lattice,
and compaction rules are intentionally deferred to their roadmap phase.  This
module only establishes an acyclic interface boundary for future nodes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from .certificates import ProvenanceKind


@dataclass(frozen=True, slots=True)
class KnowledgeRecord:
    """Opaque Phase-1 knowledge record used by synthetic infrastructure tests."""

    payload: Any
    provenance: ProvenanceKind


@runtime_checkable
class KnowledgeStore(Protocol):
    """Minimal persistent-knowledge interface used by later graph nodes."""

    def commit(self, record: KnowledgeRecord) -> None:
        """Commit sound information without losing previously stored semantics."""
        ...

    def snapshot(self) -> tuple[KnowledgeRecord, ...]:
        """Return an immutable inspection snapshot."""
        ...


class AppendOnlyKnowledgeStore:
    """Simple Phase-1 monotone store.

    It intentionally performs no semantic compaction; later phases replace or
    extend this with geometry-first dominance/consistency logic.
    """

    __slots__ = ("_records",)

    def __init__(self) -> None:
        self._records: list[KnowledgeRecord] = []

    def commit(self, record: KnowledgeRecord) -> None:
        if not isinstance(record, KnowledgeRecord):
            raise TypeError("record must be a KnowledgeRecord")
        self._records.append(record)

    def snapshot(self) -> tuple[KnowledgeRecord, ...]:
        return tuple(self._records)
