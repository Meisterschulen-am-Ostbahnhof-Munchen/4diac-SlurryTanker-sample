# QUARTER (AQ) — 2-Bit-Wert für einfache Enable/Disable-Signale

`AQ` ist der Adapter-Typ für 1 Event + 2 Bit Nutzdaten (in einem BYTE
transportiert). Für ein einfaches Enable/Disable-Signal (ISO 11783-6:2018
Table J.5, **Function Type 0**, "Boolean Latching (maintains position),
On/Off"):

| Bitwert (Binär) | Dezimal | Bedeutung |
|---|---|---|
| 00 | 0 | Off |
| 01 | 1 | On |

Die Standard selbst definiert für Type 0 nur diese zwei Werte (Value 1 =
0/1, siehe Tabelle unten). Der Fehler-/Nicht-verfügbar-Zustand (`10`/`11`)
ist keine ISO-11783-6-Vorgabe für Type 0, sondern eine zusätzliche,
projekt-/bibliotheksweite Konvention, konsistent übernommen aus der
Standard-4diac-IDE-Bibliothek `eclipse4diac::signalprocessing::FIELDBUS_SIGNAL`
(`typelibrary/signalprocessing-3.0.0/typelib/FIELDBUS_SIGNAL.gcf`, nicht im
Projekt vendored, aber von hier aus referenziert, z.B. über
`FIELDBUS_PERCENT_TO_WORD` in `F_PWM_PERCENT_TO_RAW.SUB`):
`ERROR_INDI_2bit = BYTE#16#2` (=10b), `NOT_AVAILABLE_2bit = BYTE#16#3` (=11b)
— exakt dieselbe Konvention wie im projekteigenen `quarter.gcf`
(`STATUS_ERROR = 2#10`, `STATUS_NOT_AVAILABLE = 2#11`).

## Zweirichtungssignale (Heben/Senken etc.) — kein `AQ`, sondern eigene Bitmuster

**Nicht mit `AQ` (2-Bit) verwechseln:** ein Zweirichtungssignal wie
Heben/Senken wird in ISO 11783-6:2018 Table J.5 durch eigene **Function
Types** mit jeweils eigenem Bitmuster abgedeckt — keine zusammenhängende
2-Bit-Zahl 0-3, sondern pro Richtung ein eigenes Bit (bzw. Bit-Paar):

**Function Type 5** — "Dual Boolean Both Latching (Maintain positions),
On/Off/On" (Three-Position Switch, latching in all positions, Centre Off).
Das ist die Quelle für den zuvor genannten Hinweis "0 = Off = centre /
1 = On = forward, up or right / 4 = On = backward, down or left":

| Wert | Binär | Bedeutung |
|---|---|---|
| 0 | 000 | Off = centre |
| 1 | 001 | On = forward, up or right |
| 4 | 100 | On = backward, down or left |

Bit 0 = "Vorwärts/Hoch/Rechts"-Flag, Bit 2 = "Rückwärts/Runter/Links"-Flag —
**zwei unabhängige Einzel-Bits**, kein fortlaufendes 2- oder 3-Bit-Feld
(Bit 1 ist bei diesem Function Type ungenutzt, Werte 2/3/5/6/7 kommen bei
Type 5 nicht vor).

**Function Type 6** — "Dual Boolean Both Non-Latching (Momentary),
Increase/Off/Decrease" (Three-Position Switch, returning to centre,
Momentary) macht daraus **zwei gepackte `AQ`-artige 2-Bit-Felder** in
einem Byte, eines pro Richtung:

| Wert | Binär | Bedeutung |
|---|---|---|
| 0 | 0000 | Off |
| 1 | 0001 | Momentary = forward, up or right |
| 2 | 0010 | held forward, up, or right |
| 4 | 0100 | Momentary = backward, down or left |
| 8 | 1000 | held backward, down, or left |

Bits[1:0] = Vorwärts-Zustand (0=Aus, 1=Momentary, 2=Held — dieselbe
0/1/2-Kodierung wie `AQ`s `STATUS_ENABLED`/`STATUS_...`, hier aber nicht
denselben Fehler/N-A-Zustand nutzend), Bits[3:2] = Rückwärts-Zustand,
identisch codiert, nur um 2 Bit nach links verschoben (`4`=Bit2,
`8`=Bit3). Function Types 7/8 (Latching Up/Momentary Down bzw. umgekehrt)
nutzen dieselbe Bit-Aufteilung mit gemischt latching/momentary
Bedeutung je Bit.

**Fazit für `A2X` (2 Events, 2 BOOL: `UP`/`DOWN`):** `A2X` bildet am
ehesten Function Type 5 ab (je ein einzelnes Bit für Hoch/Runter, keine
Momentary/Held-Unterscheidung) — eine `A2X_TO_AQ`/`AQ_TO_A2X`-Konvertierung
müsste daher NICHT die reguläre `quarter.gcf`-Konvention verwenden, sondern
eigene Bitmasken (Bit 0 und Bit 2, nicht Bit 0 und Bit 1) ansetzen, falls
sie exakt Type 5 nachbilden soll.

Quelle: ISO 11783-6:2018-06, Table J.5 — Auxiliary Function Type 2 types
(`G:\Geteilte Ablagen\Classroom\Students\Literatur\Normen\ISO 11783 ISOBUS\
ISO 11783-6_2018-06-00_EN_2866291.pdf`, S. 310-312), direkt in der PDF
verifiziert.
