' -----------------------------------------------------------------------------
'
' Installation script for Lisa Tauxe's PmagPy Python Package
' Written by Rupert C. J. Minnett, Ph.D.
' Last updated 11/21/2014
'
' 11/13/2014 Change Log:
'
' - Fixed a bug that allowed the test to run even if No is pressed in the final message box.
' - The path is set in the registry instead of using the SETX command.
' - The script now automatically re-executes with elevated permissions if necessary.
' - If the second command line argument is "elevated", then the script doesn't attempt to re-execute with elevated permissions.
'
' -----------------------------------------------------------------------------

' Create objects needed in this script
Set Shell = WScript.CreateObject("WScript.Shell")
Set FileSystemObject = WScript.CreateObject("Scripting.FileSystemObject")

' Retrieve the user's "My Documents" path
' NOTE: unlike "%UserProfile%\Documents\", this will handle international
'       and older versions of Windows
my_documents_path = Shell.SpecialFolders("MyDocuments")

' Construct the default installation path
installation_path = my_documents_path & "\PmagPy"

' Confirm that the default installation path should be used
installation_path_prompted = False
While Not installation_path_prompted And Vartype(installation_path) = 0 Or installation_path = ""

	installation_path_prompted = True
	installation_path = InputBox("Install PmagPy to the default directory (your 'My Documents' directory)? " & _ 
	                             vbNewLine & vbNewline & _ 
	                             "If not, please edit the installation path below and press 'OK'.", _
	                             "PmagPy Installation Directory", installation_path)

	'Warn that the installation path is invalid
	If Vartype(installation_path) = 0 Or installation_path = "" Then 
		x = MsgBox("The installation path is invalid. Please restart the the PmagPy installation.", 16, "Invalid Installation Path")
	End If

WEnd

' As long as the requested installation path exists
overwrite = False
While FileSystemObject.FolderExists(installation_path) And Not overwrite

	' Confirm that the installation path should be overwritten
	new_installation_path = InputBox("The PmagPy installation directory below already exists. " & _
	                                 "Is it OK to overwrite this directory? " & _ 
	                                 vbNewLine & vbNewline & _ 
	                                 "If not, please edit the installation path below and press 'OK'.", _
	                                 "PmagPy Installation Directory Exists", installation_path)

	' If the installation path wasn't changed, allow overwriting
	If new_installation_path = installation_path Then overwrite = True

	' Update the installation path
	If Not Vartype(new_installation_path) = 0 And new_installation_path <> "" Then installation_path = new_installation_path

WEnd


' Copy the current directory's contents into the installation directory
Shell.Run "xcopy.exe /K /Y /C /E /H /R """ & Shell.CurrentDirectory & """ """ & installation_path & """", 0, True

' 
Set file = FileSystemObject.CreateTextFile(installation_path & "\pmagpy_prompt.bat", True)
file.WriteLine("@ECHO OFF")
file.WriteLine("SET ""PATH=" & installation_path & ";%PATH%""")
file.WriteLine("ECHO -------------------------------------------------------------------------------")
file.WriteLine("ECHO ^|                                                                             ^|")
file.WriteLine("ECHO ^| Welcome to the PmagPy Command Prompt for Windows!                           ^|")
file.WriteLine("ECHO ^|                                                                             ^|")
file.WriteLine("ECHO ^| To test your installation, type ""eqarea.py -h"" at the prompt below and      ^|")
file.WriteLine("ECHO ^| you should see the PmagPy Equal Area routine help information.              ^|")
file.WriteLine("ECHO ^|                                                                             ^|")
file.WriteLine("ECHO ^| For more information, refer to the PmagPy Cookbook:                         ^|")
file.WriteLine("ECHO ^| http://earthref.org/PmagPy/cookbook/                                        ^|")
file.WriteLine("ECHO ^|                                                                             ^|")
file.WriteLine("ECHO -------------------------------------------------------------------------------")
file.Close

Set lnk = Shell.CreateShortcut(installation_path & "\PmagPy Prompt.LNK")
lnk.TargetPath = "%comspec%"
lnk.Arguments = " /k """ & installation_path & "\pmagpy_prompt.bat"""
lnk.IconLocation = installation_path & "\images\PmagPy.ICO, 0"
lnk.WorkingDirectory = my_documents_path
lnk.Save

If MsgBox("PmagPy installed successfully in """ & installation_path & """!" & _ 
	      vbNewLine & vbNewline & _ 
          "Would you like to make a shortcut to the PmagPy Command Prompt on the desktop?", _
          vbYesNo, "PmagPy Installed Successfully") = vbYes Then
	FileSystemObject.CopyFile installation_path & "\PmagPy Prompt.LNK", Shell.SpecialFolders("Desktop") & "\PmagPy Prompt.LNK", True
End If

' Ask if a PmagPy test should be run
'If MsgBox("PmagPy installed successfully in """ & installation_path & """!" & _ 
'	      vbNewLine & vbNewline & _ 
'          "Would you like to run a PmagPy test (equivalent to executing 'eqarea.py -h' on the command line)?", _
'          vbYesNo, "PmagPy Installed Successfully") = vbYes Then Shell.Run installation_path & "\install_Windows_test.bat", 10, True