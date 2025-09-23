# Step 2: Creating Android Virtual Device (AVD)
# Original script from step_scripts.py

# Find next available number for AVD
$PhoneNumber = 1
do {
    $AvdName = "phone$PhoneNumber"
    $AvdExists = & "C:\Program Files\Android\cmdline-tools\latest\bin\avdmanager.bat" list avd | Select-String -Pattern "Name: $AvdName"
    if ($AvdExists) {
        $PhoneNumber++
    }
} while ($AvdExists)

$AndroidHome = "C:\Program Files\Android"
$AvdManagerPath = "$AndroidHome\cmdline-tools\latest\bin\avdmanager.bat"

Write-Host "Creating Android Virtual Device..." -ForegroundColor Yellow
Write-Host "AVD Name: $AvdName" -ForegroundColor Cyan

if (!(Test-Path $AvdManagerPath)) {
    Write-Host "ERROR: AVD Manager not found at: $AvdManagerPath" -ForegroundColor Red
    Write-Host "Make sure Android SDK is installed correctly" -ForegroundColor Yellow
    exit 1
}

try {
    $CreateAvdCmd = "`"$AvdManagerPath`" create avd -n `"$AvdName`" -k `"system-images;android-36;google_apis_playstore;x86_64`" --force"
    Write-Host "Executing command: $CreateAvdCmd" -ForegroundColor Gray
    
    $ProcessInfo = New-Object System.Diagnostics.ProcessStartInfo
    $ProcessInfo.FileName = "cmd.exe"
    $ProcessInfo.Arguments = "/c $CreateAvdCmd"
    $ProcessInfo.UseShellExecute = $false
    $ProcessInfo.RedirectStandardInput = $true
    $ProcessInfo.RedirectStandardOutput = $true
    $ProcessInfo.RedirectStandardError = $true
    
    $Process = [System.Diagnostics.Process]::Start($ProcessInfo)
    $Process.StandardInput.WriteLine("no")  # Answer "no" to custom hardware profile question
    $Process.StandardInput.Close()
    $Process.WaitForExit(60000)  # Wait maximum 1 minute
    
    if ($Process.ExitCode -eq 0) {
        Write-Host "SUCCESS: AVD $AvdName created successfully" -ForegroundColor Green
        Write-Host "AVD_NAME: $AvdName" -ForegroundColor Cyan
        
        # Check that AVD was actually created
        $AvdPath = "$env:USERPROFILE\.android\avd\$AvdName.avd"
        if (Test-Path $AvdPath) {
            Write-Host "AVD_PATH: $AvdPath" -ForegroundColor Cyan
        }
    } else {
        Write-Host "ERROR: Failed to create AVD. Exit code: $($Process.ExitCode)" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "ERROR: AVD creation error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
