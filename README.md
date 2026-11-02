# Elektrobock PT32 WiFi pro Home Assistant

Vlastní integrace termostatu **Elektrobock PT32 WiFi** (aplikace EOB PT-WIFI). Termostat komunikuje jen
šifrovaně s cloudem výrobce, proto integrace jde přes něj:

- přihlášení: `https://data.elektrobock.cz/api/Auth/login`, seznam zařízení `/api/UsersDevices/withFcmData`
  (PT32 WiFi = `deviceType` 0; z odpovědi `uniqueIdentifier` a `mqttPass`),
- MQTT přes WebSocket `wss://mqtt.elbock.cz:8081/wss`, uživatel `PTWIFI_<uid6>`, heslo `mqttPass`,
  příkazy do `PTWIFI/I/<uid6>`, odpovědi z `PTWIFI/O/<uid6>`.

## Protokol (zjištěno odposlechem)

Zprávy jsou v base64. Rámec: `[hlavička 2 B][délka 2 B][položky…]`, hlavička požadavku `7FFF`
(jinou termostat odmítne chybou `37DD 4002`), odpovědi `FFFF`, v délce je příznak `0x4000`.
Položka: `[typ 2 B][délka 2 B][data]`, typ s bitem `0x8000` = čtení.

| Položka | Význam |
|---|---|
| `0x0002` stav | `[0]` skutečná teplota (celé °C), `[4]` 1 = auto / 0 = ruční, `[5]` nastavená × 2, `[6]` `0x40` = topí, `[7]` příznaky (`0x20` NTP, `0x40` zámek) |
| `0x0002` zápis | 3 B: `[01][režim: 0x01 auto, 0x04 ignorovat teplotu, 0x20 NTP][teplota × 2]` |
| `0x0007` hodiny | `rr mm dd hh mm ss` |
| `0x0005` | NTP server (text) |

## Instalace

Zkopírujte `custom_components/eob_pt32` do `/config/custom_components/`, restartujte HA a přidejte
integraci **Elektrobock PT32 WiFi** (e-mail a heslo z aplikace).

## Omezení

- Teplota v místnosti chodí jen v celých stupních.
- Režim „vypnuto“ ani týdenní program zatím nejsou zmapované.
