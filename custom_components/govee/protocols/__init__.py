"""Protocol interfaces for Govee integration.

Defines contracts between layers following Hexagonal/Clean Architecture.
"""

from .api import IApiClient, IAuthProvider
from .state import IStateProvider, IStateObserver

__all__ = [
    "IApiClient",
    "IAuthProvider",
    "IStateProvider",
    "IStateObserver",
]
