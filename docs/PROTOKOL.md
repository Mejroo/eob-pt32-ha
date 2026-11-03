# Protokol termostatu PT32 WiFi

Popis vychází z odposlechu komunikace aplikace **EOB PT-WIFI** s termostatem (firmware 14.03).
Výrobce protokol nezveřejnil; co tu není uvedeno jako ověřené, je odhad.

> ⚠️ Integrace zapisuje jen položky, jejichž zápis aplikace prokazatelně posílá. Pokud budete
> zkoumat další položky, nezapisujte hodnoty, které aplikace neposílá – termostat je může
> přijmout a uložit i nesmyslné.

## Cesta ke cloudu

Termostat komunikuje jen šifrovaně (TLS, port 8883) s cloudem výrobce, lokální řízení proto
není možné. Integrace se připojuje stejně jako aplikace:

1. **Přihlášení** – `POST https://data.elektrobock.cz/api/Auth/login` s `{"userName", "password"}`
   → `authToken`, `id`.
2. **Seznam zařízení** – `GET /api/UsersDevices/withFcmData?userId=<id>` s hlavičkou
   `Authorization: Bearer <authToken>`. PT32 WiFi má `deviceType` 0; z odpovědi je potřeba
   `uniqueIdentifier`, `mqttPass`, `name` a `firmwareVersionStringFromDevice`.
3. **MQTT přes WebSocket** – `wss://mqtt.elbock.cz:8081/wss`, uživatel `PTWIFI_<uid6>`
   (`uniqueIdentifier` doplněný nulami na 6 číslic), heslo `mqttPass`.
   - příkazy do `PTWIFI/I/<uid6>`,
   - odpovědi z `PTWIFI/O/<uid6>`.

   Broker povolí i odběr `PTWIFI/I/<uid6>` (je vidět, co posílá aplikace). Odběr `#` nebo
   `PTWIFI/#` broker potrestá odpojením.

## Rámec

Zprávy jsou v base64. Rámec:

```
[hlavička 2 B][délka 2 B][položka][položka]…
```

- hlavička požadavku **musí** být `7FFF` (jinou termostat odmítne chybou `37DD 4002`),
- odpověď má hlavičku `FFFF`,
- v délce je nastavený příznak `0x4000` (skutečná délka = `délka & 0x3FFF`).

Položka:

```
[typ 2 B][délka 2 B][data]
```

Bit `0x8000` v typu znamená čtení (`8002` = přečti stav). Termostat odpovídá položkou
s nastaveným bitem a aktuální hodnotou – i na zápis, takže odpověď slouží jako potvrzení.

## Položky

| Typ | Směr | Význam |
|---|---|---|
| `0x0001`, `0x0008` | čtení | čítač změn |
| `0x0002` | čtení | stav (viz níže) |
| `0x0002` | zápis | 3 B: `[program][režim][teplota × 2]` |
| `0x0003` | čtení | firmware: `14 03 …` = verze 14.03 (číslice jsou šestnáctkové) |
| `0x0005` | čtení | NTP server (text, např. `cz.pool.ntp.org`) |
| `0x0007` | čtení / zápis | hodiny `rr mm dd hh mm ss`; aplikace při otevření zapíše místní čas |
| `0x000D` | čtení s 1 B čísla | program 1–9 (viz níže) |
| `0x000E` | čtení | pravděpodobně pravidla letního času – nezmapováno |
| `0x0013` | zápis | posílá aplikace v servisním režimu – nezmapováno, integrace nepoužívá |
| `0x0022` | dotaz s 1 B `00` | doba provozu kotle `[hodiny 2 B][minuty]` |

### Stav (`0x0002`)

| Bajt | Význam |
|---|---|
| 0 | skutečná teplota, celé °C |
| 2 | desetiny skutečné teploty |
| 3 | číslo aktivního programu |
| 4 | `1` = auto (program), `0` = manuál |
| 5 | nastavená teplota × 2 (ve vypnutém stavu 0) |
| 6 | `0x40` = kotel sepnutý, `0x04` = vypnuto |
| 7 | příznaky: `0x20` = čas z NTP |

Režim při zápisu: auto `0x21`, manuál `0x20`, vypnuto `0x24` (`0x20` = ponechat NTP).
Příklad z aplikace: `0x0002 = 02 21 26` = program 2, auto, 19 °C.

### Program (`0x000D`)

Odpověď: `[číslo][rozvrh 7 × 12 B][00][název 16 B]`.

Den (Po–Ne) má 6 párů `[čas][teplota × 2]`. Čas je v osminách hodiny (`0x28` = 5:00,
`0x98` = 19:00), nepoužité úseky termostat vyplní kopií předchozího. Název je v cp1250,
doplněný nulami nebo mezerami.

Příklad – pondělí „Hlavni program“ `00 28 28 2a 28 2a 28 2a 28 2a 98 28`:
0:00 20 °C, 5:00 21 °C, 19:00 20 °C (ověřeno proti aplikaci).

Zápis rozvrhu zatím nebyl odposlechnut.

### Nastavení

Nastavení mají za typ dvě ASCII písmena: zápis `4B54` („KT“), čtení `CB54`. Aplikace je při
otevření čte všechna jedním rámcem a zápis termostat potvrdí stejnou hodnotou
(`4B54=58` → `CB54=58`).

| Kód | Význam | Kódování | Zápis ověřen |
|---|---|---|---|
| `KT` | korekce teploty | (h − 100) / 10 °C, `0x57` = −1,3 | ✅ |
| `HS` | hystereze | h / 10 °C, `0x03` = 0,3 | ✅ |
| `HM` | minimální doba zapnutí kotle | minuty | ✅ |
| `LK` | zámek klávesnice | `A` / `N` | ✅ |
| `MI`, `MX` | rozsah nastavitelné teploty | °C × 2 (`0x14`, `0x32` = 10–25 °C) | – |
| `RR`, `RM`, `RD` | datum údržby kotle | rok − 2000, měsíc od 0, den | – |
| `JA` | jazyk? | `C` | – |
| `PZ` | předčasné zapnutí? | `0` = vypnuto | – |
| `LR`, `LS`, `LE`, `TK` | sudý/lichý týden, hlídání teploty…? | `A` / `N` | – |
| `DR` | druh regulace? | `H` = topení | – |
| `PM`, `PP`, `PI`, `UT`, `TC`, `L\0` | nezmapováno | | – |

### Další hlavičky

Obrazovka „Informace o zařízení“ v aplikaci používá jiné hlavičky rámce (`3722`, `3716`,
`B781`, `B77F`) pro MAC, IP adresu a SSID. Integrace je nepoužívá.

## Měřicí skripty

Ve složce [`tools/`](../tools) jsou skripty v Node.js, které odposlouchávají příkazy aplikace
a odpovědi termostatu a vedou vás jednotlivými kroky:

```bash
cd tools
npm install
node eob_kroky3.js
```

Přihlašovací údaje se zadávají do terminálu a nikam se neukládají. Log (`*_log.txt`) obsahuje
surová data z termostatu včetně položky `0x002E`, která vypadá jako klíč zařízení – nesdílejte ho.
