; Inno Setup template for StructuralPro
#define MyAppName "StructuralPro"
#define MyAppVersion "0.1.0"
#define MyAppExeName "StructuralPro.exe"
[Setup]
AppId={{E2E3D4D5-7C21-4A1A-9D4A-STRUCTURALPRO}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\StructuralPro
OutputDir=dist\installer
OutputBaseFilename=StructuralPro-Setup
Compression=lzma
SolidCompression=yes
[Files]
Source: "dist\StructuralPro\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion
[Icons]
Name: "{autoprograms}\StructuralPro"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\StructuralPro"; Filename: "{app}\{#MyAppExeName}"
[UninstallDelete]
Type: filesandordirs; Name: "{app}"
