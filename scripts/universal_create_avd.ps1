# Universal AVD Creation Script
# Works with different Android SDK configurations

Write-Host "=== UNIVERSAL AVD CREATION ===" -ForegroundColor Cyan

# Load configuration
$ConfigPath = "C:\Scripts\config.json"
if (Test-Path $ConfigPath) {
    $Config = Get-Content $ConfigPath | ConvertFrom-Json
    $SDKRoot = $Config.android_sdk.sdk_root
    $AvdManager = $Config.android_sdk.avdmanager
    $Emulator = $Config.android_sdk.emulator
} else {
    Write-Host "Configuration file not found. Running SDK detection first..." -ForegroundColor Yellow
    & "C:\Scripts\find_android_sdk.ps1"
    
    if (Test-Path $ConfigPath) {
        $Config = Get-Content $ConfigPath | ConvertFrom-Json
        $SDKRoot = $Config.android_sdk.sdk_root
        $AvdManager = $Config.android_sdk.avdmanager
        $Emulator = $Config.android_sdk.emulator
    } else {
        Write-Host "ERROR: Could not detect Android SDK" -ForegroundColor Red
        exit 1
    }
}

Write-Host "Using SDK: $SDKRoot" -ForegroundColor White

# Find next available phone number
$PhoneNumber = 1
do {
    $AvdName = "phone$PhoneNumber"
    $AvdPath = "$env:USERPROFILE\.android\avd\$AvdName.avd"
    $AvdExists = Test-Path $AvdPath
    if ($AvdExists) {
        Write-Host "AVD $AvdName exists, trying next..." -ForegroundColor Yellow
        $PhoneNumber++
    }
} while ($AvdExists)

Write-Host "Creating AVD: $AvdName" -ForegroundColor Yellow

# Check if we have AVD Manager
if ($AvdManager -and (Test-Path $AvdManager)) {
    Write-Host "Using AVD Manager: $AvdManager" -ForegroundColor Green
    
    # Create AVD using avdmanager
    $SystemImage = "system-images;android-33;google_apis;x86_64"
    $CreateCommand = "`"$AvdManager`" create avd -n `"$AvdName`" -k `"$SystemImage`" --force"
    
    Write-Host "Command: $CreateCommand" -ForegroundColor Gray
    
    try {
        $ProcessInfo = New-Object System.Diagnostics.ProcessStartInfo
        $ProcessInfo.FileName = "cmd.exe"
        $ProcessInfo.Arguments = "/c $CreateCommand"
        $ProcessInfo.UseShellExecute = $false
        $ProcessInfo.RedirectStandardInput = $true
        $ProcessInfo.RedirectStandardOutput = $true
        $ProcessInfo.RedirectStandardError = $true
        
        $Process = [System.Diagnostics.Process]::Start($ProcessInfo)
        $Process.StandardInput.WriteLine("no")  # Answer "no" to custom hardware profile
        $Process.StandardInput.Close()
        $Process.WaitForExit(60000)
        
        if ($Process.ExitCode -eq 0) {
            Write-Host "SUCCESS: AVD created with avdmanager" -ForegroundColor Green
        } else {
            Write-Host "WARNING: avdmanager failed, trying manual creation..." -ForegroundColor Yellow
            $ManualCreation = $true
        }
    } catch {
        Write-Host "WARNING: avdmanager error, trying manual creation..." -ForegroundColor Yellow
        $ManualCreation = $true
    }
} else {
    Write-Host "AVD Manager not found, using manual creation..." -ForegroundColor Yellow
    $ManualCreation = $true
}

# Manual AVD creation if avdmanager is not available
if ($ManualCreation) {
    Write-Host "Creating AVD manually..." -ForegroundColor Yellow
    
    # Create AVD directory structure
    $AvdDir = "$env:USERPROFILE\.android\avd"
    $AvdPath = "$AvdDir\$AvdName.avd"
    $IniFile = "$AvdDir\$AvdName.ini"
    
    # Ensure .android directory exists
    if (!(Test-Path "$env:USERPROFILE\.android")) {
        New-Item -Path "$env:USERPROFILE\.android" -ItemType Directory -Force
    }
    if (!(Test-Path $AvdDir)) {
        New-Item -Path $AvdDir -ItemType Directory -Force
    }
    
    # Create AVD directory
    New-Item -Path $AvdPath -ItemType Directory -Force
    
    # Create AVD .ini file
    $IniContent = @"
avd.ini.encoding=UTF-8
path=$AvdPath
path.rel=avd\$AvdName.avd
target=android-33
"@
    Set-Content -Path $IniFile -Value $IniContent
    
    # Create config.ini file
    $ConfigIni = "$AvdPath\config.ini"
    $ConfigContent = @"
avd.ini.displayname=$AvdName
avd.ini.encoding=UTF-8
abi.type=x86_64
disk.dataPartition.size=6442450944
hw.accelerometer=yes
hw.audioInput=yes
hw.audioOutput=yes
hw.battery=yes
hw.camera.back=webcam0
hw.camera.front=webcam0
hw.cpu.arch=x86_64
hw.cpu.ncore=4
hw.dPad=no
hw.device.hash2=MD5:6930e145748b87e87d3f40cabd140a41
hw.device.manufacturer=Google
hw.device.name=pixel_6
hw.gps=yes
hw.gpu.enabled=yes
hw.gpu.mode=host
hw.keyboard=yes
hw.lcd.density=420
hw.lcd.height=2400
hw.lcd.width=1080
hw.mainKeys=no
hw.ramSize=2048
hw.sdCard=yes
hw.sensors.orientation=yes
hw.sensors.proximity=yes
hw.trackBall=no
image.sysdir.1=system-images\android-33\google_apis\x86_64\
runtime.network.latency=none
runtime.network.speed=full
tag.display=Google APIs
tag.id=google_apis
vm.heapSize=256
"@
    Set-Content -Path $ConfigIni -Value $ConfigContent
    
    Write-Host "SUCCESS: AVD created manually" -ForegroundColor Green
}

# Verify AVD creation
$FinalAvdPath = "$env:USERPROFILE\.android\avd\$AvdName.avd"
if (Test-Path $FinalAvdPath) {
    Write-Host ""
    Write-Host "=== AVD CREATION RESULT ===" -ForegroundColor Cyan
    Write-Host "AVD NAME: $AvdName" -ForegroundColor White
    Write-Host "AVD PATH: $FinalAvdPath" -ForegroundColor White
    Write-Host "SDK ROOT: $SDKRoot" -ForegroundColor White
    Write-Host "EMULATOR: $Emulator" -ForegroundColor White
    Write-Host ""
    Write-Host "SUCCESS: AVD $AvdName is ready!" -ForegroundColor Green
    
    # Test emulator if available
    if ($Emulator -and (Test-Path $Emulator)) {
        Write-Host ""
        Write-Host "Testing emulator availability..." -ForegroundColor Yellow
        try {
            $EmulatorList = & $Emulator -list-avds 2>$null
            if ($EmulatorList -contains $AvdName) {
                Write-Host "✅ Emulator can see the AVD" -ForegroundColor Green
            } else {
                Write-Host "⚠️ Emulator may need restart to see new AVD" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "⚠️ Could not test emulator" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "ERROR: Failed to create AVD" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=== AVD CREATION COMPLETE ===" -ForegroundColor Cyan
