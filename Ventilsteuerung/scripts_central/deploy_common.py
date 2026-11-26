#!/usr/bin/env python3
"""Gemeinsame Konfiguration/Hilfsfunktion zum Finden der lokalen
4diac_training1-Deploy-Dateien (fboot) - genutzt von
make_4diac_training1_deploy.py (Upload) UND make_libs_manifest.py (lokale
Manifest-Erzeugung, kein Upload). Python-Portierung von deploy_common.sh.

IP-Zuordnung: NUR AX ist aktuell bekannt (192.168.178.45, seit 2026-11-04; vorher .55, von Franz genannt
2026-10-09). B-Station-IP ist noch nicht bekannt - sobald Franz sie nennt,
hier ergaenzen.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

# Im Repo liegt dieses Modul unter Ventilsteuerung/scripts_central/ (2 Ebenen
# runter von Ventilsteuerung). training1 hat (anders als Krauternter) keinen
# flachen Release-Ordner, die Erkennung ist hier also nie wirklich gefordert -
# wird trotzdem 1:1 mitgefuehrt, damit beide Repos dieselbe Logik behalten
# (siehe elf_libs_manifest_lib.py fuer die Begruendung).
_SCRIPT_DIR = Path(__file__).resolve().parent
if (_SCRIPT_DIR.parent / "4diacIDE-workspace").is_dir():
    VENTILSTEUERUNG_DIR = _SCRIPT_DIR.parent
else:
    VENTILSTEUERUNG_DIR = _SCRIPT_DIR

NODE_BASES: dict[str, list[str]] = {
    # Franz, 2026-11-04: neuer AX-Knoten 192.168.178.45 (C_45), ersetzt .55
    "192.168.178.45": ["test_AX_FORTE_PC_AX.fboot"],
    # "<B-IP-noch-unbekannt>": ["test_B_FORTE_PC_B.fboot"],
}

REPO_PATHS: dict[str, str] = {
    "test_AX_FORTE_PC_AX.fboot": "boot-files/test_AX_FORTE_PC_AX.fboot",
    "test_B_FORTE_PC_B.fboot": "boot-files/test_B_FORTE_PC_B.fboot",
}

NODE_ORDER: list[str] = ["192.168.178.45"]

# Grundausstattung an ELF-Libs, die make_4diac_training1_elf_preload.py OHNE
# Bootfile/Manifest vorab nach /data/elf-libs/ spielt und die das normale
# Deploy beim Aufraeumen NICHT loescht (Franz, 2026-10-18) - so muss pro
# Uebung nur noch Bootfile + Manifest hoch. Auswahl: Libs, die in >= ~15 %
# der Uebungs-.SUB/.sys direkt genutzt werden (Scan 2026-10-18, 957 Dateien);
# deren requires (MANIFEST.MF) kommen automatisch dazu, siehe
# preload_libs_with_requires().
PRELOAD_LIBS: list[str] = [
    "events",
    "adapter_types",
    "logiBUS_io",
    "iec61131-3",
    "iec61131-3-bool",
    "isobus_UT",
    "adapter",
    "adapter_events",
    "isobus_UT_io",
    "adapter_conversion",
    "isobus_UT_adapter",
    # Franz, 2026-10-18: gehoert ebenfalls dazu (unter der 15-%-Schwelle).
    "isobus_UT_io_adapter",
    # Franz/Online-Deploy-Test 2026-10-18: AX_SEL (adapter_iec61131-3) und die
    # OPC-UA-Adapter (net_adapter) fehlten - stecken meist in MyLib-SUBs unter
    # .lib/, die der Nutzungs-Scan nicht mitgezaehlt hat.
    "net_adapter",
    "adapter_iec61131-3",
    # Online-Deploy Servo_Slider_OPC 2026-11-04: F_ClampReal (logiBUS_signalprocessing)
    # und FIELDBUS_PERCENT_TO_WORD (signalprocessing) -> UNSUPPORTED_TYPE.
    "logiBUS_signalprocessing",
    "signalprocessing",
    # Online-Deploy Button_AI_OPC_UA 2026-11-04: events::init::INIT (init_stages)
    # -> UNSUPPORTED_TYPE; steckt in MyLib_AX SystemTick und Remote_Init_Retry.
    "init_stages",
    # Servo_AI4_Calibrate_OPC 2026-11-04: INI_AR2 (logiBUS_storage) in
    # MyLib_AX logiBUS_AI_Calibrate_3P_OPC (INI-Persistenz der Kalibrierpunkte).
    "logiBUS_storage",
    # Online-Deploy Uebung_251 2026-11-05: SEC_SWITCH_LR_BIT_WORD -> UNSUPPORTED_TYPE;
    # Uebung_253 nutzt SEC_SWITCH_LR_QUARTER_WORD.
    "logiBUS_sections_bit",
    "logiBUS_sections_quarter",
]

# Nie vorab laden: das Board "Trainer" hat keinen CAN2 (Funk, DataPanel,
# BlinkMarine haengen daran), Bosch ebenfalls nicht noetig (Franz).
PRELOAD_EXCLUDE: set[str] = {"Funk", "DataPanel", "BlinkMarine", "logiBUS_bosch"}


def preload_libs_with_requires() -> list[str]:
    """PRELOAD_LIBS plus alle (transitiven) requires laut MANIFEST.MF, ohne
    PRELOAD_EXCLUDE. Reihenfolge: erst PRELOAD_LIBS, dann neu hinzugekommene
    Abhaengigkeiten in Fundreihenfolge."""
    from elf_libs_manifest_lib import lib_requires_of

    result: list[str] = []
    todo = list(PRELOAD_LIBS)
    while todo:
        lib = todo.pop(0)
        if lib in result or lib in PRELOAD_EXCLUDE:
            continue
        result.append(lib)
        todo.extend(name for name, _range in lib_requires_of(lib))
    return result


def resolve_local_path(base: str) -> Optional[Path]:
    """Liefert den tatsaechlichen lokalen Pfad zu einer Basisdatei: zuerst
    gestempelte Variante im Ventilsteuerung-Wurzelverzeichnis, dann
    unbestempelte Variante dort, dann Repo-Fallback-Pfad. None, wenn nichts
    gefunden (entspricht resolve_local_path() in deploy_common.sh).

    Bei mehreren gestempelten Treffern (Stempel ist "<ISO-Datum>_<Git-Kurz-
    Hash>", siehe make_krauternter_release.py) den zuletzt geschriebenen
    nehmen (st_mtime), NICHT den alphabetisch ersten: der Hash-Teil ist
    innerhalb desselben Tages nicht chronologisch sortierbar, ein reiner
    Namens-Sort koennte also faelschlich einen aelteren Export waehlen
    (Sourcery-Finding, PR #288)."""
    name, _, ext = base.rpartition(".")
    stamped = list(VENTILSTEUERUNG_DIR.glob(f"{name}_*.{ext}"))
    if stamped:
        return max(stamped, key=lambda p: p.stat().st_mtime)
    plain = VENTILSTEUERUNG_DIR / base
    if plain.is_file():
        return plain
    repo_rel = REPO_PATHS.get(base)
    if repo_rel:
        repo = VENTILSTEUERUNG_DIR / repo_rel
        if repo.is_file():
            return repo
    return None
