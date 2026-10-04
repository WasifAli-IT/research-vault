; Inno Setup script for Research Vault
; This script builds a Setup.exe that installs the PyInstaller-built
; app (from dist\ResearchVault) to a user-chosen location, creates
; Start Menu shortcuts, and provides an uninstaller.

#define MyAppName "Research Vault"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "Research Vault"
#define MyAppExeName "ResearchVault.exe"

[Setup]
AppId={{8F1E2B3A-5C4D-4E6F-9A1B-2C3D4E5F6A7B}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=installer_output
OutputBaseFilename=ResearchVault-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
; Allow the user to change the install location (this is the default
; behavior, but stated explicitly here for clarity):
AllowNoIcons=yes
PrivilegesRequired=lowest

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "dist\ResearchVault\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent