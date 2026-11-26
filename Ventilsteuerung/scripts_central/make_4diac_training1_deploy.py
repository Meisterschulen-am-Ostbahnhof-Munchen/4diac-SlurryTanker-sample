#!/usr/bin/env python3
"""Verteilt die aktuellen 4diac_training1-Boot-Dateien per HTTP auf die
Trainings-Knoten (file_server-Baustein aus LOGIBUS_integration_datapanel/
Application/components/file_server, POST /upload/<datei> mit rohem
Binaerinhalt nach /data/<datei>) - gleicher Mechanismus wie bei Krauternter
(Ventilsteuerung/make_krauternter_deploy.sh), ANNAHME: die Trainings-Station
laeuft auf derselben Firmware (LOGIBUS_integration_datapanel).

Python-Portierung von make_4diac_training1_deploy.sh, reine Stdlib
(http.client) - keine externe Abhaengigkeit (kein requests), damit
`python make_4diac_training1_deploy.py` ohne pip-Installation laeuft und
kein Git Bash mehr noetig ist.

Laedt nur hoch, rebootet NICHT automatisch - FORTE liest *.fboot nur beim
Booten neu ein, ein Neustart des Knotens muss also manuell ausgeloest werden
(z.B. ueber den "Reboot"-Button auf der Knoten-Weboberflaeche http://<ip>/).

Baut selbst nichts - Boot-Files (4diac-IDE-Export) muessen vorher aktuell
exportiert sein.
"""

from __future__ import annotations

import http.client
import re
import sys
import tempfile
import time
from pathlib import Path
from typing import Optional

from deploy_common import NODE_BASES, NODE_ORDER, REPO_PATHS, preload_libs_with_requires, resolve_local_path
from elf_libs_manifest_lib import (
    LIB_VERSIONS,
    SUPPORTED_ARCHS,
    ManifestResult,
    internal_host,
    is_internal_host,
    build_libs_manifest,
    resolve_host,
    resolve_node_arch,
    resolve_required_libs,
    sha256_of,
)

# Generell eingeschaltet - siehe elf_libs_manifest_lib.py/.sh fuer das
# Firmware-Verhalten bei fehlendem/ungueltigem Manifest (existiert eine
# *.libs.json und ist sie nicht ladbar, startet FORTE NICHT, Netzwerk/
# Dateiserver bleiben aktiv).
ENABLE_ELF_LIBS = True

# 2026-10-10: Ein fehlendes logiBUS_utils auf Krauternter-STG1 nach einem
# echten ENABLE_ELF_LIBS=True-Deploy stammte NICHT von einem zusaetzlichen
# Vorab-Check, sondern von einem Firmware-Bug im ALTEN Upload-Handler
# (Zielverzeichnis kam aus dem zuletzt in der Weboberflaeche angezeigten
# Ordner, nach einem Boot ohne Browser-Zugriff leer -> "Failed to create
# file", aber trotzdem HTTP 303 "Erfolg" zurueckgemeldet) - siehe
# Cross-Session-Austausch mit ELFLOADER. Mit ELFLOADER abgestimmtes neues
# Protokoll (Firmware-seitig noch nicht gebaut/geflasht):
#   - GET /sha256/ (ohne Pfad) liefert ALLE bekannten Hashes in einem
#     Request ("<hash>  <pfad>" je Zeile) - wird EINMAL pro Knoten geholt,
#     nicht pro Datei.
#   - GET /sha256/<pfad> verifiziert NACH einem Upload, ob die Datei
#     wirklich angekommen ist - deckt genau den 303-aber-nicht-gespeichert-
#     Fall auf.
# Auto-Erkennung: antwortet GET /sha256/ mit 200, gilt der Knoten als
# "sha256-faehig" (neue Firmware) und bekommt den vollen Skip+Verify-Ablauf;
# jede andere Antwort (404 = alte Firmware, Verbindungsfehler) schaltet
# BEIDES komplett ab - laeuft dann exakt wie vor dieser Erweiterung.
_SHA256_LISTING_RE = re.compile(r'^([0-9a-f]{64})\s+(\S+)$', re.MULTILINE)


def http_remote_sha256_listing(ip: str, timeout: float = 10) -> Optional[dict[str, str]]:
    """GET /sha256/ - liefert alle bekannten (Pfad -> Hash)-Paare in einem
    Request. None wenn die neue Firmware (noch) nicht vorhanden ist (Status
    != 200, Verbindungsfehler) - dann ist der Knoten NICHT sha256-faehig,
    auch wenn er zufaellig gar keine Dateien hat (leeres dict waere sonst
    nicht von "Firmware unterstuetzt es nicht" zu unterscheiden).

    Live beobachtet (2026-10-10): das Listing liefert die Pfade mit
    "/data/"-Praefix (z.B. "/data/adapter-3.0.0-riscv32.elf",
    "/data/elf-libs/adapter-3.0.0-riscv32.elf"). Nur dieses Praefix wird
    entfernt - NICHT auf den nackten Dateinamen kuerzen! Ein ELF liegt seit
    der elf-libs/-Umstellung unter "elf-libs/<name>", eine gleichnamige
    Datei direkt in /data/ (von einem aelteren Deploy) ist etwas ANDERES -
    beim Kuerzen auf den nackten Namen wuerden beide auf denselben
    Schluessel fallen und ein Upload faelschlich uebersprungen (genau das
    ist am 2026-10-10 passiert: alle ELFs wurden als "schon in elf-libs/
    vorhanden" erkannt, obwohl sie nur noch am alten Ort lagen - keiner
    wurde tatsaechlich nach elf-libs/ hochgeladen)."""
    try:
        status, body = _http(ip, "GET", "/sha256/", timeout)
        if status != 200:
            return None
        text = body.decode("ascii", errors="ignore")
        result = {}
        for h, path in _SHA256_LISTING_RE.findall(text):
            name = path[len("/data/"):] if path.startswith("/data/") else path
            result[name] = h.lower()
        return result
    except OSError:
        return None


FBOOT_SUFFIX = ".fboot"
_FBOOT_HREF_RE = re.compile(r'href="/([^"]*\.fboot)"')
_MANIFEST_HREF_RE = re.compile(r'href="/([^"]*\.libs\.json)"')
_ELF_LIBS_HREF_RE = re.compile(r'href="/elf-libs/([^"]*\.elf)"')


def _http(ip: str, method: str, path: str, timeout: float, body: Optional[bytes] = None) -> tuple[int, bytes]:
    # nur Knoten im internen Netz; sonst NonInternalHostError (ein OSError,
    # die Aufrufer behandeln ihn wie einen nicht erreichbaren Knoten)
    conn = http.client.HTTPConnection(internal_host(ip), timeout=timeout)
    try:
        conn.request(method, path, body=body)
        resp = conn.getresponse()
        return resp.status, resp.read()
    finally:
        conn.close()


def http_warmup(ip: str) -> None:
    """Manche Knoten-Webserver antworten auf den allerersten Request nach dem
    Booten nicht zuverlaessig - ein Aufwaerm-Request VOR der eigentlichen
    Erreichbarkeitspruefung behebt das. Ergebnis wird bewusst ignoriert."""
    try:
        _http(ip, "GET", "/", 5)
    except OSError:
        pass


def http_reachable(ip: str) -> bool:
    """Wie curl -m 5 -o /dev/null ...: jede empfangene HTTP-Antwort (auch
    4xx/5xx) zaehlt als erreichbar, nur ein Verbindungsfehler/Timeout als
    nicht erreichbar."""
    try:
        _http(ip, "GET", "/application/", 5)
        return True
    except OSError:
        return False


def http_listing(ip: str, path: str = "/", timeout: float = 5, missing_ok: bool = False) -> Optional[str]:
    """GET <path> (Default "/") als Text fuer die href-Listing-Regexe. None
    bei Verbindungsfehler ODER einem nicht-200-Status - ANDERS als fruehere
    Versionen (leerer String bzw. der rohe Body jedes Status): ein leeres
    Verzeichnis, eine Fehlerseite und ein fehlgeschlagener Request waren
    sonst nicht zu unterscheiden, eine 404-Fehlerseite waere sogar versucht
    worden als Listing zu parsen (CodeRabbit-Finding, PR #288).

    missing_ok=True: ein HTTP 404 gilt als "Verzeichnis existiert (noch)
    nicht" und liefert "" (keine hrefs) statt None - Normalfall fuer
    /elf-libs/ auf einem Knoten vor dem allerersten ELF-Upload (z.B. nach
    "Format File System"), kein Fehler. path kann ein Unterverzeichnis sein
    (z.B. "/elf-libs/")."""
    try:
        status, data = _http(ip, "GET", path, timeout)
        if status == 404 and missing_ok:
            return ""
        if status != 200:
            return None
        return data.decode("utf-8", errors="replace")
    except OSError:
        return None


def http_delete(ip: str, name: str, timeout: float = 10) -> bool:
    """POST /delete/<name>. Gibt True nur bei HTTP 303 (dokumentierter
    Erfolgsstatus, wie bei POST /upload/<name>) oder 404 (Datei war schon
    weg - ebenfalls ein Erfolg aus Aufrufersicht) zurueck, sonst False -
    sowohl bei einem Verbindungsfehler als auch bei jedem anderen HTTP-
    Status (z.B. 500), den die fruehere Version faelschlich als Erfolg
    gewertet haette (CodeRabbit-Finding, PR #288)."""
    try:
        status, _body = _http(ip, "POST", f"/delete/{name}", timeout)
        return status in (303, 404)
    except OSError:
        return False


def http_reset_current_directory(ip: str, timeout: float = 5) -> bool:
    """GET / - die alte Firmware merkt sich serverseitig das zuletzt per GET
    angezeigte Verzeichnis und legt dort JEDEN nachfolgenden pfadlosen Upload
    ab (live bestaetigt 2026-10-10 mit ELFLOADER: ein Manifest-Upload nach
    der ELF-Upload-Runde landete dadurch in /data/elf-libs/ statt /data/ -
    der Loader sucht *.libs.json aber nur direkt in /data/ und findet dort
    dann keins, FORTE startet ohne Libs). Vor jedem pfadlosen Upload, der auf
    eine Unterverzeichnis-Listung (z.B. /elf-libs/) folgen koennte, wird das
    Verzeichnis hierueber wieder auf /data/ zurueckgesetzt. Gibt True nur bei
    HTTP 200 zurueck - der Aufrufer kann einen Fehlschlag so wenigstens
    melden (keine echte Serialisierung gegen einen GLEICHZEITIGEN Zugriff
    eines anderen Clients auf denselben Knoten, das bleibt ein bekanntes,
    akzeptiertes Restrisiko bei diesem unauthentifizierten Protokoll)."""
    try:
        status, _body = _http(ip, "GET", "/", timeout)
        return status == 200
    except OSError:
        return False


_SHA256_RE = re.compile(r'^[0-9a-f]{64}$')


def http_remote_sha256(ip: str, remote_name: str, timeout: float = 5) -> Optional[str]:
    """GET /sha256/<remote_name> - optionale Firmware-Erweiterung (Stand
    2026-10-10: noch nicht gebaut, mit ELFLOADER-Session abgestimmt), die die
    SHA256 einer bereits vorhandenen Datei zurueckgibt, um unveraenderte
    ELF-Uploads einzusparen. None bei JEDEM Fehler (Endpunkt existiert noch
    nicht -> 404, Datei fehlt, falsche Firmware, Verbindungsfehler) - der
    Aufrufer laedt dann einfach wie bisher hoch, keine Fehlerbehandlung
    noetig, kein Verhaltensunterschied zu vorher."""
    try:
        status, body = _http(ip, "GET", f"/sha256/{remote_name}", timeout)
        if status != 200:
            return None
        text = body.decode("ascii", errors="ignore").strip().lower()
        return text if _SHA256_RE.match(text) else None
    except OSError:
        return None


def http_upload_file(
    ip: str,
    local_path: Path,
    remote_name: str,
    timeout: float,
    local_sha256: Optional[str] = None,
    remote_hashes: Optional[dict[str, str]] = None,
    verify_after_upload: bool = False,
) -> str:
    """POST /upload/<remote_name> mit dem rohen Binaerinhalt von local_path,
    OHNE Redirects zu folgen (http.client folgt nie automatisch, wie curl
    ohne -L). Gibt zurueck:
    - "SKIP": remote_hashes[remote_name] == local_sha256 (aus einem vorher
      per http_remote_sha256_listing() geholten Listing) UND eine zusaetzliche
      Einzelpruefung per http_remote_sha256() bestaetigt das - Datei liegt
      bereits unveraendert vor, kein Upload noetig.
    - "VERIFY_FAILED": Upload wurde mit HTTP 303 quittiert, aber
      verify_after_upload ist gesetzt und die anschliessende
      http_remote_sha256()-Pruefung zeigt einen abweichenden/fehlenden Hash -
      die Firmware hat "Erfolg" gemeldet, obwohl die Datei nicht (korrekt)
      gespeichert wurde.
    - "RECOVERED": der Upload-Request selbst ist mit einem Verbindungsfehler/
      Timeout abgebrochen (frueher "000"), die Datei liegt laut
      http_remote_sha256() aber vollstaendig mit dem erwarteten Hash auf dem
      Knoten - wird vom Aufrufer wie "303" als Erfolg gewertet.
    - den HTTP-Status als String sonst ("303" = echter, verifizierter
      Erfolg), "000" bei jedem Verbindungsfehler/nicht lesbarer Datei, der
      sich auch per Hash-Abfrage nicht als angekommen bestaetigen laesst.
    Alle neuen Parameter sind optional, damit alte Aufrufer unveraendert
    funktionieren (kein lokaler Hash -> kein Skip, keine Verifikation).
    remote_name darf einen Unterordner enthalten (z.B. "elf-libs/x.elf") -
    der SKIP-Vergleich nutzt den VOLLEN remote_name als Schluessel (nicht
    nur den Dateinamen!), weil remote_hashes (siehe
    http_remote_sha256_listing()) ebenfalls volle, nur um das "/data/"-
    Praefix gekuerzte Pfade als Schluessel hat - "elf-libs/x.elf" und ein
    gleichnamiges "x.elf" direkt in /data/ sind unterschiedliche Dateien,
    ein Vergleich nur ueber den nackten Namen haette hier beide
    faelschlich gleichgesetzt (siehe Kommentar in
    http_remote_sha256_listing(), 2026-10-10)."""
    if remote_hashes is not None and local_sha256 is not None and remote_hashes.get(remote_name) == local_sha256:
        # Die Batch-Liste (http_remote_sha256_listing()) kommt laut
        # ELFLOADER (2026-10-10) aus einem RAM-Cache, der ein "Format File
        # System" nicht leert und nicht prueft, ob die Datei noch existiert -
        # nach einem Format kann sie also den Hash einer laengst geloeschten
        # Datei zeigen (live beobachtet: ein .fboot wurde so faelschlich
        # uebersprungen). Der Einzel-Endpunkt macht vorher einen stat() und
        # liefert bei fehlender Datei zuverlaessig 404/None, deshalb hier vor
        # jedem SKIP nochmal einzeln gegenpruefen.
        if http_remote_sha256(ip, remote_name) == local_sha256:
            return "SKIP"
    try:
        data = local_path.read_bytes()
    except OSError:
        return "000"
    # Die Firmware (file_server.cpp, upload_post_handler) berechnet nach dem
    # letzten Byte noch den SHA-256 der ganzen Datei, BEVOR sie antwortet -
    # bei grossen Dateien und laufendem FORTE reichten 30 s nicht (Krauternter
    # STG1, 2,4 MB, 2026-10-18: HTTP 000, Datei war aber vollstaendig da,
    # Analyse ELFMASTER). Zeitlimit daher mit der Dateigroesse wachsen lassen.
    timeout = max(timeout, 30 + 20 * len(data) / 1_000_000)
    try:
        status, _body = _http(ip, "POST", f"/upload/{remote_name}", timeout, body=data)
    except OSError:
        # Antwort verloren (Timeout/Verbindungsabriss) heisst nicht, dass die
        # Datei fehlt: per Hash nachsehen, ob sie vollstaendig angekommen ist
        # (der Hash kann kurz noch in Berechnung sein, daher mehrfach).
        if verify_after_upload and local_sha256 is not None:
            for _ in range(10):
                if http_remote_sha256(ip, remote_name) == local_sha256:
                    return "RECOVERED"
                time.sleep(3)
        return "000"
    if status == 303 and verify_after_upload and local_sha256 is not None:
        # Live gegen die erste echte sha256-faehige Firmware beobachtet
        # (2026-10-10): der Hash wird laut ELFLOADER "nach jedem Upload neu"
        # im Hintergrund berechnet - eine Verifikation UNMITTELBAR nach dem
        # Upload kann dadurch kurz einen veralteten/fehlenden Hash sehen,
        # obwohl die Datei korrekt gespeichert wurde (manuelle Nachpruefung
        # Sekunden spaeter zeigte den richtigen Hash). Deshalb kurz erneut
        # versuchen, bevor ein echter Fehler gemeldet wird.
        verified = http_remote_sha256(ip, remote_name)
        if verified != local_sha256:
            time.sleep(1)
            verified = http_remote_sha256(ip, remote_name)
        if verified != local_sha256:
            return "VERIFY_FAILED"
    return str(status)


def main() -> int:
    missing = False
    for ip in NODE_ORDER:
        for base in NODE_BASES.get(ip, []):
            if resolve_local_path(base) is None:
                print(f"FEHLER: Deploy-Datei fehlt: {base} (weder gestempelt noch unter {REPO_PATHS.get(base)})")
                missing = True
    if missing:
        print("Abbruch: Fehlende Dateien zuerst neu bauen/exportieren (4diac-IDE-Export).")
        return 1

    reboot_needed: list[str] = []
    unreachable: list[str] = []
    upload_failed: list[str] = []

    for node in NODE_ORDER:
        print("-" * 78)
        # Name einmal aufloesen, danach nur noch die IP (siehe resolve_host);
        # NODE_BASES und die Ergebnislisten bleiben beim Namen aus NODE_ORDER
        ip = resolve_host(node)
        if ip is None:
            print(f"Knoten {node}")
            print(f"WARNUNG: {node} nicht aufloesbar - uebersprungen.")
            unreachable.append(node)
            continue
        print(f"Knoten {node}" if ip == node else f"Knoten {node} ({ip})")

        if not is_internal_host(ip):
            print(f"FEHLER: {ip} ist kein Knoten im internen Netz (erlaubt: 10.x, 172.16-31.x, 192.168.x, 169.254.x, *.local) - uebersprungen.")
            unreachable.append(node)
            continue

        http_warmup(ip)

        if not http_reachable(ip):
            print(f"WARNUNG: {ip} nicht erreichbar - uebersprungen.")
            unreachable.append(node)
            continue

        node_ok = True
        node_local_files: list[Path] = []
        node_fboot_file: Optional[Path] = None

        # Geraet VOR jedem Upload pruefen, aber nur wenn das .fboot ELF-Libs
        # braucht (rein lokal aus dem .fboot). Passt das Geraet nicht, wird fuer
        # diesen Knoten nichts hochgeladen - sonst laege das neue Bootfile neben
        # dem alten Manifest, der Loader lehnt das beim Start ab und FORTE
        # startet nicht (Sourcery-Finding, PR #351).
        fboot_bases = [b for b in NODE_BASES.get(node, []) if b.endswith(FBOOT_SUFFIX)]
        planned_fboot = resolve_local_path(fboot_bases[0]) if fboot_bases else None
        required_libs: list[str] = (
            resolve_required_libs(planned_fboot) if ENABLE_ELF_LIBS and planned_fboot is not None else []
        )
        arch: Optional[str] = None
        if required_libs:
            arch = resolve_node_arch(ip)
            if not arch:
                print(f"  FEHLER: Architektur/FORTE_ABI fuer {ip} nicht passend oder unbekannt - fuer diesen Knoten nichts hochgeladen.")
                upload_failed.append(node)
                continue

        remote_hashes = http_remote_sha256_listing(ip)
        sha256_capable = remote_hashes is not None
        if remote_hashes is None:
            remote_hashes = {}

        for base in NODE_BASES.get(node, []):
            local_file = resolve_local_path(base)
            assert local_file is not None  # durch die MISSING-Pruefung oben ausgeschlossen
            node_local_files.append(local_file)
            if base.endswith(FBOOT_SUFFIX):
                node_fboot_file = local_file

            remote_name = local_file.name

            http_code = http_upload_file(
                ip, local_file, remote_name, 30,
                sha256_of(local_file), remote_hashes, sha256_capable,
            )
            if http_code == "SKIP":
                print(f"  {local_file} -> {remote_name}: unveraendert (Hash stimmt), Upload uebersprungen")
            elif http_code == "VERIFY_FAILED":
                print(f"  FEHLER: {local_file} -> {remote_name}: Upload mit HTTP 303 quittiert, Datei laut Geraet aber nicht/falsch gespeichert!")
                node_ok = False
            else:
                print(f"  Lade {local_file} -> http://{ip}/upload/{remote_name}")
                if http_code == "303":
                    print(f"  OK (HTTP {http_code})")
                elif http_code == "RECOVERED":
                    print("  OK (Antwort verloren, Datei laut Hash aber vollstaendig angekommen)")
                else:
                    print(f"  WARNUNG: Upload fehlgeschlagen (HTTP {http_code})")
                    node_ok = False

            # Bei .fboot-Dateien anders benannte alte Bootfiles entfernen,
            # sonst entscheidet FORTE beim Booten per alphabetischer
            # Sortierung ueber mehrere *.fboot-Kandidaten. ERST NACHDEM der
            # neue Bootfile nachweislich auf dem Knoten liegt (SKIP oder
            # echter 303-Erfolg oben) - sonst wuerde ein fehlgeschlagener
            # Upload den Knoten komplett ohne funktionierenden Bootfile
            # zuruecklassen (Sourcery-Finding, PR #288).
            if remote_name.endswith(FBOOT_SUFFIX) and http_code in ("SKIP", "303", "RECOVERED"):
                listing = http_listing(ip)
                if listing is None:
                    print("  WARNUNG: Verzeichnis-Listing fehlgeschlagen - alte Bootfile-Kandidaten NICHT geprueft/entfernt.")
                    node_ok = False
                else:
                    for existing in _FBOOT_HREF_RE.findall(listing):
                        if existing != remote_name:
                            print(f"  Entferne alten Bootfile-Kandidaten: {existing}")
                            if not http_delete(ip, existing):
                                print(f"  WARNUNG: Loeschen von {existing} fehlgeschlagen.")
                                node_ok = False

        # ENTWURF/EXPERIMENTAL (Standard AN): ELFs + Libs-Manifest zusaetzlich
        # zum fboot hochladen. Fehlt lokal auch nur ein benoetigtes ELF, wird
        # dieser Teil fuer den Knoten uebersprungen - der normale fboot-
        # Upload oben ist davon unberuehrt.
        if node_ok and ENABLE_ELF_LIBS and node_fboot_file is not None:
            # arch und required_libs stehen seit der Pruefung vor dem Upload fest
            # (arch nur gesetzt, wenn required_libs nicht leer ist)
            manifest_name = f"{node_fboot_file.stem}.libs.json"

            with tempfile.TemporaryDirectory() as tmp_dir:
                manifest_tmp = Path(tmp_dir) / "manifest.json"
                if required_libs and arch:
                    result = build_libs_manifest(arch, node_local_files, manifest_tmp, required_libs)
                else:
                    print("  Keine bekannten ausgelagerten Libs in diesem .fboot referenziert - kein Libs-Manifest noetig.")
                    result = ManifestResult(True)

                if not result.ok:
                    print("  WARNUNG: Manifest-Erzeugung fehlgeschlagen (siehe Warnung oben) - Deploy fuer diesen Knoten fehlgeschlagen.")
                    node_ok = False
                else:
                    # Manifest-Kandidaten liegen in /data/ (root), ELFs
                    # seit der elf-libs/-Umstellung in /data/elf-libs/ -
                    # getrennte Listings/Cleanups. IMMER aufraeumen, auch
                    # wenn dieses Boot-Image gar keine Libs mehr braucht
                    # (required_libs leer, keep_names dann leer) - sonst
                    # bliebe ein Manifest/ELFs eines frueheren Programms
                    # stehen, die der Loader gegen das neue Boot-Image
                    # prueft und beim Start ablehnt (Sourcery-Finding,
                    # PR #288). Lose ELFs direkt in /data/ von AELTEREN
                    # Deploys (vor der elf-libs/-Umstellung) werden
                    # bewusst NICHT automatisch entfernt (Franz raeumt
                    # das einmalig per "Format File System" auf).
                    listing = http_listing(ip)
                    if listing is None:
                        print("  WARNUNG: Verzeichnis-Listing fehlgeschlagen - alte Manifest-Kandidaten NICHT geprueft/entfernt.")
                        node_ok = False
                    else:
                        for existing in _MANIFEST_HREF_RE.findall(listing):
                            if existing != manifest_name or not required_libs:
                                print(f"  Entferne alten Lib-Kandidaten: {existing}")
                                if not http_delete(ip, existing):
                                    print(f"  WARNUNG: Loeschen von {existing} fehlgeschlagen.")
                                    node_ok = False

                    keep_names = {p.name for p in result.elf_paths}
                    # Grundausstattung (make_4diac_training1_elf_preload.py)
                    # nie loeschen, auch wenn dieses Manifest sie nicht
                    # braucht - sonst laedt der naechste Uebungswechsel sie
                    # wieder komplett hoch. Alte Versionen derselben Lib
                    # fallen weiterhin raus (nur die aktuelle Datei bleibt).
                    # Ohne benoetigte Libs ist arch nicht bekannt (das Geraet
                    # wird dann nicht geprueft), daher die Namen fuer alle
                    # Architekturen - auf dem Geraet liegt ohnehin nur seine.
                    for lib in preload_libs_with_requires():
                        for elf_arch in SUPPORTED_ARCHS:
                            keep_names.add(f"{lib}-{LIB_VERSIONS[lib]}-{elf_arch}.elf")
                    elf_listing = http_listing(ip, "/elf-libs/", missing_ok=True)
                    if elf_listing is None:
                        print("  WARNUNG: elf-libs/-Listing fehlgeschlagen - alte ELF-Kandidaten NICHT geprueft/entfernt.")
                        node_ok = False
                    else:
                        for existing in _ELF_LIBS_HREF_RE.findall(elf_listing):
                            if existing not in keep_names:
                                print(f"  Entferne alten Lib-Kandidaten: elf-libs/{existing}")
                                if not http_delete(ip, f"elf-libs/{existing}"):
                                    print(f"  WARNUNG: Loeschen von elf-libs/{existing} fehlgeschlagen.")
                                    node_ok = False

                    if required_libs and node_ok:
                        elf_ok = True
                        for elf_path in result.elf_paths:
                            elf_name = elf_path.name
                            elf_remote_path = f"elf-libs/{elf_name}"
                            http_code = http_upload_file(
                                ip, elf_path, elf_remote_path, 60,
                                sha256_of(elf_path), remote_hashes, sha256_capable,
                            )
                            if http_code == "SKIP":
                                print(f"  {elf_path} -> {elf_remote_path}: unveraendert (Hash stimmt), Upload uebersprungen")
                            elif http_code == "VERIFY_FAILED":
                                print(f"  FEHLER: {elf_path} -> {elf_remote_path}: Upload mit HTTP 303 quittiert, Datei laut Geraet aber nicht/falsch gespeichert!")
                                elf_ok = False
                            else:
                                print(f"  Lade {elf_path} -> http://{ip}/upload/{elf_remote_path}")
                                if http_code == "303":
                                    print(f"  OK (HTTP {http_code})")
                                elif http_code == "RECOVERED":
                                    print("  OK (Antwort verloren, Datei laut Hash aber vollstaendig angekommen)")
                                else:
                                    print(f"  WARNUNG: ELF-Upload fehlgeschlagen (HTTP {http_code})")
                                    elf_ok = False

                        # Manifest bewusst ZULETZT hochladen: fehlt es,
                        # laedt die Firmware keine Lib - ein
                        # abgebrochener Upload ist so erkennbar.
                        if elf_ok and not http_reset_current_directory(ip):
                            print("  WARNUNG: Verzeichnis-Reset vor dem Manifest-Upload fehlgeschlagen - Manifest-Upload uebersprungen.")
                            node_ok = False
                        elif elf_ok:
                            print(f"  Lade {manifest_tmp} -> http://{ip}/upload/{manifest_name}")
                            http_code = http_upload_file(
                                ip, manifest_tmp, manifest_name, 30,
                                sha256_of(manifest_tmp), None, sha256_capable,
                            )
                            if http_code == "303":
                                print(f"  OK (HTTP {http_code})")
                            elif http_code == "RECOVERED":
                                print("  OK (Antwort verloren, Datei laut Hash aber vollstaendig angekommen)")
                            else:
                                reason = "Datei laut Geraet nicht/falsch gespeichert" if http_code == "VERIFY_FAILED" else f"HTTP {http_code}"
                                print(
                                    f"  WARNUNG: Manifest-Upload fehlgeschlagen ({reason}) - "
                                    "Libs auf dem Knoten sind damit unvollstaendig/inkonsistent.",
                                )
                                node_ok = False
                        else:
                            print("  WARNUNG: Mindestens ein ELF-Upload fehlgeschlagen - Manifest wird bewusst NICHT hochgeladen.")
                            node_ok = False

        if node_ok:
            reboot_needed.append(node)
        else:
            upload_failed.append(node)

    print("-" * 78)
    print(f"ZUSAMMENFASSUNG ({len(reboot_needed)}/{len(NODE_ORDER)} Knoten erfolgreich):")
    if len(reboot_needed) == len(NODE_ORDER):
        print(f"  ALLE {len(NODE_ORDER)} KNOTEN ERFOLGREICH HOCHGELADEN:")
        for ip in reboot_needed:
            print(f"  - {ip}: OK")
    else:
        for ip in NODE_ORDER:
            if ip in reboot_needed:
                print(f"  - {ip}: OK")
            elif ip in upload_failed:
                print(f"  - {ip}: FEHLER (Upload fehlgeschlagen, siehe Warnungen oben)")
            elif ip in unreachable:
                print(f"  - {ip}: NICHT ERREICHBAR (uebersprungen)")

    if upload_failed:
        print()
        print("ACHTUNG: Diese Knoten jetzt NICHT neu starten, sondern das Deploy einfach wiederholen:")
        for ip in upload_failed:
            print(f"  - {ip}")
        print(
            "  (Nach einem abgebrochenen Upload liegen dort neue und alte Dateien gemischt, z.B. ein neues\n"
            "   Bootfile mit dem alten Libs-Manifest - ein Neustart in diesem Zustand kann FORTE am Start hindern.\n"
            "   Bereits angekommene Dateien werden beim zweiten Lauf per Hash erkannt und uebersprungen.)",
        )

    if reboot_needed:
        print()
        print("Neue Dateien werden erst nach einem Neustart aktiv.")
        print('Manuell neu starten (z.B. "Reboot"-Button auf http://<ip>/):')
        for ip in reboot_needed:
            print(f"  - {ip}")

    return 0 if len(reboot_needed) == len(NODE_ORDER) else 1


if __name__ == "__main__":
    # Ohne stdout zeilengepuffert zu erzwingen, sammelt Python die Ausgabe
    # blockweise, sobald stdout kein echtes Terminal ist (z.B. External Tool
    # in der 4diac IDE, .bat-Aufruf) - die Fortschrittsmeldungen erscheinen
    # dann erst in grossen Schueben oder gar erst am Ende, obwohl der Upload
    # laengst laeuft (sieht aus wie Haengenbleiben, ist nur Pufferung).
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except (AttributeError, ValueError):
        pass

    # Keine "Enter druecken"-Pause am Ende: das Skript laeuft ueber die
    # Launches in der 4diac IDE, dort stoert die Abfrage (Franz, 2026-10-18).
    sys.exit(main())
