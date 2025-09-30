# Create emulator from phone1 template with apps - FIXED VERSION
# Based on manually tested commands
param(
    [string]$EmulatorName = "TestPhone",
    [string]$TemplateAvdPath = "C:\Users\user\.android\avd\phone1.avd"
)

Write-Host "=== CREATE EMULATOR FROM PHONE1 TEMPLATE ===" -ForegroundColor Yellow
Write-Host "Emulator: $EmulatorName" -ForegroundColor Cyan
Write-Host "Template: $TemplateAvdPath" -ForegroundColor Cyan
Write-Host ""

# 1. Find last user using net user (works in scripts)
Write-Host "=== STEP 1: Find last user ===" -ForegroundColor Yellow

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
    Write-Host "Found users: $($UserNumbers -join ', ')" -ForegroundColor Gray
    Write-Host "Using last user: $LastValidUser" -ForegroundColor Gray
} else {
    Write-Host "ERROR: No User* found" -ForegroundColor Red
    exit 1
}

$UserNum = $LastValidUser.Replace('User', '')
$NewAvdName = "User$UserNum`_$EmulatorName"

Write-Host "Copying ready AVD..." -ForegroundColor Yellow
Write-Host "Template: $TemplateAvdPath" -ForegroundColor Gray
Write-Host "New AVD: $NewAvdName" -ForegroundColor Cyan
Write-Host "User: $LastValidUser" -ForegroundColor Gray

# 2. Check template
Write-Host ""
Write-Host "=== STEP 2: Check template ===" -ForegroundColor Yellow

if (!(Test-Path $TemplateAvdPath)) {
    Write-Host "ERROR: Template AVD not found: $TemplateAvdPath" -ForegroundColor Red
    exit 1
} else {
    Write-Host "SUCCESS: Template found!" -ForegroundColor Green
}

# Get template size
$TemplateSize = (Get-ChildItem -Path $TemplateAvdPath -Recurse | Measure-Object -Property Length -Sum).Sum
$TemplateSizeMB = [math]::Round($TemplateSize / 1MB, 2)
Write-Host "Template size: $TemplateSizeMB MB" -ForegroundColor Gray

# 3. Determine target paths
Write-Host ""
Write-Host "=== STEP 3: Determine target paths ===" -ForegroundColor Yellow

$UserProfilePath = "C:\Users\$LastValidUser"
$UserProfilePathHP = "C:\Users\$LastValidUser.HP"
$ActualUserProfile = if (Test-Path $UserProfilePathHP) { $UserProfilePathHP } else { $UserProfilePath }

$TargetAndroidDir = "$ActualUserProfile\.android\avd"
$TargetAvdPath = "$TargetAndroidDir\$NewAvdName.avd"
$TargetIniPath = "$TargetAndroidDir\$NewAvdName.ini"

Write-Host "Target directory: $TargetAndroidDir" -ForegroundColor Gray
Write-Host "Target AVD: $TargetAvdPath" -ForegroundColor Gray

# 4. Create directories and copy AVD
Write-Host ""
Write-Host "=== STEP 4: Prepare and copy ===" -ForegroundColor Yellow

$AndroidBaseDir = "$ActualUserProfile\.android"
if (!(Test-Path $AndroidBaseDir)) {
    New-Item -ItemType Directory -Path $AndroidBaseDir -Force | Out-Null
    Write-Host "Created directory: $AndroidBaseDir" -ForegroundColor Gray
}
if (!(Test-Path $TargetAndroidDir)) {
    New-Item -ItemType Directory -Path $TargetAndroidDir -Force | Out-Null
    Write-Host "Created directory: $TargetAndroidDir" -ForegroundColor Gray
}

# Remove existing AVD if exists
if (Test-Path $TargetAvdPath) {
    Write-Host "Removing existing AVD..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force $TargetAvdPath -ErrorAction SilentlyContinue
}

if (Test-Path $TargetIniPath) {
    Remove-Item -Force $TargetIniPath -ErrorAction SilentlyContinue
}

# Copy AVD
Write-Host "Copying AVD directory..." -ForegroundColor Yellow
$StartTime = Get-Date
Copy-Item -Path $TemplateAvdPath -Destination $TargetAvdPath -Recurse -Force
$EndTime = Get-Date
$Duration = ($EndTime - $StartTime).TotalSeconds
Write-Host "AVD directory copied in $([math]::Round($Duration, 1)) seconds" -ForegroundColor Green

# 5. Update config.ini with new paths
Write-Host ""
Write-Host "=== STEP 5: Update configuration ===" -ForegroundColor Yellow

$ConfigPath = "$TargetAvdPath\config.ini"
if (Test-Path $ConfigPath) {
    Write-Host "Updating config.ini..." -ForegroundColor Yellow

    $ConfigContent = Get-Content $ConfigPath
    $ConfigContent = $ConfigContent -replace "phone1", $NewAvdName
    $ConfigContent = $ConfigContent -replace "user", $LastValidUser
    $ConfigContent = $ConfigContent -replace "C:\\Users\\user", $ActualUserProfile

    Set-Content -Path $ConfigPath -Value $ConfigContent -Encoding UTF8
    Write-Host "config.ini updated" -ForegroundColor Green
} else {
    Write-Host "WARNING: config.ini not found in $ConfigPath" -ForegroundColor Yellow
}

# 6. Create .ini file and set permissions
Write-Host ""
Write-Host "=== STEP 6: Create INI and set permissions ===" -ForegroundColor Yellow

$IniContent = @"
avd.ini.encoding=UTF-8
path=$TargetAvdPath
path.rel=avd\$NewAvdName.avd
target=android-36
hw.audioInput=yes
hw.audioOutput=yes
"@

Set-Content -Path $TargetIniPath -Value $IniContent -Encoding UTF8
Write-Host ".ini file created" -ForegroundColor Green

# Set permissions
Write-Host "Setting permissions..." -ForegroundColor Yellow
try {
    icacls $AndroidBaseDir /grant "Everyone:(OI)(CI)F" /T /Q | Out-Null
    icacls $TargetAvdPath /grant "Everyone:(OI)(CI)F" /T /Q | Out-Null
    icacls $TargetIniPath /grant "Everyone:F" /Q | Out-Null
    Write-Host "Permissions set" -ForegroundColor Green
} catch {
    Write-Host "WARNING: Could not set some permissions" -ForegroundColor Yellow
}

# 7. Show result
Write-Host ""
Write-Host "=== STEP 7: Copy result ===" -ForegroundColor Yellow

$AvdSize = (Get-ChildItem -Path $TargetAvdPath -Recurse | Measure-Object -Property Length -Sum).Sum
$AvdSizeMB = [math]::Round($AvdSize / 1MB, 2)

Write-Host ""
Write-Host "SUCCESS: AVD successfully copied from template!" -ForegroundColor Green
Write-Host "AVD_NAME: $NewAvdName" -ForegroundColor Cyan
Write-Host "AVD_PATH: $TargetAvdPath" -ForegroundColor Cyan
Write-Host "AVD_SIZE: $AvdSizeMB MB" -ForegroundColor Cyan
Write-Host ""

# 8. Create FIXED batch file for launching copied AVD
Write-Host "=== STEP 8: Create FIXED batch file ===" -ForegroundColor Yellow

$BatchFilePath = "C:\Scripts\$NewAvdName.bat"

# Ensure Scripts directory exists
if (!(Test-Path "C:\Scripts")) {
    New-Item -ItemType Directory -Path "C:\Scripts" -Force | Out-Null
}

# Create batch content as array to avoid BOM issues
$BatchLines = @(
    "@echo off",
    "REM Android emulator for user $LastValidUser",
    "REM AVD: $NewAvdName (copied from ready template)",
    "",
    "echo ========================================",
    "echo Android Emulator - $NewAvdName",
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
    "echo Starting emulator $NewAvdName...",
    "echo Command: emulator -avd `"$NewAvdName`" -no-snapshot -gpu host -memory 4096 -no-boot-anim -netdelay none -netspeed full -dns-server 8.8.8.8,8.8.4.4 -verbose",
    "echo.",
    "",
    "emulator -avd `"$NewAvdName`" -no-snapshot -gpu host -memory 4096 -no-boot-anim -netdelay none -netspeed full -dns-server 8.8.8.8,8.8.4.4 -verbose",
    "",
    "if %ERRORLEVEL% NEQ 0 (",
    "    echo [!] Start error, trying with wipe-data...",
    "    emulator -avd `"$NewAvdName`" -no-snapshot -gpu host -memory 4096 -no-boot-anim -netdelay none -netspeed full -dns-server 8.8.8.8,8.8.4.4 -verbose -wipe-data",
    ")",
    "",
    "echo.",
    "echo Emulator finished",
    "pause"
)

# Write batch file without BOM using ASCII encoding
$BatchLines | Out-File -FilePath $BatchFilePath -Encoding ASCII
Write-Host "SUCCESS: FIXED Batch file created: $BatchFilePath" -ForegroundColor Green

# 9. Show information about created files
Write-Host ""
Write-Host "=== AVD CREATION RESULT ===" -ForegroundColor Cyan
Write-Host "AVD_NAME: $NewAvdName" -ForegroundColor Yellow
Write-Host "AVD_PATH: $TargetAvdPath" -ForegroundColor Yellow
Write-Host "BATCH_FILE: $BatchFilePath" -ForegroundColor Yellow
Write-Host "AVD_SIZE: $AvdSizeMB MB (template: $TemplateSizeMB MB)" -ForegroundColor Yellow
Write-Host ""

Write-Host "Ready emulator with preinstalled apps is ready to use!" -ForegroundColor Green
Write-Host "To launch execute: $BatchFilePath" -ForegroundColor Cyan

# Quality control - check file count
$TemplateFileCount = (Get-ChildItem -Path $TemplateAvdPath -Recurse -File).Count
$TargetFileCount = (Get-ChildItem -Path $TargetAvdPath -Recurse -File).Count

Write-Host ""
Write-Host "=== QUALITY CONTROL ===" -ForegroundColor Yellow
Write-Host "Files in template: $TemplateFileCount" -ForegroundColor Gray
Write-Host "Files in copy: $TargetFileCount" -ForegroundColor Gray

if ($TargetFileCount -eq $TemplateFileCount) {
    Write-Host "SUCCESS: File count matches - copy successful!" -ForegroundColor Green
} else {
    Write-Host "WARNING: File count mismatch - possible issues" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Execution time: $([math]::Round($Duration, 1)) seconds" -ForegroundColor Gray
Write-Host "Emulator ready to launch!" -ForegroundColor Green
