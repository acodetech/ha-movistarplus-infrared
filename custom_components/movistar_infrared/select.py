"""Select platform for Movistar+ Infrared integration."""

import re

from homeassistant.components.infrared import InfraredEmitterConsumerEntity
from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    MOVISTAR_CHANNELS,
    async_send_key_sequence,
    build_device_info,
    get_entry_settings,
)

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Movistar+ IR channel selector from config entry."""
    emitter_entity_id, repeat_count, digit_delay_ms = get_entry_settings(entry)

    async_add_entities(
        [MovistarChannelSelect(entry, emitter_entity_id, repeat_count, digit_delay_ms)]
    )


class MovistarChannelSelect(InfraredEmitterConsumerEntity, SelectEntity):
    """Native channel selector entity for Movistar+ decoder."""

    _attr_has_entity_name = True
    _attr_name = "Canal"
    _attr_icon = "mdi:television-play"
    _attr_options = list(MOVISTAR_CHANNELS)

    def __init__(
        self,
        entry: ConfigEntry,
        infrared_emitter_entity_id: str,
        repeat_count: int,
        digit_delay_ms: int,
    ) -> None:
        """Initialize the channel selector."""
        self._entry = entry
        self._infrared_emitter_entity_id = infrared_emitter_entity_id
        self._repeat_count = repeat_count
        self._digit_delay_ms = digit_delay_ms
        self._attr_unique_id = f"{entry.entry_id}_channel"
        self._attr_current_option = MOVISTAR_CHANNELS[0]
        self._attr_device_info = build_device_info(entry)

    async def async_select_option(self, option: str) -> None:
        """Tune the decoder to the selected channel number."""
        match = re.match(r"^(\d+)", option.strip())
        if not match:
            return
        keys = [f"num_{digit}" for digit in match.group(1)]
        await async_send_key_sequence(
            self._send_command,
            keys,
            self._repeat_count,
            self._digit_delay_ms / 1000.0,
        )
        self._attr_current_option = option
        self.async_write_ha_state()
