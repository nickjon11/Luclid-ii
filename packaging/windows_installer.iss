; One-time Windows installer for the GitHub Actions-built native application.
; The version is injected by ISCC /DAppVersion=... from VERSION.
#ifndef AppVersion
  #error AppVersion must be supplied by the release build
#endif
#define AppName "Luclid-ii"
[Setup]
AppId={{6DB3C623-395A-4B0D-B837-AE25A19DE892}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} v{#AppVersion}
DefaultDirName={localappdata}\Programs\Luclid-ii
DefaultGroupName=Luclid-ii
OutputDir=..\release-installers
OutputBaseFilename=Luclid-ii-Setup-v{#AppVersion}-Windows
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
WizardStyle=modern
UninstallDisplayIcon={app}\Luclid-ii.exe
DisableProgramGroupPage=yes
ArchitecturesAllowed=x64compatible
[Files]
Source: "..\dist\Luclid-ii\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{autoprograms}\Luclid-ii"; Filename: "{app}\Luclid-ii.exe"
Name: "{autodesktop}\Luclid-ii"; Filename: "{app}\Luclid-ii.exe"; Tasks: desktopicon
[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: checkedonce
[Run]
Filename: "{app}\Luclid-ii.exe"; Description: "Launch Luclid-ii"; Flags: nowait postinstall skipifsilent unchecked
