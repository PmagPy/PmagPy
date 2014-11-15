' -----------------------------------------------------------------------------
'
' Installation script for Lisa Tauxe's PmagPy Python Package
' Written by Rupert C. J. Minnett, Ph.D.
' Last updated 11/13/2014
'
' 11/13/2014 Change Log:
'
' - Fixed a bug that allowed the test to run even if No is pressed in the final message box.
' - The path is set in the registry instead of using the SETX command.
'
' -----------------------------------------------------------------------------

' Create objects needed in this script
Set Shell = WScript.CreateObject("WScript.Shell")
Set FileSystemObject = WScript.CreateObject("Scripting.FileSystemObject")
Set OSList = GetObject("winmgmts:").InstancesOf("Win32_OperatingSystem")

' Retrieve the user's "My Documents" path
' NOTE: unlike "%UserProfile%\Documents\", this will handle international
'       and older versions of Windows
my_documents_path = Shell.SpecialFolders("MyDocuments")

' Construct the default installation path
installation_path = FileSystemObject.BuildPath(my_documents_path, "PmagPy")

' Confirm that the default installation path should be used
installation_path = InputBox("Install PmagPy to the default directory (your 'My Documents' directory)? " & _ 
	                         vbNewLine & vbNewline & _ 
                             "If not, please edit the installation path below and press 'OK'.", _
                             "PmagPy Installation Directory", installation_path)
If Vartype(installation_path) = 0 Or installation_path = "" Then WScript.Quit

' As long as the requested installation path exists
overwrite = False
While FileSystemObject.FolderExists(installation_path) And Not overwrite

	' Confirm that the installation path should be overwritten
	new_installation_path = InputBox("The PmagPy installation directory below already exists. " & _
	                                 "Is it OK to overwrite this directory? " & _ 
	                                 vbNewLine & vbNewline & _ 
	                                 "If not, please edit the installation path below and press 'OK'.", _
	                                 "PmagPy Installation Directory Exists", installation_path)
	If Vartype(new_installation_path) = 0 Or new_installation_path = "" Then WScript.Quit

	' If the installation path wasn't changed, allow overwriting
	If new_installation_path = installation_path Then overwrite = True

	' Update the installation path
	installation_path = new_installation_path

WEnd

' The installation directory either didn't exist or has been deleted, so create a one
'FileSystemObject.CreateFolder(installation_path)

' Copy the current directory's contents into the installation directory
Shell.Run "xcopy.exe """ & Shell.CurrentDirectory & """ """ & installation_path & """ /R /Y", 0, True

' Remove the installation path from the PATH environment variable if it exists
Shell.Run "pathman /rs """ & installation_path & """", 0, True

' Add the installation path to the PATH environment variable
Shell.Run "pathman /as """ & installation_path & """", 0, True

' Make sure the current directory is not the PmagPy installation directory to that PmagPy can be tested properly
If Shell.SpecialFolders("Desktop") <> installation_path Then
	Shell.CurrentDirectory = Shell.SpecialFolders("Desktop")
ElseIf Shell.SpecialFolders("MyDocuments") <> installation_path Then 
	Shell.CurrentDirectory = Shell.SpecialFolders("MyDocuments")
End If

' Ask if a PmagPy test should be run
If MsgBox("PmagPy installed successfully in """ & installation_path & """!" & _ 
	      vbNewLine & vbNewline & _ 
          "Would you like to run a PmagPy test (equivalent to executing 'eqarea.py -h' on the command line)?", _
          vbYesNo, "PmagPy Installed Successfully") = vbYes Then Shell.Run "install_Windows_test.bat", 10, True
