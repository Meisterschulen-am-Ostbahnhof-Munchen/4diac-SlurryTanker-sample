::Script

@echo off & setlocal


del ..\FBs\Ventilsteuerung\DefaultPool.gcf
python GcfScript.py --oldfile ..\..\ISO-DesignerProjects\Workspace\DefaultPool\Output\DefaultPool.iop.h --newfolder FBs\Ventilsteuerung\ --newfile DefaultPool
