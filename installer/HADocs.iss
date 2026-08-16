; Inno Setup script for HADocs. The installer wraps the canonical portable
; staging payload and adds only the installed-runtime marker.

#define MyAppName "HADocs"
#define MyAppVersion "0.17.0-rc5"
#define MyAppPublisher "SirBlondieDK"
#define MyAppURL "https://github.com/SirBlondieDK/HADocs"
#define MyAppExeName "HADocs.exe"

#ifndef MyPayloadDir
  #define MyPayloadDir "..\dist\windows\staging\HADocs"
#endif
#ifndef MyOutputDir
  #define MyOutputDir "..\dist\windows\installer"
#endif
#ifndef MyOutputBaseFilename
  #define MyOutputBaseFilename "HADocs_Setup_v0.17.0-rc5"
#endif

[Setup]
AppId={{E9F1CB32-9E0A-4A72-9F5A-HADOCS0160}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=..\LICENSE
OutputDir={#MyOutputDir}
OutputBaseFilename={#MyOutputBaseFilename}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
; Per-user runtime data is intentionally outside installer ownership. App code
; resolves LOCALAPPDATA for the user who actually launches HADocs.
UsedUserAreasWarning=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

[Dirs]
Name: "{localappdata}\HADocs"

[Files]
Source: "{#MyPayloadDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "installed-runtime.marker"; DestDir: "{app}"; DestName: ".hadocs-installed"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{localappdata}\HADocs"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{localappdata}\HADocs"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{localappdata}\HADocs"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
