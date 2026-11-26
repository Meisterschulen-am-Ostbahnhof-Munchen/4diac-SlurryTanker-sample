# PWM-Ausgänge (logiBUS_io) – Konzept

Stand 2026-11-05, Entwurf zur Abstimmung. Noch nichts umgesetzt.

## Ausgangslage

Heute gibt es `logiBUS_QD_PWM` und den Adapter-Wrapper `logiBUS_QDA_PWM`: ein Tastgrad `OUT` als 13-bit-Rohwert
(0..8191), sonst nichts. Alles andere ist in der Firmware fest verdrahtet
(`4diac-forte/logiBUS-modules/logiBUS-io/handle/esp32_digital_out/IOHandleESP32PWMO.cpp`):

| Eigenschaft | heute | einstellbar? |
|---|---|---|
| Frequenz | 400 Hz, ein LEDC-Timer (TIMER_0) für alle PWM-Ausgänge | nein |
| Auflösung | 13 bit | nein |
| Übergang | jeder neue Wert als Hardware-Rampe über 500 ms (`LEDC_TEST_FADE_TIME`, Rest aus dem ESP-IDF-Beispiel) | nein |

Folgen:
- Der Kunde kann weder die Frequenz noch das Verhalten beim Wertwechsel (Sprung oder Rampe) bestimmen.
- **Fehler:** Kommt ein neuer Wert, während die vorige 500-ms-Rampe läuft, wartet `ledc_set_fade_with_time()` ohne
  Timeout auf deren Ende. Das hält den FORTE-Event-Thread der Resource bis zu 500 ms an, alle anderen Bausteine der
  Resource stehen mit. Bei einem Regler, der den PWM-Wert laufend schreibt, wird die ganze Station träge
  (Krauternter, Achslenkung bei laufender Aufnahme-Automatik).
- Ein Frequenzausgang (fester Tastgrad 50 %, Frequenz veränderlich) fehlt ganz.

## Hardware-Grenzen (ESP-IDF 6.1, `soc_caps.h`)

| | ESP32-S3 | ESP32-P4 | ESP32-S31 |
|---|---|---|---|
| LEDC-Kanäle | 8 | 8 | 8 |
| LEDC-Timer | 4 | 4 | 4 |
| Timer-Bitbreite max. | 14 | 20 | 20 |
| `ledc_fade_stop()` | ja | ja | ja |
| MCPWM | ja | ja | ja |

Wichtig für das Interface:
- **Die Frequenz gehört zum Timer, nicht zum Kanal.** Alle Kanäle an einem Timer laufen mit derselben Frequenz. Es gibt
  4 Timer für alle LEDC-Ausgänge zusammen, heute schon belegt: TIMER_0 PWM (400 Hz), TIMER_1 Servo (250 Hz),
  TIMER_2 LED-Blinken. Frei ist also nur einer.
- Die 8 Kanäle teilen sich PWM, Servo und LED-PWM (`LEDCChannelPool`).
- Frequenz und Auflösung hängen zusammen: Auflösung ≈ log2(Taktfrequenz / PWM-Frequenz). Bei 80 MHz sind 13 bit bis
  etwa 9,7 kHz möglich, darüber weniger. Die untere Grenze ergibt sich aus dem Teiler (S3 etwa im einstelligen
  Hz-Bereich, P4/S31 wegen 20 bit tiefer). Genaue Grenzen je Chip noch nachmessen.

## Leistungsstufen auf den Boards

Was ein Ausgang an Frequenz und Rampe verträgt, hängt von der Leistungsstufe dahinter ab, nicht vom ESP32. Auf den
Boards sind verbaut (Franz, 2026-11-05):

| Baustein | Art | PWM laut bisheriger Recherche | aus dem Datenblatt noch zu holen |
|---|---|---|---|
| BTS7030-2EPA | PROFET+2 12 V, 2 × 30 mΩ, High-Side, auf **Dual Out 12V, Hutschienenmoped 12V, Hutschienenmoped 2026 (Q1–Q4), Deca Out, Octa Out** | keine Grenze angegeben; Schaltzeiten 60/50 µs typ., max. 110/100 µs → sinnvoll bis einige 100 Hz | erledigt, siehe unten |
| BTT6030-2ERA | PROFET+2 12/24 V, 2 × 30 mΩ, High-Side (Lkw, Ventile, Lampen), auf **APIXON 20 Q1–Q12** und **APIXON 15 PWR Q7–Q12** | keine Grenze angegeben, „Eingang PWM-tauglich“; Schaltzeiten 50/55 µs typ., max. 150 µs → sinnvoll bis einige 100 Hz | erledigt, siehe unten |
| BTH50030-1LUA | Power PROFET+ 24/48 V, 1 × 3 mΩ, 25 A, auf **APIXON 15 PWR Q1** | **max. 100 Hz** (`fIN`, Datenblatt) | erledigt, siehe unten |
| BTH6070-2EPV | PROFET+ 48 V, 2 × 60 mΩ, „fast switching“, auf **Dual Out 12-24-48V** | keine Grenze angegeben; Schaltzeiten 32 µs typ., max. 80 µs → sinnvoll bis einige 100 Hz | erledigt, siehe unten |
| BTM9010EP | MOTIX Vollbrücke (H-Brücke) für DC-Motoren, 2 × auf **Hutschienenmoped 2026** | bis 20 kHz (Infineon-Produktseite), Schaltzeiten im µs-Bereich (Datenblatt) | erledigt, siehe unten |

**BTS7030-2EPA** (Datenblatt 2024-07-29), verbaut auf Dual Out 12V, Hutschienenmoped 12V, Deca Out und Octa Out (jeweils alle Ausgänge) sowie Hutschienenmoped 2026 (nur Q1–Q4):

- Betrieb 4,1..28 V, Strommessung `IS` (kILIS typ. 2715), Diagnose über `DEN`/`DSEL`.
- Bei 13,5 V: Einschaltverzögerung 35 µs (10..60), Ausschaltverzögerung 25 µs (10..50), Einschaltzeit 60 µs (30..110),
  Ausschaltzeit 50 µs (15..100), Slew Rate 0,6 V/µs. Eine maximale PWM-Frequenz nennt das Datenblatt nicht.
- Abschätzung: Ein Schaltvorgang dauert bis zu etwa 0,2 ms. Bei 400 Hz (2,5 ms Periode) gehen unten und oben etwa je
  4..8 % Tastgrad nicht linear. Bei 100 Hz etwa 1..2 %. Höher als einige 100 Hz ergibt keinen Sinn, die Schaltverluste
  steigen mit der Frequenz.
- Induktive Last ohne Freilaufdiode: Jedes Ausschalten wird über die interne Klemmung (VDS(CLAMP) ≥ 35 V) abgebaut,
  wiederholt höchstens 18 mJ je Puls (`EAR` bei IL(NOM), TJ 85 °C). Bei PWM eines Ventils fällt diese Energie in jeder
  Periode an. **Ventil-PWM braucht eine Freilaufdiode** am Ausgang, sonst überhitzt der Schalter. Wie das auf den
  Boards gelöst ist, ist offen.

**BTT6030-2ERA** (Datenblatt Rev. 2019-03-09), verbaut auf APIXON 20 (Q1–Q12) und APIXON 15 PWR (Q7–Q12):

- Betrieb 5..36 V (erweitert bis 48 V), IL(NOM) 6 A ein Kanal / 4 A beide, Strommessung kILIS typ. 2240.
- Einschaltzeit 50 µs (20..150), Ausschaltzeit 55 µs (20..150), Verzögerung je 30 µs (max. 70), Slew Rate 0,8 V/µs
  (0,3..1,4). Laut Datenblatt ist der Eingang „compatible with PWM applications“, eine Höchstfrequenz steht nicht drin.
- Abschätzung wie beim BTS7030: Bis zu 0,3 ms je Schaltvorgang, also bei 400 Hz unten und oben bis etwa 10 % Tastgrad
  nicht linear, bei 100 Hz etwa 3 %. Für Ventil-PWM eher 100..200 Hz als 400 Hz.
- Klemmung VDS(AZ) 66..75 V. Die Energieangabe ist ein Einzelpuls (`EAS` 85 mJ bei 4 A, TJ(0) 150 °C), und das
  Datenblatt sagt ausdrücklich, dass die Schutzfunktionen nicht für dauernden oder wiederholten Betrieb ausgelegt sind.
  **Ventil-PWM nur mit Freilaufdiode**, nicht über die Klemmung.

**BTH6070-2EPV** (Datenblatt Rev. 1.00, 2025-11-15), verbaut auf Dual Out 12-24-48V (dieselbe Bestückung für 12, 24 und 48 V, der Baustein deckt 8..54 V ab):

- Betrieb 8..54 V (nominal 48 V), IL(NOM) 2,17 A bei 85 °C, Strommessung kILIS typ. 1730, Eingänge 3,3/5 V.
- Bei 48 V: Verzögerung 17/20 µs (max. 40/50), Ein-/Ausschaltzeit je 32 µs (5..80), Slew Rate 3,6 V/µs. Damit der
  schnellste der PROFETs hier, PWM steht aber nicht als Grenze im Datenblatt.
- Abschätzung: bis etwa 0,13 ms je Schaltvorgang, bei 400 Hz unten und oben etwa je 2..5 % Tastgrad nicht linear.
- Klemmung VDS(CLAMP) 65..75 V, `EAS` 40 mJ Einzelpuls bei IL(NOM). Laut Datenblatt sind die Schutzfunktionen nicht
  für dauernden oder wiederholten Betrieb ausgelegt. **Ventil-PWM nur mit Freilaufdiode.**

**BTH50030-1LUA** (Datenblatt), verbaut auf APIXON 15 PWR Q1:

- Betrieb 12..54 V, 3 mΩ, IL(NOM) 22,5 A, Kurzschlussschwelle min. 55 A, Strommessung kILIS typ. 34000, Diagnose über
  `DEN`.
- **Maximale Eingangsfrequenz `fIN` = 100 Hz**, Retry im Fehlerfall ebenfalls ≤ 100 Hz. Das Datenblatt nennt den Baustein
  ausdrücklich für „PWM applications with low frequency“. Die Überlastabschaltung (Overpower) kann die mögliche
  Frequenz noch weiter senken.
- Slew Rate 1,5 V/µs (0,5 V/µs im erweiterten Bereich), Schaltenergie bei hoher Last etwa 9..12,5 mJ je Einschalten und
  7..10 mJ je Ausschalten. Schon bei 100 Hz sind das um 2 W Schaltverlust.
- „Smart clamping“ für induktive Lasten mit schnellem Abschalten. Nach dem Abschalten darf der Eingang erst nach
  `tIN(RESETDELAY)` wieder eingeschaltet werden.
- Für Heizungen, Lüfter und Pumpen gedacht. An diesem Ausgang nur langsame PWM (≤ 100 Hz, besser 10..50 Hz) und keine
  schnellen Rampen in vielen kleinen Schritten.

**BTM9010EP** (Datenblatt BTM9010EP/BTM9011EP Rev. 1.0, 2024-06-30; die BTM9011EP ist dieselbe Brücke mit SPI):

- **Verbaut auf Hutschienenmoped 2026** (`ESP32S3_HutschienenmopedXL26`), zwei Vollbrücken an Q5–Q8 (Franz bestätigt). Belegung laut
  `Application/components/io_digital_out/esp32s3_HutschienenmopedXL26/digital_out.cpp` (Annahme INA/INB/PWM aus der
  Wahrheitstabelle, bitte mit dem Schaltplan bestätigen):

  | Brücke | INA (High-Side A) | INB (High-Side B) | PWM (beide Low-Sides) |
  |---|---|---|---|
  | 1 | Q5 = GPIO41 | Q6 = GPIO42 | Q56 = GPIO16 |
  | 2 | Q7 = GPIO1 | Q8 = GPIO2 | Q78 = GPIO15 |

  Für die Low-Side gibt es in der Lib die Konstanten `Output_Q56` und `Output_Q78` (`logiBUS_DO.gcf`). Auf dem
  Node-ISO 20 sind sie `GPIO_NUM_NC`. PWM läuft hier auf der Low-Side (`PWM`-Pin), die High-Sides (Q5..Q8) stehen
  statisch. `SEL` und `IS` sind in der Pin-Tabelle nicht aufgeführt: fest verdrahtet oder nicht angeschlossen?
- Versorgung 7..18 V (erweitert 4,5..40 V), Strombegrenzung min. 10 A, Eingänge bis 6 V (3,3-V-Logik passt).
- Ansteuerung über **4 Logik-Eingänge**: `INA` (High-Side A), `INB` (High-Side B), `PWM` (Low-Sides, wenn die
  High-Side aus ist), `SEL` (welcher Schalter auf `IS` gemessen wird). Wahrheitstabelle (Table 7), Auszug:

  | INA | INB | PWM | Wirkung |
  |---|---|---|---|
  | 0 | 1 | 1 | vorwärts (HSB + LSA) |
  | 1 | 0 | 1 | rückwärts (HSA + LSB) |
  | 0 | 0 | 1 | Bremsen über beide Low-Sides (slow decay) |
  | 1 | 1 | 0 | Bremsen über beide High-Sides |
  | 0 | 1 | 0 | nur HSB an (fast decay, Freilauf) |
  | 1 | 0 | 0 | nur HSA an (fast decay, Freilauf) |
  | 0 | 0 | 0 | aus, nach Ablauf der Blanking-Zeit Standby |

  Für Geschwindigkeit wird also **nur der `PWM`-Pin getaktet**, die Richtung steht statisch auf `INA`/`INB`. Es braucht
  einen PWM-Kanal und drei normale GPIOs je Brücke, keine Gegentakt-Ausgänge und keine Totzeit vom ESP32: Die Brücke
  hat einen eigenen Querstromschutz (3,3 µs schnell, 7 µs langsam typ.).
- Schaltzeiten (13,5 V, 5,6 Ω): Einschaltverzögerung 0,6/1 µs, Ausschaltverzögerung 1,9/3,4 µs, Flanken 0,25..1,1 µs
  (schnelle/langsame Slew Rate). Damit sind 20 kHz realistisch. Die Slew Rate wird über eine Folge an den Eingängen
  gewählt (nach dem Einschalten langsam) und lässt sich am `IS`-Pin zurücklesen.
- `IS`-Pin: Strommessung (Verhältnis typ. 2250 bei 2,5 A) **und** Fehler-Flag (Überstrom, Übertemperatur, Unterspannung,
  offene Last) auf demselben Pin. Er gehört an einen Analogeingang. Nach jedem Schalten 1..10 µs Blanking.

**Bestückung je Board** (Franz, 2026-11-05; Lücken noch offen):

| Board | Ausgänge | Leistungsstufe | PWM sinnvoll bis (Abschätzung) |
|---|---|---|---|
| APIXON 20 (Node-ISO 20, ESP32-P4) | Q1–Q12 | BTT6030-2ERA | einige 100 Hz, für Ventile 100..200 Hz |
| APIXON 15 PWR | Q7–Q12 | BTT6030-2ERA | wie oben |
| APIXON 15 PWR | Q1 (Q2–Q6 gibt es nicht) | BTH50030-1LUA | **max. 100 Hz** (Datenblatt), besser 10..50 Hz |
| Dual Out 12-24-48V | Q1–Q2 (nur 2 Ausgänge) | BTH6070-2EPV | einige 100 Hz |
| Dual Out 12V | Q1–Q2 (nur 2 Ausgänge) | BTS7030-2EPA | einige 100 Hz |
| Hutschienenmoped 12V | alle | BTS7030-2EPA | einige 100 Hz |
| Hutschienenmoped 2026 (`ESP32S3_HutschienenmopedXL26`) | Q1–Q4 | BTS7030-2EPA | einige 100 Hz |
| Hutschienenmoped 2026 | Q5–Q8 + Low-Side Q56/Q78 | 2 × BTM9010EP | bis 20 kHz (PWM auf der Low-Side) |
| Deca Out | alle (Q1–Q10) | BTS7030-2EPA | einige 100 Hz |
| Octa Out | alle (Q1–Q8) | BTS7030-2EPA | einige 100 Hz |
| Trainer20 (ESP32-S31) | alle | keine (LED direkt am Ausgang, Messpunkte) | LEDC-Grenze |

**Freilaufdiode:** Alle Ausgänge der logiBUS-Boards haben eine Freilaufdiode (Franz, 2026-11-05). Bei Ventil-PWM baut
also die Diode die Spulenenergie ab, nicht die Klemmung der PROFETs. Die Energiegrenzen (`EAS`/`EAR`) oben gelten nur
für den Fall ohne Diode bzw. bei Diodenausfall. Die Energiebetrachtung je Ausgang dokumentiert die Session dokumaster.

Daraus folgt für das Konzept:
- **Frequenzgrenzen der Leistungsstufen stehen nur in der Doku** (entschieden, Franz 2026-11-05): in dieser Tabelle,
  in den Baustein-Kommentaren und in den Übungen. Die Firmware lässt jede Frequenz auf jedem Ausgang zu und prüft
  nichts gegen die Leistungsstufe. Die Firmware meldet nur, was der ESP32 selbst nicht kann (kein Timer/Kanal frei,
  Frequenz vom Chip nicht erzeugbar).
- Auch die kleinste Einschaltzeit begrenzt: Ganz kleine und ganz große Tastgrade werden von langsamen High-Side-Schaltern
  nicht mehr sauber abgebildet.
- Die BTM9010EP ist kein Einzelausgang, sondern eine Brücke. Für Motoren braucht es eher einen eigenen Baustein
  (Richtung + PWM, Bremsen), statt zwei einzelne PWM-Bausteine.

Am **Trainer20** (ESP32-S31) hängen LEDs direkt an den Ausgängen, dazu gibt es Messpunkte für das Oszilloskop. Dort
sind alle Übungen ohne Leistungsstufe möglich: Gamma-Vergleich, Rampen, Frequenzen bis weit über die Grenzen der
PROFETs, Sigma-Delta. Die Übungen sollten sagen, welche Werte nur am Trainer gehen und welche auch an einer
Station mit Ventilen.

## Vorschlag

### 1. Firmware: Timer-Pool und nicht blockierender Wertwechsel

- **Timer dynamisch verteilen (Timer-Pool)** wie der vorhandene `LEDCChannelPool`. Kein Timer ist mehr einer Art von
  Ausgang fest zugeordnet (heute: TIMER_0 PWM, TIMER_1 Servo, TIMER_2 LED). Alle LEDC-Nutzer (PWM, PWM mit Gamma,
  LED-Blinken) holen sich ihren Timer aus demselben Pool:
  - Ein Ausgang fordert beim INIT (Frequenz, Auflösung) an. Gibt es schon einen Timer mit genau dieser Frequenz, teilt
    er ihn (Zähler +1), sonst bekommt er einen freien und konfiguriert ihn.
  - Beim Abbau des Ausgangs (Zähler −1) wird ein Timer ohne Nutzer wieder frei.
  - Ist keiner frei: `QO = FALSE`, `STATUS = "Kein LEDC-Timer frei für <f> Hz (max. 4 verschiedene Frequenzen,
    belegt: <f1>, <f2>, <f3>, <f4> Hz)"`.
  - Beispiele: 4 Ausgänge mit 100 Hz und 4 mit 400 Hz → 2 Timer belegt, 2 frei, aber alle 8 Kanäle belegt.
    Je 2 Ausgänge mit 50, 100 und 400 Hz und ein LED-Blinken → 4 Timer und 7 Kanäle belegt. Ein weiterer Ausgang
    mit 100 Hz geht noch (Kanal 8), einer mit 1 kHz bekommt den Timer-Fehler. Der Servo zählt nicht mit, er
    läuft auf MCPWM.
  - Grenzen bleiben: höchstens 4 verschiedene Frequenzen und 8 Kanäle über alle LEDC-Nutzer zusammen.
  - `FREQ` der PWM-Bausteine wird nur bei INIT gelesen (entschieden 2026-11-06, Frage 4). Neue Frequenz = neues INIT.
    Zur Laufzeit änderbar ist die Frequenz nur bei den Frequenz-Bausteinen `logiBUS_QD_FREQ`/`QDA_FREQ`.
  Der Servo zieht auf MCPWM um (entschieden 2026-11-05, Abschnitt 7) und braucht keinen LEDC-Timer mehr.
- **Auflösung automatisch** aus der Frequenz (größte mögliche, höchstens 13 bit, damit `OUT` 0..8191 gleich bleibt).
  Bei geringerer Auflösung wird intern skaliert, der Baustein bleibt bei 0..8191.
- **Sprung (Rampenzeit 0):** `ledc_set_duty()` + `ledc_update_duty()`, keine Fade-Funktion, blockiert nie.
- **Rampe (Rampenzeit > 0):** vor jeder neuen Rampe `ledc_fade_stop()`, dann `ledc_set_fade_with_time()` +
  `ledc_fade_start(NO_WAIT)`. Die neue Rampe startet am aktuellen Ist-Wert, nichts wartet auf die alte.
- Damit ist der Blockier-Fehler behoben, unabhängig vom Rest.

### 2. IDE: Baustein-Interfaces (logiBUS_io, Paket `logiBUS::io::DQ`)

**PWM-Ausgang** – `logiBUS_QD_PWM` / `logiBUS_QDA_PWM` um zwei Eingänge erweitern (vorhandene Instanzen bekommen die
Default-Werte, Übungen bleiben gültig):

| Eingang | Typ | Default | Wann gelesen | Bedeutung |
|---|---|---|---|---|
| `FREQ` | UDINT | 400 | INIT | PWM-Frequenz in Hz. Ausgänge mit gleicher Frequenz teilen einen Timer. |
| `RAMP` | TIME | T#0ms | INIT und REQ (`QDA`: nur INIT) | Übergangszeit zum neuen Wert, T#0ms = Sprung. Beim `QDA` kommt der Wert über den Adapter, die Eingänge des Composite werden nur bei INIT übernommen. |
| `OUT` | DWORD / Adapter AD | – | REQ | Tastgrad 0..8191 wie bisher |

**Frequenzausgang** – neu `logiBUS_QD_FREQ` / `logiBUS_QDA_FREQ`, Tastgrad fest 50 %:

| Eingang | Typ | Default | Wann gelesen | Bedeutung |
|---|---|---|---|---|
| `FREQ` | DWORD / Adapter AD | 0 | REQ | Frequenz in mHz (1000 = 1 Hz), 0 = Ausgang aus (low). Wie ISOBUS-DDI 583 „Setpoint Frequency“ (Auflösung 0,001 Hz, Bereich 0..2147483647). Größere Werte: begrenzen und `STATUS` melden. |
| `FMIN`, `FMAX` | DWORD (mHz) | 10000 / 10000000 (10 Hz / 10 kHz) | INIT | Bereich, `FMIN` legt die Auflösung des Timers fest. `FREQ` außerhalb wird begrenzt, `STATUS` meldet es. Was der Chip nicht erzeugen kann: ebenso. Grenzen der Leistungsstufe: nur Doku. |

Obergrenze laut DDI 583: 2147483647 mHz ≈ 2,15 MHz. Hohe Frequenzen braucht keiner (Franz, 2026-11-06); die Firmware
nimmt den nächsten Wert, den MCPWM erzeugen kann (160 MHz / n, oben grob gestuft), ohne weitere Optimierung. Praktische
Grenze sind die Leistungsstufen (Hinweis im Kommentar, siehe „Bestückung je Board“).

Der Frequenzausgang läuft auf **MCPWM** (entschieden 2026-11-06, Abschnitt 7) mit eigenem Timer je Ausgang, Tastgrad
50 % über den Comparator. Er belegt keinen LEDC-Timer (auf LEDC wirkt `ledc_set_freq()` auf alle Kanäle des Timers).

**Gamma (entschieden 2026-11-05): jeden PWM-Baustein gibt es mit und ohne Gamma.**

| ohne Gamma (linear) | mit Gamma |
|---|---|
| `logiBUS_QD_PWM` / `logiBUS_QDA_PWM` | `logiBUS_QD_PWM_G` / `logiBUS_QDA_PWM_G` |
| `logiBUS_QD_FREQ` / `logiBUS_QDA_FREQ` | – (fester Tastgrad 50 %, Gamma sinnlos) |

- Ohne Gamma: Tastgrad = `OUT`, für Ventile, Motoren, Heizungen und alles, was linear auf den Tastgrad reagiert.
- Mit Gamma: `OUT` ist die Helligkeit, wie das Auge sie sieht. Der Tastgrad wird daraus berechnet:
  Tastgrad = 8191 · (`OUT` / 8191)^`GAMMA`. Zusätzlicher Eingang `GAMMA` (REAL, Default 2.2, gelesen bei INIT). Gedacht
  für LEDs und Lampen, damit jeder Schritt gleich hell wirkt (linear wirkt unten zu schnell und oben zu langsam).
- Die Umrechnung macht die Firmware im Handle, nicht der Baustein. So stimmt die Kurve auch während der Rampe: Eine
  Rampe mit Gamma läuft gleichmäßig in der Helligkeit, nicht im Tastgrad. Auf P4/S31 kann das die Hardware-Rampe
  (Gamma-Fade, bis 16 Abschnitte), auf dem S3 wird die Rampe in Abschnitte zerlegt, die nacheinander laufen.
  Beides darf den Event-Thread nicht blockieren (siehe Schritt 1).
- Vorlage: ESP-IDF-Beispiel `examples/peripherals/ledc/ledc_gamma_curve_fade` (lokal unter
  `~/.espressif/v6.1/esp-idf/examples/peripherals/ledc/ledc_gamma_curve_fade`). Unterstützte Targets dort: P4 und S31,
  **nicht S3** (kein `SOC_LEDC_GAMMA_CURVE_FADE_SUPPORTED`). Ablauf im Beispiel:
  - `gamma_correction_calculator(duty)` = `pow(duty / 2^13, GAMMA_FACTOR) · 2^13` (Beispiel: 2.8), wahlweise
    Tabelle mit 101 Werten für 0..100 % (Beispiel-Tabelle nur für Gamma 2.6)
  - `ledc_fill_multi_fade_param_list(mode, channel, start, end, SOC_LEDC_GAMMA_CURVE_FADE_RANGE_MAX, fade_time,
    gamma_correction_calculator, …)` zerlegt die Rampe in bis zu 16 lineare Abschnitte entlang der Kurve
  - `ledc_set_multi_fade(mode, channel, gamma(start), list, n)` und `ledc_fade_start(…, LEDC_FADE_NO_WAIT)`
  - Auch `ledc_set_multi_fade()` wartet wie `ledc_set_fade_with_time()` auf das Ende einer laufenden Rampe. Deshalb
    vorher `ledc_fade_stop()`, sonst wieder der Blockier-Fehler.
  - S3: gleiche Berechnung (`pow` oder Tabelle) für Sprünge, die Rampe als Folge kurzer linearer Fades aus einem
    eigenen Task oder Timer, nicht im Event-Thread.

**Gamma: Möglichkeiten** (für die Doku der `_G`-Bausteine): ESP-IDF legt keinen Gamma-Wert fest. Die Kurve wird als
Funktionszeiger `uint32_t (*)(uint32_t)` an `ledc_fill_multi_fade_param_list()` übergeben, jede Formel geht. Das
Espressif-Beispiel zeigt zwei Wege: `pow()` mit frei wählbarem Faktor (dort 2.8) oder eine Tabelle (dort nur für 2.6).
Wir nehmen `pow()` mit dem Eingang `GAMMA`:
- 1.0: keine Korrektur (wie der Baustein ohne `_G`)
- 2.2: sRGB-Standard, Default
- 2.6 / 2.8: die Werte aus dem Espressif-Beispiel, für viele LEDs gleichmäßiger
- andere Werte für Lampen oder Lasten mit eigener Kennlinie; am besten an der Trainer-LED ausprobieren (Übung)
Der Funktionszeiger hat keinen Kontext-Parameter: Der Handle setzt den Gamma-Wert des Ausgangs vor dem Aufruf in eine
statische Variable (mit Mutex), die Funktion rechnet synchron. Gamma-Rampe in Hardware nur auf P4/S31, auf dem S3 in
Abschnitten aus einem eigenen Task.
Ob eine Lampe Gamma bekommt, entscheidet die Wahl des Bausteins (`_G` oder nicht), auch beim Dimmer.

**Dimmer (Schaltung wie im Wohnzimmer)** – neu `logiBUS_QD_DIMMER` / `logiBUS_QD_DIMMER_G` (entschieden 2026-11-06):
ein eigener Ausgangsbaustein mit eigenem `Output`, Bibliothek `logiBUS_io`. Für Lampen ist meist `_G` richtig.
Eingänge `TOGGLE`, `DIM_START`, `DIM_STOP`, `SWITCH_ON`, `SWITCH_OFF`, `DIM_TIME`, `LEVEL_MIN`, `LEVEL_MAX`, `START`, `SOFT`, `FREQ`, beim `_G`
auch `GAMMA`; Ausgänge `ON_STATE`, `LEVEL`, `RAMPO`:

- **Tippen bei aus:** an, mit der zuletzt eingestellten Helligkeit (Speicher, beim ersten Mal `START`).
- **Tippen bei an:** aus. Die Helligkeit bleibt gespeichert.
- **Lange drücken:** dimmen, solange gedrückt. Die Richtung wechselt mit jedem langen Druck. Der erste lange Druck nach
  dem Einschalten dimmt herunter. Bei `LEVEL_MIN`/`LEVEL_MAX` bleibt der Wert stehen.
- **Lange drücken bei aus:** an mit `LEVEL_MIN` und hochdimmen.

| Anschluss | Typ | Default | Bedeutung |
|---|---|---|---|
| Ereignis `TOGGLE` | Event | – | Tippen (`BUTTON_SINGLE_CLICK` von `logiBUS_IE`) |
| Ereignis `DIM_START` / `DIM_STOP` | Event | – | langer Druck Beginn / Ende (`BUTTON_LONG_PRESS_START` / `BUTTON_LONG_PRESS_UP`) |
| Ereignis `SWITCH_ON` / `SWITCH_OFF` | Event | – | direkt ein/aus, z. B. Zentral-Aus |
| `DIM_TIME` | TIME | T#4s | Zeit für den ganzen Bereich `LEVEL_MIN`→`LEVEL_MAX` beim Dimmen |
| `LEVEL_MIN`, `LEVEL_MAX`, `START` | REAL (%) | 10 / 100 / 100 | Grenzen und erste Helligkeit |
| `SOFT` | TIME | T#300ms | Rampenzeit beim Ein-/Ausschalten durch Tippen |
| `Output` | logiBUS_DO_S | Invalid | Ausgang Q1..Qn, wie bei den PWM-Bausteinen |
| `FREQ` | UDINT | 400 | PWM-Frequenz in Hz, gelesen bei INIT (teilt den Timer-Pool mit den PWM-Bausteinen) |
| `GAMMA` | REAL | 2.2 | nur `_G`, gelesen bei INIT |
| Ereignis `RAMPO` | Event | – | Rampe fertig (Ziel `LEVEL_MIN`/`LEVEL_MAX` erreicht oder Ein-/Ausschalten beendet) |
| `ON_STATE`, `LEVEL` | BOOL, REAL (%) | – | Zustand und Helligkeit für die VT-Anzeige |

**Stufenlos über die Hardware-Rampe (entschieden 2026-11-06).** Kein Takt mit `E_CYCLE`, keine Einzelschritte: Das
wäre stufig, das will keiner.
- Langer Druck beginnt: Rampe zum Ziel starten, hoch auf `LEVEL_MAX`, runter auf `LEVEL_MIN` (kleiner Wert, nie 0). Rampenzeit
  nach Reststück, damit die Geschwindigkeit immer gleich ist: `t = DIM_TIME · |Ziel − Ist| / (MAX − MIN)`.
- Loslassen: `ledc_fade_stop()` (S3, P4, S31: `SOC_LEDC_SUPPORT_FADE_STOP`; Tastgrad steht spätestens eine PWM-Periode
  danach fest, nur bei Start mit `LEDC_FADE_NO_WAIT`), dann `ledc_get_duty()` lesen und als Helligkeit speichern.
- Ziel erreicht, während noch gedrückt: `RAMPO`, Wert bleibt stehen.
- Tippen: kurze Rampe `SOFT` auf die gespeicherte Helligkeit bzw. aus.
- Mit Gamma läuft die Rampe in der Helligkeit: P4/S31 Gamma-Fade in Hardware, S3 in Abschnitten aus dem eigenen Task,
  der beim Loslassen ebenfalls anhält.

Warum ein eigener Ausgangsbaustein: Über den Adapter AD läuft nur ein Wert, „Rampe stoppen“ und „Ist-Wert zurück“
nicht. Ein Logik-Dimmer vor `QDA_PWM` bräuchte dafür ein Ereignis `STOP` und einen Ist-Wert-Ausgang am PWM-Baustein und
wäre umständlich zu verdrahten. Ein bidirektionaler Adapter (`VALUE`/`RAMP` mit `SET`/`STOP` hin, `ACT`/`RAMPO`
zurück) ginge, bringt aber keinen Vorteil (Franz, 2026-11-06): Er wäre nur für den Dimmer da, jeder PWM-Baustein
bräuchte eine dritte Variante (auch mit `_G`), und stufenlos geht es ohnehin nur direkt am LEDC-Kanal (SDM hat keine
Hardware-Rampe, ein Ausgang über den Bus kann die Rampe nicht mitten im Lauf anhalten).

Die Ereignis-Eingänge passen auch zu VT-Softkeys und -Buttons (gedrückt/gehalten/losgelassen) und zu zwei Tastern
(auf/ab). Derselbe Baustein dient also für Hardware-Taster und Bedienung am Terminal.

**Hinweis auf die Leistungsstufe, wie beim Servo:** Der Kommentar von `FREQ` an jedem PWM-Baustein und jede
PWM-Übung nennen die Grenzen aus der Tabelle „Bestückung je Board“ (z. B. „APIXON 15 PWR Q1 (BTH50030): max. 100 Hz;
BTS7030/BTT6030/BTH6070: für Ventile 100..200 Hz; Trainer20: ohne Leistungsstufe“). Die Firmware prüft das nicht.

Gemeinsam für alle: `QI = FALSE` → Ausgang 0 / low. Fehler (Pin belegt, kein Kanal, kein Timer, Frequenz vom Chip nicht erzeugbar)
stehen im Klartext in `STATUS`, wie bei den anderen logiBUS-Bausteinen.

### 3. Übungen (test_AX, Adapter-Version; test_B wie gewohnt nachziehen)

| Übung | Inhalt | Baustein |
|---|---|---|
| PWM sprungartig | Numeric Input → PWM Q1, `RAMP = T#0ms`. LED / Ventil schaltet sofort auf den neuen Wert. | `logiBUS_QDA_PWM` |
| PWM mit Rampe | Gleicher Aufbau, `RAMP = T#500ms` und `T#2s`. Unterschied zur Software-Rampe (`RampLimitFS`) zeigen. | `logiBUS_QDA_PWM` |
| PWM-Frequenz | Gleicher Tastgrad mit `FREQ` 100 / 400 / 1000 Hz. Hörbar am Ventil, messbar am Oszilloskop. | `logiBUS_QDA_PWM` |
| Timer-Grenze | Vier Ausgänge mit vier verschiedenen Frequenzen und LED-Blinken dazu → `STATUS` meldet „Kein LEDC-Timer frei“. Lehrt Ressourcen der Hardware. | `logiBUS_QDA_PWM` |
| Frequenzgenerator | Numeric Input (mHz wie ISOBUS-DDI 583, am VT mit Skalierung 0,001 als Hz angezeigt) → Frequenzausgang Q1, fester Tastgrad 50 %. | `logiBUS_QDA_FREQ` |
| Linear oder Gamma | Ein Wert auf zwei LEDs: Q1 mit `logiBUS_QDA_PWM`, Q2 mit `logiBUS_QDA_PWM_G`. Mit dem Numeric Input in 10-%-Schritten durchfahren, Unterschied sehen. | `logiBUS_QDA_PWM`, `logiBUS_QDA_PWM_G` |
| Gamma mit Rampe | Wie vorher mit `RAMP = T#2s`: die Gamma-LED wird gleichmäßig heller, die lineare scheinbar nicht. | beide |
| Dimmer mit Taster | Taster I1 (`logiBUS_IEA`) → `logiBUS_QD_DIMMER_G` an Q1 mit LED. Tippen an/aus, lange drücken dimmt stufenlos. | `logiBUS_QD_DIMMER_G` |
| Dimmer am Terminal | Wie vorher, zusätzlich Softkey am VT und Helligkeit als Bargraph. Zwei Bedienstellen auf einen Dimmer. | `logiBUS_QD_DIMMER_G`, VT-Bausteine |
| Frequenz messen | Q1 des Frequenzgenerators auf einen Impulseingang brücken, mit `logiBUS_PI_IDA` zurückmessen, Soll und Ist am VT. Grundlage für die PI/PID-Übungen (152/153) ohne echte Welle. | `logiBUS_QDA_FREQ`, `logiBUS_PI_IDA` |

Bestehende PWM-Übungen (034, 034a1, 034b, 247, 248) bleiben, sie laufen mit den Defaults weiter.

### 4. Vorlagen von Espressif (ESP-IDF 6.1, lokal unter `~/.espressif/v6.1/esp-idf/examples/peripherals/ledc/`)

| Beispiel | Targets | Was wir daraus nehmen |
|---|---|---|
| `ledc_basic` | alle (S3, P4, S31) | Sprung ohne Rampe: `ledc_set_duty()` + `ledc_update_duty()`. Die heutigen 400 Hz und „Duty 4095 = 50 %“ stammen von hier (400 Hz ist dort nur die Variante mit Light-Sleep und `LEDC_USE_RC_FAST_CLK`, sonst 4 kHz). |
| `ledc_fade` | alle | Rampe mit `ledc_set_fade_with_time()` + `ledc_fade_start(NO_WAIT)`, Sprung mit `ledc_set_duty()` + `ledc_update_duty()`. Das heutige `LEDC_TEST_FADE_TIME` stammt von hier (dort 3000 ms, bei uns 500 ms). Das Beispiel wartet in seinem eigenen Task per Semaphor auf das Ende jeder Rampe: `ledc_cb_register()` mit `fade_cb`, der im ISR (IRAM) einen Semaphor gibt. Dieses Warten darf bei uns nie im Event-Thread passieren. Brauchbar ist der `fade_cb` aber für „Rampe fertig“: als Ereignis an den Baustein (über eine IRAM-Funktion der Firmware wie `elf_isr.h`, weil Code der ELF-Libs nicht im IRAM liegt) und auf dem S3 zum Weiterschalten der Gamma-Abschnitte aus einem Task. |
| `ledc_gamma_curve_fade` | P4, S31 | Gamma-Rampe, siehe oben. |
| `ledc_dimmer` | P4, S31 (braucht ETM) | Phasenanschnitt für Netz-Dimmer (TRIAC), siehe unten. |

### 5. Phasenanschnitt (Netz-Dimmer mit TRIAC) – nicht jetzt (entschieden 2026-11-06), nur zur Erinnerung

Das Beispiel `ledc_dimmer` ist kein PWM mit fester Frequenz, sondern Phasenanschnitt: Ein Nulldurchgangs-Detektor am
Eingang setzt per ETM bei jeder Halbwelle (100 Hz bei 50-Hz-Netz) den LEDC-Timer zurück. Der Zündimpuls für den TRIAC
(über einen Opto-Triac) wird über `hpoint` innerhalb der Halbwelle verschoben. Früher zünden heißt heller.

- Nur P4 und S31 (ETM), nicht S3.
- Braucht Hardware, die es auf den logiBUS-Boards heute nicht gibt: isolierter Nulldurchgangs-Eingang und
  Opto-Triac-Ausgang an 230 V.
- Wenn gewünscht, als eigener Baustein `logiBUS_QD_PHASE` / `QDA_PHASE` (Eingänge: Nulldurchgangs-Eingang, Helligkeit,
  mit/ohne Gamma) mit eigenem Timer je Ausgang. Der Dimmer-Baustein oben passt unverändert davor.

### 6. Sigma-Delta (SDM) – zusätzliche Kanäle für LEDs

Vorlage: `examples/peripherals/sigma_delta/sdm_led` (S3, P4, S31), daneben `sdm_dac`. Kein PWM mit fester Frequenz,
sondern Pulsdichte-Modulation:

- eigene Hardware mit 8 Kanälen auf allen drei Chips (`_SDM_CHANS_PER_INST 8`), **unabhängig von LEDC**: belegt weder
  LEDC-Kanäle noch -Timer
- Ablauf: `sdm_new_channel()` (GPIO, `sample_rate_hz`, im Beispiel 1 MHz), `sdm_channel_enable()`,
  `sdm_channel_set_pulse_density(-128..127)`. Das Setzen blockiert nicht.
- nur 8 bit (256 Stufen), keine Hardware-Rampe. Rampe und Gamma muss die Firmware in Schritten aus einem Task machen
  (das Beispiel tut genau das: alle 10 ms ein Schritt). Mit Gamma werden die untersten Stufen grob.
- schaltet mit hunderten kHz. **Nur für Logik-Ausgänge**: Status-LEDs, LED-Treiber mit Logik-Eingang,
  Hintergrundbeleuchtung, oder über RC-Filter als einfache Analogspannung (`sdm_dac`). Die Leistungsausgänge der
  logiBUS-Boards (Ventile, Lampen über High-Side-Schalter) können das nicht schalten, dort bleibt LEDC.

Vorschlag: eigener Baustein `logiBUS_QD_SDM` / `QDA_SDM` (und `_G` mit Gamma), Eingang Helligkeit wie beim PWM-Baustein
(0..8191, intern auf 8 bit), `RAMP` wie oben. Damit lassen sich mehr als 8 dimmbare LEDs betreiben, ohne die
LEDC-Kanäle für Ventile zu verbrauchen. Welche GPIOs auf welchem Board Logik-Pegel ohne Leistungsstufe haben, steht
noch aus.

**Analogausgang über SDM + Tiefpass** (Vorlage `examples/peripherals/sigma_delta/sdm_dac`, S3, P4, S31):

- S3, P4 und S31 haben **keinen echten DAC** (`SOC_DAC_SUPPORTED` fehlt bei allen drei). SDM mit RC-Tiefpass ist der
  einzige Weg zu einer Analogspannung ohne Zusatzbaustein.
- Spannung nach dem Filter: Vout = VDD_IO / 256 · density + VDD_IO / 2, also etwa 0..3,3 V in 256 Stufen. Das
  Beispiel nimmt 10 MHz Abtastrate.
- **Gleichspannung** (Sollwert, z. B. 0..10-V-Eingang eines Fremdgeräts über Verstärker): Wert setzen genügt, kein
  Takt nötig. Baustein `logiBUS_QW_AO` / `QWA_AO`, Eingang in mV oder 0..8191.
- **Kurvenform** (Sinus usw.): Das Beispiel schreibt aus einem GPTimer-Interrupt alle 100 µs den nächsten Wert einer
  Tabelle (100 Hz Sinus). Bei uns müsste dieser Interrupt in der Firmware im IRAM liegen (wie `elf_isr.h`), nicht in
  der ELF-Lib. Nur sinnvoll als Lehrbeispiel (Signalgenerator), mit Frequenz und Amplitude als Eingänge.
- Braucht ein RC-Glied auf dem Board oder als Zusatzplatine. Die Leistungsausgänge sind dafür nicht geeignet.

Übung, wenn es das gibt: Analogausgang auf einen Analogeingang brücken und mit `logiBUS_AI_IDA` zurückmessen
(wie beim Frequenzausgang und Impulseingang). Soll und Ist am VT, Fehler von Filter und ADC sichtbar machen.

### 7. Servo, Frequenzausgang und Motor auf MCPWM statt LEDC

Heute läuft der Servo (`logiBUS_QW_SERVO`, `IOHandleESP32ServoO.cpp`) auf LEDC: eigener Timer TIMER_1 mit 250 Hz
(4 ms Periode, für das Digital-Servo aus dem Conrad-Datenblatt), 13 bit. Der Eingang `OUT` (0..0xFAFF) wird fest auf
0,80..2,18 ms Pulsbreite umgerechnet. Das funktioniert, hat aber Nachteile:

- Der Servo verbraucht einen der 4 LEDC-Timer und LEDC-Kanäle, die für PWM und LED fehlen.
- Frequenz und Pulsbereich sind fest im Code. Ein normales Analog-Servo (50 Hz, 20 ms, 1..2 ms bzw. 0,5..2,5 ms)
  lässt sich nicht einstellen.
- Die Pulsbreite wird über Prozent der Periode und eine Konstante 81.91 gerechnet statt direkt in µs.

Espressif nimmt für Servos MCPWM (`examples/peripherals/mcpwm/mcpwm_servo_control`, S3, P4, S31): Timer mit 1 MHz
(1 µs pro Takt), Periode 20000 Takte = 20 ms, `mcpwm_comparator_set_compare_value()` direkt in µs. Ein neuer Wert
wird erst am Periodenende übernommen (kein Störimpuls) und blockiert nicht.

MCPWM-Ausstattung (`mcpwm_ll.h`): S3 und P4 haben je 2 Gruppen à 3 Timer, 3 Operatoren und 2 Generatoren (6 Timer,
12 Ausgänge). Der S31 hat 4 Gruppen (12 Timer, 24 Ausgänge). Das ist alles unabhängig von LEDC.

Vorschlag: **Aufteilung nach Aufgabe**

| Peripherie | wofür | warum |
|---|---|---|
| LEDC | PWM für Ventile/Lampen, LED-Dimmen, mit und ohne Gamma | Hardware-Rampe und Gamma-Rampe (P4/S31) gibt es nur hier |
| MCPWM | Servo, Frequenzausgang, Motor (BTM9010EP) | eigene Timer je Aufgabe, Takte in µs, Totzeit und Gegentakt für Brücken |
| SDM | Logik-LEDs, Analogausgang mit RC | zusätzliche 8 Kanäle |

- **Servo auf MCPWM (entschieden, Franz 2026-11-05):** `logiBUS_QW_SERVO`/`QWA_SERVO` bekommen `FREQ` (Default 50 Hz) sowie `PULSE_MIN` und
  `PULSE_MAX` (TIME oder µs, Default 1000/2000 µs). Der Wert bleibt 0..0xFAFF (oder Winkel, offen). Servos an einer
  Gruppe mit gleicher Frequenz teilen einen Timer. Damit belegt der Servo keinen LEDC-Timer mehr. Mit dem
  dynamischen Timer-Pool (Abschnitt 1) stehen alle 4 LEDC-Timer für PWM und LED zur Verfügung, je nachdem was das
  Programm nutzt: ohne LED-Blinken bis zu 4 verschiedene PWM-Frequenzen, mit LED-Blinken 3. Heute ist es genau 1
  (TIMER_0 mit 400 Hz, TIMER_3 ungenutzt).
  `FREQ` ist die Wiederholrate des Servo-Signals (50 Hz = alle 20 ms ein Puls), `PULSE_MIN`/`PULSE_MAX` sind die
  Pulsbreiten für Wert 0 bzw. Vollausschlag.
  Das heutige Conrad-Servo **Blue Bird BMS-L530MG** (Datenblatt 2023-03-02, Analog-Servo für 1/5- und 1/6-RC-Autos)
  nennt „Working Frequency & Neutral: 250 Hz & 1520 µs“ und 90° Stellweg bei 1100..1900 µs. Daher die 250 Hz im
  heutigen Code. Viele Auto-Servos sind für die schnelle Wiederholrate moderner Auto-Empfänger ausgelegt. Der
  Standard für Flug- und Standard-Servos bleibt 50 Hz. Der heutige Code fährt 800..2180 µs, also über die 1100..1900 µs
  des Datenblatts hinaus (Anschlag möglich). Für dieses Servo also `FREQ = 250`, `PULSE_MIN = 1100`,
  `PULSE_MAX = 1900`. Der Default 50 Hz / 1000..2000 µs gilt für Standard-Servos.
- **Frequenzausgang auf MCPWM** (entschieden 2026-11-06, Frage 3): eigener Timer je Ausgang, Frequenz zur Laufzeit ändern ohne
  andere Ausgänge zu stören.
- **Motor** (Frage 13): Die BTM9010EP braucht nur einen PWM-Kanal auf dem `PWM`-Pin plus `INA`/`INB`/`SEL` als GPIOs
  (siehe Leistungsstufen). Totzeit und Gegentakt aus `mcpwm_bdc_speed_control` sind dafür nicht nötig. Der PWM-Kanal
  kann also LEDC (mit `RAMP`) oder MCPWM sein. Baustein `logiBUS_QD_MOTOR` / `QDA_MOTOR`: Eingänge Drehzahl
  (−100..100 % oder Betrag + Richtung), `FREQ` (bis 20 kHz), `RAMP`, Bremsart (Low-Side/High-Side/Freilauf) bei 0;
  Ausgänge Strom (vom `IS`-Pin über den ADC) und Fehler.

Achtung Servo-Signal: Ein Servo braucht ein Signal auf Logik-Pegel (3,3/5 V). Über einen PROFET-Ausgang käme ein
12/24-V-Puls, und der PROFET ist für 1-µs-genaue Pulse zu langsam. Das Servo-Signal muss deshalb vor der
Leistungsstufe abgegriffen werden (Trainer20, Abzweigung am Hutschienenmoped). Die Firmware prüft das nicht.

Servos heute: am **Trainer20 an Q1–Q8** (Franz, 2026-11-05). Dort hängen die Ausgänge direkt am GPIO (Q1..Q6 =
GPIO40..35, Q7 = GPIO20, Q8 = GPIO21 laut `Application/components/io_digital_out/esp32s31_TRAINER20/digital_out.cpp`),
also Logik-Pegel, passt. 8 Servos auf MCPWM: je Gruppe 3 Operatoren à 2 Generatoren = 6 Ausgänge, 8 Servos belegen
also 2 Gruppen (S31 hat 4). Mit gleicher Frequenz reicht ein Timer je Gruppe. Auf S3/P4 (2 Gruppen) ginge das auch:
8 Servos brauchen 4 Operatoren (3 in Gruppe 0, 1 in Gruppe 1). In Gruppe 1 bleiben dann 2 Operatoren und 2 Timer frei,
also Platz für 2 Frequenzausgänge (oder 1 Frequenzausgang und 1 Motor-PWM).

Außerdem am **Hutschienenmoped per Abzweigung direkt von den CPU-Pins** (Franz, 2026-11-05): Das Servo-Signal wird vor
der Leistungsstufe abgegriffen, hat also Logik-Pegel. Folge: Derselbe GPIO steuert weiterhin auch den PROFET des
Ausgangs. Der Leistungsausgang Qn schaltet also im Servo-Takt (z. B. 50 Hz, 1..2 ms) mit. Dort darf keine Last
hängen, oder sie muss das vertragen. Die Firmware kann das nicht erkennen. Der Servo-Baustein weist im Kommentar und in der
Übung darauf hin. **Die Firmware lässt den Servo auf jedem Ausgang zu** (entschieden, Franz 2026-11-05), keine
Sperre über die Board-Tabelle. Wo das Signal abgegriffen wird, verantwortet der Anwender.

## Reihenfolge

1. Firmware Schritt 1 (Timer-Pool, Sprung/Rampe ohne Blockieren). Allein schon Fehlerbehebung für Krauternter.
2. IDE-Typen `FREQ`/`RAMP` an `logiBUS_QD_PWM`/`QDA_PWM`, dazu die Gamma-Varianten `logiBUS_QD_PWM_G`/`QDA_PWM_G`
   (Handle mit Gamma-Umrechnung und Gamma-Rampe). FORTE-Code headless aus der IDE generieren:
   `./export_lib.sh logiBUS_io` im LOGIBUS-Wurzelverzeichnis (Ant `build_export_lib.xml`, Ziel
   `4diac-forte/logiBUS-modules/logiBUS-io/fb`, vorher Modul in git sauber). Danach FBT-Coverage-Check,
   logiBUS_io-ELF neu bauen. Gilt genauso nach jedem weiteren neuen oder geänderten Typ (Schritte 3, 4, Servo, Motor).
3. Frequenzausgang `logiBUS_QD_FREQ`/`QDA_FREQ` (Typ + Handle).
4. `logiBUS_QD_DIMMER` / `_G` (Typ + Handle: Rampe starten, `ledc_fade_stop()`, Ist-Wert lesen; braucht Schritt 1).
5. Übungen.

**Umsetzung Schritt 2 (Stand 2026-11-06, gebaut und getestet noch nicht):**
- Typen: `logiBUS_QD_PWM`/`QDA_PWM` mit `FREQ`, `RAMP`, `RAMPO`; neu `logiBUS_QD_PWM_G`/`QDA_PWM_G` mit `GAMMA`.
- forte: Die SIFBs `QD_PWM`/`QD_PWM_G` sind handgeschrieben, die Logik steckt in `handler/logiBUSPWMOutputFB`. Der
  IDE-Export überschreibt SIFBs (`overwrite=true`) – nach `./export_lib.sh logiBUS_io` die beiden SIFB-Dateien mit
  `git checkout` zurückholen. Die Composites `QDA_PWM`/`QDA_PWM_G` sind im Stil des Generators geschrieben.
- Handle `IOHandleESP32PWMO`: Timer aus dem Pool mit `FREQ`, `RAMP` je Wert, Gamma mit `powf()`; P4/S31 Gamma-Fade in
  Hardware, S3 bis zu 16 lineare Stücke (je mindestens 20 ms) nacheinander aus dem Task.
- `RAMPO`: Der LEDC-Fade-Callback läuft im Interrupt und muss im IRAM liegen. Er ist deshalb in der Firmware
  (`elf_isr_ledc_fade_end()` in `elf_isr.c`, wie bei PCNT und ADC) und schreibt nur in eine Queue. Ein Task
  (`LEDCFadeNotifier`) ruft den Handle auf, der startet das nächste Stück oder meldet `RAMPO` (`onChange()`). Ein Ende
  zählt nur, wenn der Tastgrad dem Ziel der laufenden Rampe entspricht (`ledc_fade_stop()` löst den Callback auch aus).
  Kein `RAMPO` nach dem ersten Wert (INIT).
- Folge: Firmware und logiBUS_io-ELF zusammen neu bauen (neue Host-Symbole, u. a. `elf_isr_ledc_fade_end`,
  `ledc_cb_register`, `ledc_get_duty`, `powf`).

**Umsetzung Schritt 3 (Stand 2026-11-06, gebaut und getestet noch nicht):**
- Typen `logiBUS_QD_FREQ` (Eingang `FREQ`, DWORD in mHz) und `logiBUS_QDA_FREQ` (Socket `FREQ`, Adapter AD), `FMIN`/`FMAX`
  bei INIT, Default 10 Hz / 10 kHz. Keine Rampe: MCPWM (und LEDC für die Frequenz) hat keine Hardware-Rampe; eine
  Rampe ginge nur in Schritten aus einem Task, später nachrüstbar.
- Handle `IOHandleESP32FreqO`: je Ausgang ein eigener MCPWM-Timer, Operator, Comparator und Generator, Tastgrad 50 %
  (high am Periodenanfang, low beim Vergleichswert = Periode / 2). Neue Frequenz am Ende der laufenden Periode
  (`update_period_on_empty`, `update_cmp_on_tez`), kein Störimpuls. `FREQ = 0`: Generator fest low.
- Auflösung: 160 MHz / N, N der kleinste Teiler von 160 MHz, mit dem `FMIN` noch in 65535 Takte passt und den Gruppen-
  und Timer-Prescaler (je 1..256) exakt machen. Default `FMIN` 10 Hz → 640 kHz (Stufe 1,6 Hz bei 1 kHz, 156 Hz bei
  10 kHz). Höchstens Auflösung / 2.
- Der Gruppen-Prescaler gilt für alle Timer einer Gruppe. Der Handle nimmt die erste Gruppe mit freiem Timer und
  Operator, deren Prescaler passt. `FMIN` ab etwa 9,6 Hz bleibt bei Gruppen-Prescaler 1 und verträgt sich mit allem
  (auch Servo 1 MHz); kleinere `FMIN` ändern den Gruppen-Prescaler.
- `STATUS` nach REQ: `OK` oder z. B. „FREQ 5000 mHz below FMIN 10000 mHz, limited“.
- forte: MCPWM-Include-Pfade in den Toolchain-Dateien (S3, P4, S31); Firmware: `esp_driver_mcpwm` in
  `elf_libs_loader` (Host-Symbole `mcpwm_*`). Firmware und logiBUS_io-ELF zusammen neu bauen.
- logiBUS_io 3.2.0 (neue Typen, neue Host-Symbole).

**Umsetzung Servo, SDM und Analogausgang (Stand 2026-11-06, gebaut und getestet noch nicht), logiBUS_io 3.3.0:**
- Servo `logiBUS_QW_SERVO`/`QWA_SERVO` auf MCPWM: `FREQ` (UDINT, Default 50 Hz), `PULSE_MIN`/`PULSE_MAX` (TIME,
  Default `T#1000us`/`T#2000us`), alle bei INIT. Timer 1 MHz, Vergleichswert = Pulsbreite in µs, neuer Wert am
  Periodenende. `MCPWMServoPool`: Servos mit gleicher `FREQ` in einer Gruppe teilen einen Timer, je zwei einen
  Operator (6 je Gruppe). Werte über 0xFAFF lassen den letzten Puls stehen. Der Servo belegt kein LEDC mehr.
  **Verhaltensänderung:** bisher fest 250 Hz und 800..2180 µs. Für das Conrad-Servo (Blue Bird BMS-L530MG)
  `FREQ = 250`, `PULSE_MIN = T#1100us`, `PULSE_MAX = T#1900us` setzen.
- Sigma-Delta `logiBUS_QD_SDM`/`QDA_SDM` und `_G` (mit `GAMMA`): Wert 0..8191 → Pulsdichte 8 bit, 1 MHz, ohne Rampe.
  Nur für Logik-Ausgänge (LEDs, LED-Treiber), nicht für die Leistungsausgänge. 8 Kanäle, unabhängig von LEDC/MCPWM.
- Analogausgang `logiBUS_QW_AO`/`QWA_AO` (Paket `logiBUS::io::AO`): `OUT` in mV als WORD (QW-Baustein, Adapter AW),
  0..3287 mV in 256 Stufen nach RC-Tiefpass (VDD_IO als 3300 mV angenommen), 10 MHz. Höhere Werte werden begrenzt,
  `STATUS` meldet es. Teilt sich die 8 SDM-Kanäle mit `QD_SDM`.
- forte: Handle `IOHandleESP32SdmO` (beide Arten), `logiBUSSdmOutputFB`; Toolchains, ELF-Build (`fb_lib`) und Firmware
  (`elf_libs_loader`) mit `esp_driver_sdm`. Firmware und logiBUS_io-ELF zusammen neu bauen (Host-Symbole `sdm_*`).

`FORTE_ABI` bleibt (nur logiBUS_io-Bausteine und -Handles ändern sich, keine forte-Basisklassen).

**Umsetzung Schritt 4 Dimmer (Stand 2026-11-07, kompiliert für S3/P4/S31, gebaut und getestet noch nicht):**
- Typen `logiBUS_QD_DIMMER` / `logiBUS_QD_DIMMER_G` wie in Abschnitt 2, Ereignis-Eingänge lesen `QI`, `DIM_TIME`, `LEVEL_MIN`,
  `LEVEL_MAX`, `START`, `SOFT` (also auch während des Betriebs änderbar), `FREQ` und `GAMMA` nur bei INIT. `CNF` nach jedem
  Ereignis-Eingang mit `ON_STATE` und `LEVEL`.
- forte: `handler/logiBUSDimmerFB` (Zustand: an/aus, Richtung, gespeicherte Helligkeit), die beiden SIFBs sind
  handgeschrieben wie `QD_PWM`. Handle ist `IOHandleESP32PWMO`, neu `stop()` (Rampe anhalten, kein `RAMPO`),
  `getBrightness()` (Ist-Wert, Gamma herausgerechnet) und `isRamping()`.
- Ergänzung: Steht die Helligkeit bei einem langen Druck schon am Ende in der fälligen Richtung (z. B. `LEVEL_MAX` und
  „hoch“), dimmt er in die andere Richtung, statt nichts zu tun.
- Langer Druck bei aus: Rampe ab 0 (nicht ab `LEVEL_MIN`), Zeit nach demselben Maßstab. Wird vor `LEVEL_MIN` losgelassen, geht
  der Ausgang mit `SOFT` auf `LEVEL_MIN` (dann kommt ausnahmsweise ein `RAMPO`).
- Kein `STOP` am normalen `QD_PWM` (Franz, 2026-11-07): Ein neuer Wert unterbricht die Rampe schon, „anhalten, wo sie
  steht“ braucht bisher nur der Dimmer.
- Namen (Franz, 2026-11-07): `ON`, `OFF`, `MIN` und `MAX` sind in der 4diac IDE reservierte Schlüsselwörter, die
  Anschlüsse heißen deshalb `SWITCH_ON`, `SWITCH_OFF`, `LEVEL_MIN` und `LEVEL_MAX`.

## Entscheidungen (Franz)

Stand 2026-11-06.

1. ~~Default `RAMP`~~ – entschieden: T#0ms (Sprung). Bestehende Programme ändern damit ihr Verhalten (kein weiches
   Anfahren mehr); wer es weiter will, setzt `RAMP = T#500ms`. In den Übungen und im Changelog erwähnen.
2. ~~Tastgrad-Einheit~~ – entschieden: bleibt 0..8191 bei allen PWM-Bausteinen.
3. ~~Frequenzausgang~~ – entschieden: MCPWM (eigener Timer je Ausgang, stört LEDC nicht, siehe Abschnitt 7).
4. ~~`FREQ` des PWM-Ausgangs zur Laufzeit ändern~~ – entschieden: nein, bei den PWM-Bausteinen nur bei INIT. Bei den
   Frequenz-Bausteinen ist die Frequenz zur Laufzeit änderbar.
5. **Namen:**
   - entschieden: `logiBUS_QD_PWM_G` / `QDA_PWM_G`, `logiBUS_QD_SDM` / `QDA_SDM` und `_G`, `logiBUS_QW_AO`,
     `logiBUS_QD_MOTOR` / `QDA_MOTOR` (Name reserviert, Umsetzung später, siehe 13), Ports `FREQ`, `RAMP`, `GAMMA`,
     `PULSE_MIN`, `PULSE_MAX`, `FMIN`, `FMAX`, Ereignis `RAMPO` (Rampe fertig).
   - entschieden: `logiBUS_QD_FREQ` / `QDA_FREQ`, Frequenz DWORD in mHz, siehe 17.
   - entschieden: Dimmer `logiBUS_QD_DIMMER` / `logiBUS_QD_DIMMER_G`, eigener Ausgangsbaustein, stufenlos über die
     Hardware-Rampe (Abschnitt 2).
6. ~~Dimmer, Richtung~~ – entschieden: jeder lange Druck wechselt die Richtung, der erste nach dem Einschalten dimmt
   herunter.
7. ~~Gamma~~ – entschieden: jeden PWM-Baustein mit und ohne Gamma (`_G`), auch SDM. Nicht bei Servo, Frequenzausgang,
   Motor und `logiBUS_LED_PWM_QX`. `GAMMA` ist ein Eingang (REAL, Default 2.2, gelesen bei INIT). Die Doku der
   `_G`-Bausteine erklärt die Möglichkeiten (siehe Abschnitt „Gamma: Möglichkeiten“).
8. ~~Dimmer, Bibliothek~~ – entschieden: `logiBUS_io` (der Dimmer ist ein Ausgangsbaustein).
9. ~~Phasenanschnitt~~ – entschieden: nein, kein `logiBUS_QD_PHASE`. Vielleicht später einmal.
10. ~~Ereignis „Rampe fertig“~~ – entschieden: ja, Ereignis-Ausgang `RAMPO` an allen Bausteinen mit `RAMP` (über
    `fade_cb`, siehe `ledc_fade`). Bei `RAMP = T#0ms` kommt `RAMPO` sofort nach dem Sprung.
11. ~~Sigma-Delta-Baustein~~ – entschieden: ja, `logiBUS_QD_SDM` / `QDA_SDM` und `_G`.
12. ~~Analogausgang über SDM~~ – entschieden: ja, `logiBUS_QW_AO`. RC-Glieder sind reichlich vorhanden.
13. **Motor-Baustein für die BTM9010EP:** erst mal nicht umsetzen (Name `logiBUS_QD_MOTOR` reserviert). Offen bleiben
    `SEL`/`IS` auf dem XL26 und ob die Brücken heute als Motor genutzt werden.
14. **Bestückung je Board:** Es fehlen noch Boards (z. B. dual_io, M5, lilygo). Kann warten.
15. ~~Servo auf MCPWM umziehen~~ – entschieden: ja (Abschnitt 7). Eingang bleibt 0..0xFAFF: Der Handle rechnet in C++ auf
    die Pulsbreite um, `PULSE_MIN + OUT · (PULSE_MAX − PULSE_MIN) / 0xFAFF` µs, und gibt sie als Vergleichswert an
    `mcpwm_comparator_set_compare_value()` (Timer-Auflösung 1 MHz, 1 Tick = 1 µs wie im Espressif-Beispiel). Im
    IEC-Baustein ist keine Umrechnung nötig. Servos hängen heute am Trainer20 an Q1–Q8 (direkt am GPIO) und am
    Hutschienenmoped per Abzweigung von den CPU-Pins (geklärt).
16. ~~Heutige 400 Hz auf APIXON 15 PWR Q1 (BTH50030, max. 100 Hz)~~ – geklärt: Heute fährt dort niemand PWM. Soll
    irgendwann gehen; die Firmware lässt es zu, der Hinweis auf 100 Hz steht in Kommentar und Übung.
17. ~~Frequenzausgang, Typ der Frequenz~~ – entschieden: DWORD in mHz (1000 = 1 Hz), wie ISOBUS-DDI 583 „Setpoint
    Frequency“ (Auflösung 0,001 Hz, Bereich 0..2147483647). Passt zu `QD_FREQ` und zum Adapter AD. `FREQ` der
    PWM-Bausteine bleibt UDINT in Hz (LEDC kennt nur ganze Hz, `freq_hz`).
18. **Belegung INA/INB/PWM am XL26** mit dem Schaltplan abgleichen – später.
19. ~~Frequenzausgang, Defaults~~ – entschieden: `FMIN` 10 Hz, `FMAX` 10 kHz (in mHz: 10000 / 10000000).
20. ~~Frequenzausgang, Rampe~~ – entschieden: keine (keine Hardware-Rampe für Frequenzen), nur Sprung am Periodenende.
21. ~~Frequenzausgang, Namen und Bereich~~ – entschieden: Eingang und Socket heißen `FREQ`; `FREQ` außerhalb
    `FMIN`..`FMAX` wird begrenzt und in `STATUS` gemeldet, `FREQ = 0` ist aus.
22. ~~Servo, Typ der Pulsbreite~~ – entschieden: `PULSE_MIN`/`PULSE_MAX` als TIME.
23. ~~Servo, Defaults~~ – entschieden: 50 Hz, 1000..2000 µs (Standard-Servos); das Conrad-Servo braucht 250 Hz,
    1100..1900 µs.
24. ~~SDM, Rampe~~ – entschieden: erst ohne Rampe (nur Sprung), `RAMP`/`RAMPO` später nachrüstbar.
25. ~~Analogausgang, Einheit~~ – entschieden: mV. Als WORD, weil der Baustein `QW_AO` heißt und am Adapter AW hängt.
