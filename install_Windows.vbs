' -----------------------------------------------------------------------------
' Installation script for Lisa Tauxe's PmagPy Python Package
' Written by Rupert C. J. Minnett, Ph.D.
' Last updated 8/31/2012
' -----------------------------------------------------------------------------

' Create objects needed in this script
set Shell = WScript.CreateObject("WScript.Shell")
set FileSystemObject = WScript.CreateObject("Scripting.FileSystemObject")


' Retrieve the user's "My Documents" path
' NOTE: unlike "%UserProfile%\Documents\", this will handle international
'       and older versions of Windows
my_documents_path = Shell.SpecialFolders("MyDocuments")

' Construct the installation path
installation_path = FileSystemObject.BuildPath(my_documents_path, "PmagPy")

' Confirm that the default installation path should be used
installation_path = InputBox("Install PmagPy to the default directory (your 'My Documents' directory)? " & _ 
	                         vbNewLine & vbNewline & _ 
                             "If not, please edit the installation path below and press 'OK'.", _
                             "PmagPy Installation Directory", installation_path)
if Vartype(installation_path) = 0 OR installation_path = "" then WScript.Quit

' As long as the requested installation path exists
while FileSystemObject.FolderExists(installation_path)

	' Confirm that the installation path should be overwritten
	new_installation_path = InputBox("The PmagPy installation directory below already exists. " & _
	                                 "Is it OK to overwrite this directory? " & _ 
	                                 vbNewLine & vbNewline & _ 
	                                 "If not, please edit the installation path below and press 'OK'.", _
	                                 "PmagPy Installation Directory Exists", installation_path)
	if Vartype(new_installation_path) = 0 OR new_installation_path = "" then WScript.Quit

	' If the installation path wasn't changed, delete the existing directory
	if new_installation_path = installation_path then FileSystemObject.DeleteFolder(installation_path)

	' Update the installation path
	installation_path = new_installation_path

wend

' The installation directory either didn't exist or has been deleted, so create a one
FileSystemObject.CreateFolder(installation_path)

' Copy the current directory's contents into the installation directory
FileSystemObject.CopyFolder Shell.CurrentDirectory, installation_path
Shell.CurrentDirectory = installation_path

' Permanently append the installation path to the user's PATH environment variable
Shell.Run "SETX PATH %PATH%;" & installation_path, 0, true

' Ask if a PmagPy test should be run
if MsgBox("PmagPy installed successfully!" & _ 
	      vbNewLine & vbNewline & _ 
          "Would you like to run a PmagPy test (equivalent to executing 'eqarea.py -h' on the command line)?", _
          vbYesNo, "PmagPy Installed Successfully") then Shell.Run "install_Windows_test.bat", 10, true

