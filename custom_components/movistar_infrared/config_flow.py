"""Config flow for Movistar+ Infrared integration."""

from typing import Any
import voluptuous as vol

from homeassistant.components.infrared import (
    DOMAIN as INFRARED_DOMAIN,
    async_get_emitters,
)
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TextSelector,
)

from .const import (
    CONF_DIGIT_DELAY_MS,
    CONF_INFRARED_EMITTER_ENTITY_ID,
    CONF_REPEAT_COUNT,
    DEFAULT_DIGIT_DELAY_MS,
    DEFAULT_NAME,
    DEFAULT_REPEAT_COUNT,
    DOMAIN,
)


def _emitter_selector(emitters: list[str]) -> EntitySelector:
    """Build an EntitySelector for infrared emitters."""
    config = (
        EntitySelectorConfig(domain=INFRARED_DOMAIN, include_entities=emitters)
        if emitters
        else EntitySelectorConfig(domain=INFRARED_DOMAIN)
    )
    return EntitySelector(config)


class MovistarInfraredConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle config flow for Movistar+ Infrared."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> "MovistarInfraredOptionsFlow":
        """Return the options flow."""
        return MovistarInfraredOptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle initial user step."""
        emitter_entity_ids = list(async_get_emitters(self.hass))
        if not emitter_entity_ids:
            return self.async_abort(reason="no_emitters")

        if user_input is not None:
            entity_id = user_input[CONF_INFRARED_EMITTER_ENTITY_ID]
            name = user_input.get("name", DEFAULT_NAME)

            await self.async_set_unique_id(f"movistar_infrared_{entity_id}")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(title=name, data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("name", default=DEFAULT_NAME): TextSelector(),
                    vol.Required(CONF_INFRARED_EMITTER_ENTITY_ID): _emitter_selector(
                        emitter_entity_ids
                    ),
                }
            ),
        )


class MovistarInfraredOptionsFlow(OptionsFlow):
    """Handle options flow for Movistar+ Infrared."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the integration options."""
        if user_input is not None:
            return self.async_create_entry(
                title="",
                data={
                    CONF_INFRARED_EMITTER_ENTITY_ID: user_input[
                        CONF_INFRARED_EMITTER_ENTITY_ID
                    ],
                    CONF_REPEAT_COUNT: int(user_input[CONF_REPEAT_COUNT]),
                    CONF_DIGIT_DELAY_MS: int(user_input[CONF_DIGIT_DELAY_MS]),
                },
            )

        current_emitter = self.config_entry.options.get(
            CONF_INFRARED_EMITTER_ENTITY_ID,
            self.config_entry.data.get(CONF_INFRARED_EMITTER_ENTITY_ID, ""),
        )
        current_repeats = int(
            self.config_entry.options.get(CONF_REPEAT_COUNT, DEFAULT_REPEAT_COUNT)
        )
        current_delay = int(
            self.config_entry.options.get(CONF_DIGIT_DELAY_MS, DEFAULT_DIGIT_DELAY_MS)
        )

        emitters = list(async_get_emitters(self.hass))
        if current_emitter and current_emitter not in emitters:
            emitters.insert(0, current_emitter)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_INFRARED_EMITTER_ENTITY_ID, default=current_emitter
                    ): _emitter_selector(emitters),
                    vol.Required(
                        CONF_REPEAT_COUNT, default=current_repeats
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=1,
                            max=5,
                            step=1,
                            mode=NumberSelectorMode.BOX,
                        )
                    ),
                    vol.Required(
                        CONF_DIGIT_DELAY_MS, default=current_delay
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=100,
                            max=1000,
                            step=50,
                            unit_of_measurement="ms",
                            mode=NumberSelectorMode.BOX,
                        )
                    ),
                }
            ),
        )
