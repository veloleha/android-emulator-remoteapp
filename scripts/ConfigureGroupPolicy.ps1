# Group Policy Configuration for Microphone Support in RemoteApp
# This script addresses the 3-second microphone cutoff issue

param(
    [string]$LogFile = "C:\Scripts\log.txt"
)

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogEntry = "[$Timestamp] [$Level] $Message"
    Write-Host $LogEntry
    Add-Content -Path $LogFile -Value $LogEntry
}

Write-Log "Configuring Group Policy settings for microphone support"

try {
    # Create the registry path for Terminal Services policies if it doesn't exist
    $TSPolicyPath = "HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\Terminal Services"
    if (!(Test-Path $TSPolicyPath)) {
        New-Item -Path $TSPolicyPath -Force
        Write-Log "Created Terminal Services policy registry path"
    }

    # Disable session timeouts that can interrupt audio
    Set-ItemProperty -Path $TSPolicyPath -Name "MaxConnectionTime" -Value 0 -Type DWord
    Set-ItemProperty -Path $TSPolicyPath -Name "MaxIdleTime" -Value 0 -Type DWord  
    Set-ItemProperty -Path $TSPolicyPath -Name "MaxDisconnectionTime" -Value 0 -Type DWord
    Write-Log "Disabled session timeouts"

    # Enable audio capture and redirection
    Set-ItemProperty -Path $TSPolicyPath -Name "fDisableAudioCapture" -Value 0 -Type DWord
    Set-ItemProperty -Path $TSPolicyPath -Name "fDisableCam" -Value 0 -Type DWord
    Write-Log "Enabled audio capture and camera"

    # Configure audio quality settings
    Set-ItemProperty -Path $TSPolicyPath -Name "AudioQualityMode" -Value 0 -Type DWord  # High quality
    Set-ItemProperty -Path $TSPolicyPath -Name "AudioCaptureRedirectionMode" -Value 1 -Type DWord
    Write-Log "Configured audio quality settings"

    # RDP-Tcp specific settings
    $RDPTcpPath = "HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp"
    Set-ItemProperty -Path $RDPTcpPath -Name "fDisableAudioCapture" -Value 0 -Type DWord
    Set-ItemProperty -Path $RDPTcpPath -Name "fDisableCam" -Value 0 -Type DWord
    Write-Log "Configured RDP-Tcp audio settings"

    # Windows Audio Service settings
    $AudioServicePath = "HKLM:\SYSTEM\CurrentControlSet\Services\AudioSrv"
    Set-ItemProperty -Path $AudioServicePath -Name "Start" -Value 2 -Type DWord  # Automatic start
    Write-Log "Configured Windows Audio Service"

    # Additional RemoteApp specific settings
    $RemoteAppPath = "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Terminal Server\TSAppAllowList"
    Set-ItemProperty -Path $RemoteAppPath -Name "fDisabledAllowList" -Value 0 -Type DWord
    Write-Log "Enabled RemoteApp allow list"

    Write-Log "Group Policy configuration completed successfully"
    Write-Host "Group Policy settings have been applied. A system restart may be required." -ForegroundColor Green
}
catch {
    Write-Log "Failed to configure Group Policy: $($_.Exception.Message)" "ERROR"
    Write-Host "Error configuring Group Policy: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
