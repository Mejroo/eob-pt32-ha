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
| `0x0003` firmware | `14 03` = verze 14.03 |
| `0x0002` zápis | 3 B: `[program][režim][teplota × 2]`, režim auto `0x21`, manual `0x20`, off `0x24` |
| `0x0001`, `0x0008` | čítač změn |
| `0x000D` program | čtení s 1 B čísla (1–9) → `[číslo][rozvrh 7 × 6 párů][00][název 16 B]`, pár = `[čas v osminách hodiny][teplota × 2]` (`28 2a` = 5:00 21 °C) |
| `0x0022` kotel | dotaz s 1 B `00` → `[hodiny 2 B][minuty]` doby provozu kotle |
| `0x0007` hodiny | `rr mm dd hh mm ss`; aplikace při otevření zapíše místní čas, termostat s NTP ukazuje o 1 h víc |
| nastavení | dvoupísmenné ASCII kódy, zápis `4B54` („KT“), čtení `CB54`, termostat zápis potvrdí stejnou hodnotou: `KT` korekce (h − 100)/10 °C, `HS` hystereze h/10 °C, `HM` min. doba zapnutí (min), `LK` zámek klávesnice `A`/`N`, `MI`/`MX` rozsah teploty × 2, `RR`/`RM`/`RD` údržba kotle (měsíc od 0) |
| `0x0005` | NTP server (text) |

## Instalace

Zkopírujte `custom_components/eob_pt32` do `/config/custom_components/`, restartujte HA a přidejte
integraci **Elektrobock PT32 WiFi** (e-mail a heslo z aplikace).

## Entity

- `climate`: teplota s desetinami, režimy Auto (program), Topit = manual (nastavitelná teplota), Vypnuto; změna teploty v auto přepne na manual.
- `binary_sensor` **Kotel**: sepnutí kotle (zapnuto/vypnuto).
- `select` **Program**: výběr z 9 programů termostatu (názvy z termostatu, výběr přepne do auto).
- `sensor` **Hodiny provozu kotle**: počítadlo termostatu (h).
- `number` **Korekce teploty**, **Hystereze**, **Minimální doba zapnutí** a `switch` **Zámek klávesnice** (zápis s potvrzením a opakováním).
- Diagnostika: **Spojení**, **Naposledy viděn**, **Firmware**, **Údržba kotle**.
- Rozvrh aktivního programu je v atributech entity Program (Po–Ne), rozsah teploty climate se bere z termostatu.
- Hodiny termostatu se při připojení a každou hodinu nastaví na čas HA (stejně jako to dělá aplikace).
- Název termostatu se jednou za hodinu převezme z účtu (přejmenování v aplikaci).

## Omezení

- Rozvrh programů se jen zobrazuje, needituje (zápis zatím nebyl odposlechnut).
- Přejmenování termostatu z HA není: aplikace volá REST `/api/Device/Rename` přes HTTPS a parametry nejdou z MQTT odposlechu zjistit.
- Měřicí skripty jsou v `tools/` (Node, `npm install` ve složce, pak `node eob_kroky3.js`).
