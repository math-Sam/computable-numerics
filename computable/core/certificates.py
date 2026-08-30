"""Certificate provenance vocabulary and Phase-1 certificate interfaces."""

from __future__ import annotations

from enum import Enum
from typing import Protocol, runtime_checkable


class ProvenanceKind(Enum):
    """Origin classification for persistent certified/trusted knowledge."""

    KERNEL_VERIFIED = "kernel_verified"
    TRUSTED_SOURCE = "trusted_source"
    USER_ASSERTED = "user_asserted"
    DERIVED = "derived"


@runtime_checkable
class Certificate(Protocol):
    """Minimal certificate protocol; concrete certificate payloads come later."""

    @property
    def provenance(self) -> ProvenanceKind:
        ...
