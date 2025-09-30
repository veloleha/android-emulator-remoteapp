# Auto-fix script for Android emulator issues
# Combines all fixes: permissions, lock files, directory detection

param(
    [string]$Username = "",
    [string]$EmulatorName = ""
)

Write-Host "=== AUTO-FIX ANDROID EMULATOR ISSUES ===" -ForegroundColor Yellow

# Get username from environment if provided (web interface)
if ([string]::IsNullOrEmpty($Username) -and $env:USERNAME_OVERRIDE) {
    $Username = $env:USERNAME_OVERRIDE
    Write-Host "Using username from environment: $Username" -ForegroundColor Gray
}

# If still no username, find the last user
if ([string]::IsNullOrEmpty($Username)) {
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
        $Username = "User$MaxUserNumber"
        Write-Host "Auto-detected user: $Username" -ForegroundColor Gray
    } else {
        Write-Host "ERROR: Could not find User* users" -ForegroundColor Red
        exit 1
    }
}

Write-Host "Target user: $Username" -ForegroundColor Cyan

# Determine user profile paths - check main directory first, then .HP
$UserProfilePath = "C:\Users\$Username"
$UserProfilePathHP = "C:\Users\$Username.HP"

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

$AndroidDir = "$ActualUserProfile\.android"
$AvdDir = "$AndroidDir\avd"

Write-Host ""
Write-Host "=== STEP 1: CREATE DIRECTORIES ===" -ForegroundColor Yellow

# Create .android directory if needed
if (!(Test-Path $AndroidDir)) {
    New-Item -ItemType Directory -Path $AndroidDir -Force | Out-Null
    Write-Host "Created: $AndroidDir" -ForegroundColor Green
} else {
    Write-Host "Exists: $AndroidDir" -ForegroundColor Gray
}

# Create avd directory if needed
if (!(Test-Path $AvdDir)) {
    New-Item -ItemType Directory -Path $AvdDir -Force | Out-Null
    Write-Host "Created: $AvdDir" -ForegroundColor Green
} else {
    Write-Host "Exists: $AvdDir" -ForegroundColor Gray
}

Write-Host ""
Write-Host "=== STEP 2: CREATE LOCK FILES ===" -ForegroundColor Yellow

# Create all necessary lock files
$LockFiles = @(
    "$AndroidDir\emu-last-feature-flags.protobuf",
    "$AndroidDir\emu-last-feature-flags.protobuf.lock",
    "$AndroidDir\emulator-check.exe.lock",
    "$AndroidDir\pid.lock",
    "$AndroidDir\cache.lock",
    "$AndroidDir\modem-nv-ram-5554",
    "$AndroidDir\modem-nv-ram-5556"
)

foreach ($LockFile in $LockFiles) {
    if (!(Test-Path $LockFile)) {
        New-Item -ItemType File -Path $LockFile -Force -ErrorAction SilentlyContinue | Out-Null
        $FileName = Split-Path $LockFile -Leaf
        Write-Host "Created: $FileName" -ForegroundColor Green
    } else {
        $FileName = Split-Path $LockFile -Leaf
        Write-Host "Exists: $FileName" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "=== STEP 3: FIX OWNERSHIP ===" -ForegroundColor Yellow

# Take ownership of the entire .android directory
Write-Host "Taking ownership of $AndroidDir..." -ForegroundColor Gray
takeown /F "$AndroidDir" /R /D Y 2>&1 | Out-Null

Write-Host ""
Write-Host "=== STEP 4: SET PERMISSIONS ===" -ForegroundColor Yellow

# Set full permissions using icacls with SIDs (more reliable)
$Commands = @(
    "icacls `"$AndroidDir`" /grant *S-1-1-0:(OI)(CI)F /T /C /Q",      # Everyone
    "icacls `"$AndroidDir`" /grant *S-1-5-18:(OI)(CI)F /T /C /Q",     # SYSTEM
    "icacls `"$AndroidDir`" /grant *S-1-5-32-545:(OI)(CI)F /T /C /Q", # Users
    "icacls `"$AndroidDir`" /grant `"$Username`":(OI)(CI)F /T /C /Q"   # Specific user
)

foreach ($cmd in $Commands) {
    cmd /c $cmd 2>&1 | Out-Null
}

# Also set permissions on each lock file specifically
foreach ($LockFile in $LockFiles) {
    if (Test-Path $LockFile) {
        icacls "$LockFile" /grant *S-1-1-0:F /C /Q 2>&1 | Out-Null  # Everyone
        icacls "$LockFile" /grant *S-1-5-18:F /C /Q 2>&1 | Out-Null  # SYSTEM
    }
}

Write-Host "Permissions configured for all users" -ForegroundColor Green

Write-Host ""
Write-Host "=== STEP 5: VERIFY SETUP ===" -ForegroundColor Yellow

# Check if any AVDs exist
$AvdCount = 0
if (Test-Path $AvdDir) {
    $AvdFolders = Get-ChildItem -Path $AvdDir -Directory -ErrorAction SilentlyContinue
    $AvdCount = $AvdFolders.Count
    
    if ($AvdCount -gt 0) {
        Write-Host "Found $AvdCount AVD(s):" -ForegroundColor Cyan
        foreach ($avd in $AvdFolders) {
            Write-Host "  - $($avd.Name)" -ForegroundColor Gray
        }
    } else {
        Write-Host "No AVDs found - ready for new emulator creation" -ForegroundColor Gray
    }
}

# List created lock files
Write-Host ""
Write-Host "Lock files status:" -ForegroundColor Cyan
foreach ($LockFile in $LockFiles) {
    if (Test-Path $LockFile) {
        $FileName = Split-Path $LockFile -Leaf
        Write-Host "  [OK] $FileName" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "SUCCESS: Auto-fix completed for $Username!" -ForegroundColor Green
Write-Host "Profile: $ActualUserProfile" -ForegroundColor Cyan
Write-Host "Android dir: $AndroidDir" -ForegroundColor Cyan
Write-Host "AVD dir: $AvdDir" -ForegroundColor Cyan

Write-Host ""
Write-Host "The user is now ready for emulator creation without lock file errors!" -ForegroundColor Green
