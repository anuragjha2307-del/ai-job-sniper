Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "D:\ai job searcg"
WshShell.Run "pythonw.exe agent.py", 0, False
Set WshShell = Nothing

