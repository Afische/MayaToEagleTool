Set objFSO = CreateObject("Scripting.FileSystemObject")
strScriptPath = objFSO.GetParentFolderName(WScript.ScriptFullName)
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run chr(34) & strScriptPath & "\runMayaToEagleTool.bat" & chr(34), 0
Set WshShell = Nothing
