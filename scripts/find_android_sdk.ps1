# Universal Android SDK Detection Script
# Finds Android SDK on different machines and updates config

Write-Host "=== ANDROID SDK DETECTION ===" -ForegroundColor Cyan

# Common Android SDK installation paths
$CommonPaths = @(
    "C:\Program Files\Android\Sdk",
    "C:\Android\Sdk",
    "C:\Users\$env:USERNAME\AppData\Local\Android\Sdk",
    "C:\Program Files (x86)\Android\android-sdk",
    "D:\Android\Sdk",
    "E:\Android\Sdk"
)

# Environment variables to check
$EnvVars = @("ANDROID_HOME", "ANDROID_SDK_ROOT")

Write-Host "Searching for Android SDK..." -ForegroundColor Yellow

$FoundSDK = $null

# Check environment variables first
foreach ($EnvVar in $EnvVars) {
    $EnvPath = [Environment]::GetEnvironmentVariable($EnvVar)
    if ($EnvPath -and (Test-Path $EnvPath)) {
        Write-Host "Found SDK via ${EnvVar}: ${EnvPath}" -ForegroundColor Green
        $FoundSDK = $EnvPath
        break
    }
}

# If not found in env vars, check common paths
if (-not $FoundSDK) {
    foreach ($Path in $CommonPaths) {
        if (Test-Path $Path) {
            Write-Host "Found SDK at: $Path" -ForegroundColor Green
            $FoundSDK = $Path
            break
        }
    }
}

# If still not found, search in Program Files
if (-not $FoundSDK) {
    Write-Host "Searching in Program Files..." -ForegroundColor Yellow
    $SearchResult = Get-ChildItem -Path "C:\Program Files*" -Recurse -Directory -Name "*Android*" -ErrorAction SilentlyContinue | Where-Object { Test-Path "$_\cmdline-tools" -or Test-Path "$_\tools" } | Select-Object -First 1
    if ($SearchResult) {
        $FoundSDK = $SearchResult
        Write-Host "Found SDK via search: $FoundSDK" -ForegroundColor Green
    }
}

if ($FoundSDK) {
    Write-Host "SUCCESS: Android SDK found!" -ForegroundColor Green
    Write-Host "SDK Path: $FoundSDK" -ForegroundColor White
    
    # Detect SDK structure and tools
    $CmdLineTools = $null
    $AvdManager = $null
    $SdkManager = $null
    $Emulator = $null
    
    # Check for different SDK structures
    $PossibleCmdLinePaths = @(
        "$FoundSDK\cmdline-tools\latest\bin",
        "$FoundSDK\cmdline-tools\bin",
        "$FoundSDK\tools\bin"
    )
    
    foreach ($CmdPath in $PossibleCmdLinePaths) {
        if (Test-Path "$CmdPath\avdmanager.bat") {
            $CmdLineTools = $CmdPath
            $AvdManager = "$CmdPath\avdmanager.bat"
            $SdkManager = "$CmdPath\sdkmanager.bat"
            break
        }
    }
    
    # Find emulator
    $PossibleEmulatorPaths = @(
        "$FoundSDK\emulator\emulator.exe",
        "$FoundSDK\tools\emulator.exe"
    )
    
    foreach ($EmuPath in $PossibleEmulatorPaths) {
        if (Test-Path $EmuPath) {
            $Emulator = $EmuPath
            break
        }
    }
    
    Write-Host ""
    Write-Host "=== SDK COMPONENTS ===" -ForegroundColor Cyan
    Write-Host "SDK Root: $FoundSDK" -ForegroundColor White
    Write-Host "Command Line Tools: $CmdLineTools" -ForegroundColor White
    Write-Host "AVD Manager: $AvdManager" -ForegroundColor White
    Write-Host "SDK Manager: $SdkManager" -ForegroundColor White
    Write-Host "Emulator: $Emulator" -ForegroundColor White
    
    # Update config file
    $ConfigPath = "C:\Scripts\config.json"
    if (Test-Path $ConfigPath) {
        Write-Host ""
        Write-Host "Updating configuration file..." -ForegroundColor Yellow
        
        $Config = Get-Content $ConfigPath | ConvertFrom-Json
        $Config.android_sdk.sdk_root = $FoundSDK
        $Config.android_sdk.cmdline_tools = $CmdLineTools
        $Config.android_sdk.avdmanager = $AvdManager
        $Config.android_sdk.sdkmanager = $SdkManager
        $Config.android_sdk.emulator = $Emulator
        
        $Config | ConvertTo-Json -Depth 10 | Set-Content $ConfigPath
        Write-Host "Configuration updated successfully!" -ForegroundColor Green
    }
    
    # Test tools
    Write-Host ""
    Write-Host "Testing SDK tools..." -ForegroundColor Yellow
    
    if ($AvdManager -and (Test-Path $AvdManager)) {
        try {
            $AvdList = & $AvdManager list avd 2>$null
            Write-Host "✅ AVD Manager: Working" -ForegroundColor Green
        } catch {
            Write-Host "⚠️ AVD Manager: Found but may have issues" -ForegroundColor Yellow
        }
    } else {
        Write-Host "❌ AVD Manager: Not found" -ForegroundColor Red
    }
    
    if ($SdkManager -and (Test-Path $SdkManager)) {
        try {
            $SdkList = & $SdkManager --list 2>$null | Select-Object -First 5
            Write-Host "✅ SDK Manager: Working" -ForegroundColor Green
        } catch {
            Write-Host "⚠️ SDK Manager: Found but may have issues" -ForegroundColor Yellow
        }
    } else {
        Write-Host "❌ SDK Manager: Not found" -ForegroundColor Red
    }
    
    if ($Emulator -and (Test-Path $Emulator)) {
        Write-Host "✅ Emulator: Found" -ForegroundColor Green
    } else {
        Write-Host "❌ Emulator: Not found" -ForegroundColor Red
    }
    
} else {
    Write-Host "❌ ERROR: Android SDK not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Android SDK or set ANDROID_HOME environment variable" -ForegroundColor Yellow
    Write-Host "Common installation methods:" -ForegroundColor Yellow
    Write-Host "1. Android Studio (includes SDK)" -ForegroundColor Gray
    Write-Host "2. Command line tools only" -ForegroundColor Gray
    Write-Host "3. Manual SDK installation" -ForegroundColor Gray
    exit 1
}

Write-Host ""
Write-Host "=== SDK DETECTION COMPLETE ===" -ForegroundColor Cyan
