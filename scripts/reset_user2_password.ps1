# Reset User2 Password to Known Value
# Сброс пароля User2 на известное значение

Write-Host "=== RESETTING USER2 PASSWORD ===" -ForegroundColor Cyan

# Check if running as administrator
$IsAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
if (-not $IsAdmin) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    exit 1
}

# Set simple password for User2
$NewPassword = "Android123!"
$SecurePassword = ConvertTo-SecureString $NewPassword -AsPlainText -Force

try {
    # Reset User2 password
    Set-LocalUser -Name "User2" -Password $SecurePassword
    Write-Host "SUCCESS: User2 password has been reset!" -ForegroundColor Green
    
    Write-Host ""
    Write-Host "=== USER2 LOGIN CREDENTIALS ===" -ForegroundColor Cyan
    Write-Host "USERNAME: User2" -ForegroundColor White
    Write-Host "PASSWORD: $NewPassword" -ForegroundColor White
    Write-Host ""
    
} catch {
    Write-Host "ERROR: Failed to reset password: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host "=== PASSWORD RESET COMPLETE ===" -ForegroundColor Cyan
