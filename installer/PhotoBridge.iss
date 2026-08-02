; Inno Setup installer for PhotoBridge
; This script creates a Windows installer that:
; - Installs PhotoBridge.exe to Program Files
; - Creates Start Menu and optional Desktop shortcuts
; - Configures Windows Firewall (inbound rule on private networks)
; - Registers a standard Windows uninstaller

#define MyAppName "PhotoBridge"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "PhotoBridge"
#define MyAppURL "https://github.com/yourusername/my-photos-app"
#define MyAppExeName "PhotoBridge.exe"
#define MyAppIconName "icon.ico"

[Setup]
AppId={{5C7D3A1F-2B4E-4A9C-8D6B-9F1A2E3C4D5E}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=no
OutputDir=.\installer-output
OutputBaseFilename=PhotoBridgeSetup
SetupIconFile=.\desktop_gui\{#MyAppIconName}
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64
ArchitecturesAllowed=x64
UninstallDisplayIcon={app}\{#MyAppExeName}
LicenseFile=README.md

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "firewallrule"; Description: "Configure Windows Firewall inbound rule (Port 8000)"; GroupDescription: "Network Configuration"; Flags: checkedonce

[Files]
Source: "dist\PhotoBridge\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\PhotoBridge\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "powershell.exe"; Parameters: "-NoProfile -WindowStyle Hidden -Command ""if (-not (Get-NetFirewallRule -DisplayName 'PhotoBridge Port 8000' -ErrorAction SilentlyContinue)) {{ New-NetFirewallRule -DisplayName 'PhotoBridge Port 8000' -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow -Profile Private }}"""; Flags: runhidden; Tasks: firewallrule; StatusMsg: "Configuring Windows Firewall..."; Check: ShouldConfigureFirewall

[UninstallRun]
Filename: "powershell.exe"; Parameters: "-NoProfile -WindowStyle Hidden -Command ""if (Get-NetFirewallRule -DisplayName 'PhotoBridge Port 8000' -ErrorAction SilentlyContinue) {{ Remove-NetFirewallRule -DisplayName 'PhotoBridge Port 8000' }}"""; Flags: runhidden; StatusMsg: "Removing Windows Firewall rule..."

[Code]
function ShouldConfigureFirewall: Boolean;
begin
  Result := True;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssInstall then
  begin
    // This procedure runs after all files are copied
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usUninstall then
  begin
    // This procedure runs before uninstall
  end;
end;

[Messages]
BeveledLabel={#MyAppName} v{#MyAppVersion}

