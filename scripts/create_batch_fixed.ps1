# FIXED VERSION - Create batch file without BOM
# For web interface usage
param(
    [string]$EmulatorName = "Emulator"
)

Write-Host "=== CREATING BATCH FILE (NO BOM) ===" -ForegroundColor Yellow

# 1. Find last user via net user
$AllUsers = net user | Where-Object { $_ -match "User\d+" }
$UserNumbers = @()
foreach ($line in $AllUsers) {
    $users = $line -split '\s+' | Where-Object { $_ -match "^User\d+$" }
    foreach ($user in $users) {
        if ($user -match "^User(\d+)$") {
            $UserNumbers += [int]$matches[1]
        }
    }
}

if ($UserNumbers.Count -gt 0) {
    $MaxUserNumber = ($UserNumbers | Measure-Object -Maximum).Maximum
    $LastValidUser = "User$MaxUserNumber"
    Write-Host "Using user: $LastValidUser" -ForegroundColor Gray
} else {
    Write-Host "ERROR: Could not find User* users" -ForegroundColor Red
    exit 1
}

# 2. Form names
$UserNum = $LastValidUser.Replace('User', '')
$SafeEmulatorName = $EmulatorName -replace '[^a-zA-Z0-9_]', '_'
$AvdName = "User$UserNum`_$SafeEmulatorName"

# 3. Determine paths - check main directory first, then .HP
$UserProfilePath = "C:\Users\$LastValidUser"
$UserProfilePathHP = "C:\Users\$LastValidUser.HP"

# Check which directory has .android folder or use main directory
$MainAndroidDir = "$UserProfilePath\.android"
$HPAndroidDir = "$UserProfilePathHP\.android"

if (Test-Path $MainAndroidDir) {
    $ActualUserProfile = $UserProfilePath
    Write-Host "Using main profile (has .android): $ActualUserProfile" -ForegroundColor Gray
} elseif (Test-Path $HPAndroidDir) {
    $ActualUserProfile = $UserProfilePathHP
    Write-Host "Using HP profile (has .android): $ActualUserProfile" -ForegroundColor Gray
} elseif (Test-Path $UserProfilePath) {
    $ActualUserProfile = $UserProfilePath
    Write-Host "Using main profile (exists): $ActualUserProfile" -ForegroundColor Gray
} else {
    $ActualUserProfile = $UserProfilePathHP
    Write-Host "Using HP profile (fallback): $ActualUserProfile" -ForegroundColor Gray
}

# 4. Create batch file
$BatchFilePath = "C:\Scripts\$AvdName.bat"

Write-Host "Creating batch file: $BatchFilePath" -ForegroundColor Cyan

# Ensure Scripts directory exists
if (!(Test-Path "C:\Scripts")) {
    New-Item -ItemType Directory -Path "C:\Scripts" -Force | Out-Null
}

# 5. Create batch content as array of strings (avoid BOM)
$BatchLines = @(
    "@echo off",
    "REM Android emulator for user $LastValidUser",
    "REM AVD: $AvdName (copied from phone1 template with apps)",
    "",
    "echo ========================================",
    "echo Android Emulator - $AvdName",
    "echo Ready emulator with preinstalled apps",
    "echo ========================================",
    "",
    "REM Set Android SDK environment variables",
    "set ANDROID_HOME=C:\Program Files\Android",
    "set ANDROID_SDK_ROOT=C:\Program Files\Android",
    "set JAVA_HOME=C:\Program Files\Microsoft\jdk-17.0.16.8-hotspot",
    "",
    "REM Determine AVD directory",
    "if exist `"$ActualUserProfile\.android\avd`" (",
    "    set ANDROID_AVD_HOME=$ActualUserProfile\.android\avd",
    "    echo Using profile: $ActualUserProfile",
    ") else (",
    "    set ANDROID_AVD_HOME=C:\Users\$LastValidUser\.android\avd",
    "    echo Using standard directory: C:\Users\$LastValidUser\.android\avd",
    ")",
    "",
    "set PATH=%JAVA_HOME%\bin;%ANDROID_HOME%\platform-tools;%ANDROID_HOME%\emulator;%ANDROID_HOME%\cmdline-tools\latest\bin;%PATH%",
    "",
    "echo Environment variables:",
    "echo ANDROID_HOME=%ANDROID_HOME%",
    "echo ANDROID_AVD_HOME=%ANDROID_AVD_HOME%",
    "echo.",
    "",
    "echo Changing to emulator directory...",
    "cd /d `"%ANDROID_HOME%\emulator`"",
    "",
    "if not exist `"%ANDROID_HOME%\emulator\emulator.exe`" (",
    "    echo ERROR: Emulator not found at %ANDROID_HOME%\emulator\emulator.exe",
    "    echo Trying alternative path...",
    "    if exist `"C:\Program Files\Android\emulator\emulator.exe`" (",
    "        cd /d `"C:\Program Files\Android\emulator`"",
    "        echo Using: C:\Program Files\Android\emulator",
    "    ) else (",
    "        echo ERROR: Cannot find emulator.exe",
    "        pause",
    "        exit /b 1",
    "    )",
    ")",
    "",
    "echo Starting emulator $AvdName...",
    "echo Command: emulator -avd `"$AvdName`" -no-snapshot -gpu host -memory 4096 -no-boot-anim -netdelay none -netspeed full -dns-server 8.8.8.8,8.8.4.4 -verbose",
    "echo.",
    "",
    "emulator -avd `"$AvdName`" -no-snapshot -gpu host -memory 4096 -no-boot-anim -netdelay none -netspeed full -dns-server 8.8.8.8,8.8.4.4 -verbose",
    "",
    "if %ERRORLEVEL% NEQ 0 (",
    "    echo [!] Start error, trying with wipe-data...",
    "    emulator -avd `"$AvdName`" -no-snapshot -gpu host -memory 4096 -no-boot-anim -netdelay none -netspeed full -dns-server 8.8.8.8,8.8.4.4 -verbose -wipe-data",
    ")",
    "",
    "echo.",
    "echo Emulator finished",
    "pause"
)

try {
    # 6. Write batch file without BOM using ASCII encoding
    $BatchLines | Out-File -FilePath $BatchFilePath -Encoding ASCII
    Write-Host "SUCCESS: Batch file created without BOM!" -ForegroundColor Green
    Write-Host "BATCH_FILE: $BatchFilePath" -ForegroundColor Cyan
    
    # Check file size
    $FileSize = (Get-Item $BatchFilePath).Length
    Write-Host "File size: $FileSize bytes" -ForegroundColor Gray
    
} catch {
    Write-Host "ERROR: Error creating batch file: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
