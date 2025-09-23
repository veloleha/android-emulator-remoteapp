# Add User1 to proper groups

Write-Host "Adding User1 to groups..." -ForegroundColor Yellow

# Get all group names
$AllGroups = Get-LocalGroup | Select-Object -ExpandProperty Name
Write-Host "Found groups:" -ForegroundColor Cyan
$AllGroups | ForEach-Object { Write-Host "- $_" }

Write-Host ""

# Find Users group (different possible names)
$UsersGroup = $AllGroups | Where-Object { 
    $_ -eq "Пользователи" -or 
    $_ -eq "Users" -or 
    $_ -like "*пользователи*" 
} | Select-Object -First 1

if ($UsersGroup) {
    try {
        Add-LocalGroupMember -Group $UsersGroup -Member "User1" -ErrorAction Stop
        Write-Host "Added to Users group: $UsersGroup" -ForegroundColor Green
    } catch {
        Write-Host "Failed to add to Users group: $($_.Exception.Message)" -ForegroundColor Red
    }
} else {
    Write-Host "Users group not found" -ForegroundColor Red
}

# Find RDP group (different possible names)
$RDPGroup = $AllGroups | Where-Object { 
    $_ -eq "Пользователи удаленного рабочего стола" -or 
    $_ -eq "Remote Desktop Users" -or 
    $_ -like "*удаленного*" -or
    $_ -like "*remote*desktop*"
} | Select-Object -First 1

if ($RDPGroup) {
    try {
        Add-LocalGroupMember -Group $RDPGroup -Member "User1" -ErrorAction Stop
        Write-Host "Added to RDP group: $RDPGroup" -ForegroundColor Green
    } catch {
        Write-Host "Failed to add to RDP group: $($_.Exception.Message)" -ForegroundColor Red
    }
} else {
    Write-Host "RDP group not found" -ForegroundColor Red
}

Write-Host ""
Write-Host "User1 groups:" -ForegroundColor Cyan
$UserGroups = @()
Get-LocalGroup | ForEach-Object {
    $GroupName = $_.Name
    $GroupMembers = Get-LocalGroupMember -Group $GroupName -ErrorAction SilentlyContinue
    if ($GroupMembers | Where-Object Name -like "*User1*") {
        $UserGroups += $GroupName
    }
}

if ($UserGroups.Count -gt 0) {
    $UserGroups | ForEach-Object { Write-Host "- $_" -ForegroundColor Green }
} else {
    Write-Host "No groups found for User1" -ForegroundColor Yellow
}
