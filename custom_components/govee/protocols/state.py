"""State management protocol interfaces.

Defines contracts for state providers and observers.
Enables separation between polling, MQTT push, and UI layers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from ..models.device import GoveeDevice
    from ..models.state import GoveeDeviceState


@runtime_checkable
class IStateObserver(Protocol):
    """Protocol for state change observers.

    Implemented by entities and other components that need
    to be notified when device state changes.
    """

    def on_state_changed(
        self,
        device_id: str,
        state: GoveeDeviceState,
    ) -> None:
        """Called when device state changes.

        Args:
            device_id: Device that changed.
            state: New device state.
        """
        ...


@runtime_checkable
class IStateProvider(Protocol):
    """Protocol for state providers.

    Implemented by coordinator and MQTT client to provide
    device state to the integration.
    """

    def get_device(self, device_id: str) -> GoveeDevice | None:
        """Get device by ID.

        Args:
            device_id: Device identifier.

        Returns:
            GoveeDevice or None if not found.
        """
        ...

    def get_state(self, device_id: str) -> GoveeDeviceState | None:
        """Get current state for a device.

        Args:
            device_id: Device identifier.

        Returns:
            Current state or None if unavailable.
        """
        ...

    @property
    def devices(self) -> dict[str, GoveeDevice]:
        """All known devices."""
        ...

    @property
    def states(self) -> dict[str, GoveeDeviceState]:
        """Current states for all devices."""
        ...

    def register_observer(self, observer: IStateObserver) -> None:
        """Register a state change observer.

        Args:
            observer: Observer to register.
        """
        ...

    def unregister_observer(self, observer: IStateObserver) -> None:
        """Unregister a state change observer.

        Args:
            observer: Observer to unregister.
        """
        ...
