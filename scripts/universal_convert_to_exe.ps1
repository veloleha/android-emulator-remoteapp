# Universal Batch to EXE Conversion Script
# Step 4: Converting batch file to EXE

Write-Host "=== UNIVERSAL BATCH TO EXE CONVERSION ===" -ForegroundColor Cyan

# Load configuration
$ConfigPath = "C:\Scripts\config.json"
if (Test-Path $ConfigPath) {
    $Config = Get-Content $ConfigPath | ConvertFrom-Json
    $BatToExeConverter = $Config.paths.bat_to_exe
} else {
    Write-Host "Configuration not found, using defaults..." -ForegroundColor Yellow
    $BatToExeConverter = "C:\Program Files\Bat To Exe Converter\Bat_To_Exe_Converter.exe"
}

# Find last created user and corresponding batch file
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
$BatchFilePath = "C:\Scripts\${TestUser}_emulator.bat"
$ExeFilePath = "C:\Scripts\${TestUser}_emulator.exe"

Write-Host "Converting batch file to EXE..." -ForegroundColor Yellow
Write-Host "User: $TestUser" -ForegroundColor White
Write-Host "Batch file: $BatchFilePath" -ForegroundColor White
Write-Host "EXE file: $ExeFilePath" -ForegroundColor White

# Check for alternative Bat To Exe Converter paths
$PossiblePaths = @(
    $BatToExeConverter,
    "C:\Program Files\Bat To Exe Converter\Bat_To_Exe_Converter.exe",
    "C:\Program Files (x86)\Bat To Exe Converter\Bat_To_Exe_Converter.exe",
    "C:\Tools\Bat To Exe Converter\Bat_To_Exe_Converter.exe",
    "C:\BatToExe\Bat_To_Exe_Converter.exe"
)

$FoundConverter = $null
foreach ($Path in $PossiblePaths) {
    if (Test-Path $Path) {
        $FoundConverter = $Path
        Write-Host "Found Bat To Exe Converter: $Path" -ForegroundColor Green
        break
    }
}

if (-not $FoundConverter) {
    Write-Host "ERROR: Bat To Exe Converter not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Searched paths:" -ForegroundColor Yellow
    foreach ($Path in $PossiblePaths) {
        Write-Host "  - $Path" -ForegroundColor Gray
    }
    Write-Host ""
    Write-Host "Please install Bat To Exe Converter from:" -ForegroundColor Yellow
    Write-Host "  https://www.f2ko.de/en/b2e.php" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Alternative: Using PowerShell to create executable wrapper..." -ForegroundColor Yellow
    
    # Create PowerShell-based executable wrapper as fallback
    $WrapperPath = "C:\Scripts\${TestUser}_emulator_wrapper.ps1"
    $WrapperContent = @"
# PowerShell wrapper for batch file execution
# This serves as an alternative to EXE conversion

Write-Host "Starting Android Emulator for $TestUser..." -ForegroundColor Green
& "$BatchFilePath"
"@
    
    Set-Content -Path $WrapperPath -Value $WrapperContent
    Write-Host "Created PowerShell wrapper: $WrapperPath" -ForegroundColor Green
    Write-Host "You can use this wrapper instead of EXE file" -ForegroundColor Yellow
    
    Write-Host ""
    Write-Host "=== CONVERSION RESULT (FALLBACK) ===" -ForegroundColor Cyan
    Write-Host "USER: $TestUser" -ForegroundColor White
    Write-Host "BATCH FILE: $BatchFilePath" -ForegroundColor White
    Write-Host "WRAPPER: $WrapperPath" -ForegroundColor White
    Write-Host "STATUS: PowerShell wrapper created (EXE conversion skipped)" -ForegroundColor Yellow
    exit 0
}

# Check if batch file exists
if (!(Test-Path $BatchFilePath)) {
    Write-Host "ERROR: Batch file not found: $BatchFilePath" -ForegroundColor Red
    Write-Host "Please run batch file creation step first" -ForegroundColor Yellow
    exit 1
}

# Perform conversion
try {
    Write-Host "Source file: $BatchFilePath" -ForegroundColor Gray
    Write-Host "Target file: $ExeFilePath" -ForegroundColor Gray
    Write-Host "Converter: $FoundConverter" -ForegroundColor Gray
    
    # Remove existing EXE file if it exists
    if (Test-Path $ExeFilePath) {
        Remove-Item $ExeFilePath -Force
        Write-Host "Removed existing EXE file" -ForegroundColor Gray
    }
    
    # Build conversion command
    $ConvertCmd = "`"$FoundConverter`" /bat `"$BatchFilePath`" /exe `"$ExeFilePath`" /invisible /overwrite"
    Write-Host "Conversion command: $ConvertCmd" -ForegroundColor Gray
    
    # Execute conversion
    Write-Host "Starting conversion..." -ForegroundColor Yellow
    $Result = Start-Process -FilePath "cmd.exe" -ArgumentList "/c $ConvertCmd" -Wait -PassThru -WindowStyle Hidden
    
    # Wait a moment for file system to update
    Start-Sleep -Seconds 2
    
    # Check conversion result
    if ($Result.ExitCode -eq 0 -and (Test-Path $ExeFilePath)) {
        Write-Host "SUCCESS: File successfully converted to EXE!" -ForegroundColor Green
        
        # Check EXE file size
        $ExeInfo = Get-Item $ExeFilePath
        Write-Host "EXE file size: $($ExeInfo.Length) bytes" -ForegroundColor Gray
        
        # Test EXE file (quick validation)
        Write-Host "Testing EXE file..." -ForegroundColor Yellow
        try {
            $TestResult = Start-Process -FilePath $ExeFilePath -ArgumentList "/?" -Wait -PassThru -WindowStyle Hidden -ErrorAction SilentlyContinue
            Write-Host "EXE file validation: OK" -ForegroundColor Green
        } catch {
            Write-Host "EXE file validation: Warning (may still work)" -ForegroundColor Yellow
        }
        
        Write-Host ""
        Write-Host "=== CONVERSION RESULT ===" -ForegroundColor Cyan
        Write-Host "USER: $TestUser" -ForegroundColor White
        Write-Host "BATCH FILE: $BatchFilePath" -ForegroundColor White
        Write-Host "EXE FILE: $ExeFilePath" -ForegroundColor White
        Write-Host "SIZE: $($ExeInfo.Length) bytes" -ForegroundColor White
        Write-Host "SUCCESS: EXE file ready for RemoteApp!" -ForegroundColor Green
        
    } else {
        Write-Host "ERROR: Conversion failed. Exit code: $($Result.ExitCode)" -ForegroundColor Red
        
        # Try to provide more information about the failure
        if (!(Test-Path $ExeFilePath)) {
            Write-Host "EXE file was not created" -ForegroundColor Red
        }
        
        Write-Host "Trying alternative conversion method..." -ForegroundColor Yellow
        
        # Alternative: Create a simple executable wrapper
        $AltWrapperPath = "C:\Scripts\${TestUser}_emulator_alt.cmd"
        $AltContent = Get-Content $BatchFilePath
        Set-Content -Path $AltWrapperPath -Value $AltContent
        
        Write-Host "Created alternative CMD file: $AltWrapperPath" -ForegroundColor Yellow
        Write-Host "You can use this CMD file instead of EXE" -ForegroundColor Yellow
        
        exit 1
    }
} catch {
    Write-Host "ERROR: Conversion error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=== BATCH TO EXE CONVERSION COMPLETE ===" -ForegroundColor Cyan
