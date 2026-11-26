#!/usr/bin/env python3
"""ELF-Verwaltung mit Oberflaeche: zeigt alle ELF-Libs dieses Repos, welche
davon auf dem Knoten liegen und welche das aktive Manifest laedt. Angehakte
Libs (plus ihre requires laut MANIFEST.MF) werden hochgeladen und als
elf_grundausstattung.libs.json eingetragen - wie
make_4diac_training1_elf_preload.py, nur mit frei waehlbarer Lib-Liste.

Wichtig: Der Loader laedt nur Libs, die im Manifest stehen. Eine ELF, die nur
in elf-libs/ liegt, ist fuer FORTE nicht da.

Wie beim Preload werden andere *.libs.json und alle *.fboot auf dem Knoten
geloescht. Wirksam nach dem Neustart des Knotens.

Aufruf:
    python elf_manager_gui.py                 (logibus.local)
    python elf_manager_gui.py 192.168.178.45
"""

from __future__ import annotations

import contextlib
import json
import queue
import re
import sys
import threading
import tkinter as tk
import webbrowser
from tkinter import messagebox, ttk

from deploy_common import PRELOAD_EXCLUDE, preload_libs_with_requires
from elf_libs_manifest_lib import (
    LIB_VERSIONS,
    MAX_LIBS,
    is_internal_host,
    lib_requires_of,
    query_device_info,
    resolve_elf_path,
    resolve_host,
    resolve_node_arch,
    sha256_of,
)
from make_4diac_training1_deploy import (
    _MANIFEST_HREF_RE,
    _http,
    http_listing,
    http_reachable,
    http_remote_sha256_listing,
    http_warmup,
)
from make_4diac_training1_elf_preload import DEFAULT_ARCH, DEFAULT_NODES, preload_node

ON, OFF = "☑", "☐"


def with_requires(libs: list[str]) -> list[str]:
    """Auswahl plus transitive requires (ohne PRELOAD_EXCLUDE - was der Nutzer
    anhakt, bekommt auch seine Abhaengigkeiten)."""
    result: list[str] = []
    todo = list(libs)
    while todo:
        lib = todo.pop(0)
        if lib not in result:
            result.append(lib)
            todo.extend(name for name, _range in lib_requires_of(lib))
    return result


def _connect(host: str) -> tuple[str, str]:
    """Host aufloesen und pruefen; liefert (IP, Architektur)."""
    ip = resolve_host(host)
    if ip is None:
        raise RuntimeError(f"{host} nicht aufloesbar")
    if not is_internal_host(ip):
        raise RuntimeError(f"{ip} ist kein Knoten im internen Netz")
    http_warmup(ip)
    if not http_reachable(ip):
        raise RuntimeError(f"{ip} nicht erreichbar")
    arch = resolve_node_arch(ip, DEFAULT_ARCH)
    if not arch:
        raise RuntimeError(f"{ip}: Architektur/FORTE_ABI passt nicht (Firmware zu alt oder zu neu?)")
    return ip, arch


def _lib_status(lib: str, ver: str, arch: str, hashes: dict) -> str:
    """Stand einer Lib am Knoten gegen die ELF im Repo."""
    local = resolve_elf_path(lib, ver, arch)
    if local is None:
        return "keine ELF im Repo"
    remote = hashes.get(f"elf-libs/{local.name}")
    if remote == sha256_of(local):
        return "aktuell"
    if remote:
        return "anderer Stand"
    other = re.compile(rf"elf-libs/{re.escape(lib)}-\d+\.\d+\.\d+-{arch}\.elf$")
    return "alte Version" if any(other.match(k) for k in hashes) else "fehlt"


def _active_manifest(ip: str) -> tuple[str, set[str]]:
    """Aktives Manifest (alphabetisch erstes) und die darin geladenen Libs."""
    names = sorted(_MANIFEST_HREF_RE.findall(http_listing(ip) or ""))
    if not names:
        return "", set()
    manifest = names[0]   # der Loader nimmt das alphabetisch erste
    try:
        code, body = _http(ip, "GET", "/" + manifest, 10)
        if code == 200:
            return manifest, {e.get("name", "") for e in json.loads(body).get("libs", [])}
    except (OSError, ValueError):
        pass
    return manifest, set()


_SPACE_RE = re.compile(r"([\d.]+)\s*kB\s+of\s+([\d.]+)\s*kB\s+used")


def read_space(ip: str) -> tuple[tuple[int, int] | None, tuple[int, int] | None]:
    """Belegung von /data (LittleFS) und PSRAM, je (belegt, gesamt) in Bytes.
    GET /space/?json (Firmware nach b-214, PSRAM nur mit psram_*), sonst die
    erste HTML-Zeile "X kB of Y kB used" (ab b-214). Was fehlt, ist None.
    Dauert ~1 s (laeuft das Dateisystem ab), daher nicht pollen."""
    try:
        code, body = _http(ip, "GET", "/space/?json", 8)
    except OSError:
        return None, None
    if code != 200:
        return None, None
    text = body.decode("utf-8", errors="replace")
    with contextlib.suppress(ValueError, TypeError, KeyError, AttributeError):
        d = json.loads(text)
        space = (int(d["used"]), int(d["total"]))
        psram = None
        if d.get("psram_size") and "psram_free" in d:
            psram = (int(d["psram_size"]) - int(d["psram_free"]), int(d["psram_size"]))
        return space, psram
    m = _SPACE_RE.search(text)   # ankert auf "used", nicht die PSRAM-Zeile
    if m:
        return (round(float(m.group(1)) * 1024), round(float(m.group(2)) * 1024)), None
    return None, None


def read_psram(ip: str) -> tuple[int, int] | None:
    """PSRAM als (belegt, gesamt) in Bytes aus /deviceinfo/ (Ersatz, wenn
    /space/?json kein psram_* liefert). Dort laufen die ELFs; belegt zaehlt
    aber auch FORTE und Puffer mit."""
    state, info = query_device_info(ip)
    ps = (info or {}).get("psram") or {}
    if state != "ok" or not ps.get("size") or "free" not in ps:
        return None
    return ps["size"] - ps["free"], ps["size"]


def read_node(host: str) -> dict:
    """Knoten abfragen: IP, Architektur, Status je Lib, Libs im aktiven
    Manifest, Belegung von /data und PSRAM."""
    ip, arch = _connect(host)
    hashes = http_remote_sha256_listing(ip) or {}
    status = {lib: _lib_status(lib, ver, arch, hashes) for lib, ver in LIB_VERSIONS.items()}
    manifest, active = _active_manifest(ip)
    space, psram = read_space(ip)
    return {"ip": ip, "arch": arch, "status": status, "active": active, "manifest": manifest,
            "space": space, "psram": psram or read_psram(ip)}


class QueueWriter:
    def __init__(self, q: queue.Queue):
        self.q = q

    def write(self, s: str) -> int:
        self.q.put(s)
        return len(s)

    def flush(self) -> None:
        # nichts zu tun: jede Ausgabe geht sofort in die Queue
        pass


class App:
    def __init__(self, root: tk.Tk, host: str):
        self.root = root
        self.q: queue.Queue = queue.Queue()
        self.checked: set[str] = set()
        self.node: dict | None = None
        root.title("logiBUS ELF-Verwaltung")
        root.geometry("960x660")

        top = ttk.Frame(root, padding=6)
        top.pack(fill="x")
        ttk.Label(top, text="Knoten:").pack(side="left")
        self.host = tk.StringVar(value=host)
        ttk.Entry(top, textvariable=self.host, width=24).pack(side="left", padx=4)
        self.btn_read = ttk.Button(top, text="Verbinden / Aktualisieren", command=self.connect)
        self.btn_read.pack(side="left")
        ttk.Button(top, text="Weboberfläche", command=self.open_web).pack(side="left", padx=4)
        self.info = tk.StringVar(value="Noch nicht verbunden")
        ttk.Label(root, textvariable=self.info, padding=(6, 0)).pack(fill="x")

        meters = ttk.Frame(root, padding=(6, 4))
        meters.pack(fill="x")
        meters.columnconfigure(1, weight=1)
        self.meters = {}
        for row, (key, title) in enumerate((("space", "Speicher (/data)"), ("psram", "RAM (PSRAM)"))):
            ttk.Label(meters, text=title, width=16).grid(row=row, column=0, sticky="w")
            pb = ttk.Progressbar(meters, maximum=100)
            pb.grid(row=row, column=1, sticky="ew", padx=4, pady=1)
            txt = tk.StringVar(value="–")
            ttk.Label(meters, textvariable=txt, width=34).grid(row=row, column=2, sticky="w")
            self.meters[key] = (pb, txt)

        cols = ("sel", "lib", "ver", "size", "pct", "node", "loaded")
        self.tree = ttk.Treeview(root, columns=cols, show="headings", height=18)
        self.titles = {}
        self.sort_col, self.sort_rev = "lib", False
        for c, t, w, a in (("sel", "", 30, "w"), ("lib", "Lib", 250, "w"), ("ver", "Version", 70, "w"),
                           ("size", "Größe", 80, "e"), ("pct", "% /data", 70, "e"),
                           ("node", "Auf dem Knoten", 140, "w"), ("loaded", "Wird geladen", 100, "w")):
            self.titles[c] = t
            self.tree.heading(c, text=t, command=lambda c=c: self.sort_by(c))
            self.tree.column(c, width=w, anchor=a)
        self.tree.tag_configure("missing", foreground="#b00000")
        self.tree.pack(fill="both", expand=True, padx=6)
        self.tree.bind("<Button-1>", self.toggle)
        self.tree.bind("<space>", self.toggle)

        bar = ttk.Frame(root, padding=6)
        bar.pack(fill="x")
        ttk.Button(bar, text="Nur Grundausstattung", command=self.select_base).pack(side="left")
        ttk.Button(bar, text="Aktuelles Manifest", command=self.select_active).pack(side="left", padx=4)
        self.btn_go = ttk.Button(bar, text="Angehakte installieren", command=self.install)
        self.btn_go.pack(side="right")
        self.count = tk.StringVar()
        ttk.Label(bar, textvariable=self.count).pack(side="right", padx=8)

        self.log = tk.Text(root, height=10, wrap="word")
        self.log.pack(fill="both", padx=6, pady=(0, 6))
        self.fill()
        root.after(100, self.pump)

    # --- Anzeige -------------------------------------------------------------
    def elf_size(self, lib: str) -> int | None:
        """Groesse der ELF im Repo (Architektur des Knotens, sonst Standard)."""
        arch = self.node["arch"] if self.node else DEFAULT_ARCH
        path = resolve_elf_path(lib, LIB_VERSIONS[lib], arch)
        return path.stat().st_size if path else None

    def data_total(self) -> int | None:
        space = self.node.get("space") if self.node else None
        return space[1] if space else None

    def sort_key(self, lib: str):
        col = self.sort_col
        if col == "sel":
            return (lib not in self.checked, lib.lower())
        if col in ("size", "pct"):
            return (self.elf_size(lib) or -1, lib.lower())
        if col == "ver":
            return (tuple(int(x) for x in LIB_VERSIONS[lib].split(".") if x.isdigit()), lib.lower())
        if col == "node":
            return (self.node["status"].get(lib, "") if self.node else "", lib.lower())
        if col == "loaded":
            return (lib not in (self.node["active"] if self.node else set()), lib.lower())
        return lib.lower()

    def sort_by(self, col: str) -> None:
        self.sort_rev = not self.sort_rev if col == self.sort_col else False
        self.sort_col = col
        self.fill()

    def fill(self) -> None:
        self.tree.delete(*self.tree.get_children())
        for c, t in self.titles.items():
            arrow = (" ▼" if self.sort_rev else " ▲") if c == self.sort_col else ""
            self.tree.heading(c, text=t + arrow)
        st = self.node["status"] if self.node else {}
        active = self.node["active"] if self.node else set()
        total = self.data_total()
        for lib in sorted(LIB_VERSIONS, key=self.sort_key, reverse=self.sort_rev):
            node = st.get(lib, "?")
            name = lib + ("  (CAN2, nicht am Trainer)" if lib in PRELOAD_EXCLUDE else "")
            size = self.elf_size(lib)
            self.tree.insert("", "end", iid=lib, tags=("missing",) if node in ("fehlt", "alte Version", "anderer Stand") else (),
                             values=(ON if lib in self.checked else OFF, name, LIB_VERSIONS[lib],
                                     f"{size / 1024:.1f} kB" if size else "",
                                     f"{100 * size / total:.1f} %" if size and total else "",
                                     node, "ja" if lib in active else ""))
        self.update_count()

    def show_meters(self) -> None:
        for key, (pb, txt) in self.meters.items():
            val = self.node.get(key) if self.node else None
            if not val:
                pb["value"] = 0
                txt.set("keine Angabe (Firmware zu alt?)" if self.node else "–")
                continue
            used, total = val
            pb["value"] = 100 * used / total
            txt.set(f"{(total - used) / 1048576:.1f} MiB frei von {total / 1048576:.1f} MiB"
                    f" ({100 * (total - used) / total:.0f} %)")

    def update_count(self) -> None:
        full = with_requires(sorted(self.checked))
        extra = len(full) - len(self.checked)
        size = sum(s for s in (self.elf_size(lib) for lib in full if lib in LIB_VERSIONS) if s)
        total = self.data_total()
        self.count.set(f"{len(self.checked)} angehakt" + (f" + {extra} Abhängigkeiten" if extra else "")
                       + f" (max. {MAX_LIBS}), {size / 1024:.0f} kB"
                       + (f" = {100 * size / total:.0f} % von /data" if total else ""))

    def toggle(self, event) -> None:
        if event.type == tk.EventType.ButtonPress and self.tree.identify_region(event.x, event.y) != "cell":
            return
        lib = self.tree.identify_row(event.y) if event.type == tk.EventType.ButtonPress else self.tree.focus()
        if not lib:
            return
        self.checked.symmetric_difference_update({lib})
        self.tree.set(lib, "sel", ON if lib in self.checked else OFF)
        self.update_count()

    def select_base(self) -> None:
        self.checked = set(preload_libs_with_requires())
        self.fill()

    def select_active(self) -> None:
        self.checked = set(self.node["active"]) if self.node and self.node["active"] else set(preload_libs_with_requires())
        self.fill()

    def say(self, s: str) -> None:
        self.log.insert("end", s)
        self.log.see("end")

    def pump(self) -> None:
        while not self.q.empty():
            item = self.q.get()
            if callable(item):
                item()
            else:
                self.say(item)
        self.root.after(100, self.pump)

    def busy(self, on: bool) -> None:
        for b in (self.btn_read, self.btn_go):
            b.state(["disabled"] if on else ["!disabled"])

    def run(self, job, done) -> None:
        self.busy(True)

        def work():
            res, err = None, None
            with contextlib.redirect_stdout(QueueWriter(self.q)):
                try:
                    res = job()
                except Exception as e:  # noqa: BLE001 - jede Meldung in die Oberflaeche
                    err = e
            self.q.put(lambda: (self.busy(False), done(res, err)))
        threading.Thread(target=work, daemon=True).start()

    # --- Aktionen ------------------------------------------------------------
    def connect(self) -> None:
        host = self.host.get().strip()
        self.say(f"Verbinde mit {host} ...\n")

        def done(res, err):
            if err:
                self.info.set(f"Fehler: {err}")
                self.say(f"FEHLER: {err}\n")
                return
            self.node = res
            self.info.set(f"{host} ({res['ip']}), {res['arch']}, aktives Manifest: {res['manifest'] or 'keins'}"
                          f" mit {len(res['active'])} Libs")
            self.select_active()
            self.show_meters()
            self.say("Verbunden.\n")
        self.run(lambda: read_node(host), done)

    def install(self) -> None:
        if not self.checked:
            messagebox.showinfo("ELF-Verwaltung", "Nichts angehakt.")
            return
        full = with_requires(sorted(self.checked))
        if len(full) > MAX_LIBS:
            messagebox.showerror("ELF-Verwaltung", f"{len(full)} Libs, die Firmware lädt höchstens {MAX_LIBS}.")
            return
        extra = [lib for lib in full if lib not in self.checked]
        text = (f"{len(full)} Libs hochladen und ins Manifest eintragen?\n\n"
                + (f"Dazu kommen die Abhängigkeiten: {', '.join(extra)}\n\n" if extra else "")
                + "Andere Manifeste und alle Bootfiles (*.fboot) auf dem Knoten werden gelöscht.\n"
                  "Wirksam nach dem Neustart des Knotens.")
        if not messagebox.askyesno("ELF-Verwaltung", text):
            return
        host = self.host.get().strip()

        def done(ok, err):
            if err or not ok:
                self.say(f"\nFEHLER: {err or 'siehe Meldungen oben'}\n")
                messagebox.showerror("ELF-Verwaltung", "Nicht alles hat geklappt, siehe Meldungen.")
                return
            self.say("\nFertig. Jetzt den Knoten neu starten (Weboberfläche, Reboot).\n")
            messagebox.showinfo("ELF-Verwaltung", "Fertig. Jetzt den Knoten neu starten (Weboberfläche, Reboot).")
            self.connect()
        self.run(lambda: preload_node(host, full), done)

    def open_web(self) -> None:
        webbrowser.open(f"http://{self.host.get().strip()}/")


def main(argv: list[str]) -> int:
    root = tk.Tk()
    App(root, argv[0] if argv else DEFAULT_NODES[0])
    root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
