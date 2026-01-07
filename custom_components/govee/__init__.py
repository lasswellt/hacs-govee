from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_DELAY
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import issue_registry as ir

from .api import GoveeApiClient, GoveeApiError, GoveeAuthError
from .const import CONFIG_ENTRY_VERSION, DEFAULT_POLL_INTERVAL, DOMAIN, PLATFORMS
from .coordinator import GoveeDataUpdateCoordinator
from .models import GoveeConfigEntry, GoveeRuntimeData

__all__ = ["GoveeConfigEntry", "GoveeRuntimeData"]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: GoveeConfigEntry) -> bool:
    _LOGGER.debug("Setting up Govee integration")

    config = entry.data
    options = entry.options
    api_key = options.get(CONF_API_KEY, config.get(CONF_API_KEY, ""))
    poll_interval = options.get(CONF_DELAY, config.get(CONF_DELAY, DEFAULT_POLL_INTERVAL))

    session = async_get_clientsession(hass)
    client = GoveeApiClient(api_key, session=session)

    coordinator = GoveeDataUpdateCoordinator(
        hass,
        entry,
        client,
        update_interval=timedelta(seconds=poll_interval),
    )

    try:
        await coordinator.async_config_entry_first_refresh()
    except GoveeAuthError as err:
        _LOGGER.error("Invalid API key: %s", err)
        await client.close()
        raise ConfigEntryAuthFailed("Invalid API key") from err
    except GoveeApiError as err:
        _LOGGER.error("Failed to connect to Govee API: %s", err)
        await client.close()
        raise ConfigEntryNotReady(f"Failed to connect: {err}") from err

    entry.runtime_data = GoveeRuntimeData(
        client=client,
        coordinator=coordinator,
        devices=coordinator.devices,
    )

    # Validate poll interval is sustainable for device count
    device_count = len(coordinator.devices)
    sustainable = GoveeDataUpdateCoordinator.calculate_sustainable_interval(device_count)
    issue_id = f"poll_interval_unsustainable_{entry.entry_id}"

    if poll_interval < sustainable:
        _LOGGER.warning(
            "Poll interval %ds may cause rate limit issues with %d devices. "
            "Recommended minimum: %ds. Adaptive polling will throttle automatically.",
            poll_interval,
            device_count,
            sustainable,
        )
        ir.async_create_issue(
            hass,
            DOMAIN,
            issue_id,
            is_fixable=True,
            is_persistent=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key="poll_interval_unsustainable",
            translation_placeholders={
                "configured": str(poll_interval),
                "recommended": str(sustainable),
                "device_count": str(device_count),
            },
        )
    else:
        # Clear issue if interval is now sustainable
        ir.async_delete_issue(hass, DOMAIN, issue_id)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Start MQTT subscription for real-time device events
    # This runs in background and gracefully degrades if aiomqtt unavailable
    await coordinator.async_setup_mqtt(api_key)
    entry.async_on_unload(coordinator.async_stop_mqtt)

    entry.async_on_unload(entry.add_update_listener(async_options_updated))

    _LOGGER.info(
        "Govee integration set up with %d devices (poll: %ds, MQTT: %s)",
        device_count,
        poll_interval,
        "active" if coordinator.mqtt_connected else "connecting",
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: GoveeConfigEntry) -> bool:
    _LOGGER.debug("Unloading Govee integration")

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        await entry.runtime_data.client.close()

    return unload_ok


async def async_options_updated(hass: HomeAssistant, entry: GoveeConfigEntry) -> None:
    """Handle options update - dynamically update poll interval without reload.

    Only triggers a full reload if the API key changed. Poll interval changes
    are applied immediately to the coordinator.
    """
    old_api_key = entry.data.get(CONF_API_KEY, "")
    new_api_key = entry.options.get(CONF_API_KEY, old_api_key)

    # Only reload if API key changed
    if new_api_key != old_api_key:
        _LOGGER.info("API key changed, reloading integration")
        await hass.config_entries.async_reload(entry.entry_id)
        return

    # Dynamic update for poll interval (no restart required)
    coordinator = entry.runtime_data.coordinator
    new_interval = entry.options.get(CONF_DELAY, DEFAULT_POLL_INTERVAL)
    old_user_interval = coordinator._user_interval.total_seconds()

    if new_interval != old_user_interval:
        # Update user's preferred interval (used by adaptive polling to restore)
        coordinator._user_interval = timedelta(seconds=new_interval)
        coordinator.update_interval = timedelta(seconds=new_interval)
        _LOGGER.info(
            "Poll interval updated from %ds to %ds (no restart required)",
            int(old_user_interval),
            new_interval,
        )

    _LOGGER.debug("Options updated (dynamic update applied)")


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.debug("Migrating config entry from version %s", entry.version)

    if entry.version < CONFIG_ENTRY_VERSION:
        new_data = dict(entry.data)
        new_options = dict(entry.options)

        hass.config_entries.async_update_entry(
            entry,
            data=new_data,
            options=new_options,
            version=CONFIG_ENTRY_VERSION,
        )

        _LOGGER.info("Migration to version %s successful", CONFIG_ENTRY_VERSION)

    return True
