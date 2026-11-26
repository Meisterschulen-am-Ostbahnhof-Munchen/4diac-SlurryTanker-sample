::Script
:: Macht die Trainings-Knoten bereit fuer Online-Deploy aus der IDE: ELF-
:: Grundausstattung (deploy_common.PRELOAD_LIBS) + eigenes Manifest ohne
:: Bootfile, loescht vorhandene Bootfiles/Manifeste - siehe
:: scripts_central/make_4diac_training1_elf_preload.py. Danach neu starten.

@echo off & setlocal

cd /d "%~dp0"

echo === Spiele ELF-Grundausstattung auf Trainings-Knoten auf (make_4diac_training1_elf_preload.py) ===
python ../../../scripts_central/make_4diac_training1_elf_preload.py %* < NUL
if errorlevel 1 exit /b 1
