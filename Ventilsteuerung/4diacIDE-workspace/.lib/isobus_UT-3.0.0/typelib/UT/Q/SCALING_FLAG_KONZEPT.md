# `xScale`-Flag für Pixel-Bausteine — Konzept

Dieses Dokument beschreibt das neue `xScale`-Feld, das auf den folgenden acht ISO
11783-6-Kommando-Bausteinen (`isobus::UT::Q`) ergänzt wurde:

| Baustein | Pixel-Feld(er) |
|---|---|
| `Q_ChildPosition.fbt` | `s16Xposition`/`s16Yposition` |
| `Q_ChildPosition_AI.fbt` | `s16Xposition`/`s16Yposition` (über AI-Sockets) |
| `Q_ChildLocation.fbt` | `u8Xchange`/`u8Ychange` |
| `Q_Size.fbt` | `u16Width`/`u16Height` |
| `Q_EndPoint.fbt` | `u16Width`/`u16Height` (Linien-Endpunkt) |
| `Q_ChangePolygonScale.fbt` | `u16NewWidth`/`u16NewHeight` |
| `Q_ChangePolygonPoint.fbt` | `u16NewXValue`/`u16NewYValue` |
| `Q_LineAttributes.fbt` | `u8LineWidth` |

## `xScale` (BOOL, Default `FALSE`)

- **`FALSE` (Default) = Bypass.** Die Pixel-Werte werden unverändert durchgereicht — exakt
  das bisherige Verhalten. Bestehende SubApp-Instanzen in diesem Repo sind dadurch
  unverändert lauffähig, ohne dass irgendetwas nachgezogen werden muss.
- **`TRUE` = Scale.** Der Baustein soll die Pixel-Werte mit dem passenden Scaling-Faktor
  multiplizieren, bevor er sie an das VT sendet.

Welcher Faktor (DataMask oder SoftKeyMask/Aux) angewendet wird, entscheidet sich nach der
Objekt-ID-Bereichstabelle in `visual-programming-languages-docs/docs/en/runtime/isobus/Scaling.md`
(`C:\git\ms-docs\visual-programming-languages-docs`): bei `Q_ChildPosition`/
`Q_ChildPosition_AI`/`Q_ChildLocation` anhand `u16ObjIdParent` (der Pixel-Offset lebt im
Koordinatenraum des Parents), bei den übrigen fünf Bausteinen anhand `u16ObjId` (Pixelwert
bezieht sich auf das Objekt selbst).

## Wichtige Einschränkung

Alle acht Bausteine (außer `Q_ChildPosition_AI`) sind **Service-Interface-Bausteine ohne
`<FBNetwork>`/`<BasicFB>`/`<Algorithm>`** in diesem Repository — ihre `.fbt`-Datei besteht
nur aus `InterfaceList` + `Documentation`-Attribut. Das eigentliche ISO-11783-6-Kommando läuft
zur Laufzeit über eine native, in FORTE kompilierte C++-Implementierung außerhalb dieses Repos.

Das Hinzufügen von `xScale` erweitert also den **deklarierten Vertrag** (mit sinnvollem
Default `FALSE`, sodass bestehende Übungen unverändert weiterlaufen) — die eigentliche
Multiplikation muss noch in der dahinterliegenden nativen Implementierung umgesetzt werden.

`Q_ChildPosition_AI.fbt` ist die einzige Ausnahme mit echtem `<FBNetwork>` in diesem Set —
dort ist `xScale` bereits real bis zur inneren `Q_ChildPosition`-Instanz durchverdrahtet.
