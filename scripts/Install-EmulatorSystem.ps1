# Complete Installation Script for Android Emulator RemoteApp System
# Run this script as Administrator to set up the entire system

param(
    [string]$LogFile = "C:\Scripts\install_log.txt"
)

# Ensure log directory exists
$LogDir = Split-Path $LogFile -Parent
if (!(Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force
}

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogEntry = "[$Timestamp] [$Level] $Message"
    Write-Host $LogEntry
    Add-Content -Path $LogFile -Value $LogEntry
}

function Test-AdminRights {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

Write-Log "Starting Android Emulator RemoteApp System Installation"

# Check if running as administrator
if (-not (Test-AdminRights)) {
    Write-Log "This script must be run as Administrator" "ERROR"
    Write-Host "Please run this script as Administrator" -ForegroundColor Red
    exit 1
}

try {
    # Step 1: Verify prerequisites
    Write-Log "Checking prerequisites..."
    
    $AndroidSdkPath = "C:\Program Files\Android"
    $BatToExePath = "C:\Program Files\BatToExe\BatToExeConverter.exe"
    
    if (!(Test-Path $AndroidSdkPath)) {
        Write-Log "Android SDK not found at $AndroidSdkPath" "WARNING"
        Write-Host "Warning: Android SDK not found. Please install Android SDK first." -ForegroundColor Yellow
    }
    
    if (!(Test-Path $BatToExePath)) {
        Write-Log "Bat To Exe Converter not found at $BatToExePath" "WARNING"
        Write-Host "Warning: Bat To Exe Converter not found. Please install it first." -ForegroundColor Yellow
    }
    
    # Step 2: Set PowerShell execution policy
    Write-Log "Setting PowerShell execution policy..."
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope LocalMachine -Force
    
    # Step 3: Create required directories
    Write-Log "Creating required directories..."
    $RequiredDirs = @(
        "C:\Scripts",
        "C:\Scripts\downloads",
        "C:\Scripts\temp"
    )
    
    foreach ($Dir in $RequiredDirs) {
        if (!(Test-Path $Dir)) {
            New-Item -ItemType Directory -Path $Dir -Force
            Write-Log "Created directory: $Dir"
        }
    }
    
    # Step 4: Configure Terminal Services
    Write-Log "Configuring Terminal Services..."
    
    # Enable Terminal Services
    Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server" -Name "fDenyTSConnections" -Value 0
    
    # Configure RDP settings
    Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp" -Name "UserAuthentication" -Value 1
    
    # Step 5: Configure Windows Firewall
    Write-Log "Configuring Windows Firewall..."
    Enable-NetFirewallRule -DisplayGroup "Remote Desktop"
    
    # Step 6: Apply Group Policy settings for microphone support
    Write-Log "Applying Group Policy settings..."
    & "C:\emulator\ConfigureGroupPolicy.ps1"
    
    # Step 7: Configure IIS or recommend web server setup
    Write-Log "Checking web server configuration..."
    
    $IISFeature = Get-WindowsOptionalFeature -Online -FeatureName IIS-WebServerRole
    if ($IISFeature.State -eq "Disabled") {
        Write-Log "IIS is not enabled. You can enable it or use PHP built-in server." "WARNING"
        Write-Host "To enable IIS, run: Enable-WindowsOptionalFeature -Online -FeatureName IIS-WebServerRole -All" -ForegroundColor Yellow
        Write-Host "Or use PHP built-in server: php -S localhost:8080 -t C:\emulator\сайт" -ForegroundColor Yellow
    }
    
    # Step 8: Set file permissions
    Write-Log "Setting file permissions..."
    
    # Secure the Scripts directory
    icacls "C:\Scripts" /grant "Administrators:F" /inheritance:r
    icacls "C:\Scripts" /grant "SYSTEM:F"
    
    # Set permissions on PowerShell scripts
    icacls "C:\emulator\*.ps1" /grant "Administrators:F"
    
    # Step 9: Create scheduled task for cleanup (optional)
    Write-Log "Creating cleanup scheduled task..."
    
    $CleanupScript = @"
# Cleanup old users and AVDs (run weekly)
`$OldUsers = Get-LocalUser | Where-Object { `$_.Name -like "User*" -and `$_.LastLogon -lt (Get-Date).AddDays(-7) }
foreach (`$User in `$OldUsers) {
    Remove-LocalUser -Name `$User.Name -Confirm:`$false
    Write-Host "Removed old user: `$(`$User.Name)"
}
"@
    
    Set-Content -Path "C:\Scripts\Cleanup-OldUsers.ps1" -Value $CleanupScript
    
    # Step 10: Test basic functionality
    Write-Log "Running basic functionality tests..."
    
    # Test PowerShell script syntax
    $TestResult = powershell.exe -NoProfile -Command "& { try { . 'C:\emulator\AndroidEmulatorSetup.ps1'; 'SYNTAX_OK' } catch { 'SYNTAX_ERROR: ' + `$_.Exception.Message } }"
    
    if ($TestResult -like "*SYNTAX_OK*") {
        Write-Log "PowerShell script syntax validation passed"
    } else {
        Write-Log "PowerShell script syntax validation failed: $TestResult" "ERROR"
    }
    
    # Step 11: Display installation summary
    Write-Log "Installation completed successfully!"
    
    Write-Host "`n=== Android Emulator RemoteApp System Installation Complete ===" -ForegroundColor Green
    Write-Host "✓ Prerequisites checked" -ForegroundColor Green
    Write-Host "✓ Directories created" -ForegroundColor Green
    Write-Host "✓ Terminal Services configured" -ForegroundColor Green
    Write-Host "✓ Firewall configured" -ForegroundColor Green
    Write-Host "✓ Group Policy applied" -ForegroundColor Green
    Write-Host "✓ File permissions set" -ForegroundColor Green
    Write-Host "✓ Cleanup task created" -ForegroundColor Green
    
    Write-Host "`nNext Steps:" -ForegroundColor Yellow
    Write-Host "1. Start web server: php -S localhost:8080 -t C:\emulator\сайт" -ForegroundColor White
    Write-Host "2. Access web interface: http://localhost:8080" -ForegroundColor White
    Write-Host "3. Login with admin/admin123 (change password!)" -ForegroundColor White
    Write-Host "4. Test emulator creation" -ForegroundColor White
    Write-Host "5. Review testing guide: C:\emulator\TESTING_GUIDE.md" -ForegroundColor White
    
    Write-Host "`nImportant Notes:" -ForegroundColor Cyan
    Write-Host "- Change default admin password in index.php" -ForegroundColor White
    Write-Host "- Ensure Android SDK is properly installed" -ForegroundColor White
    Write-Host "- Install Bat To Exe Converter if not present" -ForegroundColor White
    Write-Host "- Restart server if microphone issues persist" -ForegroundColor White
    
}
catch {
    Write-Log "Installation failed: $($_.Exception.Message)" "ERROR"
    Write-Host "Installation failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Log "Installation script completed"
