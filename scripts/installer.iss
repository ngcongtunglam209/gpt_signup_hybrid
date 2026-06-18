; Inno Setup script — GSH installer
;
; Compile: ISCC.exe scripts/installer.iss
; Output:  dist/GSH-Setup.exe
;
; Cài vào %LOCALAPPDATA%\GSH (per-user, KHÔNG cần admin / UAC).
; Tạo shortcut Desktop + Start Menu. Uninstaller tự generate.
;
; Yêu cầu trước khi compile:
;   - dist/GSH.exe đã build xong (chạy scripts/build_exe.py trước).

#define MyAppName "GSH"
#define MyAppVersion "1.0"
#define MyAppPublisher "GSH"
#define MyAppExeName "GSH.exe"

[Setup]
AppId={{B5F8D8C0-2A9F-4E1D-9A3F-7F4E6C2D0001}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=..\dist
OutputBaseFilename=GSH-Setup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
; Cho phép user thay đổi DefaultDirName nếu muốn
DisableDirPage=auto
; UninstallDisplayIcon — thư mục cài có icon riêng
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "vietnamese"; MessagesFile: "compiler:Languages\Vietnamese.isl"

[Tasks]
Name: "desktopicon"; Description: "Tạo shortcut trên Desktop"; GroupDescription: "Shortcuts:"; Flags: checkedonce
Name: "quicklaunchicon"; Description: "Tạo shortcut Quick Launch"; GroupDescription: "Shortcuts:"; Flags: unchecked

[Files]
; Single onefile exe — đã chứa toàn bộ code + Chromium bundled (xem
; scripts/build_exe.py).
Source: "..\dist\GSH.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
; Sau khi cài xong, hỏi user có muốn launch ngay
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Cleanup state file để uninstall sạch
Type: files; Name: "{app}\.state"
Type: dirifempty; Name: "{app}"
