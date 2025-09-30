# Duplicate AVD from template (phone1) to user directory
param(
    [string]$TemplateAvdName = "phone1",
    [string]$TargetAvdName = "User26_WithApps", 
    [string]$TargetUserName = "User26"
)

Write-Host "=== DUPLICATE FROM TEMPLATE ===" -ForegroundColor Yellow
Write-Host "Template: $TemplateAvdName (from user directory)" -ForegroundColor Cyan
Write-Host "Target: $TargetAvdName (for $TargetUserName)" -ForegroundColor Cyan
Write-Host ""

# Template paths (from user directory)
$TemplateAvdDir = "C:\Users\user\.android\avd\$TemplateAvdName.avd"
$TemplateIniFile = "C:\Users\user\.android\avd\$TemplateAvdName.ini"

# Target user paths with .HP support
$UserProfilePath = "C:\Users\$TargetUserName"
$UserProfilePathHP = "C:\Users\$TargetUserName.HP"

if (Test-Path $UserProfilePathHP) {
    $ActualUserProfile = $UserProfilePathHP
} else {
    $ActualUserProfile = $UserProfilePath
}

Write-Host "Template source: C:\Users\user\.android\avd\" -ForegroundColor Gray
Write-Host "Target profile: $ActualUserProfile" -ForegroundColor Gray

# Target AVD paths
$TargetAvdBaseDir = "$ActualUserProfile\.android\avd"
$TargetAvdDir = "$TargetAvdBaseDir\$TargetAvdName.avd"
$TargetIniFile = "$TargetAvdBaseDir\$TargetAvdName.ini"

Write-Host ""
Write-Host "=== STEP 1: Validate Template AVD ===" -ForegroundColor Yellow

# Check template AVD exists
if (!(Test-Path $TemplateAvdDir)) {
    Write-Host "ERROR: Template AVD not found: $TemplateAvdDir" -ForegroundColor Red
    exit 1
}

if (!(Test-Path $TemplateIniFile)) {
    Write-Host "ERROR: Template INI not found: $TemplateIniFile" -ForegroundColor Red
    exit 1
}

Write-Host "SUCCESS: Template AVD found" -ForegroundColor Green
Write-Host "   Folder: $TemplateAvdDir" -ForegroundColor Gray
Write-Host "   INI: $TemplateIniFile" -ForegroundColor Gray

# Get template size
$TemplateSize = (Get-ChildItem -Path $TemplateAvdDir -Recurse | Measure-Object -Property Length -Sum).Sum
$TemplateSizeMB = [math]::Round($TemplateSize / 1MB, 2)
Write-Host "   Size: $TemplateSizeMB MB" -ForegroundColor Gray

Write-Host ""
Write-Host "=== STEP 2: Prepare Target Directory ===" -ForegroundColor Yellow

# Create target .android directory if not exists
$TargetAndroidDir = "$ActualUserProfile\.android"
if (!(Test-Path $TargetAndroidDir)) {
    New-Item -ItemType Directory -Path $TargetAndroidDir -Force | Out-Null
    Write-Host "Created .android directory" -ForegroundColor Green
}

if (!(Test-Path $TargetAvdBaseDir)) {
    New-Item -ItemType Directory -Path $TargetAvdBaseDir -Force | Out-Null
    Write-Host "Created avd directory" -ForegroundColor Green
}

# Remove existing target AVD if exists
if (Test-Path $TargetAvdDir) {
    Write-Host "Removing existing target AVD..." -ForegroundColor Yellow
    Remove-Item -Path $TargetAvdDir -Recurse -Force
}

if (Test-Path $TargetIniFile) {
    Remove-Item -Path $TargetIniFile -Force
}

Write-Host ""
Write-Host "=== STEP 3: Copy Template AVD ===" -ForegroundColor Yellow

# Copy AVD folder
Write-Host "Copying AVD folder..." -ForegroundColor Cyan
$StartTime = Get-Date
Copy-Item -Path $TemplateAvdDir -Destination $TargetAvdDir -Recurse -Force
$EndTime = Get-Date
$Duration = ($EndTime - $StartTime).TotalSeconds
Write-Host "SUCCESS: AVD folder copied in $([math]::Round($Duration, 1)) seconds" -ForegroundColor Green

# Copy INI file
Write-Host "Copying INI file..." -ForegroundColor Cyan
Copy-Item -Path $TemplateIniFile -Destination $TargetIniFile -Force
Write-Host "SUCCESS: INI file copied" -ForegroundColor Green

Write-Host ""
Write-Host "=== STEP 4: Update INI File ===" -ForegroundColor Yellow

# Edit INI file
$IniContent = Get-Content -Path $TargetIniFile
$NewIniContent = @()

foreach ($line in $IniContent) {
    if ($line -match "^path=") {
        $NewIniContent += "path=$TargetAvdDir"
        Write-Host "Updated path in INI: $TargetAvdDir" -ForegroundColor Gray
    } elseif ($line -match "^path\.rel=") {
        $NewIniContent += "path.rel=avd\$TargetAvdName.avd"
        Write-Host "Updated relative path in INI" -ForegroundColor Gray
    } else {
        $NewIniContent += $line
    }
}

Set-Content -Path $TargetIniFile -Value $NewIniContent
Write-Host "SUCCESS: INI file updated" -ForegroundColor Green

Write-Host ""
Write-Host "=== STEP 5: Update config.ini ===" -ForegroundColor Yellow

# Edit config.ini inside AVD
$ConfigIniPath = "$TargetAvdDir\config.ini"
if (Test-Path $ConfigIniPath) {
    $ConfigContent = Get-Content -Path $ConfigIniPath
    $NewConfigContent = @()
    
    foreach ($line in $ConfigContent) {
        if ($line -match "^AvdId=") {
            $NewConfigContent += "AvdId=$TargetAvdName"
            Write-Host "Updated AvdId: $TargetAvdName" -ForegroundColor Gray
        } elseif ($line -match "^avd\.name=") {
            $NewConfigContent += "avd.name=$TargetAvdName"
            Write-Host "Updated avd.name: $TargetAvdName" -ForegroundColor Gray
        } else {
            $NewConfigContent += $line
        }
    }
    
    Set-Content -Path $ConfigIniPath -Value $NewConfigContent
    Write-Host "SUCCESS: config.ini updated" -ForegroundColor Green
} else {
    Write-Host "WARNING: config.ini not found" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== STEP 6: Set Permissions ===" -ForegroundColor Yellow

# Set permissions for RemoteApp compatibility
try {
    icacls $ActualUserProfile /grant "Everyone:(OI)(CI)F" /T /Q | Out-Null
    icacls "$ActualUserProfile\.android" /grant "Everyone:(OI)(CI)F" /T /Q | Out-Null
    icacls $TargetAvdDir /grant "Everyone:(OI)(CI)F" /T /Q | Out-Null
    Write-Host "SUCCESS: Permissions set for RemoteApp" -ForegroundColor Green
} catch {
    Write-Host "WARNING: Could not set some permissions" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== STEP 7: Verify Result ===" -ForegroundColor Yellow

# Check target AVD
if (Test-Path $TargetAvdDir) {
    $TargetSize = (Get-ChildItem -Path $TargetAvdDir -Recurse | Measure-Object -Property Length -Sum).Sum
    $TargetSizeMB = [math]::Round($TargetSize / 1MB, 2)
    
    $TemplateFileCount = (Get-ChildItem -Path $TemplateAvdDir -Recurse -File).Count
    $TargetFileCount = (Get-ChildItem -Path $TargetAvdDir -Recurse -File).Count
    
    Write-Host "SUCCESS: Target AVD created!" -ForegroundColor Green
    Write-Host "   Folder: $TargetAvdDir" -ForegroundColor Gray
    Write-Host "   INI: $TargetIniFile" -ForegroundColor Gray
    Write-Host "   Size: $TargetSizeMB MB (template: $TemplateSizeMB MB)" -ForegroundColor Gray
    Write-Host "   Files: $TargetFileCount (template: $TemplateFileCount)" -ForegroundColor Gray
    
    if ($TargetFileCount -eq $TemplateFileCount) {
        Write-Host "SUCCESS: File count matches - copy successful!" -ForegroundColor Green
    } else {
        Write-Host "WARNING: File count mismatch - possible issues" -ForegroundColor Yellow
    }
} else {
    Write-Host "ERROR: Target AVD not created" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "SUCCESS: Template duplication completed!" -ForegroundColor Green
Write-Host "New AVD '$TargetAvdName' contains all apps from template '$TemplateAvdName'" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Create batch file: $TargetUserName`_$TargetAvdName.bat" -ForegroundColor Gray
Write-Host "2. Test emulator launch" -ForegroundColor Gray
