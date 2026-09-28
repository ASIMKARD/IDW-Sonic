# IDW Sonic the Hedgehog — reading-order tracker

Live: **https://asimkard.github.io/IDW-Sonic/**

Comics, games and shows in one chronological order, 1991–2026. Works offline,
installs to a phone home screen, keeps progress in the browser — no account.

## Scope

**777 rows.** 364 comics · 29 games · 384 screen entries.

| Band | Rows |
|---|---|
| Before the Blue Blur (1991–97) | 7 |
| The Long Modern Age (1998–2017) | 19 |
| A Mysterious Mastermind (2018–19) | 24 |
| The Metal Virus (2019–20) | 33 |
| Rebuilding and the Starline Plot (2021–22) | 30 |
| Frontiers (2022–24) | 63 |
| The Current Run (2024–26) | 57 |
| Elsewhere (separate continuities) | 543 |

Included: the IDW ongoing, its miniseries, annuals and one-shots, Sonic x
Godzilla, 29 games with playtimes, Sonic Prime, ~45 animated shorts, the
Chaotix Casefiles podcast, and — walled off in **Elsewhere** — six cartoons,
the 1996 OVA, Fleetway's *Sonic the Comic* (224 issues) and DC x Sonic.

Out of scope: the Paramount films and *Knuckles* (not canon), mobile tie-in
games, and anything unreleased at build time.

## Files

| Path | What it is |
|---|---|
| `index.html`, `styles.css`, `sw.js`, `manifest.json`, `qrcode.js` | the app |
| `data.js` | generated — do not hand-edit |
| `IDW-Sonic-reading-order.xlsx` | **the source of truth**, 7 tabs |
| `gen.py` | workbook → `data.js` |
| `source/workbook.py` | workbook ↔ `source/rows.json`, plus `verify` |
| `source/*.csv` | the sourced research behind the workbook |
| `test.js` | 122 assertions (jsdom) |
| `layout-check.py` | real-browser layout checks (Playwright) |

## Rebuilding

```
python3 source/workbook.py verify   # workbook integrity
python3 gen.py                      # rebuild data.js
node test.js                        # needs: npm install jsdom
python3 layout-check.py             # needs: pip install playwright
```

Bump `CACHE` in `sw.js` and the build tag in `index.html` **together** — a test
asserts they match. Verify a deploy by hash, not HTTP 200. GitHub Pages takes
about 100 seconds.

## Offline

Open the installed app once **with a connection**: iOS gives a home-screen web
app its own service worker, so installing the shortcut does not inherit
Safari's offline copy. Settings → Offline reports readiness.

## Known gaps

All recorded in the workbook's Maintenance tab:

- Four items have no sourced date: Frontiers Prologue: Divergence, the Secret
  Rings comic, Sonic Colors Comics, the Forces digital comic
- The Japanese Shogakukan manga and Sonic the Comic Specials are not included —
  no reliable source
- Chaotix 30th Anniversary Special: 22 Oct vs 2 Nov 2025, unresolved
- Sonic the Comic #0, #169, #186 and #198 carry deduced dates, each flagged
- Arc Master's Importance, Quality, Key Events and Crossover Ties are
  intentionally empty — they need reading judgement, not metadata
