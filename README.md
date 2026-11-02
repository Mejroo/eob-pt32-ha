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
| `0x0002` stav | `[0]` teplota celé °C, `[2]` desetiny, `[3]` číslo programu, `[4]` 1 = auto / 0 = manual, `[5]` nastavená × 2 (v off 0), `[6]` `0x40` = kotel sepnutý, `0x04` = off, `[7]` příznaky (`0x20` NTP, `0x40` zámek) |
| `0x0002` zápis | 3 B: `[program][režim][teplota × 2]`, režim auto `0x21`, manual `0x20`, off `0x24` |
| `0x0001`, `0x0008` | čítač změn |
| `0x000D` program | čtení s 1 B čísla (1–9) → `[číslo][týdenní rozvrh][název 16 B]` |
| `0x0022` kotel | dotaz s 1 B `00` → `[hodiny 2 B][minuty]` doby provozu kotle |
| `0x0007` hodiny | `rr mm dd hh mm ss` |
| `0x0005` | NTP server (text) |

## Instalace

Zkopírujte `custom_components/eob_pt32` do `/config/custom_components/`, restartujte HA a přidejte
integraci **Elektrobock PT32 WiFi** (e-mail a heslo z aplikace).

## Entity

- `climate`: teplota s desetinami, režimy Auto (program), Topit = manual (nastavitelná teplota), Vypnuto; změna teploty v auto přepne na manual.
- `binary_sensor` **Kotel**: sepnutí kotle (zapnuto/vypnuto).
- `select` **Program**: výběr z 9 programů termostatu (názvy z termostatu, výběr přepne do auto).
- `sensor` **Hodiny provozu kotle**: počítadlo termostatu (h).
- Název termostatu se jednou za hodinu převezme z účtu (přejmenování v aplikaci).

## Omezení

- Rozvrh programů se zatím nezobrazuje ani needituje.
