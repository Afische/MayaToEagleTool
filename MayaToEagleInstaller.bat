@echo off
set "target=%~dp0runMayaToEagleTool.vbs"
set "icon=%~d0/Perforce/Tools/potterP3/mayaToEagleTool/eagleIcon.ico"
set "shortcut=%USERPROFILE%\Desktop\MayaToEagleTool.lnk"

echo Set oWS = WScript.CreateObject("WScript.Shell") > "%TEMP%\CreateShortcut.vbs"
echo Set oLink = oWS.CreateShortcut("%shortcut%") >> "%TEMP%\CreateShortcut.vbs"
echo oLink.TargetPath = "%target%" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.IconLocation = "%icon%" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.Save >> "%TEMP%\CreateShortcut.vbs"

cscript //nologo "%TEMP%\CreateShortcut.vbs"
del "%TEMP%\CreateShortcut.vbs"
