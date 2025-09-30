# Simple AVD duplication script
param(
    [string]$SourceAvdName = "User26_87",
    [string]$TargetAvdName = "User26_88",
    [string]$UserName = "User26"
)

Write-Host "Duplicating AVD: $SourceAvdName -> $TargetAvdName" -ForegroundColor Yellow

# Determine paths
$UserProfilePath = "C:\Users\$UserName"
$UserProfilePathHP = "C:\Users\$UserName.HP"

if (Test-Path $UserProfilePathHP) {
    $ActualUserProfile = $UserProfilePathHP
} else {
    $ActualUserProfile = $UserProfilePath
}

Write-Host "Profile: $ActualUserProfile" -ForegroundColor Gray

# AVD paths
$AvdBaseDir = "$ActualUserProfile\.android\avd"
$SourceAvdDir = "$AvdBaseDir\$SourceAvdName.avd"
$SourceIniFile = "$AvdBaseDir\$SourceAvdName.ini"
$TargetAvdDir = "$AvdBaseDir\$TargetAvdName.avd"
$TargetIniFile = "$AvdBaseDir\$TargetAvdName.ini"

# Check source AVD
if (!(Test-Path $SourceAvdDir)) {
    Write-Host "ERROR: Source AVD not found: $SourceAvdDir" -ForegroundColor Red
    exit 1
}

if (!(Test-Path $SourceIniFile)) {
    Write-Host "ERROR: Source INI not found: $SourceIniFile" -ForegroundColor Red
    exit 1
}

Write-Host "Source AVD found" -ForegroundColor Green

# Remove target AVD if exists
if (Test-Path $TargetAvdDir) {
    Write-Host "Removing existing target AVD..." -ForegroundColor Yellow
    Remove-Item -Path $TargetAvdDir -Recurse -Force
}

if (Test-Path $TargetIniFile) {
    Remove-Item -Path $TargetIniFile -Force
}

# Copy AVD folder
Write-Host "Copying AVD folder..." -ForegroundColor Cyan
Copy-Item -Path $SourceAvdDir -Destination $TargetAvdDir -Recurse -Force

# Copy INI file
Write-Host "Copying INI file..." -ForegroundColor Cyan
Copy-Item -Path $SourceIniFile -Destination $TargetIniFile -Force

# Edit INI file
Write-Host "Editing INI file..." -ForegroundColor Cyan
$IniContent = Get-Content -Path $TargetIniFile
$NewIniContent = @()

foreach ($line in $IniContent) {
    if ($line -match "^path=") {
        $NewIniContent += "path=$TargetAvdDir"
    } elseif ($line -match "^path\.rel=") {
        $NewIniContent += "path.rel=avd\$TargetAvdName.avd"
    } else {
        $NewIniContent += $line
    }
}

Set-Content -Path $TargetIniFile -Value $NewIniContent

# Edit config.ini
Write-Host "Editing config.ini..." -ForegroundColor Cyan
$ConfigIniPath = "$TargetAvdDir\config.ini"

if (Test-Path $ConfigIniPath) {
    $ConfigContent = Get-Content -Path $ConfigIniPath
    $NewConfigContent = @()
    
    foreach ($line in $ConfigContent) {
        if ($line -match "^AvdId=") {
            $NewConfigContent += "AvdId=$TargetAvdName"
        } elseif ($line -match "^avd\.name=") {
            $NewConfigContent += "avd.name=$TargetAvdName"
        } else {
            $NewConfigContent += $line
        }
    }
    
    Set-Content -Path $ConfigIniPath -Value $NewConfigContent
}

Write-Host "SUCCESS: AVD $TargetAvdName created!" -ForegroundColor Green
Write-Host "Path: $TargetAvdDir" -ForegroundColor Gray
