# Universal Batch File Creation Script
# Step 3: Creating batch file for emulator launch

Write-Host "=== UNIVERSAL BATCH FILE CREATION ===" -ForegroundColor Cyan

# Load configuration
$ConfigPath = "C:\Scripts\config.json"
if (Test-Path $ConfigPath) {
    $Config = Get-Content $ConfigPath | ConvertFrom-Json
    $SDKRoot = $Config.android_sdk.sdk_root
    $Emulator = $Config.android_sdk.emulator
} else {
    Write-Host "Configuration not found, using defaults..." -ForegroundColor Yellow
    $SDKRoot = "C:\Users\user\AppData\Local\Android\Sdk"
    $Emulator = "$SDKRoot\emulator\emulator.exe"
}

# Find last created user
$UserNumber = 1
$LastValidUser = $null
do {
    $TestUser = "User$UserNumber"
    $UserExists = Get-LocalUser -Name $TestUser -ErrorAction SilentlyContinue
    if ($UserExists) {
        $LastValidUser = $TestUser
        $UserNumber++
    }
} while ($UserExists)

if (-not $LastValidUser) {
    Write-Host "ERROR: No users found. Please create a user first." -ForegroundColor Red
    exit 1
}

# Use last created user
$TestUser = $LastValidUser
$UserNumber = $TestUser.Replace('User', '')
$AvdName = "phone$UserNumber"
$BatchFilePath = "C:\Scripts\${TestUser}_emulator.bat"

Write-Host "Creating batch file for emulator launch..." -ForegroundColor Yellow
Write-Host "User: $TestUser" -ForegroundColor White
Write-Host "AVD: $AvdName" -ForegroundColor White
Write-Host "Batch file: $BatchFilePath" -ForegroundColor White

# Ensure Scripts directory exists
if (!(Test-Path "C:\Scripts")) {
    New-Item -ItemType Directory -Path "C:\Scripts" -Force
    Write-Host "Created directory C:\Scripts" -ForegroundColor Gray
}

# Get emulator directory from config
$EmulatorDir = Split-Path $Emulator -Parent
Write-Host "Emulator directory: $EmulatorDir" -ForegroundColor Gray

# Create batch file content
$BatchContent = @"
@echo off
REM Android Emulator Launcher Script
REM User: $TestUser
REM AVD: $AvdName
REM Created: $(Get-Date)
REM SDK: $SDKRoot

echo ========================================
echo Android Emulator Launcher
echo ========================================
echo User: $TestUser
echo AVD: $AvdName
echo SDK: $SDKRoot
echo ========================================

echo Changing to emulator directory...
cd /d "$EmulatorDir"
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Could not change to emulator directory
    echo Directory: $EmulatorDir
    pause
    exit /b 1
)

echo Current directory: %CD%
echo.

echo Checking if AVD exists...
if not exist "%USERPROFILE%\.android\avd\$AvdName.avd" (
    echo ERROR: AVD $AvdName not found
    echo Expected path: %USERPROFILE%\.android\avd\$AvdName.avd
    pause
    exit /b 1
)

echo AVD found: $AvdName
echo.

echo Starting emulator with optimized settings...
echo Command: emulator -avd "$AvdName" -no-snapshot -gpu host -memory 2048 -no-boot-anim -netdelay none -netspeed full -audio-in on -audio-out on -verbose
echo.

REM Start emulator with optimized settings for RemoteApp
emulator -avd "$AvdName" -no-snapshot -gpu host -memory 2048 -no-boot-anim -netdelay none -netspeed full -audio-in on -audio-out on -verbose

echo.
echo Emulator has finished
pause
"@

try {
    Set-Content -Path $BatchFilePath -Value $BatchContent -Encoding ASCII
    Write-Host "SUCCESS: Batch file created: $BatchFilePath" -ForegroundColor Green
    
    # Check file size
    $FileInfo = Get-Item $BatchFilePath
    Write-Host "File size: $($FileInfo.Length) bytes" -ForegroundColor Gray
    
    # Verify AVD exists
    $AvdPath = "$env:USERPROFILE\.android\avd\$AvdName.avd"
    if (Test-Path $AvdPath) {
        Write-Host "✅ AVD verified: $AvdName exists" -ForegroundColor Green
    } else {
        Write-Host "⚠️ WARNING: AVD $AvdName not found at $AvdPath" -ForegroundColor Yellow
    }
    
    # Verify emulator exists
    if (Test-Path $Emulator) {
        Write-Host "✅ Emulator verified: $Emulator exists" -ForegroundColor Green
    } else {
        Write-Host "⚠️ WARNING: Emulator not found at $Emulator" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "=== BATCH FILE CREATION RESULT ===" -ForegroundColor Cyan
    Write-Host "USER: $TestUser" -ForegroundColor White
    Write-Host "AVD: $AvdName" -ForegroundColor White
    Write-Host "BATCH FILE: $BatchFilePath" -ForegroundColor White
    Write-Host "EMULATOR: $Emulator" -ForegroundColor White
    Write-Host "SUCCESS: Batch file ready for conversion to EXE!" -ForegroundColor Green
    
} catch {
    Write-Host "ERROR: Failed to create batch file: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=== BATCH FILE CREATION COMPLETE ===" -ForegroundColor Cyan
