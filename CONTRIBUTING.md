# Přispívání

Díky, že chcete pomoct! Integrace vzniká odposlechem aplikace, takže nejcennější jsou
ověřené popisy dalších funkcí – postup je v [docs/PROTOKOL.md](docs/PROTOKOL.md).

## Pravidla

- **Zapisujte jen to, co posílá aplikace.** Nový zápis do termostatu přidejte, jen když je
  ověřený odposlechem a zapsaná hodnota se v aplikaci projeví stejně.
- **Žádné citlivé údaje** v kódu, issue ani logu: e-mail, heslo, `authToken`, `mqttPass`,
  `uniqueIdentifier`, položka `0x002E`, IP adresa, SSID, název termostatu nebo poloha.
- Kód a komentáře jsou česky, v souborech nepoužívejte apostrof `'`.

## Commity

Zprávy commitů používají [Conventional Commits](https://www.conventionalcommits.org/cs/):

```
feat: zápis rozvrhu programu
fix: desetiny teploty pod nulou
docs: popis položky 0x000E
```

| Typ | Kdy | Ve vydání |
|---|---|---|
| `feat` | nová funkce | zvýší verzi 0.x → 0.(x+1) |
| `fix` | oprava chyby | zvýší poslední číslo verze |
| `docs` | dokumentace | jen v CHANGELOGu |
| `refactor`, `ci`, `chore` | úpravy bez změny chování | ne |

Nekompatibilní změnu (např. jiné `entity_id`) označte `feat!:` nebo řádkem
`BREAKING CHANGE:` v těle zprávy.

## Vydání

Vydání jsou automatická ([release-please](https://github.com/googleapis/release-please)):
z commitů na `main` se průběžně připravuje pull request s novou verzí a CHANGELOGem.
Jeho sloučením vznikne tag `vX.Y.Z`, GitHub Release a balíček `eob_pt32.zip`, který si
stáhne HACS. Verze v `manifest.json` se zvyšuje sama – neměňte ji ručně.

## Kontrola

Každý push projde kontrolou [hassfest](https://developers.home-assistant.io/blog/2020/04/16/hassfest/)
a [HACS](https://hacs.xyz/docs/publish/action). Před pull requestem prosím vyzkoušejte změnu
ve vlastním Home Assistantu.
