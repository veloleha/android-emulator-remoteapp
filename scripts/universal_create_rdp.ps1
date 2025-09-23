# Universal RDP File Creation Script
# Step 6: Creating RDP file for RemoteApp connection

Write-Host "=== UNIVERSAL RDP FILE CREATION ===" -ForegroundColor Cyan

# Find last created user and corresponding RemoteApp
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
$RdpFilePath = "C:\Scripts\${TestUser}_emulator.rdp"

# Get server IP address automatically
try {
    $ServerAddress = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -ne "127.0.0.1" -and $_.PrefixOrigin -eq "Dhcp"} | Select-Object -First 1).IPAddress
    if (-not $ServerAddress) {
        $ServerAddress = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -ne "127.0.0.1"} | Select-Object -First 1).IPAddress
    }
    if (-not $ServerAddress) {
        $ServerAddress = "localhost"
    }
} catch {
    $ServerAddress = "localhost"
}

Write-Host "Creating RDP file for RemoteApp connection..." -ForegroundColor Yellow
Write-Host "User: $TestUser" -ForegroundColor White
Write-Host "App Name: $AppName" -ForegroundColor White
Write-Host "RDP File: $RdpFilePath" -ForegroundColor White
Write-Host "Server Address: $ServerAddress" -ForegroundColor White

# Verify RemoteApp exists in registry
$RemoteAppPath = "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Terminal Server\TSAppAllowList\Applications\$AppName"
if (!(Test-Path $RemoteAppPath)) {
    Write-Host "ERROR: RemoteApp not found in registry: $AppName" -ForegroundColor Red
    Write-Host "Please run RemoteApp configuration step first" -ForegroundColor Yellow
    exit 1
}

# Get user password (for convenience, though user will be prompted)
try {
    $UserInfo = Get-LocalUser -Name $TestUser
    Write-Host "User found: $($UserInfo.Name) (Enabled: $($UserInfo.Enabled))" -ForegroundColor Gray
} catch {
    Write-Host "Warning: Could not get user info" -ForegroundColor Yellow
}

# Create RDP content with optimized settings for Android Emulator
$RdpContent = @"
full address:s:$ServerAddress`:3389
remoteapplicationmode:i:1
remoteapplicationname:s:$AppName
remoteapplicationprogram:s:||$AppName
alternate shell:s:rdpinit.exe
disableremoteappcapscheck:i:1
prompt for credentials on client:i:1
username:s:$TestUser
audiomode:i:0
audioqualitymode:i:2
audiocapturemode:i:1
microphone redirection:i:1
audio redirection:i:0
compression:i:1
bitmapcachepersistenable:i:1
videomode:i:32
session bpp:i:32
desktopwidth:i:1280
desktopheight:i:720
allow font smoothing:i:1
disable wallpaper:i:0
disable full window drag:i:0
disable menu anims:i:0
disable themes:i:0
disable cursor setting:i:0
bitmapcachesize:i:1500
experience:i:0
connection type:i:7
networkautodetect:i:1
bandwidthautodetect:i:1
enablecredsspsupport:i:1
authentication level:i:2
gatewayusagemethod:i:0
gatewayprofileusagemethod:i:0
gatewaycredentialssource:i:0
use redirection server name:i:0
rdgiskdcproxy:i:0
kdcproxyname:s:
drivestoredirect:s:
devicestoredirect:s:
winposstr:s:0,1,0,0,800,600
"@

try {
    # Remove existing RDP file if it exists
    if (Test-Path $RdpFilePath) {
        Remove-Item $RdpFilePath -Force
        Write-Host "Removed existing RDP file" -ForegroundColor Gray
    }
    
    # Create RDP file
    Set-Content -Path $RdpFilePath -Value $RdpContent -Encoding UTF8
    Write-Host "SUCCESS: RDP file created!" -ForegroundColor Green
    
    # Verify file creation
    if (Test-Path $RdpFilePath) {
        $FileInfo = Get-Item $RdpFilePath
        $FileContent = Get-Content $RdpFilePath
        
        Write-Host "File created successfully:" -ForegroundColor Gray
        Write-Host "  Path: $RdpFilePath" -ForegroundColor Gray
        Write-Host "  Size: $($FileInfo.Length) bytes" -ForegroundColor Gray
        Write-Host "  Lines: $($FileContent.Count)" -ForegroundColor Gray
        
        # Validate key settings
        $ServerLine = $FileContent | Where-Object {$_ -like "full address:*"}
        $AppLine = $FileContent | Where-Object {$_ -like "remoteapplicationname:*"}
        $UserLine = $FileContent | Where-Object {$_ -like "username:*"}
        $MicLine = $FileContent | Where-Object {$_ -like "microphone redirection:*"}
        
        Write-Host ""
        Write-Host "Key Settings Validation:" -ForegroundColor Yellow
        Write-Host "  Server: $ServerLine" -ForegroundColor Gray
        Write-Host "  Application: $AppLine" -ForegroundColor Gray
        Write-Host "  Username: $UserLine" -ForegroundColor Gray
        Write-Host "  Microphone: $MicLine" -ForegroundColor Gray
        
        # Test RDP file syntax
        Write-Host ""
        Write-Host "Testing RDP file syntax..." -ForegroundColor Yellow
        try {
            # Try to parse RDP file (basic validation)
            $RdpLines = $FileContent | Where-Object {$_ -match "^[^:]+:[si]:.+$"}
            Write-Host "Valid RDP lines: $($RdpLines.Count)" -ForegroundColor Green
            
            if ($RdpLines.Count -gt 20) {
                Write-Host "RDP file syntax: OK" -ForegroundColor Green
            } else {
                Write-Host "RDP file syntax: Warning (few valid lines)" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "RDP file syntax: Warning (validation failed)" -ForegroundColor Yellow
        }
        
        Write-Host ""
        Write-Host "=== RDP FILE CREATION RESULT ===" -ForegroundColor Cyan
        Write-Host "USER: $TestUser" -ForegroundColor White
        Write-Host "APP NAME: $AppName" -ForegroundColor White
        Write-Host "RDP FILE: $RdpFilePath" -ForegroundColor White
        Write-Host "SERVER: $ServerAddress:3389" -ForegroundColor White
        Write-Host "MICROPHONE: Enabled" -ForegroundColor White
        Write-Host "SUCCESS: RDP file ready for connection!" -ForegroundColor Green
        
        Write-Host ""
        Write-Host "Usage Instructions:" -ForegroundColor Yellow
        Write-Host "1. Copy RDP file to client machine" -ForegroundColor Gray
        Write-Host "2. Double-click RDP file to connect" -ForegroundColor Gray
        Write-Host "3. Enter password when prompted" -ForegroundColor Gray
        Write-Host "4. Android Emulator should start automatically" -ForegroundColor Gray
        
    } else {
        Write-Host "ERROR: RDP file was not created" -ForegroundColor Red
        exit 1
    }
    
} catch {
    Write-Host "ERROR: RDP file creation failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=== RDP FILE CREATION COMPLETE ===" -ForegroundColor Cyan
