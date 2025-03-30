@echo off
assoc .ps=PlusScriptFile
ftype PlusScriptFile="C:\Path\To\plusscript_term.exe" "%1"
reg add "HKEY_CLASSES_ROOT\PlusScriptFile\DefaultIcon" /ve /d "C:\Path\To\plusscript.ico" /f
echo Done!
pause