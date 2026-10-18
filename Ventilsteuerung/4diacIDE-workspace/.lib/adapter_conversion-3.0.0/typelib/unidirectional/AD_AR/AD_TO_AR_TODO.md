# AD_TO_AR - Offener Punkt: Bit-Reinterpretation statt numerischer Umwandlung

## TODO: `AD_TO_AR` konvertiert NICHT numerisch - Falle fuer Nutzer

`AD_TO_AR` (`adapter::conversion::unidirectional::AD_AR::AD_TO_AR`) sieht auf
den ersten Blick wie "wandle den DWORD-Zahlenwert in einen REAL-Zahlenwert
um" aus (naheliegender Name, naheliegende Erwartung bei jedem, der z.B.
einen rohen Zaehler-/Analogwert (DWORD, ganzzahlig) auf einen REAL-Adapter
bringen will). **Das stimmt nicht.** Intern nutzt es
`iec61131::conversion::F_DWORD_TO_REAL`, und das ist im FORTE-Kern eine
**Bit-Reinterpretation** (IEEE754-Bitmuster-Cast), keine Wertumwandlung.

### Beleg (echter FORTE-Quellcode, nicht geraten)

`forte_real.cpp`, `CIEC_REAL::setValue(const CIEC_ANY &paValue)`:

```cpp
case e_BYTE:
case e_WORD:
case e_DWORD:
case e_LWORD:
  // bit string will cast to the binary representation of the real value
  setValueSimple(paValue);
  break;
```

Fuer DWORD/WORD/BYTE/LWORD (Bit-String-Typen) wird `setValueSimple()`
aufgerufen - ein reiner Bit-Kopiervorgang, kein numerischer Cast. Zum
Vergleich, fuer echte Integer-Typen (UDINT, DINT, etc.) macht dieselbe
Funktion einen richtigen numerischen Cast:

```cpp
case e_USINT:
case e_UINT:
case e_UDINT:
case e_ULINT:
  setTFLOAT(static_cast<TValueType>(static_cast<const CIEC_ANY_UNSIGNED &>(paValue).getUnsignedValue()));
  break;
```

### Konkrete Auswirkung

Ein roher ganzzahliger Wert (z.B. ein Analog-Rohwert `DWORD#2048`, das
Bitmuster `0x00000800`) wird durch `AD_TO_AR` NICHT zu `REAL#2048.0`,
sondern das Bitmuster `0x00000800` wird 1:1 als IEEE754-Float
reininterpretiert - eine winzige, bedeutungslose Zahl nahe Null. Ein
stiller, schwer zu findender Bug fuer jeden, der `AD_TO_AR` fuer eine
Integer-DWORD-Quelle (Analogwert, Zaehler, Rohwert) statt fuer eine
bereits-als-Bitmuster-gemeinte DWORD (z.B. Ergebnis von `F_REAL_TO_DWORD`)
einsetzt.

### Korrekter Weg fuer numerische DWORD-zu-REAL-Umwandlung (volladapterbasiert)

Zweistufig statt `AD_TO_AR`:

1. `AD_TO_AUDI` (`adapter::conversion::unidirectional::AD_AUDI::AD_TO_AUDI`)
   - Bit-Reinterpretation DWORD→UDINT, hier **gueltig**, da beide dieselbe
     32-bit-Darstellung eines vorzeichenlosen Integers teilen.
2. `AUDI_TO_AR` (`adapter::conversion::unidirectional::AR_AUDI::AUDI_TO_AR`)
   - Nutzt intern `iec61131::conversion::F_UDINT_TO_REAL` - ein echter
     numerischer Cast (`CIEC_ANY_UNSIGNED::getUnsignedValue()` →
     `setTFLOAT()`), belegt im selben `forte_real.cpp`.

Live erprobt in `MyLib::sys::F_AI_RAW_TO_PERCENT_AD.SUB` (AI-Sample,
volladapterbasierte Alternative zur datenbasierten
`F_AI_RAW_TO_PERCENT.SUB`).

### Bereits an anderer Stelle bekannt - nicht neu entdeckt

Diese Falle war schon bekannt und ist bereits **in 7 Übungen dokumentiert**
(identischer Kommentar, jeweils im `test_AX/Uebungen`-Ordner):
`Uebung_028a_AR.SUB`, `Uebung_028a2_AR.SUB`, `Uebung_028b_AR.SUB`,
`Uebung_028b2_AR.SUB`, `Uebung_028c_AR.SUB`, `Uebung_028c2_AR.SUB`,
`Uebung_028c3_AR.SUB` - jeweils ein `<Comment>`-Objekt:

> "WICHTIG ! Doppelte Konvertierung. ein AD_TO_AR wäre wie ein
> 'reinterpret_cast'"

Alle sieben verwenden bereits korrekt die `AD_TO_AUDI` → `AUDI_TO_AR`-Kette
(z.B. `Uebung_028c3_AR.SUB`, Zeilen 68-71/92/102) statt `AD_TO_AR` direkt -
decken sich exakt mit dem oben verifizierten FORTE-Quellcode-Befund. Diese
Übungen sind außerdem eine gute Vorlage für die spätere
Kalibrierungsfunktion (Schritt 2 des AI-Samples): `Uebung_028c3_AR.SUB`
zeigt eine vollständige Zwei-Punkt-Kalibrierung (`AR_CALIBRATE` mit
Kalibrier-Tastern `CO`/`CS`, persistiert über `INI_AR2`/`.ini`-Datei), inkl.
Beispiel-Kommentar "0.0 => 0,5V, 100.0 => 4,5V (Typ. Sensor Automotive)".

**Möglicherweise verwandt, noch nicht abschließend geprüft:**
`Uebung_011e_MIXA.SUB` nutzt `AD_TO_AR` direkt (ohne die
`AD_TO_AUDI`/`AUDI_TO_AR`-Kette) und ist selbst als Negativ-Beispiel
betitelt ("falsch gemischt!", Kommentar "die beiden Namespaces sind
INKOMPATIBEL !!!"). Die Übung führt die Fehlerursache auf inkompatible
`NumericObjectPool_S`-Namespaces zwischen zwei GCF-Pools zurück - nicht
geprüft, ob die Bit-Reinterpretation von `AD_TO_AR` zusätzlich oder
stattdessen die eigentliche Ursache ist. Wert einer erneuten Durchsicht,
falls diese Übung nochmal überarbeitet wird.

### Zu klaeren / festzuhalten (fuer den Kollegen, der `adapter-3.0.0` pflegt)

1. **In `AD_TO_AR.fbt` und `F_DWORD_TO_REAL.fbt`/`.fct` dokumentieren:**
   `Identification`/`Comment` um einen deutlichen Hinweis ergaenzen
   ("Bit-Reinterpretation, KEINE numerische Umwandlung - fuer numerisch
   siehe AD_TO_AUDI + AUDI_TO_AR").
2. **Ueberlegen, ob der Name irrefuehrend ist** - ein Name wie
   `AD_TO_AR_BITCAST` waere ehrlicher; alternativ einen NEUEN, numerisch
   korrekten Adapter-Baustein anbieten (z.B. `AD_TO_AR_NUMERIC`, der intern
   schon die AD_TO_AUDI+AUDI_TO_AR-Kette macht), damit der naheliegende
   Name fuer den haeufigeren Anwendungsfall (numerische Umwandlung) auch
   das Richtige tut.
3. **Pruefen, ob dieselbe Falle bei Geschwister-Bausteinen existiert**
   (`AD_TO_AL`, `AD_TO_ALI`, `AD_TO_AI`, etc. - alle DWORD/Bit-String-zu-
   Zahlentyp-Adapter-Konvertierungen, die denselben Bit-String-Zweig in
   `CIEC_ANY::cast`/`setValue` durchlaufen koennten).

## Aenderungshistorie

### 2026-08-30
- TODO angelegt im Rahmen des AI-Samples, nachdem `AD_TO_AR` als
  naheliegender 1-Schritt-Ersatz fuer die datenbasierte
  `F_AI_RAW_TO_PERCENT.SUB` erwogen, aber als Bit-Reinterpretations-Falle
  erkannt wurde (verifiziert im echten FORTE-Quellcode,
  `C:\git2\ms\4diac-forte\core\src\datatypes\forte_real.cpp`).
