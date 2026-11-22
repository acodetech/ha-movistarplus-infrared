"""Remote platform for Movistar+ Infrared integration."""

from collections.abc import Iterable
from typing import Any

from homeassistant.components.infrared import InfraredEmitterConsumerEntity
from homeassistant.components.remote import RemoteEntity, RemoteEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    MOVISTAR_CODE_MAP,
    ProntoCommand,
    async_send_key_sequence,
    build_device_info,
    expand_digit_commands,
    get_entry_settings,
)

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Movistar+ IR remote from config entry."""
    emitter_entity_id, repeat_count, digit_delay_ms = get_entry_settings(entry)

    async_add_entities(
        [MovistarIrRemote(entry, emitter_entity_id, repeat_count, digit_delay_ms)]
    )


class MovistarIrRemote(InfraredEmitterConsumerEntity, RemoteEntity):
    """Representation of a Movistar+ Remote entity."""

    _attr_has_entity_name = True
    _attr_name = "Mando"
    _attr_supported_features = RemoteEntityFeature(0)

    def __init__(
        self,
        entry: ConfigEntry,
        infrared_emitter_entity_id: str,
        repeat_count: int,
        digit_delay_ms: int,
    ) -> None:
        """Initialize remote."""
        self._entry = entry
        self._infrared_emitter_entity_id = infrared_emitter_entity_id
        self._repeat_count = repeat_count
        self._digit_delay_ms = digit_delay_ms
        self._attr_unique_id = f"{entry.entry_id}_remote"
        self._attr_is_on = True
        self._attr_device_info = build_device_info(entry)

    async def async_send_command(self, command: Iterable[str], **kwargs: Any) -> None:
        """Send a list of button keys or dial numbers."""
        raw_repeats = kwargs.get("num_repeats")
        num_repeats = self._repeat_count if raw_repeats is None else int(raw_repeats)
        raw_delay = kwargs.get("delay_secs")
        delay_secs = (
            self._digit_delay_ms / 1000.0
            if raw_delay is None
            else float(raw_delay)
        )

        keys: list[str] = []
        for cmd_key in command:
            clean_key = cmd_key.strip().lower()
            if clean_key in MOVISTAR_CODE_MAP:
                keys.append(clean_key)
            elif expanded := expand_digit_commands(clean_key):
                keys.extend(expanded)

        await async_send_key_sequence(self._send_command, keys, num_repeats, delay_secs)

    async def _async_send_power(self, is_on: bool) -> None:
        """Toggle decoder power and update optimistic state."""
        code = MOVISTAR_CODE_MAP.get("power") or MOVISTAR_CODE_MAP.get("power_toggle")
        if code:
            await self._send_command(ProntoCommand(code, repeat_count=self._repeat_count))
        self._attr_is_on = is_on
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the deco on."""
        await self._async_send_power(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the deco off."""
        await self._async_send_power(False)
