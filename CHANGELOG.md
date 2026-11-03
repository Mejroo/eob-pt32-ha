# Změny

Verze se řídí [sémantickým verzováním](https://semver.org/lang/cs/). Dokud je integrace
v betě (0.x), může se mezi menšími verzemi změnit i chování entit.

## [0.4.0] – 2026-11-03

### Přidáno
- Nastavení termostatu: **Korekce teploty**, **Hystereze**, **Minimální doba zapnutí** (number)
  a **Zámek klávesnice** (switch). Zapisují se jen hodnoty ověřené odposlechem aplikace.
- Potvrzení zápisu: integrace čeká na odpověď termostatu a zápis až dvakrát zopakuje;
  nepotvrzený zápis se v HA ohlásí jako chyba.
- Týdenní rozvrh aktivního programu v atributech entity **Program** (Po–Ne).
- Diagnostika: **Spojení**, **Naposledy viděn**, **Firmware**, **Údržba kotle**.
- Rozsah nastavitelné teploty se bere z termostatu (např. 10–25 °C).
- Hodiny termostatu se nastavují na čas HA stejně jako to dělá aplikace.

### Změněno
- Entity jsou nedostupné, když termostat 3 minuty neodpoví (dřív jen při ztrátě MQTT).

## [0.3.0] – 2026-11-02

### Přidáno
- Výběr programu (**Program**, 9 programů s názvy z termostatu).
- **Hodiny provozu kotle**.
- Název termostatu se jednou za hodinu převezme z účtu (přejmenování v aplikaci).

### Opraveno
- Zápis teploty a režimu zachová aktivní program.

## [0.2.0] – 2026-11-02

### Přidáno
- Teplota s desetinami, režim **Vypnuto**, režim **Manuál** a binární senzor **Kotel**.

## [0.1.0] – 2026-11-02

- První verze: entita climate přes cloud Elektrobock (REST + MQTT přes WebSocket).
