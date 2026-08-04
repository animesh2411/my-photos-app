; PhotoBridge Inno Setup Script
; Produces PhotoBridgeSetup.exe — a one-click Windows installer.
;
; Build with:  iscc installer\PhotoBridge.iss
; Requires:    Inno Setup 6+ (https://jrsoftware.org/isinfo.php)

#define MyAppName "PhotoBridge"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "PhotoBridge"
#define MyAppURL "https://github.com/animesh2411/my-photos-app"
#define MyAppExeName "PhotoBridge.exe"

[Setup]
AppId={{B7F4E3D2-8A1C-4F5E-9D6B-3C2A1E0F8D7A}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
; Output installer to dist/ folder
OutputDir=..\dist
OutputBaseFilename=PhotoBridgeSetup
SetupIconFile=..\desktop_gui\icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
; Minimum Windows 10
MinVersion=10.0

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Install the entire PhotoBridge directory (PyInstaller --onedir output)
Source: "..\dist\PhotoBridge\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Start Menu shortcut
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
; Desktop shortcut (optional, user-selectable)
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
; Start Menu uninstall shortcut
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"

[Run]
; Launch app after installation (optional checkbox)
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

; Create firewall rule during installation (elevated, silent)
Filename: "powershell.exe"; \
    Parameters: "-NoProfile -WindowStyle Hidden -Command ""if (-not (Get-NetFirewallRule -DisplayName 'PhotoBridge Port 8000' -ErrorAction SilentlyContinue)) {{ New-NetFirewallRule -DisplayName 'PhotoBridge Port 8000' -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow -Profile Private }}"""; \
    Flags: runhidden waituntilterminated; \
    StatusMsg: "Configuring Windows Firewall..."

[UninstallRun]
; Remove firewall rule on uninstall
Filename: "powershell.exe"; \
    Parameters: "-NoProfile -WindowStyle Hidden -Command ""Remove-NetFirewallRule -DisplayName 'PhotoBridge Port 8000' -ErrorAction SilentlyContinue"""; \
    Flags: runhidden waituntilterminated

[UninstallDelete]
; Clean up user data directory on uninstall
Type: filesandordirs; Name: "{localappdata}\PhotoBridge"
