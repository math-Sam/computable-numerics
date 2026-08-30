"""Public exception classes fixed by the v1 semantic specification."""


class ComputableError(Exception):
    """Base class for library-specific semantic/runtime errors."""


class UnresolvedDomainError(ComputableError):
    """An ordinary partial operation lacks a certified domain decision."""


class InvalidCertificateError(ComputableError):
    """A supplied certificate is malformed or fails finite verification."""


class InconsistentKnowledgeError(ComputableError):
    """Incoming knowledge finitely contradicts already committed knowledge."""
