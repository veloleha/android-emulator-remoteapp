# FIXED VERSION - Copy from phone1 template with apps
# For web interface usage
param(
    [string]$EmulatorName = "Emulator"
)

Write-Host "=== COPYING AVD FROM PHONE1 TEMPLATE ===" -ForegroundColor Yellow

# 1. Find last user via net user (works in scripts)
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
    Write-Host "Using user: $LastValidUser" -ForegroundColor Gray
} else {
    Write-Host "ERROR: Could not find User* users" -ForegroundColor Red
    exit 1
}

# 2. Form names
$UserNum = $LastValidUser.Replace('User', '')
$SafeEmulatorName = $EmulatorName -replace '[^a-zA-Z0-9_]', '_'
$AvdName = "User$UserNum`_$SafeEmulatorName"

# 3. Template settings - phone1 with apps (~12 GB)
$TemplateAvdPath = "C:\Users\user\.android\avd\phone1.avd"

Write-Host "Template AVD: $TemplateAvdPath" -ForegroundColor Gray
Write-Host "New AVD: $AvdName" -ForegroundColor Cyan

# 4. Check template existence
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

# 5. Determine target paths - check main directory first, then .HP
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

Write-Host "User profile: $ActualUserProfile" -ForegroundColor Gray

$TargetAndroidDir = "$ActualUserProfile\.android\avd"
$TargetAvdPath = "$TargetAndroidDir\$AvdName.avd"
$TargetIniPath = "$TargetAndroidDir\$AvdName.ini"

try {
    # 6. Create directories
    $AndroidBaseDir = "$ActualUserProfile\.android"
    if (!(Test-Path $AndroidBaseDir)) {
        New-Item -ItemType Directory -Path $AndroidBaseDir -Force | Out-Null
        Write-Host "Created directory: $AndroidBaseDir" -ForegroundColor Gray
    }
    if (!(Test-Path $TargetAndroidDir)) {
        New-Item -ItemType Directory -Path $TargetAndroidDir -Force | Out-Null
        Write-Host "Created directory: $TargetAndroidDir" -ForegroundColor Gray
    }

    # 7. Remove existing AVD if exists
    if (Test-Path $TargetAvdPath) {
        Write-Host "Removing existing AVD..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force $TargetAvdPath -ErrorAction SilentlyContinue
    }
    if (Test-Path $TargetIniPath) {
        Remove-Item -Force $TargetIniPath -ErrorAction SilentlyContinue
    }

    # 8. Copy AVD from template (main operation)
    Write-Host "Copying AVD from phone1 template..." -ForegroundColor Yellow
    $StartTime = Get-Date
    Copy-Item -Path $TemplateAvdPath -Destination $TargetAvdPath -Recurse -Force
    $EndTime = Get-Date
    $Duration = ($EndTime - $StartTime).TotalSeconds
    Write-Host "AVD copied in $([math]::Round($Duration, 1)) seconds" -ForegroundColor Green

    # 9. Update config.ini with new paths
    $ConfigPath = "$TargetAvdPath\config.ini"
    if (Test-Path $ConfigPath) {
        Write-Host "Updating config.ini..." -ForegroundColor Yellow
        $ConfigContent = Get-Content $ConfigPath
        $ConfigContent = $ConfigContent -replace "phone1", $AvdName
        $ConfigContent = $ConfigContent -replace "user", $LastValidUser
        $ConfigContent = $ConfigContent -replace "C:\\Users\\user", $ActualUserProfile
        
        # Add network settings for internet
        $NetworkSettings = @{
            "hw.gps" = "yes"
            "hw.gsmModem" = "yes"
            "hw.network" = "yes"
            "hw.wifi" = "yes"
            "netfast" = "yes"
            "netdelay" = "none"
            "netspeed" = "full"
        }
        
        $NewConfigContent = @()
        $SettingsAdded = @{}
        
        foreach ($line in $ConfigContent) {
            $NewConfigContent += $line
            # Mark which settings already exist
            foreach ($setting in $NetworkSettings.Keys) {
                if ($line -match "^$setting=") {
                    $SettingsAdded[$setting] = $true
                }
            }
        }
        
        # Add missing settings
        foreach ($setting in $NetworkSettings.Keys) {
            if (-not $SettingsAdded[$setting]) {
                $NewConfigContent += "$setting=$($NetworkSettings[$setting])"
            }
        }
        
        Set-Content -Path $ConfigPath -Value $NewConfigContent -Encoding UTF8
        Write-Host "config.ini updated" -ForegroundColor Green
    } else {
        Write-Host "WARNING: config.ini not found" -ForegroundColor Yellow
    }

    # 10. Create .ini file
    $IniContent = @"
avd.ini.encoding=UTF-8
path=$TargetAvdPath
path.rel=avd\$AvdName.avd
target=android-36
hw.audioInput=yes
hw.audioOutput=yes
"@
    Set-Content -Path $TargetIniPath -Value $IniContent -Encoding UTF8
    Write-Host ".ini file created" -ForegroundColor Green

    # 11. Configure permissions for RemoteApp
    Write-Host "Setting up permissions..." -ForegroundColor Yellow
    try {
        icacls $ActualUserProfile /grant "Everyone:(OI)(CI)F" /T /Q | Out-Null
        icacls $AndroidBaseDir /grant "Everyone:(OI)(CI)F" /T /Q | Out-Null
        icacls $AndroidBaseDir /grant "Users:(OI)(CI)F" /T /Q | Out-Null
        icacls $AndroidBaseDir /grant "SYSTEM:(OI)(CI)F" /T /Q | Out-Null
        icacls $TargetAvdPath /grant "Everyone:(OI)(CI)F" /T /Q | Out-Null
        icacls $TargetIniPath /grant "Everyone:F" /Q | Out-Null
        Write-Host "Permissions configured" -ForegroundColor Green
    } catch {
        Write-Host "WARNING: Could not set some permissions" -ForegroundColor Yellow
    }

    # 12. Show results and quality control
    $AvdSize = (Get-ChildItem -Path $TargetAvdPath -Recurse | Measure-Object -Property Length -Sum).Sum
    $AvdSizeMB = [math]::Round($AvdSize / 1MB, 2)
    
    # Quality control - check file count
    $TemplateFileCount = (Get-ChildItem -Path $TemplateAvdPath -Recurse -File).Count
    $TargetFileCount = (Get-ChildItem -Path $TargetAvdPath -Recurse -File).Count

    Write-Host ""
    Write-Host "SUCCESS: AVD successfully copied from phone1 template!" -ForegroundColor Green
    Write-Host "AVD_NAME: $AvdName" -ForegroundColor Cyan
    Write-Host "AVD_PATH: $TargetAvdPath" -ForegroundColor Cyan
    Write-Host "AVD_SIZE: $AvdSizeMB MB (template: $TemplateSizeMB MB)" -ForegroundColor Cyan
    Write-Host "FILES: $TargetFileCount (template: $TemplateFileCount)" -ForegroundColor Cyan
    
    if ($TargetFileCount -eq $TemplateFileCount) {
        Write-Host "SUCCESS: File count matches - copy successful!" -ForegroundColor Green
    } else {
        Write-Host "WARNING: File count mismatch - possible issues" -ForegroundColor Yellow
    }
    
    Write-Host "COPY TIME: $([math]::Round($Duration, 1)) seconds" -ForegroundColor Gray
    Write-Host ""

} catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
