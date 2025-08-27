"""Sensor platform for  integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from homeassistant.components.sensor import (
    EntityCategory,
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util, slugify

from . import DAMConfigEntry
from .const import LOGGER
from .coordinator import DAMDataUpdateCoordinator
from .entity import DAMBaseEntity

PARALLEL_UPDATES = 0


def validate_prices(
    func: Callable[
        [DAMPriceSensor],  tuple[float | None, float, float | None]
    ],
    entity: DAMPriceSensor,
    index: int,
) -> float | None:
    """Validate and return."""
    if (result := func(entity)[index]) is not None:
        return result
    return None

def get_household_price(
    entity: DAMPriceSensor,
) -> float | None:
    rate = entity.coordinator.get_current_zone_rate()
    price = entity.coordinator.config_entry.data.get("price")

    if price is not None:
        return price * rate

    return None

def get_household_selling_price(
    entity: DAMPriceSensor,
) -> float | None:
    rate = entity.coordinator.get_current_zone_rate()
    price = entity.coordinator.config_entry.data.get("price")
    rdn_price = get_prices(entity)[1]

    if price is not None and rdn_price is not None:
        # vat = 1.2
        return min((price * rate) / 1.2, rdn_price) 

    return None


def get_prices(
    entity: DAMPriceSensor,
) ->  tuple[float | None, float, float | None]:
    data = entity.coordinator.get_all_price_entries()
    last_price_entries: float | None = None
    current_price_entries: float | None = 0
    next_price_entries: float | None = None
    current_time = dt_util.now().timestamp()
    previous_time = current_time - timedelta(hours=1).total_seconds()
    next_time = current_time + timedelta(hours=1).total_seconds()
    LOGGER.debug("Price data: %s", data)
    for entry in data:
        if entry is not None and entry.contains(current_time):
            current_price_entries = entry.value
        if entry is not None and entry.contains(previous_time):
            last_price_entries = entry.value
        if entry is not None and entry.contains(next_time):
            next_price_entries = entry.value


    LOGGER.debug(
        "Last price %s, current price %s, next price %s",
        last_price_entries,
        current_price_entries,
        next_price_entries,
    )

    result = (
            last_price_entries,
            current_price_entries,
            next_price_entries,
        )
    LOGGER.debug("Prices: %s", result)
    return result


def get_min_max_price(
    entity: DAMPriceSensor,
    func: Callable[[float, float], float],
) -> tuple[float, datetime, datetime]:
    """Get the lowest price from the data."""
    data = entity.coordinator.get_data_current_day()
    price_data = data
    price: float = price_data[0].value
    start: float = price_data[0].start
    end: float = price_data[0].end
    for entry in price_data:
        _price = entry.value

        if _price == func(price, _price):
            price = _price
            start = entry.start
            end = entry.end

    return (price, datetime.fromtimestamp(start).astimezone(ZoneInfo("Europe/Kiev")), datetime.fromtimestamp(end).astimezone(ZoneInfo("Europe/Kiev")))


# def get_blockprices(
#     entity: DAMBlockPriceSensor,
# ) -> dict[str, dict[str, tuple[datetime, datetime, float, float, float]]]:
#     """Return average, min and max for block prices.

#     Output: {"SE3": {"Off-peak 1": (_datetime_, _datetime_, 9.3, 10.5, 12.1)}}
#     """
#     data = entity.coordinator.get_data_current_day()
#     result: dict[str, dict[str, tuple[datetime, datetime, float, float, float]]] = {}
#     block_prices = data.block_prices
#     for entry in block_prices:
#         for _area in entry.average:
#             if _area not in result:
#                 result[_area] = {}
#             result[_area][entry.name] = (
#                 entry.start,
#                 entry.end,
#                 entry.average[_area]["average"],
#                 entry.average[_area]["min"],
#                 entry.average[_area]["max"],
#             )

#     LOGGER.debug("Block prices: %s", result)
#     return result


@dataclass(frozen=True, kw_only=True)
class DAMDefaultSensorEntityDescription(SensorEntityDescription):
    """Describes  default sensor entity."""

    value_fn: Callable[[DAMSensor], str | float | datetime | None]


@dataclass(frozen=True, kw_only=True)
class DAMPricesSensorEntityDescription(SensorEntityDescription):
    """Describes  prices sensor entity."""

    value_fn: Callable[[DAMPriceSensor], float | None]
    extra_fn: Callable[[DAMPriceSensor], dict[str, str] | None]


@dataclass(frozen=True, kw_only=True)
class DAMBlockPricesSensorEntityDescription(SensorEntityDescription):
    """Describes  block prices sensor entity."""

    value_fn: Callable[
        [tuple[datetime, datetime, float, float, float]], float | datetime | None
    ]


DEFAULT_SENSOR_TYPES: tuple[DAMDefaultSensorEntityDescription, ...] = (
    DAMDefaultSensorEntityDescription(
        key="updated_at",
        translation_key="updated_at",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda entity: entity.coordinator.updated_at,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)
PRICES_SENSOR_TYPES: tuple[DAMPricesSensorEntityDescription, ...] = (
    DAMPricesSensorEntityDescription(
        key="current_price",
        translation_key="current_price",
        value_fn=lambda entity: validate_prices(get_prices, entity, 1),
        extra_fn=lambda entity: {
            "today_prices": [x.value for x in entity.coordinator.get_data_current_day()],
        },
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    DAMPricesSensorEntityDescription(
        key="current_household_price",
        translation_key="current_household_price",
        value_fn=lambda entity: get_household_price(entity),
        extra_fn=lambda entity: None,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        entity_registry_enabled_default=False,
    ),
    DAMPricesSensorEntityDescription(
        key="current_household_selling_price",
        translation_key="current_household_selling_price",
        value_fn=lambda entity: get_household_selling_price(entity),
        extra_fn=lambda entity: None,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        entity_registry_enabled_default=False,
    ),
    DAMPricesSensorEntityDescription(
        key="last_price",
        translation_key="last_price",
        value_fn=lambda entity: validate_prices(get_prices, entity, 0),
        extra_fn=lambda entity: None,
        suggested_display_precision=2,
    ),
    DAMPricesSensorEntityDescription(
        key="next_price",
        translation_key="next_price",
        value_fn=lambda entity: validate_prices(get_prices, entity, 2),
        extra_fn=lambda entity: None,
        suggested_display_precision=2,
    ),
    DAMPricesSensorEntityDescription(
        key="lowest_price",
        translation_key="lowest_price",
        value_fn=lambda entity: get_min_max_price(entity, min)[0],
        extra_fn=lambda entity: {
            "start": get_min_max_price(entity, min)[1].isoformat(),
            "end": get_min_max_price(entity, min)[2].isoformat(),
        },
        suggested_display_precision=2,
    ),
    DAMPricesSensorEntityDescription(
        key="highest_price",
        translation_key="highest_price",
        value_fn=lambda entity: get_min_max_price(entity, max)[0],
        extra_fn=lambda entity: {
            "start": get_min_max_price(entity, max)[1].isoformat(),
            "end": get_min_max_price(entity, max)[2].isoformat(),
        },
        suggested_display_precision=2,
    ),
)

DAILY_AVERAGE_PRICES_SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="daily_average",
        translation_key="daily_average",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        entity_registry_enabled_default=False,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DAMConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up sensor platform."""

    coordinator = entry.runtime_data
    current_day_data = entry.runtime_data.get_data_current_day()

    entities: list[DAMBaseEntity] = []


    LOGGER.debug("Setting up base sensors",)
    entities.extend(
        DAMSensor(coordinator, description)
        for description in DEFAULT_SENSOR_TYPES
    )
    LOGGER.debug(
        "Setting up price sensors for with currency"
    )
    entities.extend(
        DAMPriceSensor(coordinator, description)
        for description in PRICES_SENSOR_TYPES
    )
    entities.extend(
        DAMDailyAveragePriceSensor(coordinator, description)
        for description in DAILY_AVERAGE_PRICES_SENSOR_TYPES
    )
    async_add_entities(entities)


class DAMSensor(DAMBaseEntity, SensorEntity):
    """Representation of a  sensor."""

    entity_description: DAMDefaultSensorEntityDescription

    @property
    def native_value(self) -> str | float | datetime | None:
        """Return value of sensor."""
        return self.entity_description.value_fn(self)


class DAMPriceSensor(DAMBaseEntity, SensorEntity):
    """Representation of price sensor."""

    entity_description: DAMPricesSensorEntityDescription

    def __init__(
        self,
        coordinator: DAMDataUpdateCoordinator,
        entity_description: DAMPricesSensorEntityDescription
    ) -> None:
        """Initiate sensor."""
        super().__init__(coordinator, entity_description)
        self._attr_native_unit_of_measurement = "UAH/kWh"

    @property
    def native_value(self) -> float | None:
        """Return value of sensor."""
        return self.entity_description.value_fn(self)

    @property
    def extra_state_attributes(self) -> dict[str, str] | None:
        """Return the extra state attributes."""
        return self.entity_description.extra_fn(self)



class DAMDailyAveragePriceSensor(DAMBaseEntity, SensorEntity):
    """Representation of a  daily average price sensor."""

    entity_description: SensorEntityDescription

    def __init__(
        self,
        coordinator: DAMDataUpdateCoordinator,
        entity_description: SensorEntityDescription,
    ) -> None:
        """Initiate  sensor."""
        super().__init__(coordinator, entity_description)
        self._attr_native_unit_of_measurement = f"UAH/kWh"

    @property
    def native_value(self) -> float | None:
        """Return value of sensor."""
        data = self.coordinator.get_data_current_day()
        values = [x.value for x in data]
        ### avg value
        return sum(values) / len(values) if values else None
