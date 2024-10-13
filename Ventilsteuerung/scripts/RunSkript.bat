::Script

@echo off & setlocal


set PATH="C:\Espressif\python_env\idf5.2_py3.11_env\Scripts"

del ..\4diacIDE-workspace\test\FBs\Ventilsteuerung\Workspace\DefaultPool.gcf
python GcfScript.py --oldfile ISO-DesignerProjects\Workspace\DefaultPool\Output\DefaultPool.iop.h --newfolder 4diacIDE-workspace\test\FBs\Ventilsteuerung\Workspace\ --newfile DefaultPool

del ..\4diacIDE-workspace\test\FBs\Ventilsteuerung\Workspace_TECU\DefaultPool_TECU.gcf
python GcfScript.py --oldfile ISO-DesignerProjects\Workspace_TECU\DefaultPool\Output\DefaultPool.iop.h --newfolder 4diacIDE-workspace\test\FBs\Ventilsteuerung\Workspace_TECU\ --newfile DefaultPool_TECU

del ..\4diacIDE-workspace\test\FBs\Ventilsteuerung\Workspace_PWM\DefaultPool_PWM.gcf
python GcfScript.py --oldfile ISO-DesignerProjects\Workspace_PWM\DefaultPool\Output\DefaultPool.iop.h --newfolder 4diacIDE-workspace\test\FBs\Ventilsteuerung\Workspace_PWM\ --newfile DefaultPool_PWM