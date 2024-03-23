



set PATH="C:\Espressif\python_env\idf5.0_py3.11_env\Scripts"

del ..\4diacIDE-workspace\test\FBs\SlurryTanker\DefaultPool.globalconsts

python PoolSkript.py --oldfile ..\ISO-DesignerProjects\Workspace\DefaultPool\Output\DefaultPool.iop.h --newfile ..\4diacIDE-workspace\test\FBs\SlurryTanker\DefaultPool


