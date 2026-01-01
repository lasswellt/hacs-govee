from __future__ import annotations

import asyncio
import logging
import time
import uuid
from typing import Any, cast

import aiohttp
import async_timeout

from .const import (
    BASE_URL,
    ENDPOINT_DEVICES,
    ENDPOINT_DEVICE_CONTROL,
    ENDPOINT_DEVICE_STATE,
    ENDPOINT_DIY_SCENES,
    ENDPOINT_DYNAMIC_SCENES,
    HEADER_API_RATE_LIMIT_REMAINING,
    HEADER_API_RATE_LIMIT_RESET,
    HEADER_RATE_LIMIT_REMAINING,
    HEADER_RATE_LIMIT_RESET,
    MAX_RATE_LIMIT_WAIT,
    RATE_LIMIT_PER_DAY,
    RATE_LIMIT_PER_MINUTE,
    REQUEST_TIMEOUT,
    SECONDS_PER_DAY,
    SECONDS_PER_MINUTE,
)
from .exceptions import (
    GoveeApiError,
    GoveeAuthError,
    GoveeConnectionError,
    GoveeRateLimitError,
)

_LOGGER = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter for Govee API with dual limits (per-minute and per-day).

    Govee API Rate Limits:
    - Per-minute limit: 100 requests/minute
    - Per-day limit: 10,000 requests/day

    Rate Limiting Algorithm:
    1. Track timestamps of all recent requests (minute and day windows)
    2. Before each request, check if limits would be exceeded
    3. If limit would be exceeded, sleep until oldest request expires
    4. Update limits from API response headers (more accurate than local tracking)

    Thread Safety:
    - Uses asyncio.Lock to prevent race conditions
    - All requests must call acquire() before making API calls

    State Tracking:
    - Local tracking: List of request timestamps
    - API tracking: Updated from response headers (authoritative)
    - Returns API values when available, falls back to local estimates
    """

    def __init__(
        self,
        requests_per_minute: int = RATE_LIMIT_PER_MINUTE,
        requests_per_day: int = RATE_LIMIT_PER_DAY,
    ) -> None:
        self._per_minute = requests_per_minute
        self._per_day = requests_per_day
        self._minute_timestamps: list[float] = []
        self._day_timestamps: list[float] = []
        self._lock = asyncio.Lock()

        # Updated from API response headers (more accurate than local tracking)
        self._api_remaining_minute: int | None = None
        self._api_remaining_day: int | None = None
        self._api_reset_minute: float | None = None
        self._api_reset_day: float | None = None

    async def acquire(self) -> None:
        """Wait until a request can be made within rate limits.

        Rate Limit Algorithm:
        1. Clean expired timestamps (>60s for minute, >24h for day)
        2. Check per-minute limit: wait if at capacity
        3. Check per-day limit: wait if at capacity (max 1 hour)
        4. Record request timestamp

        Waiting Strategy:
        - Minute limit: Wait exactly until oldest request expires from window
        - Day limit: Wait up to 1 hour (prevents indefinite blocking)

        Thread Safety:
        - Acquires lock before any timestamp operations
        - Ensures atomic check-and-record operations
        """
        async with self._lock:
            now = time.time()

            self._minute_timestamps = [
                t for t in self._minute_timestamps if now - t < SECONDS_PER_MINUTE
            ]
            self._day_timestamps = [
                t for t in self._day_timestamps if now - t < SECONDS_PER_DAY
            ]

            if len(self._minute_timestamps) >= self._per_minute:
                wait_time = SECONDS_PER_MINUTE - (now - self._minute_timestamps[0])
                if wait_time > 0:
                    _LOGGER.debug("Rate limit: waiting %.1fs for minute limit", wait_time)
                    await asyncio.sleep(wait_time)
                    now = time.time()
                    self._minute_timestamps = [
                        t for t in self._minute_timestamps if now - t < SECONDS_PER_MINUTE
                    ]

            if len(self._day_timestamps) >= self._per_day:
                wait_time = SECONDS_PER_DAY - (now - self._day_timestamps[0])
                if wait_time > 0:
                    _LOGGER.warning(
                        "Daily rate limit reached. Waiting up to 1 hour. "
                        "Consider increasing poll interval."
                    )
                    await asyncio.sleep(min(wait_time, MAX_RATE_LIMIT_WAIT))
                    now = time.time()

            self._minute_timestamps.append(now)
            self._day_timestamps.append(now)

    def update_from_headers(self, headers: dict[str, str]) -> None:
        if HEADER_RATE_LIMIT_REMAINING in headers:
            self._api_remaining_minute = int(headers[HEADER_RATE_LIMIT_REMAINING])
        if HEADER_RATE_LIMIT_RESET in headers:
            self._api_reset_minute = float(headers[HEADER_RATE_LIMIT_RESET])
        if HEADER_API_RATE_LIMIT_REMAINING in headers:
            self._api_remaining_day = int(headers[HEADER_API_RATE_LIMIT_REMAINING])
        if HEADER_API_RATE_LIMIT_RESET in headers:
            self._api_reset_day = float(headers[HEADER_API_RATE_LIMIT_RESET])

    @property
    def remaining_minute(self) -> int:
        if self._api_remaining_minute is not None:
            return self._api_remaining_minute
        return self._per_minute - len(self._minute_timestamps)

    @property
    def remaining_day(self) -> int:
        if self._api_remaining_day is not None:
            return self._api_remaining_day
        return self._per_day - len(self._day_timestamps)

    @property
    def reset_minute(self) -> float | None:
        return self._api_reset_minute

    @property
    def reset_day(self) -> float | None:
        return self._api_reset_day


class GoveeApiClient:
    def __init__(
        self,
        api_key: str,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        self._api_key = api_key
        self._session = session
        self._owns_session = session is None
        self._rate_limiter = RateLimiter()

    async def __aenter__(self) -> GoveeApiClient:
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def close(self) -> None:
        if self._owns_session and self._session:
            await self._session.close()
            self._session = None

    @property
    def rate_limiter(self) -> RateLimiter:
        return self._rate_limiter

    def _headers(self) -> dict[str, str]:
        return {
            "Govee-API-Key": self._api_key,
            "Content-Type": "application/json",
        }

    async def _request(
        self,
        method: str,
        endpoint: str,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if self._session is None:
            self._session = aiohttp.ClientSession()
            self._owns_session = True

        await self._rate_limiter.acquire()

        url = f"{BASE_URL}/{endpoint}"

        try:
            async with async_timeout.timeout(REQUEST_TIMEOUT):
                async with self._session.request(
                    method,
                    url,
                    headers=self._headers(),
                    json=json_data,
                ) as response:
                    self._rate_limiter.update_from_headers(dict(response.headers))

                    try:
                        data = await response.json()
                    except aiohttp.ContentTypeError:
                        data = {"message": await response.text()}

                    if response.status == 401:
                        raise GoveeAuthError()
                    if response.status == 429:
                        retry_after = response.headers.get("Retry-After")
                        raise GoveeRateLimitError(
                            retry_after=float(retry_after) if retry_after else None
                        )
                    if response.status >= 400:
                        message = data.get("message", f"HTTP {response.status}")
                        raise GoveeApiError(message, code=response.status)

                    if data.get("code") and data.get("code") != 200:
                        raise GoveeApiError(
                            data.get("message", "Unknown error"),
                            code=data.get("code"),
                        )

                    return cast(dict[str, Any], data)

        except asyncio.TimeoutError as err:
            raise GoveeConnectionError("Request timed out") from err
        except aiohttp.ClientError as err:
            raise GoveeConnectionError(str(err)) from err

    async def get_devices(self) -> list[dict[str, Any]]:
        response = await self._request("GET", ENDPOINT_DEVICES)
        data: list[dict[str, Any]] = response.get("data", [])
        return data

    async def get_device_state(
        self,
        device_id: str,
        sku: str,
    ) -> dict[str, Any]:
        payload = {
            "requestId": str(uuid.uuid4()),
            "payload": {
                "sku": sku,
                "device": device_id,
            },
        }

        response = await self._request("POST", ENDPOINT_DEVICE_STATE, payload)
        payload_data: dict[str, Any] = response.get("payload", {})
        return payload_data

    async def control_device(
        self,
        device_id: str,
        sku: str,
        capability_type: str,
        instance: str,
        value: Any,
    ) -> dict[str, Any]:
        payload = {
            "requestId": str(uuid.uuid4()),
            "payload": {
                "sku": sku,
                "device": device_id,
                "capability": {
                    "type": capability_type,
                    "instance": instance,
                    "value": value,
                },
            },
        }

        _LOGGER.debug(
            "Control device %s: %s.%s = %s",
            device_id,
            capability_type,
            instance,
            value,
        )

        return await self._request("POST", ENDPOINT_DEVICE_CONTROL, payload)

    async def turn_on(self, device_id: str, sku: str) -> dict[str, Any]:
        from .const import CAPABILITY_ON_OFF, INSTANCE_POWER_SWITCH

        return await self.control_device(
            device_id, sku, CAPABILITY_ON_OFF, INSTANCE_POWER_SWITCH, 1
        )

    async def turn_off(self, device_id: str, sku: str) -> dict[str, Any]:
        from .const import CAPABILITY_ON_OFF, INSTANCE_POWER_SWITCH

        return await self.control_device(
            device_id, sku, CAPABILITY_ON_OFF, INSTANCE_POWER_SWITCH, 0
        )

    async def set_nightlight(
        self, device_id: str, sku: str, on: bool
    ) -> dict[str, Any]:
        from .const import CAPABILITY_TOGGLE, INSTANCE_NIGHTLIGHT_TOGGLE

        return await self.control_device(
            device_id, sku, CAPABILITY_TOGGLE, INSTANCE_NIGHTLIGHT_TOGGLE, 1 if on else 0
        )

    async def set_brightness(
        self, device_id: str, sku: str, brightness: int
    ) -> dict[str, Any]:
        from .const import CAPABILITY_RANGE, INSTANCE_BRIGHTNESS

        return await self.control_device(
            device_id, sku, CAPABILITY_RANGE, INSTANCE_BRIGHTNESS, brightness
        )

    async def set_color_rgb(
        self, device_id: str, sku: str, rgb: tuple[int, int, int]
    ) -> dict[str, Any]:
        from .const import CAPABILITY_COLOR_SETTING, INSTANCE_COLOR_RGB

        r, g, b = rgb
        color_int = (r << 16) + (g << 8) + b

        return await self.control_device(
            device_id, sku, CAPABILITY_COLOR_SETTING, INSTANCE_COLOR_RGB, color_int
        )

    async def set_color_temp(
        self, device_id: str, sku: str, temp_kelvin: int
    ) -> dict[str, Any]:
        from .const import (
            CAPABILITY_COLOR_SETTING,
            COLOR_TEMP_MAX,
            COLOR_TEMP_MIN,
            INSTANCE_COLOR_TEMP,
        )

        temp_kelvin = max(COLOR_TEMP_MIN, min(COLOR_TEMP_MAX, temp_kelvin))

        return await self.control_device(
            device_id, sku, CAPABILITY_COLOR_SETTING, INSTANCE_COLOR_TEMP, temp_kelvin
        )

    async def set_scene(
        self, device_id: str, sku: str, scene_value: dict[str, Any]
    ) -> dict[str, Any]:
        from .const import CAPABILITY_DYNAMIC_SCENE, INSTANCE_LIGHT_SCENE

        return await self.control_device(
            device_id, sku, CAPABILITY_DYNAMIC_SCENE, INSTANCE_LIGHT_SCENE, scene_value
        )

    async def set_diy_scene(
        self, device_id: str, sku: str, diy_value: dict[str, Any]
    ) -> dict[str, Any]:
        from .const import CAPABILITY_DYNAMIC_SCENE, INSTANCE_DIY_SCENE

        return await self.control_device(
            device_id, sku, CAPABILITY_DYNAMIC_SCENE, INSTANCE_DIY_SCENE, diy_value
        )

    async def set_segment_color(
        self,
        device_id: str,
        sku: str,
        segment: int,
        rgb: tuple[int, int, int],
    ) -> dict[str, Any]:
        from .const import CAPABILITY_SEGMENT_COLOR, INSTANCE_SEGMENTED_COLOR

        r, g, b = rgb
        value = {
            "segment": [segment],
            "rgb": (r << 16) + (g << 8) + b,
        }

        return await self.control_device(
            device_id, sku, CAPABILITY_SEGMENT_COLOR, INSTANCE_SEGMENTED_COLOR, value
        )

    async def set_segment_brightness(
        self,
        device_id: str,
        sku: str,
        segment: int,
        brightness: int,
    ) -> dict[str, Any]:
        from .const import CAPABILITY_SEGMENT_COLOR, INSTANCE_SEGMENTED_BRIGHTNESS

        value = {
            "segment": [segment],
            "brightness": brightness,
        }

        return await self.control_device(
            device_id,
            sku,
            CAPABILITY_SEGMENT_COLOR,
            INSTANCE_SEGMENTED_BRIGHTNESS,
            value,
        )

    async def set_music_mode(
        self,
        device_id: str,
        sku: str,
        mode: str,
        sensitivity: int = 50,
        auto_color: bool = True,
        rgb: tuple[int, int, int] | None = None,
    ) -> dict[str, Any]:
        from .const import CAPABILITY_MUSIC_SETTING, INSTANCE_MUSIC_MODE

        value: dict[str, Any] = {
            "musicMode": mode,
            "sensitivity": sensitivity,
            "autoColor": 1 if auto_color else 0,
        }

        if not auto_color and rgb:
            r, g, b = rgb
            value["color"] = (r << 16) + (g << 8) + b

        return await self.control_device(
            device_id, sku, CAPABILITY_MUSIC_SETTING, INSTANCE_MUSIC_MODE, value
        )

    async def get_dynamic_scenes(
        self, device_id: str, sku: str
    ) -> list[dict[str, Any]]:
        payload = {
            "requestId": str(uuid.uuid4()),
            "payload": {
                "sku": sku,
                "device": device_id,
            },
        }

        response = await self._request("POST", ENDPOINT_DYNAMIC_SCENES, payload)
        capabilities = response.get("payload", {}).get("capabilities", [])

        scenes = []
        for cap in capabilities:
            if cap.get("instance") == "lightScene":
                parameters = cap.get("parameters", {})
                options = parameters.get("options", [])
                scenes.extend(options)

        return scenes

    async def get_diy_scenes(self, device_id: str, sku: str) -> list[dict[str, Any]]:
        payload = {
            "requestId": str(uuid.uuid4()),
            "payload": {
                "sku": sku,
                "device": device_id,
            },
        }

        response = await self._request("POST", ENDPOINT_DIY_SCENES, payload)
        capabilities = response.get("payload", {}).get("capabilities", [])

        scenes = []
        for cap in capabilities:
            if cap.get("instance") == "diyScene":
                parameters = cap.get("parameters", {})
                options = parameters.get("options", [])
                scenes.extend(options)

        return scenes

    async def test_connection(self) -> bool:
        await self.get_devices()
        return True
