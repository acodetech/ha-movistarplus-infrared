"""Button platform for Movistar+ Infrared integration."""

from homeassistant.components.button import ButtonEntity
from homeassistant.components.infrared import InfraredEmitterConsumerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    MOVISTAR_BUTTONS,
    MovistarButtonDef,
    ProntoCommand,
    build_device_info,
    get_entry_settings,
)

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Movistar+ IR buttons from config entry."""
    emitter_entity_id, repeat_count, _ = get_entry_settings(entry)

    async_add_entities(
        [
            MovistarIrButton(entry, emitter_entity_id, btn_def, repeat_count)
            for btn_def in MOVISTAR_BUTTONS
        ]
    )


class MovistarIrButton(InfraredEmitterConsumerEntity, ButtonEntity):
    """Representation of a Movistar+ remote button."""

    _attr_has_entity_name = True

    def __init__(
        self,
        entry: ConfigEntry,
        infrared_emitter_entity_id: str,
        btn_def: MovistarButtonDef,
        repeat_count: int,
    ) -> None:
        """Initialize button."""
        self._entry = entry
        self._infrared_emitter_entity_id = infrared_emitter_entity_id
        self._btn_def = btn_def
        self._attr_unique_id = f"{entry.entry_id}_{btn_def.key}"
        self._attr_name = btn_def.name
        self._attr_icon = btn_def.icon
        self._command = ProntoCommand(btn_def.code, repeat_count=repeat_count)
        self._attr_device_info = build_device_info(entry)

    async def async_press(self) -> None:
        """Press the button."""
        await self._send_command(self._command)
