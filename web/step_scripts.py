# -*- coding: utf-8 -*-
"""
Скрипты для пошагового тестирования Android Emulator RemoteApp
Каждый шаг можно тестировать отдельно для диагностики проблем
"""

# Словарь со всеми шагами тестирования
STEP_SCRIPTS = {
    'create_user': '''
# Шаг 1: Создание пользователя Windows

# Поиск следующего доступного номера пользователя
$UserNumber = 1
do {
    $Username = "User$UserNumber"
    $UserExists = Get-LocalUser -Name $Username -ErrorAction SilentlyContinue
    if ($UserExists) {
        $UserNumber++
    }
} while ($UserExists)

$Password = [System.Guid]::NewGuid().ToString().Replace("-", "").Substring(0, 16)

Write-Host "Создание пользователя Windows..." -ForegroundColor Yellow

# Создаем пользователя
$SecurePassword = ConvertTo-SecureString $Password -AsPlainText -Force
New-LocalUser -Name $Username -Password $SecurePassword -FullName "Android Emulator User" -Description "Android Emulator User" -PasswordNeverExpires -UserMayNotChangePassword

Write-Host "Пользователь $Username создан" -ForegroundColor Green

# Добавляем в группы по SID
$UsersGroupAdded = $false
$RDPGroupAdded = $false

# Группа Users (S-1-5-32-545)
$UsersGroup = Get-LocalGroup -SID "S-1-5-32-545" -ErrorAction SilentlyContinue
if ($UsersGroup) {
    Add-LocalGroupMember -Group $UsersGroup.Name -Member $Username -ErrorAction SilentlyContinue
    Write-Host "Добавлен в группу Users: $($UsersGroup.Name)" -ForegroundColor Green
    $UsersGroupAdded = $true
} else {
    Write-Host "Не удалось найти группу Users" -ForegroundColor Red
}

# Группа Remote Desktop Users (S-1-5-32-555)
$RDPGroup = Get-LocalGroup -SID "S-1-5-32-555" -ErrorAction SilentlyContinue
if ($RDPGroup) {
    Add-LocalGroupMember -Group $RDPGroup.Name -Member $Username -ErrorAction SilentlyContinue
    Write-Host "Добавлен в группу RDP: $($RDPGroup.Name)" -ForegroundColor Green
    $RDPGroupAdded = $true
} else {
    Write-Host "Не удалось найти группу Remote Desktop Users" -ForegroundColor Red
}

# Результат
Write-Host "SUCCESS: Пользователь $Username создан успешно" -ForegroundColor Green
Write-Host "USERNAME: $Username" -ForegroundColor Cyan
Write-Host "PASSWORD: $Password" -ForegroundColor Cyan
Write-Host "PASSWORD CHANGE: Запрещена" -ForegroundColor Cyan

if ($UsersGroupAdded -and $RDPGroupAdded) {
    Write-Host "GROUPS: Users + Remote Desktop Users" -ForegroundColor Green
} else {
    if (-not $UsersGroupAdded) {
        Write-Host "Не удалось добавить в группу Users" -ForegroundColor Red
    }
    if (-not $RDPGroupAdded) {
        Write-Host "Не удалось добавить в группу Remote Desktop Users" -ForegroundColor Red
    }
}
    ''',
    
    'create_avd': '''
# Шаг 2: Создание Android Virtual Device (AVD)
# Находим следующий доступный номер для AVD
$PhoneNumber = 1
do {
    $AvdName = "phone$PhoneNumber"
    $AvdExists = & "C:\\Program Files\\Android\\cmdline-tools\\latest\\bin\\avdmanager.bat" list avd | Select-String -Pattern "Name: $AvdName"
    if ($AvdExists) {
        $PhoneNumber++
    }
} while ($AvdExists)

$AndroidHome = "C:\\Program Files\\Android"
$AvdManagerPath = "$AndroidHome\\cmdline-tools\\latest\\bin\\avdmanager.bat"

Write-Host "🔄 Создание Android Virtual Device..." -ForegroundColor Yellow
Write-Host "AVD Name: $AvdName" -ForegroundColor Cyan

if (!(Test-Path $AvdManagerPath)) {
    Write-Host "❌ ERROR: AVD Manager не найден по пути: $AvdManagerPath" -ForegroundColor Red
    Write-Host "Убедитесь, что Android SDK установлен правильно" -ForegroundColor Yellow
    exit 1
}

try {
    $CreateAvdCmd = "\\"$AvdManagerPath\\" create avd -n \\"$AvdName\\" -k \\"system-images;android-36;google_apis_playstore;x86_64\\" --force"
    Write-Host "Выполняется команда: $CreateAvdCmd" -ForegroundColor Gray
    
    $ProcessInfo = New-Object System.Diagnostics.ProcessStartInfo
    $ProcessInfo.FileName = "cmd.exe"
    $ProcessInfo.Arguments = "/c $CreateAvdCmd"
    $ProcessInfo.UseShellExecute = $false
    $ProcessInfo.RedirectStandardInput = $true
    $ProcessInfo.RedirectStandardOutput = $true
    $ProcessInfo.RedirectStandardError = $true
    
    $Process = [System.Diagnostics.Process]::Start($ProcessInfo)
    $Process.StandardInput.WriteLine("no")  # Отвечаем "no" на вопрос о custom hardware profile
    $Process.StandardInput.Close()
    $Process.WaitForExit(60000)  # Ждем максимум 1 минуту
    
    if ($Process.ExitCode -eq 0) {
        Write-Host "✅ SUCCESS: AVD $AvdName создан успешно" -ForegroundColor Green
        Write-Host "AVD_NAME: $AvdName" -ForegroundColor Cyan
        
        # Проверяем, что AVD действительно создался
        $AvdPath = "$env:USERPROFILE\\.android\\avd\\$AvdName.avd"
        if (Test-Path $AvdPath) {
            Write-Host "AVD_PATH: $AvdPath" -ForegroundColor Cyan
        }
    } else {
        Write-Host "❌ ERROR: Не удалось создать AVD. Код выхода: $($Process.ExitCode)" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ ERROR: Ошибка создания AVD: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
    ''',
    
    'create_batch': '''
# Шаг 3: Создание batch файла для запуска эмулятора
# Находим последнего созданного пользователя
$UserNumber = 1
do {
    $TestUser = "User$UserNumber"
    $UserExists = Get-LocalUser -Name $TestUser -ErrorAction SilentlyContinue
    if ($UserExists) {
        $LastValidUser = $TestUser
        $UserNumber++
    }
} while ($UserExists)
# Используем последнего созданного пользователя
$TestUser = $LastValidUser
$AvdName = "phone$($TestUser.Replace('User', ''))"
$BatchFilePath = "C:\\Scripts\\$TestUser`_emulator.bat"

Write-Host "🔄 Создание batch файла для запуска эмулятора..." -ForegroundColor Yellow

# Убедимся, что директория Scripts существует
if (!(Test-Path "C:\\Scripts")) {
    New-Item -ItemType Directory -Path "C:\\Scripts" -Force
    Write-Host "Создана директория C:\\Scripts" -ForegroundColor Gray
}

$BatchContent = @"
@echo off
REM Тестовый скрипт запуска Android эмулятора
REM Пользователь: $TestUser
REM AVD: $AvdName
REM Создан: $(Get-Date)

echo ========================================
echo Android Emulator Launcher
echo ========================================
echo Пользователь: $TestUser
echo AVD: $AvdName
echo ========================================

echo Переход в директорию эмулятора...
cd /d "C:\\Program Files\\Android\\emulator"
if %ERRORLEVEL% NEQ 0 (
    echo ОШИБКА: Не удалось перейти в директорию эмулятора
    pause
    exit /b 1
)

echo Текущая директория: %CD%
echo.

echo Запуск эмулятора с оптимизированными настройками...
echo Команда: emulator -avd "$AvdName" -no-snapshot -gpu host -memory 2048 -no-boot-anim -netdelay none -netspeed full -audio-in on -audio-out on -verbose
echo.

emulator -avd "$AvdName" -no-snapshot -gpu host -memory 2048 -no-boot-anim -netdelay none -netspeed full -audio-in on -audio-out on -verbose

echo.
echo Эмулятор завершил работу
pause
"@

try {
    Set-Content -Path $BatchFilePath -Value $BatchContent -Encoding ASCII
    Write-Host "✅ SUCCESS: Batch файл создан: $BatchFilePath" -ForegroundColor Green
    Write-Host "BATCH_FILE: $BatchFilePath" -ForegroundColor Cyan
    
    # Проверяем размер файла
    $FileInfo = Get-Item $BatchFilePath
    Write-Host "Размер файла: $($FileInfo.Length) байт" -ForegroundColor Gray
} catch {
    Write-Host "❌ ERROR: Ошибка создания batch файла: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
    ''',
    
    'convert_to_exe': '''
# Шаг 4: Конвертация batch файла в EXE
$BatchFilePath = "C:\\Scripts\\test_emulator.bat"
$ExeFilePath = "C:\\Scripts\\test_emulator.exe"
$BatToExeConverter = "C:\\Program Files\\BatToExe\\BatToExeConverter.exe"

Write-Host "🔄 Конвертация batch файла в EXE..." -ForegroundColor Yellow

if (!(Test-Path $BatToExeConverter)) {
    Write-Host "❌ ERROR: Bat To Exe Converter не найден: $BatToExeConverter" -ForegroundColor Red
    Write-Host "Скачайте и установите Bat To Exe Converter" -ForegroundColor Yellow
    exit 1
}

if (!(Test-Path $BatchFilePath)) {
    Write-Host "❌ ERROR: Batch файл не найден: $BatchFilePath" -ForegroundColor Red
    Write-Host "Сначала выполните шаг 'create_batch'" -ForegroundColor Yellow
    exit 1
}

try {
    Write-Host "Исходный файл: $BatchFilePath" -ForegroundColor Gray
    Write-Host "Целевой файл: $ExeFilePath" -ForegroundColor Gray
    
    $ConvertCmd = "\\"$BatToExeConverter\\" /bat \\"$BatchFilePath\\" /exe \\"$ExeFilePath\\" /invisible /overwrite"
    Write-Host "Команда конвертации: $ConvertCmd" -ForegroundColor Gray
    
    $Result = Start-Process -FilePath "cmd.exe" -ArgumentList "/c $ConvertCmd" -Wait -PassThru -WindowStyle Hidden
    
    if ($Result.ExitCode -eq 0 -and (Test-Path $ExeFilePath)) {
        Write-Host "✅ SUCCESS: Файл успешно конвертирован в EXE: $ExeFilePath" -ForegroundColor Green
        Write-Host "EXE_FILE: $ExeFilePath" -ForegroundColor Cyan
        
        # Проверяем размер EXE файла
        $ExeInfo = Get-Item $ExeFilePath
        Write-Host "Размер EXE файла: $($ExeInfo.Length) байт" -ForegroundColor Gray
    } else {
        Write-Host "❌ ERROR: Конвертация не удалась. Код выхода: $($Result.ExitCode)" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ ERROR: Ошибка конвертации: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
    ''',
    
    'configure_remoteapp': '''
# Шаг 5: Настройка RemoteApp в реестре Windows
$AppName = "TestAndroidEmulator"
$ExePath = "C:\\Scripts\\test_emulator.exe"
$RemoteAppPath = "HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Terminal Server\\TSAppAllowList\\Applications"

Write-Host "🔄 Настройка RemoteApp в реестре..." -ForegroundColor Yellow

try {
    # Проверяем, что EXE файл существует
    if (!(Test-Path $ExePath)) {
        Write-Host "❌ ERROR: EXE файл не найден: $ExePath" -ForegroundColor Red
        Write-Host "Сначала выполните шаг 'convert_to_exe'" -ForegroundColor Yellow
        exit 1
    }
    
    # Создаем путь в реестре если не существует
    if (!(Test-Path $RemoteAppPath)) {
        New-Item -Path $RemoteAppPath -Force
        Write-Host "Создан путь в реестре: $RemoteAppPath" -ForegroundColor Gray
    }
    
    # Создаем запись приложения
    $AppKeyPath = "$RemoteAppPath\\$AppName"
    New-Item -Path $AppKeyPath -Force
    Write-Host "Создана запись приложения: $AppKeyPath" -ForegroundColor Gray
    
    # Устанавливаем свойства приложения
    Set-ItemProperty -Path $AppKeyPath -Name "Name" -Value $AppName
    Set-ItemProperty -Path $AppKeyPath -Name "Path" -Value $ExePath
    Set-ItemProperty -Path $AppKeyPath -Name "ShowInTSWA" -Value 1
    Set-ItemProperty -Path $AppKeyPath -Name "CommandLineSetting" -Value 0
    
    # Включаем RemoteApp (отключаем блокировку)
    Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Terminal Server\\TSAppAllowList" -Name "fDisabledAllowList" -Value 0
    
    Write-Host "✅ SUCCESS: RemoteApp настроен в реестре" -ForegroundColor Green
    Write-Host "APP_NAME: $AppName" -ForegroundColor Cyan
    Write-Host "APP_PATH: $ExePath" -ForegroundColor Cyan
    
    # Проверяем настройки
    $AppSettings = Get-ItemProperty -Path $AppKeyPath
    Write-Host "Проверка настроек:" -ForegroundColor Gray
    Write-Host "  Name: $($AppSettings.Name)" -ForegroundColor Gray
    Write-Host "  Path: $($AppSettings.Path)" -ForegroundColor Gray
    Write-Host "  ShowInTSWA: $($AppSettings.ShowInTSWA)" -ForegroundColor Gray
    
} catch {
    Write-Host "❌ ERROR: Ошибка настройки RemoteApp: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Убедитесь, что скрипт запущен от имени администратора" -ForegroundColor Yellow
    exit 1
}
    ''',
    
    'create_rdp': '''
# Шаг 6: Создание RDP файла для подключения
$Username = "TestUser"
$AppName = "TestAndroidEmulator"
$RdpFilePath = "C:\\Scripts\\test_emulator.rdp"
$ServerAddress = "192.168.88.237"  # Замените на ваш IP адрес

Write-Host "🔄 Создание RDP файла..." -ForegroundColor Yellow

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
    Write-Host "✅ SUCCESS: RDP файл создан: $RdpFilePath" -ForegroundColor Green
    Write-Host "RDP_FILE: $RdpFilePath" -ForegroundColor Cyan
    
    # Проверяем содержимое файла
    $FileContent = Get-Content $RdpFilePath
    Write-Host "Количество строк в RDP файле: $($FileContent.Count)" -ForegroundColor Gray
    Write-Host "Сервер: $ServerAddress" -ForegroundColor Gray
    Write-Host "Приложение: $AppName" -ForegroundColor Gray
    Write-Host "Пользователь: $Username" -ForegroundColor Gray
    
} catch {
    Write-Host "❌ ERROR: Ошибка создания RDP файла: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
    ''',
    
    'test_microphone': '''
# Шаг 7: Тестирование настроек микрофона
Write-Host "🔄 Проверка настроек микрофона для RemoteApp..." -ForegroundColor Yellow

try {
    # Проверяем настройки RDP для аудио
    $RDPTcpPath = "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server\\WinStations\\RDP-Tcp"
    $AudioCapture = Get-ItemProperty -Path $RDPTcpPath -Name "fDisableAudioCapture" -ErrorAction SilentlyContinue
    
    if ($AudioCapture -and $AudioCapture.fDisableAudioCapture -eq 0) {
        Write-Host "✅ Захват аудио включен в RDP-Tcp" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Захват аудио отключен в RDP-Tcp" -ForegroundColor Yellow
        Set-ItemProperty -Path $RDPTcpPath -Name "fDisableAudioCapture" -Value 0
        Write-Host "✅ Захват аудио включен" -ForegroundColor Green
    }
    
    # Проверяем политики Terminal Services
    $TSPolicyPath = "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows NT\\Terminal Services"
    if (Test-Path $TSPolicyPath) {
        $TSAudioCapture = Get-ItemProperty -Path $TSPolicyPath -Name "fDisableAudioCapture" -ErrorAction SilentlyContinue
        if ($TSAudioCapture -and $TSAudioCapture.fDisableAudioCapture -eq 0) {
            Write-Host "✅ Захват аудио разрешен в политиках TS" -ForegroundColor Green
        } else {
            Write-Host "⚠️  Настройка захвата аудио в политиках TS" -ForegroundColor Yellow
            Set-ItemProperty -Path $TSPolicyPath -Name "fDisableAudioCapture" -Value 0 -Force
            Write-Host "✅ Захват аудио разрешен в политиках" -ForegroundColor Green
        }
        
        # Проверяем таймауты сессий
        $MaxConnTime = Get-ItemProperty -Path $TSPolicyPath -Name "MaxConnectionTime" -ErrorAction SilentlyContinue
        if ($MaxConnTime -and $MaxConnTime.MaxConnectionTime -eq 0) {
            Write-Host "✅ Таймаут подключения отключен" -ForegroundColor Green
        } else {
            Write-Host "⚠️  Настройка таймаута подключения" -ForegroundColor Yellow
            Set-ItemProperty -Path $TSPolicyPath -Name "MaxConnectionTime" -Value 0 -Force
            Write-Host "✅ Таймаут подключения отключен" -ForegroundColor Green
        }
    }
    
    # Проверяем службу Windows Audio
    $AudioService = Get-Service -Name "AudioSrv" -ErrorAction SilentlyContinue
    if ($AudioService) {
        if ($AudioService.Status -eq "Running") {
            Write-Host "✅ Служба Windows Audio запущена" -ForegroundColor Green
        } else {
            Write-Host "⚠️  Запуск службы Windows Audio" -ForegroundColor Yellow
            Start-Service -Name "AudioSrv"
            Write-Host "✅ Служба Windows Audio запущена" -ForegroundColor Green
        }
        
        if ($AudioService.StartType -eq "Automatic") {
            Write-Host "✅ Служба Windows Audio настроена на автозапуск" -ForegroundColor Green
        } else {
            Write-Host "⚠️  Настройка автозапуска службы Windows Audio" -ForegroundColor Yellow
            Set-Service -Name "AudioSrv" -StartupType Automatic
            Write-Host "✅ Служба настроена на автозапуск" -ForegroundColor Green
        }
    }
    
    Write-Host "✅ SUCCESS: Настройки микрофона проверены и оптимизированы" -ForegroundColor Green
    Write-Host "MICROPHONE_STATUS: Configured" -ForegroundColor Cyan
    
} catch {
    Write-Host "❌ ERROR: Ошибка проверки настроек микрофона: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
    '''
}

# Описания шагов для UI
STEP_DESCRIPTIONS = {
    'create_user': {
        'title': '1️⃣ Создание пользователя Windows',
        'description': 'Создает нового пользователя Windows с уникальным именем и добавляет его в группу Remote Desktop Users',
        'expected_output': 'USERNAME и PASSWORD нового пользователя'
    },
    'create_avd': {
        'title': '2️⃣ Создание Android Virtual Device',
        'description': 'Создает новый AVD с оптимизированными настройками для RemoteApp',
        'expected_output': 'AVD_NAME созданного виртуального устройства'
    },
    'create_batch': {
        'title': '3️⃣ Создание batch файла',
        'description': 'Генерирует batch файл для запуска эмулятора с правильными параметрами (исправляет cd /c на cd /d)',
        'expected_output': 'BATCH_FILE путь к созданному файлу'
    },
    'convert_to_exe': {
        'title': '4️⃣ Конвертация в EXE',
        'description': 'Конвертирует batch файл в исполняемый EXE файл с помощью Bat To Exe Converter',
        'expected_output': 'EXE_FILE путь к созданному исполняемому файлу'
    },
    'configure_remoteapp': {
        'title': '5️⃣ Настройка RemoteApp',
        'description': 'Регистрирует приложение в реестре Windows для работы через RemoteApp',
        'expected_output': 'APP_NAME и APP_PATH зарегистрированного приложения'
    },
    'create_rdp': {
        'title': '6️⃣ Создание RDP файла',
        'description': 'Генерирует RDP файл с настройками микрофона и оптимизацией для RemoteApp',
        'expected_output': 'RDP_FILE путь к созданному RDP файлу'
    },
    'test_microphone': {
        'title': '7️⃣ Тестирование микрофона',
        'description': 'Проверяет и настраивает все параметры для корректной работы микрофона в RemoteApp',
        'expected_output': 'MICROPHONE_STATUS статус настройки микрофона'
    }
}
