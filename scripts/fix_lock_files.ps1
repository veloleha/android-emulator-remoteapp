# Fix Android emulator lock files permissions
# This script creates and sets permissions for lock files to prevent access errors

param(
    [string]$Username = ""
)

Write-Host "=== FIXING ANDROID EMULATOR LOCK FILES ===" -ForegroundColor Yellow

# If username not provided, find the last user
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

# Determine user profile path (with .HP support)
$UserProfilePath = "C:\Users\$Username"
$UserProfilePathHP = "C:\Users\$Username.HP"
$ActualUserProfile = if (Test-Path $UserProfilePathHP) { $UserProfilePathHP } else { $UserProfilePath }

Write-Host "User profile: $ActualUserProfile" -ForegroundColor Cyan

# Create .android directory if not exists
$AndroidDir = "$ActualUserProfile\.android"
if (!(Test-Path $AndroidDir)) {
    New-Item -ItemType Directory -Path $AndroidDir -Force | Out-Null
    Write-Host "Created directory: $AndroidDir" -ForegroundColor Gray
}

# List of lock files that need to be created
$LockFiles = @(
    "$AndroidDir\emu-last-feature-flags.protobuf",
    "$AndroidDir\emu-last-feature-flags.protobuf.lock",
    "$AndroidDir\emulator-check.exe.lock",
    "$AndroidDir\pid.lock",
    "$AndroidDir\cache.lock"
)

Write-Host ""
Write-Host "Creating and fixing lock files..." -ForegroundColor Yellow

foreach ($LockFile in $LockFiles) {
    try {
        # Create file if not exists
        if (!(Test-Path $LockFile)) {
            New-Item -ItemType File -Path $LockFile -Force | Out-Null
            Write-Host "Created: $LockFile" -ForegroundColor Green
        } else {
            Write-Host "Exists: $LockFile" -ForegroundColor Gray
        }
        
        # Set full permissions for Everyone
        $acl = Get-Acl $LockFile
        
        # Remove inheritance
        $acl.SetAccessRuleProtection($true, $false)
        
        # Clear existing permissions
        $acl.Access | ForEach-Object { $acl.RemoveAccessRule($_) | Out-Null }
        
        # Add full control for Everyone
        $permission = "Everyone", "FullControl", "Allow"
        $accessRule = New-Object System.Security.AccessControl.FileSystemAccessRule $permission
        $acl.SetAccessRule($accessRule)
        
        # Add full control for SYSTEM
        $permission = "SYSTEM", "FullControl", "Allow"
        $accessRule = New-Object System.Security.AccessControl.FileSystemAccessRule $permission
        $acl.SetAccessRule($accessRule)
        
        # Add full control for the specific user
        $permission = "$Username", "FullControl", "Allow"
        $accessRule = New-Object System.Security.AccessControl.FileSystemAccessRule $permission
        $acl.SetAccessRule($accessRule)
        
        # Apply the ACL
        Set-Acl -Path $LockFile -AclObject $acl
        
        Write-Host "  Permissions set: Everyone, SYSTEM, $Username" -ForegroundColor Gray
        
    } catch {
        Write-Host "WARNING: Could not process $LockFile : $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

# Also set permissions on the entire .android directory
Write-Host ""
Write-Host "Setting permissions on .android directory..." -ForegroundColor Yellow

try {
    # Using icacls for directory permissions (more reliable)
    icacls $AndroidDir /grant "Everyone:(OI)(CI)F" /T /Q | Out-Null
    icacls $AndroidDir /grant "SYSTEM:(OI)(CI)F" /T /Q | Out-Null
    icacls $AndroidDir /grant "${Username}:(OI)(CI)F" /T /Q | Out-Null
    icacls $AndroidDir /grant "Users:(OI)(CI)F" /T /Q | Out-Null
    
    Write-Host "Directory permissions set successfully" -ForegroundColor Green
} catch {
    Write-Host "WARNING: Could not set directory permissions: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Create avd directory if not exists
$AvdDir = "$AndroidDir\avd"
if (!(Test-Path $AvdDir)) {
    New-Item -ItemType Directory -Path $AvdDir -Force | Out-Null
    Write-Host "Created AVD directory: $AvdDir" -ForegroundColor Gray
    
    # Set permissions on avd directory
    icacls $AvdDir /grant "Everyone:(OI)(CI)F" /T /Q | Out-Null
    icacls $AvdDir /grant "SYSTEM:(OI)(CI)F" /T /Q | Out-Null
    icacls $AvdDir /grant "${Username}:(OI)(CI)F" /T /Q | Out-Null
}

Write-Host ""
Write-Host "SUCCESS: Lock files fixed for user $Username" -ForegroundColor Green
Write-Host "Profile: $ActualUserProfile" -ForegroundColor Cyan
Write-Host ""
Write-Host "Lock files created and permissions set:" -ForegroundColor Gray
foreach ($LockFile in $LockFiles) {
    if (Test-Path $LockFile) {
        $FileInfo = Get-Item $LockFile
        Write-Host "  - $(Split-Path $LockFile -Leaf) ($($FileInfo.Length) bytes)" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "The emulator should now start without lock file errors!" -ForegroundColor Green
