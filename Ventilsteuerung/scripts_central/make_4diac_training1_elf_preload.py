#!/usr/bin/env python3
"""Macht einen Trainings-Knoten bereit fuer Uebungen per Online-Deploy aus
der 4diac IDE (ganz ohne Bootfile): spielt die ELF-Grundausstattung
(deploy_common.PRELOAD_LIBS + requires) nach /data/elf-libs/ und legt dazu
ein eigenes Manifest PRELOAD_MANIFEST_NAME OHNE "files"-Eintrag an (keine
Bindung an ein Bootfile - laut ELFMASTER akzeptiert elf_libs_loader.c das,
manifest_sha256 dann nur ueber libs[]). Alle anderen *.libs.json UND alle
*.fboot auf dem Knoten werden geloescht (Franz, 2026-10-18): der Loader nimmt
bei mehreren Manifesten das alphabetisch erste, und FORTE soll nach dem
Neustart leer mit geladener Grundausstattung starten.

Ein spaeteres normales make_4diac_training1_deploy.py (Bootfile-Betrieb)
ersetzt das Grundausstattungs-Manifest durch sein eigenes; die ELFs der
Grundausstattung bleiben dabei liegen und werden per Hash uebersprungen.

Aufruf:
    python make_4diac_training1_elf_preload.py            (DEFAULT_NODES: logibus.local per mDNS)
    python make_4diac_training1_elf_preload.py 192.168.178.45

Alte Versionen derselben Lib in elf-libs/ bleiben liegen (harmlos, das
Aufraeumen macht das naechste normale Deploy). Wirksam erst nach Neustart.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from deploy_common import preload_libs_with_requires
from elf_libs_manifest_lib import (
    LIB_VERSIONS,
    build_libs_manifest,
    is_internal_host,
    resolve_elf_path,
    resolve_host,
    resolve_node_arch,
    sha256_of,
)
from make_4diac_training1_deploy import (
    _FBOOT_HREF_RE,
    _MANIFEST_HREF_RE,
    http_delete,
    http_listing,
    http_reachable,
    http_reset_current_directory,
    http_remote_sha256_listing,
    http_upload_file,
    http_warmup,
)

# Nur fuer Firmware ohne GET /deviceinfo/: ohne bekannte Architektur
# (NODE_ARCH) fuer eine frei angegebene IP wird diese angenommen - das Board
# "Trainer" ist riscv32.
DEFAULT_ARCH = "riscv32"

PRELOAD_MANIFEST_NAME = "elf_grundausstattung.libs.json"

# Ohne Argument (Franz, 2026-11-04): Trainings-Platinen haengen per Link-Local
# (169.254.x.x, je Platine aus der MAC abgeleitet, also wechselnd) am PC und
# melden sich per mDNS als logibus.local - so passt der Default fuer jede
# Platine. Nur eine Platine gleichzeitig anschliessen (gleicher Hostname).
DEFAULT_NODES: list[str] = ["logibus.local"]


def preload_node(node: str, libs: list[str]) -> bool:
    # Name einmal aufloesen, danach nur noch die IP (siehe resolve_host)
    ip = resolve_host(node)
    if ip is None:
        print(f"Knoten {node}")
        print(f"WARNUNG: {node} nicht aufloesbar - uebersprungen.")
        return False
    print(f"Knoten {node}" if ip == node else f"Knoten {node} ({ip})")
    if not is_internal_host(ip):
        print(f"FEHLER: {ip} ist kein Knoten im internen Netz (erlaubt: 10.x, 172.16-31.x, 192.168.x, 169.254.x, *.local) - uebersprungen.")
        return False
    http_warmup(ip)
    if not http_reachable(ip):
        print(f"WARNUNG: {ip} nicht erreichbar - uebersprungen.")
        return False
    arch = resolve_node_arch(ip, DEFAULT_ARCH)
    if not arch:
        print(f"  FEHLER: {ip}: Architektur/FORTE_ABI passt nicht - nichts hochgeladen.")
        return False

    remote_hashes = http_remote_sha256_listing(ip)
    sha256_capable = remote_hashes is not None
    if remote_hashes is None:
        remote_hashes = {}

    ok = True
    for lib in libs:
        elf_path = resolve_elf_path(lib, LIB_VERSIONS[lib], arch)
        if elf_path is None:
            print(f"  WARNUNG: ELF fuer {lib}-{LIB_VERSIONS[lib]}-{arch} nicht gefunden.")
            ok = False
            continue
        remote_path = f"elf-libs/{elf_path.name}"
        http_code = http_upload_file(
            ip, elf_path, remote_path, 60,
            sha256_of(elf_path), remote_hashes, sha256_capable,
        )
        if http_code == "SKIP":
            print(f"  {remote_path}: unveraendert (Hash stimmt), uebersprungen")
        elif http_code == "303":
            print(f"  {remote_path}: OK (HTTP 303)")
        elif http_code == "RECOVERED":
            print(f"  {remote_path}: OK (Antwort verloren, Datei laut Hash aber vollstaendig angekommen)")
        elif http_code == "VERIFY_FAILED":
            print(f"  FEHLER: {remote_path}: mit HTTP 303 quittiert, Datei laut Geraet aber nicht/falsch gespeichert!")
            ok = False
        else:
            print(f"  WARNUNG: {remote_path}: Upload fehlgeschlagen (HTTP {http_code})")
            ok = False
    if not ok:
        print("  WARNUNG: Nicht alle ELFs angekommen - Manifest wird bewusst NICHT angelegt, Bootfile bleibt.")
        return False

    # Alte Manifeste und Bootfiles weg: mehrere *.libs.json -> der Loader
    # nimmt das alphabetisch erste; ein uebrig gebliebenes Bootfile wuerde
    # FORTE beim Neustart wieder laden statt leer zu starten.
    listing = http_listing(ip)
    if listing is None:
        print("  WARNUNG: Verzeichnis-Listing fehlgeschlagen - alte Manifeste/Bootfiles NICHT entfernt, Manifest nicht angelegt.")
        return False
    old = [n for n in _MANIFEST_HREF_RE.findall(listing) if n != PRELOAD_MANIFEST_NAME]
    old += _FBOOT_HREF_RE.findall(listing)
    for name in old:
        print(f"  Entferne: {name}")
        if not http_delete(ip, name):
            print(f"  WARNUNG: Loeschen von {name} fehlgeschlagen.")
            ok = False
    if not ok:
        return False

    with tempfile.TemporaryDirectory() as tmp_dir:
        manifest_tmp = Path(tmp_dir) / PRELOAD_MANIFEST_NAME
        result = build_libs_manifest(arch, [], manifest_tmp, libs)
        if not result.ok:
            print("  WARNUNG: Grundausstattungs-Manifest konnte nicht gebaut werden.")
            return False
        if not http_reset_current_directory(ip):
            print("  WARNUNG: Verzeichnis-Reset vor dem Manifest-Upload fehlgeschlagen - Manifest nicht angelegt.")
            return False
        http_code = http_upload_file(
            ip, manifest_tmp, PRELOAD_MANIFEST_NAME, 30,
            sha256_of(manifest_tmp), None, sha256_capable,
        )
    if http_code in ("303", "RECOVERED"):
        print(f"  {PRELOAD_MANIFEST_NAME}: OK (ohne Bootfile-Bindung, {len(libs)} Libs)")
        return True
    print(f"  WARNUNG: {PRELOAD_MANIFEST_NAME}: Upload fehlgeschlagen ({http_code}) - Knoten hat jetzt KEIN Manifest, Skript wiederholen.")
    return False


def main(argv: list[str]) -> int:
    ips = argv or DEFAULT_NODES
    libs = preload_libs_with_requires()
    print(f"Grundausstattung ({len(libs)} Libs): {' '.join(libs)}")

    failed: list[str] = []
    for ip in ips:
        print("-" * 78)
        if not preload_node(ip, libs):
            failed.append(ip)

    print("-" * 78)
    print(f"ZUSAMMENFASSUNG ({len(ips) - len(failed)}/{len(ips)} Knoten erfolgreich):")
    for ip in ips:
        print(f"  - {ip}: {'FEHLER (siehe oben)' if ip in failed else 'OK'}")
    if failed:
        print("Fehlgeschlagene Knoten einfach erneut aufrufen - vorhandene ELFs werden per Hash uebersprungen.")
    ok_ips = [ip for ip in ips if ip not in failed]
    if ok_ips:
        print("Jetzt neu starten (Reboot-Button auf http://<ip>/) - FORTE startet dann ohne Bootfile")
        print("mit geladener Grundausstattung, Uebungen per Online-Deploy aus der 4diac IDE:")
        for ip in ok_ips:
            print(f"  - {ip}")
    return 1 if failed else 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except (AttributeError, ValueError):
        pass
    sys.exit(main(sys.argv[1:]))
