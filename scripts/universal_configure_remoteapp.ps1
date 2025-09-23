# Universal RemoteApp Configuration Script
# Step 5: Configuring RemoteApp in Windows Registry

Write-Host "=== UNIVERSAL REMOTEAPP CONFIGURATION ===" -ForegroundColor Cyan

# Check if running as administrator
$IsAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
if (-not $IsAdmin) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Please restart PowerShell as Administrator and try again." -ForegroundColor Yellow
    exit 1
}

# Find last created user and corresponding executable
$UserNumber = 1
$LastValidUser = $null
do {
    $TestUser = "User$UserNumber"
    $UserExists = Get-LocalUser -Name $TestUser -ErrorAction SilentlyContinue
    if ($UserExists) {
        $LastValidUser = $TestUser
        $UserNumber++
    }
} while ($UserExists)

if (-not $LastValidUser) {
    Write-Host "ERROR: No users found. Please create a user first." -ForegroundColor Red
    exit 1
}

$TestUser = $LastValidUser
$AppName = "${TestUser}AndroidEmulator"
$ExePath = "C:\Scripts\${TestUser}_emulator_wrapper.ps1"
$RemoteAppPath = "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Terminal Server\TSAppAllowList\Applications"

Write-Host "Configuring RemoteApp in Windows Registry..." -ForegroundColor Yellow
Write-Host "User: $TestUser" -ForegroundColor White
Write-Host "App Name: $AppName" -ForegroundColor White
Write-Host "Executable: $ExePath" -ForegroundColor White

# Check if executable exists
if (!(Test-Path $ExePath)) {
    Write-Host "ERROR: Executable file not found: $ExePath" -ForegroundColor Red
    Write-Host "Please run EXE conversion step first" -ForegroundColor Yellow
    exit 1
}

try {
    # Enable Terminal Services
    Write-Host "Enabling Terminal Services..." -ForegroundColor Yellow
    Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server" -Name "fDenyTSConnections" -Value 0 -Force
    
    # Create registry path if it doesn't exist
    if (!(Test-Path $RemoteAppPath)) {
        New-Item -Path $RemoteAppPath -Force | Out-Null
        Write-Host "Created registry path: $RemoteAppPath" -ForegroundColor Gray
    }
    
    # Create application entry
    $AppKeyPath = "$RemoteAppPath\$AppName"
    if (Test-Path $AppKeyPath) {
        Remove-Item -Path $AppKeyPath -Recurse -Force
        Write-Host "Removed existing application entry" -ForegroundColor Gray
    }
    
    New-Item -Path $AppKeyPath -Force | Out-Null
    Write-Host "Created application entry: $AppKeyPath" -ForegroundColor Gray
    
    # Set application properties
    Set-ItemProperty -Path $AppKeyPath -Name "Name" -Value $AppName -Force
    Set-ItemProperty -Path $AppKeyPath -Name "Path" -Value "powershell.exe" -Force
    Set-ItemProperty -Path $AppKeyPath -Name "CommandLineSetting" -Value 1 -Force
    Set-ItemProperty -Path $AppKeyPath -Name "RequiredCommandLine" -Value "-ExecutionPolicy Bypass -File `"$ExePath`"" -Force
    Set-ItemProperty -Path $AppKeyPath -Name "ShowInTSWA" -Value 1 -Force
    Set-ItemProperty -Path $AppKeyPath -Name "IconPath" -Value "powershell.exe" -Force
    Set-ItemProperty -Path $AppKeyPath -Name "IconIndex" -Value 0 -Force
    
    Write-Host "Set application properties:" -ForegroundColor Gray
    Write-Host "  Name: $AppName" -ForegroundColor Gray
    Write-Host "  Path: powershell.exe" -ForegroundColor Gray
    Write-Host "  CommandLine: -ExecutionPolicy Bypass -File `"$ExePath`"" -ForegroundColor Gray
    
    # Enable RemoteApp (disable block list)
    $TSAppAllowListPath = "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Terminal Server\TSAppAllowList"
    Set-ItemProperty -Path $TSAppAllowListPath -Name "fDisabledAllowList" -Value 0 -Force
    Write-Host "Enabled RemoteApp (disabled block list)" -ForegroundColor Gray
    
    # Configure additional RemoteApp settings
    Write-Host "Configuring additional RemoteApp settings..." -ForegroundColor Yellow
    
    # Allow RemoteApp programs
    Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Terminal Server" -Name "fAllowToGetHelp" -Value 1 -Force
    
    # Configure audio redirection
    Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Terminal Server\WinStations\RDP-Tcp" -Name "fDisableAudioCapture" -Value 0 -Force
    Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Terminal Server\WinStations\RDP-Tcp" -Name "MaxConnectionTime" -Value 0 -Force
    Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Terminal Server\WinStations\RDP-Tcp" -Name "MaxDisconnectionTime" -Value 0 -Force
    
    Write-Host "Configured audio redirection settings" -ForegroundColor Gray
    
    # Verify configuration
    Write-Host "Verifying RemoteApp configuration..." -ForegroundColor Yellow
    $AppSettings = Get-ItemProperty -Path $AppKeyPath
    $TSSettings = Get-ItemProperty -Path $TSAppAllowListPath
    
    Write-Host "SUCCESS: RemoteApp configured in registry!" -ForegroundColor Green
    
    Write-Host ""
    Write-Host "=== REMOTEAPP CONFIGURATION RESULT ===" -ForegroundColor Cyan
    Write-Host "USER: $TestUser" -ForegroundColor White
    Write-Host "APP NAME: $AppName" -ForegroundColor White
    Write-Host "EXECUTABLE: $ExePath" -ForegroundColor White
    Write-Host "REGISTRY PATH: $AppKeyPath" -ForegroundColor White
    
    Write-Host ""
    Write-Host "Application Settings:" -ForegroundColor Gray
    Write-Host "  Name: $($AppSettings.Name)" -ForegroundColor Gray
    Write-Host "  Path: $($AppSettings.Path)" -ForegroundColor Gray
    Write-Host "  CommandLine: $($AppSettings.RequiredCommandLine)" -ForegroundColor Gray
    Write-Host "  ShowInTSWA: $($AppSettings.ShowInTSWA)" -ForegroundColor Gray
    Write-Host "  Block List Disabled: $($TSSettings.fDisabledAllowList -eq 0)" -ForegroundColor Gray
    
    Write-Host ""
    Write-Host "SUCCESS: RemoteApp ready for RDP file generation!" -ForegroundColor Green
    
} catch {
    Write-Host "ERROR: RemoteApp configuration failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Make sure the script is running as Administrator" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "=== REMOTEAPP CONFIGURATION COMPLETE ===" -ForegroundColor Cyan
