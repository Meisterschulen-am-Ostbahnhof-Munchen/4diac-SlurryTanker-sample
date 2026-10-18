# FIELDBUS_SIGNAL Erweiterung - Offene Punkte

## Übersicht Datentypen

| Bits | Name | Basis-Baustein | Adapter-Baustein | Status |
|------|------|----------------|-------------------|--------|
| 2 bit | QUARTER | FIELDBUS_QUARTER_TO_SIGNAL | AQ_FIELDBUS_QUARTER_TO_SIGNAL | ✅ |
| 3 bit | TRIO | FIELDBUS_TRIO_TO_SIGNAL | ATRIO_FIELDBUS_TRIO_TO_SIGNAL | ❌ OFFEN |
| 4 bit | NIBBLE | FIELDBUS_NIBBLE_TO_SIGNAL | ANIBBLE_FIELDBUS_NIBBLE_TO_SIGNAL | ❌ OFFEN |
| 8 bit | BYTE | FIELDBUS_BYTE_TO_SIGNAL | AB_FIELDBUS_BYTE_TO_SIGNAL | ✅ |
| 16 bit | WORD | FIELDBUS_WORD_TO_SIGNAL | AW_FIELDBUS_WORD_TO_SIGNAL | ✅ |
| 32 bit | DWORD | FIELDBUS_DWORD_TO_SIGNAL | AD_FIELDBUS_DWORD_TO_SIGNAL | ✅ |
| 64 bit | LWORD | FIELDBUS_LWORD_TO_SIGNAL | AL_FIELDBUS_LWORD_TO_SIGNAL | ✅ |
| 8 bit | USINT | FIELDBUS_USINT_TO_SIGNAL | AUS_FIELDBUS_USINT_TO_SIGNAL | ✅ |
| 16 bit | UINT | FIELDBUS_UINT_TO_SIGNAL | AUI_FIELDBUS_UINT_TO_SIGNAL | ✅ |
| 32 bit | UDINT | FIELDBUS_UDINT_TO_SIGNAL | AUDI_FIELDBUS_UDINT_TO_SIGNAL | ✅ |
| 64 bit | ULINT | FIELDBUS_ULINT_TO_SIGNAL | AULI_FIELDBUS_ULINT_TO_SIGNAL | ✅ |

## Skalierte Varianten (_SCALED)

| Bits | Name | Basis-Baustein | Adapter-Baustein | Status |
|------|------|----------------|-------------------|--------|
| 8 bit | BYTE | FIELDBUS_BYTE_TO_SIGNAL_SCALED | AB_FIELDBUS_BYTE_TO_SIGNAL_SCALED | ✅ |
| 16 bit | WORD | FIELDBUS_WORD_TO_SIGNAL_SCALED | AW_FIELDBUS_WORD_TO_SIGNAL_SCALED | ✅ |
| 32 bit | DWORD | FIELDBUS_DWORD_TO_SIGNAL_SCALED | AD_FIELDBUS_DWORD_TO_SIGNAL_SCALED | ✅ |
| 64 bit | LWORD | FIELDBUS_LWORD_TO_SIGNAL_SCALED | AL_FIELDBUS_LWORD_TO_SIGNAL_SCALED | ✅ |
| 8 bit | USINT | FIELDBUS_USINT_TO_SIGNAL_SCALED | AUS_FIELDBUS_USINT_TO_SIGNAL_SCALED | ✅ |
| 16 bit | UINT | FIELDBUS_UINT_TO_SIGNAL_SCALED | AUI_FIELDBUS_UINT_TO_SIGNAL_SCALED | ✅ |
| 32 bit | UDINT | FIELDBUS_UDINT_TO_SIGNAL_SCALED | AUDI_FIELDBUS_UDINT_TO_SIGNAL_SCALED | ✅ |
| 64 bit | ULINT | FIELDBUS_ULINT_TO_SIGNAL_SCALED | AULI_FIELDBUS_ULINT_TO_SIGNAL_SCALED | ✅ |

## Compound Scale Varianten (_COMPOUND_SCALE)

| Bits | Name | Basis-Baustein | Adapter-Baustein | Status |
|------|------|----------------|-------------------|--------|
| 16 bit | WORD | FIELDBUS_WORD_TO_SIGNAL_COMPOUND_SCALE | AW_FIELDBUS_WORD_TO_SIGNAL_COMPOUND_SCALE | ✅ |
| 16 bit | UINT | FIELDBUS_UINT_TO_SIGNAL_COMPOUND_SCALE | AUI_FIELDBUS_UINT_TO_SIGNAL_COMPOUND_SCALE | ✅ |

Verwendet für:
- MSS Machine Selected Speed (SPN 4305)
- MSSC Machine Selected Speed Command (SPN 4310, 4311)

Skalierung: Upper Byte = 0.256, Lower Byte = 0.001

## Offene Fragen

### 1. Konstanten für TRIO (3 bit)
- Welche Konstanten sollen verwendet werden?
- Vorschlag: `DONT_CARE_3bit`, `NOT_AVAILABLE_3Bit`
- Alternativen?

### 2. Konstanten für NIBBLE (4 bit)
- Welche Konstanten sollen verwendet werden?
- Vorschlag: `DONT_CARE_4bit`, `NOT_AVAILABLE_4Bit`
- Alternativen?

### 3. Gültigkeitsprüfung
- Bei QUARTER: `IF (IN < DONT_CARE_2bit)` (logisch: kleiner als DONT_CARE = gültig)
- Bei anderen: `IF (IN <= VALID_SIGNAL_XX)` (kleiner oder gleich = gültig)
- Wie soll die Prüfung für TRIO und NIBBLE aussehen?

## Adapter-Namensschema

| Prefix | Datentyp |
|--------|----------|
| AB | BYTE (8 bit) |
| AW | WORD (16 bit) |
| AD | DWORD (32 bit) |
| AL | LWORD (64 bit) |
| AUI | UINT (16 bit unsigned) |
| AUS | USINT (8 bit unsigned) |
| AULI | ULINT (64 bit unsigned) |
| AUDI | UDINT (32 bit unsigned) |
| AQ | QUARTER (2 bit) |
| ATRIO | TRIO (3 bit) | ⬅️ OFFEN
| ANIBBLE | NIBBLE (4 bit) | ⬅️ OFFEN

## Known Issues / Limitations

### ULINT/LWORD Blöcke
- FIELDBUS_ULINT_TO_SIGNAL und AULI verwenden FIELDBUS_SIGNAL mit LWORD Konstanten
- FIELDBUS_SIGNAL.gcf muss in 4diac Installation aktualisiert werden (C:\4diac\...)
- Lokale Kopie in logiBUS-3.0.0/typelib/signalprocessing/fieldbus/ ist aktuell

## Änderungshistorie

### 2026-06-01
- IEC 61131-3 Compliance Fix: Alle Vergleiche mit Bit-String Typen verwenden jetzt explizite Type-Casts
  - BYTE: `BYTE_TO_USINT(IN) <= BYTE_TO_USINT(VALID_SIGNAL_B)`
  - WORD: `WORD_TO_UINT(IN) <= WORD_TO_UINT(VALID_SIGNAL_W)`
  - DWORD: `DWORD_TO_UDINT(IN) <= DWORD_TO_UDINT(VALID_SIGNAL_DW)`
  - LWORD: `LWORD_TO_ULINT(IN) <= LWORD_TO_ULINT(VALID_SIGNAL_LW)`
- Hintergrund: IEC 61131-3 erlaubt keine Ungleichheitsvergleiche auf Bit-String Typen direkt

### 2026-05-31
- Compound Scale Blöcke erstellt (MSS, MSSC Signale)
- Alle _SCALED Varianten erstellt (16 Blöcke)
- Alle Basis- und Adapter-Blöcke erstellt (18 Blöcke)
- FIELDBUS_SIGNAL.gcf mit LWORD Konstanten erweitert
