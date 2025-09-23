# Find groups by well-known SIDs

Write-Host "Finding groups by SID..." -ForegroundColor Yellow

# Well-known SIDs for standard groups
$WellKnownSIDs = @{
    "S-1-5-32-545" = "Users"
    "S-1-5-32-555" = "Remote Desktop Users"
    "S-1-5-32-544" = "Administrators"
}

Write-Host "Searching for standard Windows groups:" -ForegroundColor Cyan

foreach ($SID in $WellKnownSIDs.Keys) {
    try {
        $Group = Get-LocalGroup -SID $SID -ErrorAction Stop
        $ExpectedName = $WellKnownSIDs[$SID]
        Write-Host "Found $ExpectedName group: $($Group.Name)" -ForegroundColor Green
        
        # Try to add User1 to this group
        if ($ExpectedName -eq "Users" -or $ExpectedName -eq "Remote Desktop Users") {
            try {
                Add-LocalGroupMember -Group $Group.Name -Member "User1" -ErrorAction Stop
                Write-Host "Successfully added User1 to: $($Group.Name)" -ForegroundColor Green
            } catch {
                if ($_.Exception.Message -like "*already a member*" -or $_.Exception.Message -like "*уже является*") {
                    Write-Host "User1 is already a member of: $($Group.Name)" -ForegroundColor Yellow
                } else {
                    Write-Host "Failed to add User1 to $($Group.Name): $($_.Exception.Message)" -ForegroundColor Red
                }
            }
        }
    } catch {
        Write-Host "Group with SID $SID not found" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Final check - User1 groups:" -ForegroundColor Cyan
$UserGroups = @()

# Check each well-known group
foreach ($SID in $WellKnownSIDs.Keys) {
    try {
        $Group = Get-LocalGroup -SID $SID -ErrorAction Stop
        $Members = Get-LocalGroupMember -Group $Group.Name -ErrorAction SilentlyContinue
        if ($Members | Where-Object Name -like "*User1*") {
            $UserGroups += $Group.Name
        }
    } catch {
        # Group not found, skip
    }
}

if ($UserGroups.Count -gt 0) {
    $UserGroups | ForEach-Object { Write-Host "- $_" -ForegroundColor Green }
} else {
    Write-Host "No standard groups found for User1" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "User1 details:" -ForegroundColor Cyan
Get-LocalUser -Name "User1" | Select-Object Name, Enabled, Description, PasswordRequired, UserMayChangePassword | Format-List
