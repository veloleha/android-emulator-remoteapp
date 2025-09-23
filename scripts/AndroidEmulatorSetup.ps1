# Android Emulator RemoteApp Automation Script
# Author: Automated Setup System
# Date: 2025-09-23
# Purpose: Create user, AVD, and RemoteApp configuration for Android emulator

param(
    [string]$AdminPassword = "",
    [string]$LogFile = "C:\Scripts\log.txt"
)

# Ensure log directory exists
$LogDir = Split-Path $LogFile -Parent
if (!(Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force
}

# Logging function
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogEntry = "[$Timestamp] [$Level] $Message"
    Write-Host $LogEntry
    Add-Content -Path $LogFile -Value $LogEntry
}

# Generate unique username and secure password
function New-UniqueUser {
    # Находим следующий доступный номер для пользователя
    $UserNumber = 1
    do {
        $Username = "User$UserNumber"
        $UserExists = Get-LocalUser -Name $Username -ErrorAction SilentlyContinue
        if ($UserExists) {
            $UserNumber++
        }
    } while ($UserExists)
    
    $Password = [System.Guid]::NewGuid().ToString().Replace("-", "").Substring(0, 16)
    
    Write-Log "Creating user: $Username"
    
    try {
        # Create new user
        $SecurePassword = ConvertTo-SecureString $Password -AsPlainText -Force
        New-LocalUser -Name $Username -Password $SecurePassword -FullName "Android Emulator User" -Description "Android Emulator User" -PasswordNeverExpires -UserMayNotChangePassword
        
        # Add to Users group
        try {
            Add-LocalGroupMember -Group "Пользователи" -Member $Username -ErrorAction SilentlyContinue
            if (-not $?) {
                Add-LocalGroupMember -Group "Users" -Member $Username
            }
        } catch {
            Write-Log "Warning: Could not add user to Users group: $($_.Exception.Message)" "WARNING"
        }
        
        # Add to Remote Desktop Users group
        try {
            Add-LocalGroupMember -Group "Пользователи удаленного рабочего стола" -Member $Username -ErrorAction SilentlyContinue
            if (-not $?) {
                Add-LocalGroupMember -Group "Remote Desktop Users" -Member $Username
            }
        } catch {
            Write-Log "Warning: Could not add user to Remote Desktop Users group: $($_.Exception.Message)" "WARNING"
        }
        
        Write-Log "User $Username created with password restrictions and added to required groups"
        
        return @{
            Username = $Username
            Password = $Password
        }
    }
    catch {
        Write-Log "Failed to create user: $($_.Exception.Message)" "ERROR"
        throw
    }
}

# Create Android Virtual Device
function New-AndroidAVD {
    param(
        [string]$AvdName,
        [string]$Username
    )
    
    Write-Log "Creating AVD: $AvdName"
    
    $AndroidSdkPath = "C:\Program Files\Android"
    $AvdManagerPath = "$AndroidSdkPath\cmdline-tools\latest\bin\avdmanager.bat"
    $EmulatorPath = "$AndroidSdkPath\emulator"
    
    # Check if Android SDK tools exist
    if (!(Test-Path $AvdManagerPath)) {
        Write-Log "AVD Manager not found at $AvdManagerPath" "ERROR"
        throw "Android SDK tools not found"
    }
    
    try {
        # Create AVD with optimized settings
        $CreateAvdCmd = "`"$AvdManagerPath`" create avd -n `"$AvdName`" -k `"system-images;android-36;google_apis_playstore;x86_64`" --force"
        Write-Log "Executing: $CreateAvdCmd"
        
        # Use Start-Process to handle the interactive AVD creation
        $ProcessInfo = New-Object System.Diagnostics.ProcessStartInfo
        $ProcessInfo.FileName = "cmd.exe"
        $ProcessInfo.Arguments = "/c `"$CreateAvdCmd`""
        $ProcessInfo.UseShellExecute = $false
        $ProcessInfo.RedirectStandardInput = $true
        $ProcessInfo.RedirectStandardOutput = $true
        $ProcessInfo.RedirectStandardError = $true
        
        $Process = [System.Diagnostics.Process]::Start($ProcessInfo)
        
        # Send "no" to custom hardware profile question
        $Process.StandardInput.WriteLine("no")
        $Process.StandardInput.Close()
        
        $Process.WaitForExit()
        
        if ($Process.ExitCode -eq 0) {
            Write-Log "AVD $AvdName created successfully"
            
            # Configure AVD settings
            $AvdConfigPath = "$env:USERPROFILE\.android\avd\$AvdName.avd\config.ini"
            if (Test-Path $AvdConfigPath) {
                Update-AvdConfig -ConfigPath $AvdConfigPath
            }
        } else {
            Write-Log "Failed to create AVD. Exit code: $($Process.ExitCode)" "ERROR"
            throw "AVD creation failed"
        }
    }
    catch {
        Write-Log "Error creating AVD: $($_.Exception.Message)" "ERROR"
        throw
    }
}

# Update AVD configuration for optimal performance and audio
function Update-AvdConfig {
    param([string]$ConfigPath)
    
    Write-Log "Updating AVD configuration at: $ConfigPath"
    
    $ConfigContent = @"
AvdId=phone
PlayStore.enabled=true
abi.type=x86_64
avd.ini.displayname=phone
avd.ini.encoding=UTF-8
disk.dataPartition.size=6G
fastboot.chosenSnapshotFile=
fastboot.forceChosenSnapshotBoot=no
fastboot.forceColdBoot=no
fastboot.forceFastBoot=yes
hw.accelerometer=yes
hw.arc=false
hw.audioInput=yes
hw.audioOutput=yes
hw.battery=yes
hw.camera.back=virtualscene
hw.camera.front=emulated
hw.cpu.arch=x86_64
hw.cpu.ncore=2
hw.dPad=no
hw.device.hash2=MD5:64b26f5eaf2f4673290cdc23d0c65386
hw.device.manufacturer=Generic
hw.device.name=small_phone
hw.gps=yes
hw.gpu.enabled=yes
hw.gpu.mode=host
hw.gyroscope=yes
hw.initialOrientation=portrait
hw.keyboard=yes
hw.lcd.density=320
hw.lcd.height=1280
hw.lcd.width=720
hw.mainKeys=no
hw.ramSize=2048
hw.sdCard=yes
hw.sensors.light=no
hw.sensors.magnetic_field=yes
hw.sensors.orientation=yes
hw.sensors.pressure=yes
hw.sensors.proximity=yes
hw.trackBall=no
image.sysdir.1=system-images\android-36\google_apis_playstore\x86_64
runtime.network.latency=none
runtime.network.speed=full
sdcard.size=512M
showDeviceFrame=yes
skin.dynamic=yes
tag.display=Google Play
tag.displaynames=Google Play
tag.id=google_apis_playstore
tag.ids=google_apis_playstore
target=android-36
vm.heapSize=500
"@
    
    try {
        Set-Content -Path $ConfigPath -Value $ConfigContent -Encoding UTF8
        Write-Log "AVD configuration updated successfully"
    }
    catch {
        Write-Log "Failed to update AVD configuration: $($_.Exception.Message)" "ERROR"
    }
}

# Create optimized batch file for emulator launch
function New-EmulatorBatchFile {
    param(
        [string]$AvdName,
        [string]$Username,
        [string]$BatchFilePath
    )
    
    Write-Log "Creating batch file: $BatchFilePath"
    
    $BatchContent = @"
@echo off
REM Android Emulator Launch Script
REM Generated automatically for user: $Username
REM AVD: $AvdName

REM Change to emulator directory (fixed cd /c error)
cd /d "C:\Program Files\Android\emulator"

REM Launch emulator with optimized settings for RemoteApp
emulator -avd "$AvdName" -no-snapshot -gpu host -memory 2048 -no-boot-anim -netdelay none -netspeed full -audio-in on -audio-out on -verbose

REM Keep window open for debugging
pause
"@
    
    try {
        Set-Content -Path $BatchFilePath -Value $BatchContent -Encoding ASCII
        Write-Log "Batch file created successfully"
        return $BatchFilePath
    }
    catch {
        Write-Log "Failed to create batch file: $($_.Exception.Message)" "ERROR"
        throw
    }
}

# Convert batch file to executable
function Convert-BatchToExe {
    param(
        [string]$BatchFilePath,
        [string]$ExeFilePath
    )
    
    Write-Log "Converting batch to exe: $BatchFilePath -> $ExeFilePath"
    
    $BatToExeConverter = "C:\Program Files\BatToExe\BatToExeConverter.exe"
    
    if (!(Test-Path $BatToExeConverter)) {
        Write-Log "Bat To Exe Converter not found at: $BatToExeConverter" "ERROR"
        throw "Bat To Exe Converter not installed"
    }
    
    try {
        # Use Bat To Exe Converter command line
        $ConvertCmd = "`"$BatToExeConverter`" /bat `"$BatchFilePath`" /exe `"$ExeFilePath`" /invisible /overwrite"
        Write-Log "Executing: $ConvertCmd"
        
        $Result = Start-Process -FilePath "cmd.exe" -ArgumentList "/c $ConvertCmd" -Wait -PassThru -WindowStyle Hidden
        
        if ($Result.ExitCode -eq 0 -and (Test-Path $ExeFilePath)) {
            Write-Log "Successfully converted to executable"
            return $ExeFilePath
        } else {
            Write-Log "Conversion failed. Exit code: $($Result.ExitCode)" "ERROR"
            throw "Batch to exe conversion failed"
        }
    }
    catch {
        Write-Log "Error during conversion: $($_.Exception.Message)" "ERROR"
        throw
    }
}

# Configure RemoteApp in registry
function Set-RemoteAppRegistry {
    param(
        [string]$AppName,
        [string]$ExePath,
        [string]$Username
    )
    
    Write-Log "Configuring RemoteApp registry for: $AppName"
    
    $RemoteAppPath = "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Terminal Server\TSAppAllowList\Applications"
    
    try {
        # Ensure the Applications key exists
        if (!(Test-Path $RemoteAppPath)) {
            New-Item -Path $RemoteAppPath -Force
        }
        
        # Create application entry
        $AppKeyPath = "$RemoteAppPath\$AppName"
        New-Item -Path $AppKeyPath -Force
        
        # Set application properties
        Set-ItemProperty -Path $AppKeyPath -Name "Name" -Value $AppName
        Set-ItemProperty -Path $AppKeyPath -Name "Path" -Value $ExePath
        Set-ItemProperty -Path $AppKeyPath -Name "ShowInTSWA" -Value 1
        Set-ItemProperty -Path $AppKeyPath -Name "CommandLineSetting" -Value 0
        
        # Enable RemoteApp
        Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Terminal Server\TSAppAllowList" -Name "fDisabledAllowList" -Value 0
        
        Write-Log "RemoteApp registry configuration completed"
    }
    catch {
        Write-Log "Failed to configure RemoteApp registry: $($_.Exception.Message)" "ERROR"
        throw
    }
}

# Configure RDP settings for microphone support
function Set-RdpMicrophoneSettings {
    Write-Log "Configuring RDP settings for microphone support"
    
    try {
        # Enable audio redirection
        Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp" -Name "fDisableAudioCapture" -Value 0
        
        # Set audio quality to high
        Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Terminal Server\TSAppAllowList" -Name "AudioCaptureMode" -Value 1
        
        # Disable session timeouts that might affect audio
        Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\Terminal Services" -Name "MaxConnectionTime" -Value 0 -Force
        Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\Terminal Services" -Name "MaxIdleTime" -Value 0 -Force
        Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\Terminal Services" -Name "MaxDisconnectionTime" -Value 0 -Force
        
        # Enable microphone redirection
        Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\Terminal Services" -Name "fDisableAudioCapture" -Value 0 -Force
        
        Write-Log "RDP microphone settings configured"
    }
    catch {
        Write-Log "Failed to configure RDP microphone settings: $($_.Exception.Message)" "ERROR"
    }
}

# Generate RDP file
function New-RdpFile {
    param(
        [string]$Username,
        [string]$AppName,
        [string]$RdpFilePath,
        [string]$ServerAddress = "192.168.88.237"
    )
    
    Write-Log "Creating RDP file: $RdpFilePath"
    
    $RdpContent = @"
full address:s:$ServerAddress`:3389
remoteapplicationmode:i:1
remoteapplicationname:s:$AppName
remoteapplicationprogram:s:||$AppName
alternate shell:s:rdpinit.exe
disableremoteappcapscheck:i:1
prompt for credentials on client:i:1
username:s:$Username
audiomode:i:0
audioqualitymode:i:2
audiocapturemode:i:1
compression:i:1
bitmapcachepersistenable:i:1
videomode:i:32
experience:i:0
desktopwidth:i:1280
desktopheight:i:720
microphone redirection:i:1
audio redirection:i:0
session bpp:i:32
allow font smoothing:i:1
disable wallpaper:i:0
disable full window drag:i:0
disable menu anims:i:0
disable themes:i:0
disable cursor setting:i:0
bitmapcachesize:i:1500
"@
    
    try {
        Set-Content -Path $RdpFilePath -Value $RdpContent -Encoding UTF8
        Write-Log "RDP file created successfully"
        
        # Set appropriate permissions
        $Acl = Get-Acl $RdpFilePath
        $AccessRule = New-Object System.Security.AccessControl.FileSystemAccessRule($Username, "ReadAndExecute", "Allow")
        $Acl.SetAccessRule($AccessRule)
        Set-Acl -Path $RdpFilePath -AclObject $Acl
        
        return $RdpFilePath
    }
    catch {
        Write-Log "Failed to create RDP file: $($_.Exception.Message)" "ERROR"
        throw
    }
}

# Main execution function
function Start-EmulatorSetup {
    Write-Log "Starting Android Emulator RemoteApp setup"
    
    try {
        # Step 1: Create unique user
        $UserInfo = New-UniqueUser
        $Username = $UserInfo.Username
        $Password = $UserInfo.Password
        
        # Step 2: Create AVD
        $AvdName = "phone_$Username"
        New-AndroidAVD -AvdName $AvdName -Username $Username
        
        # Step 3: Create batch file
        $BatchFilePath = "C:\Scripts\$Username`_emulator.bat"
        New-EmulatorBatchFile -AvdName $AvdName -Username $Username -BatchFilePath $BatchFilePath
        
        # Step 4: Convert to exe
        $ExeFilePath = "C:\Scripts\$Username`_emulator.exe"
        Convert-BatchToExe -BatchFilePath $BatchFilePath -ExeFilePath $ExeFilePath
        
        # Step 5: Configure RemoteApp
        $AppName = "AndroidEmulator_$Username"
        Set-RemoteAppRegistry -AppName $AppName -ExePath $ExeFilePath -Username $Username
        
        # Step 6: Configure RDP microphone settings
        Set-RdpMicrophoneSettings
        
        # Step 7: Generate RDP file
        $RdpFilePath = "C:\Scripts\$Username`_emulator.rdp"
        New-RdpFile -Username $Username -AppName $AppName -RdpFilePath $RdpFilePath
        
        # Step 8: Set file permissions
        $FilesToSecure = @($BatchFilePath, $ExeFilePath, $RdpFilePath)
        foreach ($File in $FilesToSecure) {
            if (Test-Path $File) {
                icacls $File /grant "$Username`:R" /inheritance:r
                Write-Log "Set permissions for: $File"
            }
        }
        
        Write-Log "Setup completed successfully!"
        
        # Return setup information
        return @{
            Username = $Username
            Password = $Password
            AvdName = $AvdName
            RdpFile = $RdpFilePath
            ExeFile = $ExeFilePath
            Success = $true
        }
    }
    catch {
        Write-Log "Setup failed: $($_.Exception.Message)" "ERROR"
        return @{
            Success = $false
            Error = $_.Exception.Message
        }
    }
}

# Execute if run directly
if ($MyInvocation.InvocationName -ne '.') {
    $Result = Start-EmulatorSetup
    
    if ($Result.Success) {
        Write-Host "Setup completed successfully!" -ForegroundColor Green
        Write-Host "Username: $($Result.Username)" -ForegroundColor Yellow
        Write-Host "Password: $($Result.Password)" -ForegroundColor Yellow
        Write-Host "RDP File: $($Result.RdpFile)" -ForegroundColor Yellow
    } else {
        Write-Host "Setup failed: $($Result.Error)" -ForegroundColor Red
        exit 1
    }
}
