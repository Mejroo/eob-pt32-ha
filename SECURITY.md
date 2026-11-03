# Bezpečnost

## Hlášení zranitelnosti

Bezpečnostní problém prosím **nehlaste veřejným issue**. Použijte
[soukromé nahlášení zranitelnosti](https://github.com/Mejroo/eob-pt32-ha/security/advisories/new)
na GitHubu. Ozvu se do týdne.

## Podporované verze

Opravy vycházejí jen pro poslední vydanou verzi.

## Citlivé údaje

Integrace ukládá e-mail a heslo k účtu Elektrobock v konfiguraci Home Assistantu
(`.storage/core.config_entries`) stejně jako ostatní cloudové integrace. Do logu je nevypisuje.

Do issue, diskuzí ani pull requestů nikdy nevkládejte e-mail, heslo, `authToken`, `mqttPass`,
`uniqueIdentifier`, položku `0x002E`, IP adresu, SSID ani polohu termostatu. Pokud se to stane,
změňte si heslo v aplikaci EOB PT-WIFI a napište mi, příspěvek skryji.
