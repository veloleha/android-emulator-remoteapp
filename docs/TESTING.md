# Android Emulator RemoteApp Testing Guide

## Overview
This guide provides comprehensive testing procedures for the Android Emulator RemoteApp automation system, including troubleshooting steps for the microphone cutoff issue.

## Prerequisites

### Required Software
- Windows 10 LTSC (version 1809 or later)
- Android SDK installed at `C:\Program Files\Android`
- PHP web server (IIS, Apache, or built-in PHP server)
- Bat To Exe Converter at `C:\Program Files\BatToExe\BatToExeConverter.exe`
- RDP Wrapper configured for multiple sessions

### Required Permissions
- Administrator privileges on the server
- Remote Desktop Services configured
- Terminal Services licensing (if required)

## Pre-Testing Setup

### 1. Verify Android SDK Installation
```powershell
# Check if Android SDK tools exist
Test-Path "C:\Program Files\Android\cmdline-tools\latest\bin\avdmanager.bat"
Test-Path "C:\Program Files\Android\emulator\emulator.exe"

# If not found, install Android SDK command-line tools
```

### 2. Configure PowerShell Execution Policy
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope LocalMachine
```

### 3. Create Required Directories
```powershell
New-Item -ItemType Directory -Path "C:\Scripts" -Force
New-Item -ItemType Directory -Path "C:\Scripts\downloads" -Force
```

### 4. Apply Group Policy Settings
```powershell
# Run as Administrator
C:\emulator\ConfigureGroupPolicy.ps1
```

## Testing Procedures

### Phase 1: PowerShell Script Testing

#### Test 1: Manual PowerShell Execution
```powershell
# Navigate to script directory
cd C:\emulator

# Execute the main script
.\AndroidEmulatorSetup.ps1

# Expected output:
# - User creation confirmation
# - AVD creation progress
# - Batch file generation
# - EXE conversion success
# - Registry configuration
# - RDP file creation
```

**Success Criteria:**
- Script completes without errors
- New user appears in Local Users and Groups
- AVD is created in `%USERPROFILE%\.android\avd\`
- EXE file is generated in `C:\Scripts\`
- RDP file is created in `C:\Scripts\`

#### Test 2: Log File Verification
```powershell
# Check log file for errors
Get-Content "C:\Scripts\log.txt" | Select-String "ERROR"

# Review complete log
notepad "C:\Scripts\log.txt"
```

### Phase 2: Web Interface Testing

#### Test 3: PHP Web Interface
1. Start web server:
   ```cmd
   # Using PHP built-in server
   cd C:\emulator\сайт
   php -S localhost:8080
   ```

2. Access web interface: `http://localhost:8080`

3. Login with credentials:
   - Username: `admin`
   - Password: `admin123` (change in production!)

4. Click "Create Emulator Session"

**Success Criteria:**
- Login successful
- Setup process initiates
- User credentials displayed
- RDP file download available

### Phase 3: RemoteApp Testing

#### Test 4: Registry Verification
```powershell
# Check RemoteApp registry entries
Get-ChildItem "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Terminal Server\TSAppAllowList\Applications"

# Verify specific application entry
$AppName = "AndroidEmulator_[USERNAME]"  # Replace with actual username
Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Terminal Server\TSAppAllowList\Applications\$AppName"
```

#### Test 5: RDP Connection Test
1. Download RDP file from web interface
2. Double-click RDP file to launch connection
3. Enter user credentials when prompted
4. Verify Android emulator launches in RemoteApp mode

**Success Criteria:**
- RDP connection establishes successfully
- Android emulator starts within RemoteApp window
- Emulator is responsive and functional

### Phase 4: Microphone Testing

#### Test 6: Audio Device Verification
1. Connect to RemoteApp session
2. Open Android emulator
3. Launch voice recorder app or Google Assistant
4. Test microphone input for more than 3 seconds

**Success Criteria:**
- Microphone input detected
- Audio recording continues beyond 3 seconds
- No audio cutoff occurs

#### Test 7: Audio Settings Verification
```powershell
# Check RDP audio settings
Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp" | Select-Object fDisableAudioCapture

# Check Terminal Services policies
Get-ItemProperty "HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\Terminal Services" | Select-Object fDisableAudioCapture, MaxConnectionTime, MaxIdleTime
```

## Troubleshooting

### Issue 1: PowerShell Script Fails

**Symptoms:**
- Script exits with errors
- User creation fails
- AVD creation fails

**Solutions:**
1. Run PowerShell as Administrator
2. Check Android SDK installation path
3. Verify Bat To Exe Converter installation
4. Review log file for specific errors

### Issue 2: Web Interface Not Accessible

**Symptoms:**
- 404 errors
- PHP errors
- Login failures

**Solutions:**
1. Verify web server is running
2. Check PHP configuration
3. Ensure correct file permissions
4. Review web server error logs

### Issue 3: RemoteApp Connection Fails

**Symptoms:**
- RDP connection refused
- Authentication failures
- RemoteApp not launching

**Solutions:**
1. Verify RDP Wrapper is installed and configured
2. Check Windows Firewall settings
3. Ensure Terminal Services are running
4. Verify user is in "Remote Desktop Users" group

### Issue 4: Microphone Cuts Off After 3 Seconds

**Symptoms:**
- Audio input stops after 3 seconds
- Microphone works in regular RDP but not RemoteApp

**Solutions:**
1. Apply Group Policy settings:
   ```powershell
   C:\emulator\ConfigureGroupPolicy.ps1
   ```

2. Restart Terminal Services:
   ```powershell
   Restart-Service TermService -Force
   ```

3. Check AVD audio configuration:
   - Ensure `hw.audioInput=yes` in AVD config
   - Verify emulator launches with `-audio-in on` flag

4. Registry fixes:
   ```powershell
   # Disable audio capture timeout
   Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\Terminal Services" -Name "MaxConnectionTime" -Value 0
   
   # Enable microphone redirection
   Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp" -Name "fDisableAudioCapture" -Value 0
   ```

5. Windows Audio Service:
   ```powershell
   # Ensure Windows Audio service is running
   Start-Service AudioSrv
   Set-Service AudioSrv -StartupType Automatic
   ```

### Issue 5: Android Emulator Performance Issues

**Symptoms:**
- Slow emulator startup
- Laggy interface
- High CPU usage

**Solutions:**
1. Enable hardware acceleration:
   - Ensure Intel HAXM or Hyper-V is installed
   - Verify `hw.gpu.mode=host` in AVD config

2. Optimize emulator parameters:
   ```batch
   emulator -avd phone1 -gpu host -memory 2048 -cores 2 -no-boot-anim
   ```

3. Adjust AVD settings:
   - Reduce `hw.ramSize` if host has limited RAM
   - Disable unnecessary features (camera, sensors)

## Performance Optimization

### Server-Side Optimizations
1. **CPU and Memory:**
   - Minimum 8GB RAM recommended
   - Multi-core CPU for better emulator performance

2. **Network:**
   - Gigabit network connection recommended
   - Low latency for better RemoteApp experience

3. **Storage:**
   - SSD storage for faster AVD loading
   - Adequate free space (10GB+ per AVD)

### Client-Side Optimizations
1. **RDP Client Settings:**
   - Use latest RDP client version
   - Enable hardware acceleration
   - Adjust display settings for performance

2. **Network:**
   - Stable internet connection
   - Low latency to server

## Security Considerations

### 1. Change Default Passwords
```php
// In index.php, change:
define('ADMIN_PASSWORD_HASH', password_hash('your_secure_password', PASSWORD_DEFAULT));
```

### 2. Implement HTTPS
- Configure SSL certificate
- Redirect HTTP to HTTPS
- Use secure session cookies

### 3. User Account Security
- Implement account lockout policies
- Use complex passwords for generated users
- Regular cleanup of temporary users

### 4. File Permissions
```powershell
# Secure script directory
icacls "C:\Scripts" /grant "Administrators:F" /inheritance:r
icacls "C:\Scripts" /grant "SYSTEM:F"
```

## Monitoring and Maintenance

### 1. Log Monitoring
```powershell
# Monitor logs for errors
Get-Content "C:\Scripts\log.txt" -Wait | Where-Object { $_ -match "ERROR" }
```

### 2. Disk Space Management
```powershell
# Clean up old AVDs and user accounts
# Implement automated cleanup script
```

### 3. Performance Monitoring
- Monitor CPU and memory usage
- Track RDP session counts
- Monitor network bandwidth

## Conclusion

This testing guide provides comprehensive procedures for validating the Android Emulator RemoteApp automation system. Follow each phase systematically and address any issues using the troubleshooting section.

For additional support, review the log files and system event logs for detailed error information.
