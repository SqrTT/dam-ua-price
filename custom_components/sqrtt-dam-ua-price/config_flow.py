"""Adds config flow for integration."""

from __future__ import annotations

from typing import Any


import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_CURRENCY
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    NumberSelectorConfig,
    NumberSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)
from homeassistant.util import dt as dt_util

from .const import METER_ZONES, DEFAULT_NAME, DOMAIN, CONF_BASE_PRICE

# SELECT_AREAS = [
#     SelectOptionDict(value=area, label=name) for area, name in AREAS.items()
# ]
SELECT_CURRENCY = ["1", "2", "3"]

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(METER_ZONES, default="2"): SelectSelector(
            SelectSelectorConfig(
                options=SELECT_CURRENCY,
                multiple=False,
                mode=SelectSelectorMode.DROPDOWN,
                sort=True,
            )
        ),
        vol.Required(CONF_BASE_PRICE, default=4.32): NumberSelector(
            NumberSelectorConfig(
                min=0,
                max=1000,
                step=0.01,
                unit_of_measurement="UAH",
                mode="box",
            )
        ),
    }
)


async def test_api(hass: HomeAssistant, user_input: dict[str, Any]) -> dict[str, str]:


    return {}


class DAMConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for integration."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input:
            errors = await test_api(self.hass, user_input)
            if not errors:
                return self.async_create_entry(
                    title=DEFAULT_NAME,
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the reconfiguration step."""
        reconfigure_entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input:
            errors = await test_api(self.hass, user_input)
            if not errors:
                return self.async_update_reload_and_abort(
                    reconfigure_entry, data_updates=user_input
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                DATA_SCHEMA, user_input or reconfigure_entry.data
            ),
            errors=errors,
        )
