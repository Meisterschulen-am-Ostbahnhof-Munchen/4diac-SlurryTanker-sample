# Hysteresis-Bausteine – Übersicht

## Bibliothekstypen
- `Hysteresis` / `Hysteresis_AR_AX` — einfache Schwelle mit Hysterese, ein BOOL-Ausgang.
- `DualHysteresis` (native, `C:\4diac\...\typelibrary\signalprocessing-3.0.0\typelib\DualHysteresis.fbt`) — 2-seitige Schwelle mit Hysterese, plain `REAL`-Eingänge (`INPUT`/`MI`/`DEAD`/`HYSTERESIS`), plain `BOOL`-Ausgänge (`DO_UP`/`DO_DOWN`). Keine Adapter, Basis-FB von Eclipse 4diac selbst.
- `DualHysteresis_AR_AX` — wie oben, aber Eingänge als `AR`-Adapter-Sockets, Ausgänge als 2 getrennte `AX`-Plugs (`DO_UP`, `DO_DOWN`).
- `DualHysteresis_AR_A2X` — wie `DualHysteresis_AR_AX`, aber `DO_UP`/`DO_DOWN` zu einem einzigen `A2X`-Plug gebündelt (`OUT`).

## Offener Punkt (dokumentiert 2026-09-05, noch nicht umgesetzt)

Frage: Braucht es eine dritte, leichtgewichtige Variante zwischen `DualHysteresis` (komplett plain) und
`DualHysteresis_AR_AX`/`_AR_A2X` (komplett adapter-isiert) — also plain `REAL`-Eingänge (`INPUT`/`MI`/`DEAD`/
`HYSTERESIS` bleiben normale Datenanschlüsse, kein `AR`-Socket nötig), aber `DO_UP`/`DO_DOWN` schon als `AX`-
bzw. `A2X`-Plug für direkte Kompatibilität mit den ILOCK-Bausteinen?

Noch nicht gebaut — zurückstellen, bis ein konkreter Anwendungsfall danach verlangt. Falls es soweit ist:
gleiches Muster wie `DualHysteresis_AR_A2X`, nur `INPUT`/`MI`/`DEAD`/`HYSTERESIS` als plain `InputVars` statt
`AR`-Sockets übernehmen.
