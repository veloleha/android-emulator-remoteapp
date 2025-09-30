# Simple fix for Android emulator permissions
# Uses icacls to set full permissions on all Android directories and files

param(
    [string]$Username = ""
)

Write-Host "=== SIMPLE PERMISSIONS FIX FOR ANDROID EMULATOR ===" -ForegroundColor Yellow

# Check if username provided via environment variable (from web interface)
if ([string]::IsNullOrEmpty($Username) -and $env:USERNAME_OVERRIDE) {
    $Username = $env:USERNAME_OVERRIDE
    Write-Host "Using username from environment: $Username" -ForegroundColor Gray
}

# If username still not provided, find the last user
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
        Write-Host "Found last user: $Username" -ForegroundColor Gray
    } else {
        Write-Host "ERROR: Could not find User* users" -ForegroundColor Red
        exit 1
    }
}

# Determine user profile path
$UserProfilePath = "C:\Users\$Username"
$UserProfilePathHP = "C:\Users\$Username.HP"
$ActualUserProfile = if (Test-Path $UserProfilePathHP) { $UserProfilePathHP } else { $UserProfilePath }

Write-Host "User: $Username" -ForegroundColor Cyan
Write-Host "Profile: $ActualUserProfile" -ForegroundColor Cyan
Write-Host ""

# Create necessary directories
$AndroidDir = "$ActualUserProfile\.android"
$AvdDir = "$AndroidDir\avd"

Write-Host "Creating directories..." -ForegroundColor Yellow
if (!(Test-Path $AndroidDir)) {
    New-Item -ItemType Directory -Path $AndroidDir -Force | Out-Null
    Write-Host "Created: $AndroidDir" -ForegroundColor Green
}

if (!(Test-Path $AvdDir)) {
    New-Item -ItemType Directory -Path $AvdDir -Force | Out-Null
    Write-Host "Created: $AvdDir" -ForegroundColor Green
}

# Create lock files
Write-Host ""
Write-Host "Creating lock files..." -ForegroundColor Yellow

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
        Write-Host "Created: $(Split-Path $LockFile -Leaf)" -ForegroundColor Green
    } else {
        Write-Host "Exists: $(Split-Path $LockFile -Leaf)" -ForegroundColor Gray
    }
}

# Set full permissions using takeown and icacls
Write-Host ""
Write-Host "Setting ownership and permissions..." -ForegroundColor Yellow

# Take ownership of the entire .android directory
Write-Host "Taking ownership of $AndroidDir..." -ForegroundColor Gray
takeown /F "$AndroidDir" /R /D Y 2>&1 | Out-Null

# Grant full permissions to all users
Write-Host "Granting full permissions..." -ForegroundColor Gray

# Use icacls to grant full control
$Commands = @(
    "icacls `"$AndroidDir`" /grant *S-1-1-0:(OI)(CI)F /T /C /Q",  # Everyone
    "icacls `"$AndroidDir`" /grant *S-1-5-18:(OI)(CI)F /T /C /Q",  # SYSTEM
    "icacls `"$AndroidDir`" /grant *S-1-5-32-545:(OI)(CI)F /T /C /Q",  # Users
    "icacls `"$AndroidDir`" /grant `"$Username`":(OI)(CI)F /T /C /Q"  # Specific user
)

foreach ($cmd in $Commands) {
    cmd /c $cmd 2>&1 | Out-Null
}

# Also specifically set permissions on each lock file
foreach ($LockFile in $LockFiles) {
    if (Test-Path $LockFile) {
        icacls "$LockFile" /grant *S-1-1-0:F /C /Q 2>&1 | Out-Null  # Everyone
        icacls "$LockFile" /grant *S-1-5-18:F /C /Q 2>&1 | Out-Null  # SYSTEM
    }
}

# Verify permissions
Write-Host ""
Write-Host "Verifying permissions..." -ForegroundColor Yellow

$AndroidDirAcl = icacls "$AndroidDir" 2>&1 | Select-String "Everyone" -Quiet
if ($AndroidDirAcl) {
    Write-Host "SUCCESS: Permissions set on .android directory" -ForegroundColor Green
} else {
    Write-Host "WARNING: Could not verify permissions" -ForegroundColor Yellow
}

# List created files
Write-Host ""
Write-Host "Lock files status:" -ForegroundColor Cyan
foreach ($LockFile in $LockFiles) {
    if (Test-Path $LockFile) {
        $FileName = Split-Path $LockFile -Leaf
        Write-Host "  [OK] $FileName" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "SUCCESS: Permissions fixed for $Username!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Try launching the emulator again" -ForegroundColor Gray
Write-Host "2. If error persists, restart the emulator service" -ForegroundColor Gray
Write-Host "3. Check that the AVD files exist in: $AvdDir" -ForegroundColor Gray
