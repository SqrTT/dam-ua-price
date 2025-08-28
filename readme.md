# Інтеграція Ринку Доби Наперед (РДН) для Home Assistant

##### [English version below](#dam-integration-for-home-assistant)

[ОРЕЕ](https://www.oree.com.ua/) — це оператор ринку, який управляє ринком електроенергії та послугами енергосистеми, включаючи торгівлю електроенергією на ринку на добу наперед в Україні.

Ця інтеграція надає спотові ринкові (погодинні, РДН) ціни на електроенергію для України.

Інтеграція надає поточну ціну з цінами на сьогодні та завтра як сенсори.

> **Увага:** Ця інтеграція використовує зворотну інженерію для отримання необхідних даних з ОРЕЕ. Це може перестати працювати в будь-який момент, якщо/коли ОРЕЕ змінить свій веб-сайт.

### Зміст
**[Встановлення](#встановлення)**<br>
**[Використання](#використання)**<br>

## Встановлення

### Вручну
Завантажте [останню версію](https://github.com/SqrTT/dam-ua-price/releases)

```bash
cd YOUR_HASS_CONFIG_DIRECTORY    # те ж місце, де configuration.yaml
mkdir -p custom_components/dam-ua-price
cd custom_components/dam-ua-price
unzip dam-ua-price-X.Y.Z.zip
mv dam-ua-price-X.Y.Z/custom_components/dam-ua-price/* .
```

## Використання

### Змінні конфігурації
| Конфігурація         | Обов'язково | Опис                          |
|----------------------| ----------- | ----------------------------- |
| meter_zones          | **так**     | Кількість зон вашого лічильника електроенергії. Зазвичай 2 зони (день/ніч) |
| price                | **так**     | Ціна на електроенергію для особистого користування (включаючи ПДВ). Наразі дорівнює 4,32 грн |

### Інтерфейс користувача
- Перейдіть до `Налаштування` -> `Пристрої та служби`
- Виберіть `+ Додати інтеграцію`
- Знайдіть `dam-ua-price` та виберіть її
- Заповніть необхідні значення та натисніть `Надіслати`

Порада: За замовчуванням інтеграція створить сенсор з назвою `dam-ua-price-<ІМЯ СЕНСОРУ>`. Рекомендується перейменувати сенсор та всі його сутності на ваш вибір. Якщо вам потрібно перестоврити свій сенсор, всі автоматизації та панелі керування продовжують працювати.


----


# DAM integration for Home Assistant

[OREE](https://www.oree.com.ua/) is a market operator that operates an electricity market and power system services, including the exchange of electricity on a Day Ahead Market in Ukraine.

This integration provides the spot market (hourly, DAM) electricity prices for the Ukraine.

The integration provides the current price with today's and tomorrow's prices as attributes.


> **Note:** This integration uses reverse engineering to obtain the necessary data from OREE. This could break at any time if\when OREE changes their website. 

### Table of Contents
**[Installation](#installation)**<br>
**[Usage](#usage)**<br>


## Installation


### Manual
Download the [latest release](https://github.com/SqrTT/dam-ua-price/releases)

```bash
cd YOUR_HASS_CONFIG_DIRECTORY    # same place as configuration.yaml
mkdir -p custom_components/dam-ua-price
cd custom_components/dam-ua-price
unzip dam-ua-price-X.Y.Z.zip
mv dam-ua-price-X.Y.Z/custom_components/dam-ua-price/* .
```

## Usage

### Configuration Variables
| Configuration        | Required | Description                   |
|----------------------| -------- | ----------------------------- |
| meter_zones          | **yes**  | Number of zones of your electricity meter. Usually 2 zones (day/night) |
| price                | **yes**  | Electricity price for personal use (including VAT). Currently is 4.32 UAH|

### UI
- Go to `Settings` -> `Devices & Services`
- Select `+ Add Integration`
- Search for `dam-ua-price` and select it
- Fill in the required fields and press `Submit`

Tip: By default, the integration will create a sensors with the names `dam-ua-price-<sensor name>`. It is recommended to rename the sensors and all its entities to your preferred variant. If you need to recreate your sensor (for example, to change the additional cost), all automations and dashboards keep working.

