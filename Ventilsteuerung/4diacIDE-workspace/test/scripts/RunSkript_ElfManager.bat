::Script
:: Oeffnet die ELF-Verwaltung (scripts_central/elf_manager_gui.py): Liste
:: aller ELF-Libs mit Status auf dem Knoten, angehakte Libs samt requires
:: hochladen und ins Manifest eintragen. Danach Knoten neu starten.

@echo off & setlocal

cd /d "%~dp0"

echo === Starte ELF-Verwaltung (elf_manager_gui.py) ===
start "" pythonw ../../../scripts_central/elf_manager_gui.py %*
