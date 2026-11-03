# Elektrobock PT32 WiFi pro Home Assistant

[![HACS](https://img.shields.io/badge/HACS-vlastní%20repozitář-41BDF5.svg)](https://hacs.xyz/docs/faq/custom_repositories/)
[![Vydání](https://img.shields.io/github/v/release/Mejroo/eob-pt32-ha)](https://github.com/Mejroo/eob-pt32-ha/releases)
[![Kontrola](https://github.com/Mejroo/eob-pt32-ha/actions/workflows/validate.yml/badge.svg)](https://github.com/Mejroo/eob-pt32-ha/actions/workflows/validate.yml)
[![Licence](https://img.shields.io/github/license/Mejroo/eob-pt32-ha)](LICENSE)

> ⚠️ **BETA** – integrace vznikla odposlechem aplikace a je v aktivním vývoji. Některé funkce
> mohou chybět nebo nefungovat. Používáte ji na vlastní riziko.

## Podporovaná zařízení

| Zařízení | Stav |
|---|---|
| **PT32 WiFi** (aplikace EOB PT-WIFI, `deviceType` 0) | ✅ podporováno, vyzkoušeno s firmwarem 14.03 |
| PT32 GSM, BPT725, PH-CJ37/38/39, BT52W, U2, TS11 … | ❌ nepodporováno (jiný protokol) |

Pro zásuvky a termostaty TS11 existuje samostatná komunitní integrace
[eob-wifi-hass](https://github.com/jakubhegr18-design/eob-wifi-hass).

## Popis

Integrace ovládá bezdrátový termostat Elektrobock PT32 WiFi stejně jako mobilní aplikace
**EOB PT-WIFI**: přes cloud výrobce (REST + MQTT přes WebSocket). Termostat sám nemá žádné
lokální rozhraní, takže bez internetu ho nejde ovládat ani touto integrací.

Zapisují se jen příkazy, které aplikace prokazatelně posílá. Každý zápis termostat potvrdí;
když potvrzení nepřijde, integrace zápis až dvakrát zopakuje a pak v HA ohlásí chybu.

## Funkce

| Entita | Typ | Popis |
|---|---|---|
| Termostat | `climate` | skutečná teplota s desetinami, nastavená teplota, režimy **Auto** (program), **Manuál** a **Vypnuto**, informace o sepnutí kotle; rozsah teploty se bere z termostatu |
| Program | `select` | výběr z 9 programů (názvy z termostatu); v atributech je týdenní rozvrh aktivního programu |
| Kotel | `binary_sensor` | kotel sepnutý / vypnutý |
| Hodiny provozu kotle | `sensor` | počítadlo termostatu (h) |
| Korekce teploty | `number` | posun měřené teploty (°C) |
| Hystereze | `number` | 0,1–1,0 °C |
| Minimální doba zapnutí | `number` | 1–10 min |
| Zámek klávesnice | `switch` | zamknutí tlačítek na termostatu |
| Spojení, Naposledy viděn | diagnostika | zda termostat odpovídá přes cloud |
| Firmware, Údržba kotle | diagnostika | verze firmwaru a datum údržby kotle z nastavení |

Další chování:

- Změna teploty v režimu Auto přepne termostat do Manuálu, stejně jako na termostatu.
- Výběr programu přepne termostat do režimu Auto.
- Název termostatu se jednou za hodinu převezme z účtu (přejmenování v aplikaci).
- Stav se čte každou minutu, nastavení a programy jednou za hodinu.

## Instalace

### HACS (doporučeno)

[![Otevřít v HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Mejroo&repository=eob-pt32-ha&category=integration)

Nebo ručně:

1. Otevřete **HACS** v Home Assistantu.
2. Vpravo nahoře **⋮ → Vlastní repozitáře**.
3. Přidejte `https://github.com/Mejroo/eob-pt32-ha` s typem **Integrace**.
4. Vyhledejte **Elektrobock PT32 WiFi** a klikněte na **Stáhnout**.
5. Restartujte Home Assistant.

### Ručně

1. Stáhněte `eob_pt32.zip` z posledního [vydání](https://github.com/Mejroo/eob-pt32-ha/releases).
2. Rozbalte ho do `config/custom_components/eob_pt32/`.
3. Restartujte Home Assistant.

## Nastavení

[![Přidat integraci](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=eob_pt32)

1. **Nastavení → Zařízení a služby → Přidat integraci**.
2. Vyhledejte **Elektrobock PT32 WiFi**.
3. Zadejte e-mail a heslo – stejné jako v aplikaci EOB PT-WIFI.

Entity se vytvoří automaticky pro všechny termostaty PT32 WiFi v účtu. Aplikaci můžete dál
používat souběžně.

## Omezení

- Rozvrh programů se jen zobrazuje, upravit ho jde zatím jen v aplikaci.
- Přejmenovat termostat jde jen v aplikaci (integrace název převezme).
- Hodiny termostatu se při zapnutém času z internetu (NTP) řídí podle termostatu; u testovaného
  kusu ukazují o hodinu víc a zápis času z aplikace ani z HA to nezmění.
- Geofencing, dovolená a servisní režim aplikace nejsou podporované – geofencing je lepší řešit
  automatizací v HA.

## Jak to funguje

Popis protokolu, který integrace používá, je v [docs/PROTOKOL.md](docs/PROTOKOL.md).
Skripty pro odposlech další funkcí aplikace jsou ve složce [tools/](tools).

Chcete pomoct s podporou další funkce nebo jiného firmwaru? Založte
[issue](https://github.com/Mejroo/eob-pt32-ha/issues) – nejvíc pomůže log z měřicího skriptu
(bez položky `0x002E`, vypadá jako klíč zařízení).

## Vydání

Přehled změn je v [CHANGELOG.md](CHANGELOG.md), balíčky ke stažení ve
[vydáních](https://github.com/Mejroo/eob-pt32-ha/releases).

- **0.4.0** – nastavení termostatu (korekce, hystereze, min. doba zapnutí, zámek klávesnice),
  potvrzení a opakování zápisu, týdenní rozvrh, diagnostika spojení, firmware a údržby kotle.
- **0.3.0** – výběr programu, hodiny provozu kotle, název z účtu.
- **0.2.0** – přesná teplota, režimy Manuál a Vypnuto, senzor kotle.
- **0.1.0** – první verze.

## Upozornění

Jde o komunitní integraci, kterou Elektrobock nevytvořil ani nepodporuje. Názvy Elektrobock,
PT32 a EOB jsou použity jen k označení podporovaného zařízení. Integrace komunikuje s cloudem
výrobce stejně jako jeho aplikace; výrobce může protokol kdykoli změnit.

Licence [MIT](LICENSE).
