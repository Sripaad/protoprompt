"""
Integration framework for TinyContext.

Provides connectivity to external systems, databases, and APIs.
"""

from .catalog import IntegrationCatalog, IntegrationDefinition
from .connectors.base_connector import BaseConnector, ConnectionStatus
from .auth.credential_manager import CredentialManager

__all__ = [
    "IntegrationCatalog",
    "IntegrationDefinition",
    "BaseConnector",
    "ConnectionStatus",
    "CredentialManager"
]