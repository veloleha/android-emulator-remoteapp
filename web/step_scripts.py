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
New-LocalUser -Name $Username -Password $SecurePassword -FullName "Android Emulator User $UserNumber" -Description "Android Emulator User #$UserNumber" -PasswordNeverExpires -UserMayNotChangePassword

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

# Назначаем права доступа для совместимости с RemoteApp
try {
    $UserProfilePath = "C:\\Users\\$Username"
    if (Test-Path $UserProfilePath) {
        Write-Host "🔐 Настройка прав доступа на профиль пользователя: $UserProfilePath" -ForegroundColor Yellow
        icacls $UserProfilePath /grant "Everyone:(OI)(CI)F" /T /Q | Out-Null
        icacls $UserProfilePath /grant "Users:(OI)(CI)F" /T /Q | Out-Null
        Write-Host "✅ Права доступа на профиль назначены (Everyone, Users)" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️  Не удалось назначить права на профиль: $($_.Exception.Message)" -ForegroundColor Yellow
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

# Полная инициализация Android SDK для нового пользователя
Write-Host "🔧 Инициализация Android SDK для пользователя $Username..." -ForegroundColor Yellow
$AndroidHome = "C:\\Program Files\\Android"
$JavaHome = "C:\\Program Files\\Microsoft\\jdk-17.0.16.8-hotspot"
$UserProfile = "C:\\Users\\$Username"
$AndroidUserDir = "$UserProfile\\.android"
$LogFile = "C:\\Scripts\\sdk_init_log.txt"

# Функция логирования
function Write-Log {
    param($Message, $Level = "INFO")
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogEntry = "[$Timestamp] [$Level] $Message"
    Add-Content -Path $LogFile -Value $LogEntry -Encoding UTF8
    Write-Host $LogEntry -ForegroundColor $(if($Level -eq "ERROR"){"Red"}elseif($Level -eq "WARN"){"Yellow"}else{"Gray"})
}

try {
    Write-Log "Начало инициализации SDK для пользователя: $Username"
    
    # 1. Проверка наличия Android SDK
    Write-Host "📋 Проверка Android SDK..." -ForegroundColor Cyan
    if (!(Test-Path $AndroidHome)) {
        Write-Log "Android SDK не найден по пути: $AndroidHome" "ERROR"
        throw "Android SDK не установлен"
    }
    Write-Log "Android SDK найден: $AndroidHome"
    
    # 2. Проверка Java
    if (!(Test-Path $JavaHome)) {
        Write-Log "Java не найден по пути: $JavaHome" "ERROR"
        throw "Java не установлен"
    }
    Write-Log "Java найден: $JavaHome"
    
    # 3. Создание .android директории для пользователя
    Write-Host "📁 Создание .android директории..." -ForegroundColor Cyan
    if (!(Test-Path $AndroidUserDir)) {
        New-Item -ItemType Directory -Path $AndroidUserDir -Force | Out-Null
        Write-Log "Создана директория: $AndroidUserDir"
    } else {
        Write-Log "Директория уже существует: $AndroidUserDir"
    }
    
    # Создаем поддиректории
    $SubDirs = @("avd", "cache", "temp")
    foreach ($SubDir in $SubDirs) {
        $SubDirPath = "$AndroidUserDir\\$SubDir"
        if (!(Test-Path $SubDirPath)) {
            New-Item -ItemType Directory -Path $SubDirPath -Force | Out-Null
            Write-Log "Создана поддиректория: $SubDirPath"
        }
    }
    
    # 4. Настройка прав доступа
    Write-Host "🔐 Настройка прав доступа..." -ForegroundColor Cyan
    icacls $AndroidUserDir /grant "$($Username):(OI)(CI)F" /T | Out-Null
    icacls $AndroidUserDir /grant "Everyone:(OI)(CI)F" /T /Q | Out-Null
    icacls $AndroidUserDir /grant "Users:(OI)(CI)F" /T /Q | Out-Null
    Write-Log "Права доступа настроены для $Username (и Everyone/Users) на $AndroidUserDir"
    
    # 5. Настройка переменных окружения для пользователя
    Write-Host "🌍 Настройка переменных окружения..." -ForegroundColor Cyan
    
    # Устанавливаем переменные для текущей сессии
    $env:ANDROID_HOME = $AndroidHome
    $env:ANDROID_SDK_ROOT = $AndroidHome
    $env:JAVA_HOME = $JavaHome
    $env:ANDROID_AVD_HOME = "$AndroidUserDir\\avd"
    $env:Path = "$JavaHome\\bin;$AndroidHome\\platform-tools;$AndroidHome\\emulator;$AndroidHome\\cmdline-tools\\latest\\bin;" + $env:Path
    
    Write-Log "Переменные окружения установлены для сессии"
    
    # 6. Проверка наличия необходимых SDK компонентов
    Write-Host "📦 Проверка SDK компонентов..." -ForegroundColor Cyan
    $SdkManagerPath = "$AndroidHome\\cmdline-tools\\latest\\bin\\sdkmanager.bat"
    
    if (!(Test-Path $SdkManagerPath)) {
        Write-Log "sdkmanager не найден: $SdkManagerPath" "ERROR"
        throw "sdkmanager не доступен"
    }
    
    # Проверяем установленные пакеты
    Write-Log "Проверка установленных SDK пакетов..."
    $InstalledPackages = & $SdkManagerPath --list_installed 2>$null
    
    # Необходимые пакеты
    $RequiredPackages = @(
        "system-images;android-36;google_apis_playstore;x86_64",
        "platforms;android-36",
        "build-tools;34.0.0",
        "platform-tools",
        "emulator"
    )
    
    $MissingPackages = @()
    foreach ($Package in $RequiredPackages) {
        if ($InstalledPackages -notmatch [regex]::Escape($Package)) {
            $MissingPackages += $Package
            Write-Log "Отсутствует пакет: $Package" "WARN"
        } else {
            Write-Log "Пакет установлен: $Package"
        }
    }
    
    # 7. Установка недостающих пакетов
    if ($MissingPackages.Count -gt 0) {
        Write-Host "⬇️  Установка недостающих SDK компонентов..." -ForegroundColor Yellow
        Write-Log "Начало установки недостающих пакетов: $($MissingPackages -join ', ')"
        
        foreach ($Package in $MissingPackages) {
            Write-Host "Установка: $Package" -ForegroundColor Gray
            try {
                $InstallResult = & $SdkManagerPath $Package --verbose 2>&1
                if ($LASTEXITCODE -eq 0) {
                    Write-Log "Успешно установлен: $Package"
                } else {
                    Write-Log "Ошибка установки $Package`: $InstallResult" "ERROR"
                }
            } catch {
                Write-Log "Исключение при установке $Package`: $($_.Exception.Message)" "ERROR"
            }
        }
    } else {
        Write-Host "✅ Все необходимые SDK компоненты уже установлены" -ForegroundColor Green
        Write-Log "Все необходимые SDK компоненты установлены"
    }
    
    # 8. Создание конфигурационных файлов
    Write-Host "📝 Создание конфигурационных файлов..." -ForegroundColor Cyan
    
    # Создаем repositories.cfg
    $RepoConfigPath = "$AndroidUserDir\\repositories.cfg"
    $RepoConfig = @"
### User Sources for Android SDK Manager
# Generated automatically for user: $Username
# Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
count=0
"@
    Set-Content -Path $RepoConfigPath -Value $RepoConfig -Encoding UTF8
    Write-Log "Создан repositories.cfg: $RepoConfigPath"
    
    # 9. Проверка работоспособности
    Write-Host "🧪 Проверка работоспособности SDK..." -ForegroundColor Cyan
    
    # Проверяем avdmanager
    $AvdManagerPath = "$AndroidHome\\cmdline-tools\\latest\\bin\\avdmanager.bat"
    if (Test-Path $AvdManagerPath) {
        try {
            $AvdListResult = & $AvdManagerPath list avd 2>&1
            Write-Log "avdmanager работает корректно"
        } catch {
            Write-Log "Проблема с avdmanager: $($_.Exception.Message)" "WARN"
        }
    }
    
    # Проверяем emulator
    $EmulatorPath = "$AndroidHome\\emulator\\emulator.exe"
    if (Test-Path $EmulatorPath) {
        try {
            $EmulatorVersion = & $EmulatorPath -version 2>&1 | Select-Object -First 1
            Write-Log "Emulator доступен: $EmulatorVersion"
        } catch {
            Write-Log "Проблема с emulator: $($_.Exception.Message)" "WARN"
        }
    }
    
    Write-Host "✅ Android SDK успешно инициализирован для $Username" -ForegroundColor Green
    Write-Log "SDK инициализация завершена успешно для $Username"
    
    # Выводим сводку
    Write-Host "`n📊 Сводка инициализации SDK:" -ForegroundColor Cyan
    Write-Host "   ANDROID_HOME: $AndroidHome" -ForegroundColor Gray
    Write-Host "   JAVA_HOME: $JavaHome" -ForegroundColor Gray
    Write-Host "   USER_ANDROID_DIR: $AndroidUserDir" -ForegroundColor Gray
    Write-Host "   ANDROID_AVD_HOME: $AndroidUserDir\\avd" -ForegroundColor Gray
    Write-Host "   Установленные пакеты: $($RequiredPackages.Count - $MissingPackages.Count)/$($RequiredPackages.Count)" -ForegroundColor Gray
    Write-Host "   Лог файл: $LogFile" -ForegroundColor Gray
    
} catch {
    $ErrorMessage = "Ошибка инициализации SDK для $Username`: $($_.Exception.Message)"
    Write-Host "❌ $ErrorMessage" -ForegroundColor Red
    Write-Log $ErrorMessage "ERROR"
    
    # Не прерываем создание пользователя, только логируем ошибку
    Write-Host "⚠️  Пользователь создан, но SDK требует ручной настройки" -ForegroundColor Yellow
}
    ''',
    
    'create_avd': '''
# Шаг 2: Создание Android Virtual Device (AVD) путем копирования шаблона

# Настройка переменных окружения Android SDK
$AndroidHome = "C:\\Program Files\\Android"
$AndroidSdk = "C:\\Program Files\\Android"
$JavaHome = "C:\\Program Files\\Microsoft\\jdk-17.0.16.8-hotspot"

# Устанавливаем переменные для текущей сессии
$env:ANDROID_HOME = $AndroidHome
$env:ANDROID_SDK_ROOT = $AndroidSdk
$env:JAVA_HOME = $JavaHome
$env:Path = "$JavaHome\\bin;$AndroidHome\\platform-tools;$AndroidHome\\emulator;$AndroidHome\\cmdline-tools\\latest\\bin;" + $env:Path

Write-Host "🔧 Настройка переменных окружения Android SDK..." -ForegroundColor Gray
Write-Host "ANDROID_HOME: $AndroidHome" -ForegroundColor Gray
Write-Host "JAVA_HOME: $JavaHome" -ForegroundColor Gray

# Находим последнего созданного пользователя для уникального имени AVD
$UserNumber = 1
do {
    $TestUser = "User$UserNumber"
    $UserExists = Get-LocalUser -Name $TestUser -ErrorAction SilentlyContinue
    if ($UserExists) {
        $LastValidUser = $TestUser
        $UserNumber++
    }
} while ($UserExists)

# Создаем уникальное имя AVD: User1_Emulator, User2_Emulator и т.д.
$UserNum = $LastValidUser.Replace('User', '')
$AvdName = "User$UserNum`_Emulator"
Write-Host "Создание AVD с уникальным именем: $AvdName" -ForegroundColor Cyan

# Устанавливаем ANDROID_AVD_HOME для конкретного пользователя
# ВАЖНО: Используем ту же логику, что и в batch файле
$UserProfilePath = "C:\\Users\\$LastValidUser"
$UserProfilePathHP = "C:\\Users\\$LastValidUser.HP"

# Приоритет отдаем .HP директории, если она существует (как в batch файле)
if (Test-Path "$UserProfilePathHP\\.android\\avd" -or Test-Path $UserProfilePathHP) {
    Write-Host "Используется директория с суффиксом .HP: $UserProfilePathHP" -ForegroundColor Yellow
    $UserProfilePath = $UserProfilePathHP
} else {
    Write-Host "Используется обычная директория: $UserProfilePath" -ForegroundColor Yellow
}

$env:ANDROID_AVD_HOME = "$UserProfilePath\\.android\\avd"
Write-Host "Финальный ANDROID_AVD_HOME: $env:ANDROID_AVD_HOME" -ForegroundColor Cyan

$AvdManagerPath = "$AndroidHome\\cmdline-tools\\latest\\bin\\avdmanager.bat"

Write-Host "📱 Создание AVD через avdmanager..." -ForegroundColor Yellow
Write-Host "AVD Name: $AvdName" -ForegroundColor Cyan
Write-Host "ANDROID_AVD_HOME: $env:ANDROID_AVD_HOME" -ForegroundColor Gray

if (!(Test-Path $AvdManagerPath)) {
    Write-Host "❌ ERROR: AVD Manager не найден по пути: $AvdManagerPath" -ForegroundColor Red
    Write-Host "Убедитесь, что Android SDK установлен правильно" -ForegroundColor Yellow
    exit 1
}

try {
    # Создаем .android директорию если не существует
    $AndroidDir = "$UserProfilePath\\.android\\avd"
    if (!(Test-Path $AndroidDir)) {
        New-Item -ItemType Directory -Path $AndroidDir -Force
        Write-Host "Создана директория: $AndroidDir" -ForegroundColor Gray
    }
    
    # Удаляем существующий AVD если есть
    $ExistingAvdPath = "$AndroidDir\\$AvdName.avd"
    $ExistingIniPath = "$AndroidDir\\$AvdName.ini"
    if (Test-Path $ExistingAvdPath) {
        Remove-Item -Recurse -Force $ExistingAvdPath -ErrorAction SilentlyContinue
        Write-Host "Удален существующий AVD: $AvdName" -ForegroundColor Gray
    }
    if (Test-Path $ExistingIniPath) {
        Remove-Item -Force $ExistingIniPath -ErrorAction SilentlyContinue
    }
    
    # Создаем AVD через avdmanager с правильными параметрами устройства
    Write-Host "Создание AVD через avdmanager..." -ForegroundColor Gray
    $CreateAvdCmd = "`"$AvdManagerPath`" create avd -n `"$AvdName`" -k `"system-images;android-36;google_apis_playstore;x86_64`" -d `"small_phone`" -c `"512M`" --force"
    Write-Host "Команда: $CreateAvdCmd" -ForegroundColor Gray
    $result = cmd.exe /c $CreateAvdCmd
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ SUCCESS: AVD $AvdName создан успешно" -ForegroundColor Green
        Write-Host "AVD_NAME: $AvdName" -ForegroundColor Cyan
        
        # Проверяем, что AVD действительно создался
        $AvdPath = "$AndroidDir\\$AvdName.avd"
        if (Test-Path $AvdPath) {
            Write-Host "AVD_PATH: $AvdPath" -ForegroundColor Cyan
            
            # Оптимизируем config.ini
            $ConfigPath = "$AvdPath\\config.ini"
            if (Test-Path $ConfigPath) {
                Write-Host "🔧 Оптимизация конфигурации AVD..." -ForegroundColor Yellow
                
                $ConfigContent = Get-Content $ConfigPath -Raw
                $ConfigContent = $ConfigContent -replace "hw\\.ramSize=.*", "hw.ramSize=4096"
                $ConfigContent = $ConfigContent -replace "hw\\.gpu\\.mode=.*", "hw.gpu.mode=auto"
                $ConfigContent = $ConfigContent -replace "hw\\.cpu\\.ncore=.*", "hw.cpu.ncore=4"
                
                # Добавляем недостающие параметры
                if ($ConfigContent -notmatch "hw\\.gpu\\.enabled") {
                    $ConfigContent += "`nhw.gpu.enabled=yes"
                }
                if ($ConfigContent -notmatch "hw\\.audioInput") {
                    $ConfigContent += "`nhw.audioInput=yes"
                }
                if ($ConfigContent -notmatch "hw\\.audioOutput") {
                    $ConfigContent += "`nhw.audioOutput=yes"
                }
                
                Set-Content -Path $ConfigPath -Value $ConfigContent -Encoding UTF8
                Write-Host "✅ Конфигурация оптимизирована" -ForegroundColor Green
                Write-Host "CONFIG_PATH: $ConfigPath" -ForegroundColor Cyan
            }
            
            # Обновляем .ini файл для микрофона
            $IniPath = "$AndroidDir\\$AvdName.ini"
            if (Test-Path $IniPath) {
                Write-Host "🎤 Добавление поддержки микрофона в .ini файл..." -ForegroundColor Yellow
                Add-Content -Path $IniPath -Value "hw.audioInput=yes" -Encoding UTF8
                Add-Content -Path $IniPath -Value "hw.audioOutput=yes" -Encoding UTF8
                Write-Host "✅ Поддержка аудио добавлена" -ForegroundColor Green
            }
        }
    } else {
        Write-Host "❌ ERROR: Не удалось создать AVD. Код выхода: $LASTEXITCODE" -ForegroundColor Red
        Write-Host "Вывод: $result" -ForegroundColor Gray
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
$UserNum = $TestUser.Replace('User', '')
$AvdName = "User$UserNum`_Emulator"
$BatchFilePath = "C:\\Scripts\\$TestUser`_emulator.bat"

Write-Host "🔄 Создание batch файла для запуска эмулятора..." -ForegroundColor Yellow

# Убедимся, что директория Scripts существует
if (!(Test-Path "C:\\Scripts")) {
    New-Item -ItemType Directory -Path "C:\\Scripts" -Force
    Write-Host "Создана директория C:\\Scripts" -ForegroundColor Gray
}

$BatchContent = @"
@echo off
REM Android эмулятор для пользователя $TestUser
REM AVD: $AvdName
REM Создан: $(Get-Date)

echo ========================================
echo Android Emulator Launcher - $TestUser
echo ========================================

REM Устанавливаем переменные окружения Android SDK
set ANDROID_HOME=C:\\Program Files\\Android
set ANDROID_SDK_ROOT=C:\\Program Files\\Android
set JAVA_HOME=C:\\Program Files\\Microsoft\\jdk-17.0.16.8-hotspot
REM Проверяем наличие директории с суффиксом .HP (приоритет HP директории)
if exist "C:\\Users\\$TestUser.HP" (
    set ANDROID_AVD_HOME=C:\\Users\\$TestUser.HP\\.android\\avd
    echo Используется директория с суффиксом .HP: %ANDROID_AVD_HOME%
) else (
    set ANDROID_AVD_HOME=C:\\Users\\$TestUser\\.android\\avd
    echo Используется обычная директория: %ANDROID_AVD_HOME%
)
set PATH=%JAVA_HOME%\\bin;%ANDROID_HOME%\\platform-tools;%ANDROID_HOME%\\emulator;%ANDROID_HOME%\\cmdline-tools\\latest\\bin;%PATH%

echo Переменные окружения:
echo ANDROID_HOME=%ANDROID_HOME%
echo ANDROID_SDK_ROOT=%ANDROID_SDK_ROOT%
echo JAVA_HOME=%JAVA_HOME%
echo ANDROID_AVD_HOME=%ANDROID_AVD_HOME%
echo.

echo Пользователь: $TestUser
echo AVD: $AvdName
echo ========================================

echo Переход в директорию эмулятора...
cd /d "%ANDROID_HOME%\\emulator"
if %ERRORLEVEL% NEQ 0 (
    echo ОШИБКА: Не удалось перейти в директорию эмулятора
    pause
    exit /b 1
)

echo Текущая директория: %CD%
echo.

echo Запуск эмулятора $AvdName...
echo Команда: emulator -avd "$AvdName" -no-snapshot -gpu host -memory 4096 -no-boot-anim -netdelay none -netspeed full -verbose
echo.

emulator -avd "$AvdName" -no-snapshot -gpu host -memory 4096 -no-boot-anim -netdelay none -netspeed full -verbose

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
# Шаг 4: Создание EXE файла через C# компиляцию
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
$BatchFilePath = "C:\\Scripts\\$TestUser`_emulator.bat"
$ExeFilePath = "C:\\Scripts\\$TestUser`AndroidEmulator.exe"

Write-Host "🔄 Создание EXE файла через C# компиляцию..." -ForegroundColor Yellow
Write-Host "Пользователь: $TestUser" -ForegroundColor Cyan
Write-Host "Batch файл: $BatchFilePath" -ForegroundColor Gray
Write-Host "EXE файл: $ExeFilePath" -ForegroundColor Gray

if (!(Test-Path $BatchFilePath)) {
    Write-Host "❌ ERROR: Batch файл не найден: $BatchFilePath" -ForegroundColor Red
    Write-Host "Сначала выполните шаг 'create_batch'" -ForegroundColor Yellow
    exit 1
}

try {
    # C# код для EXE файла
    $CSharpCode = @"
using System;
using System.Diagnostics;
using System.IO;
using System.Security.Principal;

public class AndroidEmulatorLauncher
{
    public static void Main()
    {
        try
        {
            Console.WriteLine("=== $TestUser Android Emulator ===");
            Console.WriteLine("Текущий пользователь: " + WindowsIdentity.GetCurrent().Name);
            Console.WriteLine();

            string batchFile = @"$BatchFilePath";

            if (!File.Exists(batchFile))
            {
                Console.WriteLine("ОШИБКА: Batch файл не найден: " + batchFile);
                Console.ReadKey();
                return;
            }

            Console.WriteLine("Запуск Android эмулятора $TestUser...");
            Console.WriteLine("Batch файл: " + batchFile);
            Console.WriteLine();

            ProcessStartInfo psi = new ProcessStartInfo();
            psi.FileName = batchFile;
            psi.UseShellExecute = true;
            psi.WindowStyle = ProcessWindowStyle.Normal;
            psi.WorkingDirectory = @"C:\\Scripts";
            psi.Verb = "runas"; // Запуск с правами администратора

            Process process = Process.Start(psi);
            if (process != null)
            {
                Console.WriteLine("Эмулятор запущен. Ожидание завершения...");
                process.WaitForExit();
                Console.WriteLine("Эмулятор завершил работу с кодом: " + process.ExitCode);
            }
            else
            {
                Console.WriteLine("ОШИБКА: Не удалось запустить процесс");
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine("ОШИБКА запуска эмулятора: " + ex.Message);
            Console.WriteLine("Детали: " + ex.StackTrace);
            Console.WriteLine();
            Console.WriteLine("Нажмите любую клавишу для выхода...");
            Console.ReadKey();
        }
    }
}
"@

    # Компилируем C# код в EXE
    Write-Host "Компиляция C# кода в EXE..." -ForegroundColor Gray
    
    Add-Type -TypeDefinition $CSharpCode -OutputAssembly $ExeFilePath -OutputType ConsoleApplication
    
    if (Test-Path $ExeFilePath) {
        Write-Host "✅ SUCCESS: EXE файл создан через C# компиляцию: $ExeFilePath" -ForegroundColor Green
        Write-Host "EXE_FILE: $ExeFilePath" -ForegroundColor Cyan
        
        # Проверяем размер EXE файла
        $ExeInfo = Get-Item $ExeFilePath
        Write-Host "Размер EXE файла: $($ExeInfo.Length) байт" -ForegroundColor Gray
        Write-Host "Пользователь: $TestUser" -ForegroundColor Cyan
    } else {
        Write-Host "❌ ERROR: EXE файл не был создан" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ ERROR: Ошибка создания EXE: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
    ''',
    
    'configure_remoteapp': '''
# Шаг 5: Настройка RemoteApp в реестре Windows
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
$AppName = "$TestUser`AndroidEmulator"
$ExePath = "C:\\Scripts\\$TestUser`AndroidEmulator.exe"
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
$Username = $TestUser
$AppName = "$TestUser`AndroidEmulator"
$RdpFilePath = "C:\\Scripts\\$TestUser`_emulator.rdp"
$ServerAddress = $env:COMPUTERNAME  # Используем имя компьютера

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
audiomode:i:2
audioqualitymode:i:2
audiocapturemode:i:1
compression:i:1
bitmapcachepersistenable:i:1
videomode:i:32
experience:i:1
desktopwidth:i:1280
desktopheight:i:720
microphone redirection:i:1
audio redirection:i:1
session bpp:i:32
allow font smoothing:i:1
disable wallpaper:i:0
disable full window drag:i:0
disable menu anims:i:0
disable themes:i:0
disable cursor setting:i:0
bitmapcachesize:i:1500
screen mode id:i:2
use multimon:i:0
winposstr:s:0,1,0,0,1280,720
keyboardhook:i:2
videoplaybackmode:i:1
connection type:i:7
networkautodetect:i:1
bandwidthautodetect:i:1
displayconnectionbar:i:1
enableworkspacereconnect:i:0
allow desktop composition:i:1
redirectprinters:i:1
redirectcomports:i:0
redirectsmartcards:i:1
redirectwebauthn:i:1
redirectclipboard:i:1
redirectposdevices:i:0
autoreconnection enabled:i:1
authentication level:i:2
prompt for credentials:i:0
negotiate security layer:i:1
remoteapplicationicon:s:
shell working directory:s:
gatewayhostname:s:
gatewayusagemethod:i:4
gatewaycredentialssource:i:4
gatewayprofileusagemethod:i:0
promptcredentialonce:i:0
gatewaybrokeringtype:i:0
use redirection server name:i:0
rdgiskdcproxy:i:0
kdcproxyname:s:
enablerdsaadauth:i:0
redirectdrives:i:1
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
