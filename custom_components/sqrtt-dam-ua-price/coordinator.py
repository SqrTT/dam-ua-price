"""DataUpdateCoordinator for the integration."""

from __future__ import annotations
from random import random
from typing import Any
import json
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

import aiohttp


from homeassistant.const import CONF_CURRENCY
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_point_in_utc_time
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import DOMAIN, LOGGER
from .utils import TimeRangePrice

if TYPE_CHECKING:
    from . import DAMConfigEntry

kiev_tz = ZoneInfo("Europe/Kiev")

class DAMDataUpdateCoordinator(DataUpdateCoordinator[list[TimeRangePrice]]):
    """A DAM Data Update Coordinator."""

    config_entry: DAMConfigEntry
    updated_at: datetime | None = None

    pricesDayData: dict[str, list[TimeRangePrice]]
    updateMinute: int = 0.0
    updateSecond: int = 0.0

    def __init__(self, hass: HomeAssistant, config_entry: DAMConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
        )
        self.unsubHourly: Callable[[], None] | None = None
        self.unsubSyncPrices: Callable[[], None] | None = None
        self.pricesDayData = {}

        self.updateMinute = int(random() * 59)
        self.updateSecond = int(random() * 59)

    async def init(self):
        await self.fetch_data(dt_util.utcnow())
        await self.hourly_update(dt_util.utcnow())

    def get_next_hourly_interval(self, now: datetime) -> datetime:
        """Compute next time an update should occur."""
        next_hour = dt_util.utcnow() + timedelta(hours=1)
        next_run = datetime(
            next_hour.year,
            next_hour.month,
            next_hour.day,
            next_hour.hour,
            tzinfo=dt_util.UTC,
        )
        LOGGER.debug("Next sensors update at %s", next_run)
        return next_run

    async def async_shutdown(self) -> None:
        """Cancel any scheduled call, and ignore new runs."""
        await super().async_shutdown()
        if self.unsubHourly:
            self.unsubHourly()
            self.unsubHourly = None

        if self.unsubSyncPrices:
            self.unsubSyncPrices()
            self.unsubSyncPrices = None

    async def hourly_update(self, now: datetime, retry: int = 3) -> None:
        self.unsubHourly = async_track_point_in_utc_time(
            self.hass, self.hourly_update, self.get_next_hourly_interval(now)
        )

        self.async_set_updated_data(self.pricesDayData)

    async def fetch_data(self, now: datetime) -> None:
        """Fetch data."""
        next_day = now + timedelta(days=1)
        next_run = datetime(
            next_day.year,
            next_day.month,
            next_day.day,
            20,
            minute=self.updateMinute,
            second=self.updateSecond,
            tzinfo=kiev_tz,
        )
        LOGGER.debug("Next rdn update at %s", next_run)
        kiev_now = now.astimezone(kiev_tz)

        kiev_time_str = kiev_now.strftime('%d.%m.%Y')
        kiev_time_tomorrow_str = next_day.astimezone(kiev_tz).strftime('%d.%m.%Y')

        if self.unsubSyncPrices:
            self.unsubSyncPrices()
            self.unsubSyncPrices = None

        self.unsubSyncPrices = async_track_point_in_utc_time(
            self.hass, self.fetch_data, next_run
        )

        if not self.pricesDayData.get(kiev_time_str):
            todayData = await self.api_call(now)

            if todayData: 
                self.pricesDayData[kiev_time_str] = todayData
                self.updated_at = now
        
        if kiev_now.hour >= 20 and not self.pricesDayData.get(kiev_time_tomorrow_str):
            tomorrowData = await self.api_call(next_day)

            if tomorrowData:
                self.pricesDayData[kiev_time_tomorrow_str] = tomorrowData
                self.updated_at = now
        elif kiev_now.hour < 20:
            next_run_today_later = datetime(
                kiev_now.year,
                kiev_now.month,
                kiev_now.day,
                20,
                minute=self.updateMinute,
                second=self.updateSecond,
                tzinfo=kiev_tz,
            )
            if self.unsubSyncPrices:
                self.unsubSyncPrices()
                self.unsubSyncPrices = None

            self.unsubSyncPrices = async_track_point_in_utc_time(
                self.hass, self.fetch_data, next_run_today_later
            )

    async def api_call(self, now: datetime, retry: int = 3):
        """Make api call to retrieve data with retry if failure."""
        ## array of numbers
        data: list[float] = []
        kiev_time_str = now.astimezone(kiev_tz).strftime('%d.%m.%Y')
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"https://www.oree.com.ua/index.php/PXS/get_pxs_hdata/{kiev_time_str}/DAM/2",
                    headers={'accept': 'application/json, text/javascript, */*; q=0.01', 'x-requested-with': 'XMLHttpRequest'}
                ) as response:
                    response.raise_for_status()
                    text = await response.text()
                    dataJson = json.loads(text)

                    if pricesData := dataJson.get("pricesData"):
                        data = pricesData

            except aiohttp.ClientError as error:
                LOGGER.debug("Connection error: %s", error)
                self.async_set_update_error(error)

        if data and len(data) == 24:
            priceRanges : list[TimeRangePrice] = []
            for i, value in enumerate(data):
                start = now.replace(hour=i, minute=0, second=0, microsecond=0, tzinfo=kiev_tz).timestamp()
                end = start + timedelta(hours=1).total_seconds()
                priceRanges.append(TimeRangePrice(start = start, end = end, value = value / 1000))

            return priceRanges

        self.async_set_update_error(Exception("No current day data"))
        return None
    
    def get_all_price_entries(self) -> list[TimeRangePrice]:
        """Return all price entries."""
        entries: list[TimeRangePrice] = []

        for del_period in self.pricesDayData.values():
            entries.extend(del_period)

        return entries

    def get_data_current_day(self) -> list[TimeRangePrice]:
        """Return the current day data."""
        current_day = dt_util.utcnow().astimezone(kiev_tz).strftime('%d.%m.%Y')
        delivery_period = self.pricesDayData.get(current_day)

        if delivery_period:
            return delivery_period

        return []

    def get_current_zone_rate(self) -> float:
        """Return the current zone rate."""
        meter_zones = self.config_entry.data.get("meter_zones") or "2"

        match meter_zones:
            case "1":
                return 1.0
            case "2":
                hour = dt_util.utcnow().astimezone(kiev_tz).hour
                # from 23:00 to 7:00 — 0.5
                if hour >= 23 or hour < 7:
                    return 0.5

                # from 7:00 to 23:00 — 1.0
                return 1.0
            case "3":
                hour = dt_util.utcnow().astimezone(kiev_tz).hour

                # from 23:00 to 7:00 — 0.4
                if hour >= 23 or hour < 7:
                    return 0.4
                # from 8:00 to 11:00 and from 20:00 to 22:00 — 1.5
                elif (8 <= hour <= 11) or (20 <= hour <= 22):
                    return 1.5
                # from 7:00 to 8:00, from 11:00 to 20:00 and from 22:00 to 23:00 — 1.0
                else:
                    return 1.0

