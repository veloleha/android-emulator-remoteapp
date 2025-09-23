# Fix RemoteApp Connection Issues
# Исправление проблем с подключением RemoteApp

Write-Host "=== FIXING REMOTEAPP CONNECTION ISSUES ===" -ForegroundColor Cyan

# Check if running as administrator
$IsAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
if (-not $IsAdmin) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Please restart PowerShell as Administrator and try again." -ForegroundColor Yellow
    exit 1
}

Write-Host "Fixing RemoteApp connection issues..." -ForegroundColor Yellow

try {
    # 1. Enable Terminal Services
    Write-Host "1. Enabling Terminal Services..." -ForegroundColor Yellow
    Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server" -Name "fDenyTSConnections" -Value 0 -Force
    Write-Host "   Terminal Services enabled" -ForegroundColor Green
    
    # 2. Allow multiple sessions
    Write-Host "2. Configuring multiple sessions..." -ForegroundColor Yellow
    Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server" -Name "fSingleSessionPerUser" -Value 0 -Force
    Write-Host "   Multiple sessions allowed" -ForegroundColor Green
    
    # 3. Enable RemoteApp
    Write-Host "3. Enabling RemoteApp..." -ForegroundColor Yellow
    $TSAppAllowListPath = "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Terminal Server\TSAppAllowList"
    Set-ItemProperty -Path $TSAppAllowListPath -Name "fDisabledAllowList" -Value 0 -Force
    Write-Host "   RemoteApp enabled" -ForegroundColor Green
    
    # 4. Configure RDP-Tcp settings
    Write-Host "4. Configuring RDP-Tcp settings..." -ForegroundColor Yellow
    $RDPTcpPath = "HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp"
    
    # Create RDP-Tcp key if it doesn't exist
    if (!(Test-Path $RDPTcpPath)) {
        New-Item -Path $RDPTcpPath -Force | Out-Null
        Write-Host "   Created RDP-Tcp registry key" -ForegroundColor Gray
    }
    
    # Set RDP-Tcp properties
    Set-ItemProperty -Path $RDPTcpPath -Name "fEnableWinStation" -Value 1 -Force
    Set-ItemProperty -Path $RDPTcpPath -Name "MaxConnectionTime" -Value 0 -Force
    Set-ItemProperty -Path $RDPTcpPath -Name "MaxDisconnectionTime" -Value 0 -Force
    Set-ItemProperty -Path $RDPTcpPath -Name "MaxIdleTime" -Value 0 -Force
    Set-ItemProperty -Path $RDPTcpPath -Name "fInheritMaxSessionTime" -Value 0 -Force
    Set-ItemProperty -Path $RDPTcpPath -Name "fReconnectSame" -Value 0 -Force
    Write-Host "   RDP-Tcp settings configured" -ForegroundColor Green
    
    # 5. Configure audio settings
    Write-Host "5. Configuring audio settings..." -ForegroundColor Yellow
    Set-ItemProperty -Path $RDPTcpPath -Name "fDisableAudioCapture" -Value 0 -Force -ErrorAction SilentlyContinue
    Write-Host "   Audio capture enabled" -ForegroundColor Green
    
    # 6. Configure licensing mode
    Write-Host "6. Configuring licensing mode..." -ForegroundColor Yellow
    $LicensingPath = "HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server\RCM\Licensing Core"
    if (!(Test-Path $LicensingPath)) {
        New-Item -Path $LicensingPath -Force | Out-Null
    }
    Set-ItemProperty -Path $LicensingPath -Name "LicensingMode" -Value 4 -Force -ErrorAction SilentlyContinue
    Write-Host "   Licensing mode set to Per Device" -ForegroundColor Green
    
    # 7. Restart Terminal Services
    Write-Host "7. Restarting Terminal Services..." -ForegroundColor Yellow
    try {
        Restart-Service -Name "TermService" -Force
        Write-Host "   Terminal Services restarted" -ForegroundColor Green
    } catch {
        Write-Host "   Warning: Could not restart Terminal Services automatically" -ForegroundColor Yellow
        Write-Host "   Please restart manually or reboot the server" -ForegroundColor Yellow
    }
    
    # 8. Enable Windows Firewall rules for RDP
    Write-Host "8. Configuring Windows Firewall..." -ForegroundColor Yellow
    try {
        Enable-NetFirewallRule -DisplayGroup "Remote Desktop" -ErrorAction SilentlyContinue
        Write-Host "   Windows Firewall rules enabled for RDP" -ForegroundColor Green
    } catch {
        Write-Host "   Warning: Could not configure firewall rules" -ForegroundColor Yellow
    }
    
    # 9. Verify RemoteApp application exists
    Write-Host "9. Verifying RemoteApp application..." -ForegroundColor Yellow
    $AppName = "User2AndroidEmulator"
    $AppPath = "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Terminal Server\TSAppAllowList\Applications\$AppName"
    
    if (Test-Path $AppPath) {
        $AppSettings = Get-ItemProperty -Path $AppPath
        Write-Host "   RemoteApp found: $($AppSettings.Name)" -ForegroundColor Green
        Write-Host "   Command: $($AppSettings.RequiredCommandLine)" -ForegroundColor Gray
    } else {
        Write-Host "   ERROR: RemoteApp not found: $AppName" -ForegroundColor Red
        Write-Host "   Please run RemoteApp configuration step first" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "=== REMOTEAPP FIXES APPLIED ===" -ForegroundColor Cyan
    Write-Host "SUCCESS: All RemoteApp fixes have been applied!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Wait 30 seconds for services to stabilize" -ForegroundColor Gray
    Write-Host "2. Try connecting with RDP file again" -ForegroundColor Gray
    Write-Host "3. If still issues, reboot the server" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Troubleshooting tips:" -ForegroundColor Yellow
    Write-Host "- Make sure User2 password is correct" -ForegroundColor Gray
    Write-Host "- Try connecting from different client machine" -ForegroundColor Gray
    Write-Host "- Check if console session is logged out" -ForegroundColor Gray
    
} catch {
    Write-Host "ERROR: Failed to apply fixes: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=== REMOTEAPP FIXES COMPLETE ===" -ForegroundColor Cyan
