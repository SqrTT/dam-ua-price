from homeassistant.const import Platform
import logging

LOGGER = logging.getLogger(__package__)

DOMAIN = "sqrtt-dam-ua-price"
DEFAULT_NAME = "UA Day Ahead Market Price (РДН)"

METER_ZONES = "meter_zones"

PLATFORMS = [Platform.SENSOR]

CONF_BASE_PRICE = "price"

