# -*- coding: utf-8 -*-
"""
Скрипты для пошагового тестирования Android Emulator RemoteApp
Каждый шаг можно тестировать отдельно для диагностики проблем
"""

# Словарь со всеми шагами тестирования
STEP_SCRIPTS = {
    'create_user': r'''
# Шаг 1: Создание пользователя Windows

# Поиск следующего доступного номера пользователя через net user
$AllUsers = net user | Where-Object { $_ -match "User\d+" }
$UserNumbers = @()
foreach ($line in $AllUsers) {
    $users = $line -split '\s+' | Where-Object { $_ -match "^User\d+$" }
    foreach ($user in $users) {
        if ($user -match "^User(\d+)$") {
            $UserNumbers += [int]$matches[1]
        }
    }
}

if ($UserNumbers.Count -gt 0) {
    $MaxUserNumber = ($UserNumbers | Measure-Object -Maximum).Maximum
    $UserNumber = $MaxUserNumber + 1
} else {
    $UserNumber = 1
}

$Username = "User$UserNumber"
Write-Host "Найдены пользователи: $($UserNumbers -join ', ')" -ForegroundColor Gray
Write-Host "Создается новый пользователь: $Username" -ForegroundColor Gray

# Используем единый пароль для всех операторов
$Password = if ($env:OPERATOR_PASSWORD) { $env:OPERATOR_PASSWORD } else { "UniCo2022" }

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

# Группа Administrators (S-1-5-32-544) для RemoteApp
$AdminGroup = Get-LocalGroup -SID "S-1-5-32-544" -ErrorAction SilentlyContinue
if ($AdminGroup) {
    Add-LocalGroupMember -Group $AdminGroup.Name -Member $Username -ErrorAction SilentlyContinue
    Write-Host "Добавлен в группу Administrators: $($AdminGroup.Name)" -ForegroundColor Green
} else {
    Write-Host "Не удалось найти группу Administrators" -ForegroundColor Red
}

# Назначаем права доступа для совместимости с RemoteApp
try {
    $UserProfilePath = "C:\\Users\\$Username"
    $UserProfilePathHP = "C:\\Users\\$Username.HP"
    
    # Ждем создания профиля (может потребоваться время)
    Start-Sleep -Seconds 2
    
    # Проверяем какой профиль создался (с .HP или без)
    $ActualProfilePath = $UserProfilePath
    if (Test-Path $UserProfilePathHP) {
        $ActualProfilePath = $UserProfilePathHP
        Write-Host "Обнаружен профиль с суффиксом .HP: $UserProfilePathHP" -ForegroundColor Yellow
    } elseif (Test-Path $UserProfilePath) {
        Write-Host "Обнаружен обычный профиль: $UserProfilePath" -ForegroundColor Yellow
    } else {
        Write-Host "⚠️ WARNING: Профиль пользователя не найден, ждем создания..." -ForegroundColor Yellow
        Start-Sleep -Seconds 3
        if (Test-Path $UserProfilePathHP) {
            $ActualProfilePath = $UserProfilePathHP
        }
    }
    
    if (Test-Path $ActualProfilePath) {
        Write-Host "🔐 Настройка прав доступа на профиль пользователя: $ActualProfilePath" -ForegroundColor Yellow
        icacls $ActualProfilePath /grant "Everyone:(OI)(CI)F" /T /Q | Out-Null
        icacls $ActualProfilePath /grant "Users:(OI)(CI)F" /T /Q | Out-Null
        Write-Host "✅ Права доступа на профиль назначены (Everyone, Users)" -ForegroundColor Green
        
        # Создаем .android директорию заранее с правильными правами
        $AndroidBaseDir = "$ActualProfilePath\\.android"
        if (!(Test-Path $AndroidBaseDir)) {
            New-Item -ItemType Directory -Path $AndroidBaseDir -Force | Out-Null
            Write-Host "Создана базовая директория Android: $AndroidBaseDir" -ForegroundColor Gray
        }
        
        # Создаем все необходимые поддиректории для эмулятора
        @("avd", "cache", "temp", "emulator", "logs") | ForEach-Object {
            $SubDir = "$AndroidBaseDir\\$_"
            if (!(Test-Path $SubDir)) {
                New-Item -ItemType Directory -Path $SubDir -Force | Out-Null
                Write-Host "Создана директория: $SubDir" -ForegroundColor Gray
            }
        }
        
        # Назначаем полные права на весь профиль пользователя (необходимо для RemoteApp)
        Write-Host "🔐 Настройка полных прав доступа для RemoteApp..." -ForegroundColor Yellow
        icacls $ActualProfilePath /grant "Everyone:(OI)(CI)F" /T /Q | Out-Null
        icacls $ActualProfilePath /grant "Users:(OI)(CI)F" /T /Q | Out-Null
        icacls $ActualProfilePath /grant "Administrators:(OI)(CI)F" /T /Q | Out-Null
        icacls $ActualProfilePath /grant "SYSTEM:(OI)(CI)F" /T /Q | Out-Null
        
        # Дополнительно назначаем права на .android директорию
        icacls $AndroidBaseDir /grant "Everyone:(OI)(CI)F" /T /Q | Out-Null
        icacls $AndroidBaseDir /grant "Users:(OI)(CI)F" /T /Q | Out-Null
        icacls $AndroidBaseDir /grant "Administrators:(OI)(CI)F" /T /Q | Out-Null
        icacls $AndroidBaseDir /grant "SYSTEM:(OI)(CI)F" /T /Q | Out-Null
        
        # Создаем пустые файлы для предотвращения ошибок блокировки
        $LockFiles = @(
            "$AndroidBaseDir\\emu-last-feature-flags.protobuf",
            "$AndroidBaseDir\\emu-last-feature-flags.protobuf.lock",
            "$AndroidBaseDir\\emulator-check.exe.lock"
        )
        
        foreach ($LockFile in $LockFiles) {
            if (!(Test-Path $LockFile)) {
                try {
                    New-Item -ItemType File -Path $LockFile -Force | Out-Null
                    # Назначаем полные права на lock файлы
                    icacls $LockFile /grant "Everyone:F" /Q | Out-Null
                    icacls $LockFile /grant "Users:F" /Q | Out-Null
                    icacls $LockFile /grant "Administrators:F" /Q | Out-Null
                    icacls $LockFile /grant "SYSTEM:F" /Q | Out-Null
                    Write-Host "Создан lock файл: $LockFile" -ForegroundColor Gray
                } catch {
                    Write-Host "⚠️ Не удалось создать lock файл: $LockFile" -ForegroundColor Yellow
                }
            }
        }
        
        Write-Host "✅ Права доступа и lock файлы настроены" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️  Не удалось назначить права на профиль: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Результат
Write-Host "SUCCESS: Пользователь $Username создан успешно" -ForegroundColor Green
Write-Host "USERNAME: $Username" -ForegroundColor Cyan
Write-Host "PASSWORD: $Password" -ForegroundColor Yellow
Write-Host "PASSWORD CHANGE: Запрещена" -ForegroundColor Cyan
Write-Host "ВАЖНО: Используйте пароль '$Password' для RDP подключения!" -ForegroundColor Yellow

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
    
    'copy_template_avd': r'''
# Шаг 2: Копирование готового AVD с предустановленными приложениями из phone1
Write-Host "=== COPYING AVD FROM PHONE1 TEMPLATE ===" -ForegroundColor Yellow

# Находим последнего созданного пользователя через net user
$AllUsers = net user | Where-Object { $_ -match "User\d+" }
$UserNumbers = @()
foreach ($line in $AllUsers) {
    $users = $line -split '\s+' | Where-Object { $_ -match "^User\d+$" }
    foreach ($user in $users) {
        if ($user -match "^User(\d+)$") {
            $UserNumbers += [int]$matches[1]
        }
    }
}

if ($UserNumbers.Count -gt 0) {
    $MaxUserNumber = ($UserNumbers | Measure-Object -Maximum).Maximum
    $LastValidUser = "User$MaxUserNumber"
    Write-Host "Found users: $($UserNumbers -join ', ')" -ForegroundColor Gray
    Write-Host "Using user: $LastValidUser" -ForegroundColor Gray
} else {
    Write-Host "ERROR: Could not find User* users" -ForegroundColor Red
    exit 1
}

# Form names
$UserNum = $LastValidUser.Replace('User', '')
$EmulatorName = if ($env:EMULATOR_NAME) { $env:EMULATOR_NAME } else { "Emulator" }
$SafeEmulatorName = $EmulatorName -replace '[^a-zA-Z0-9_]', '_'
$AvdName = "User$UserNum`_$SafeEmulatorName"

# Template settings - phone1 with apps (~12 GB)
$TemplateAvdPath = "C:\\Users\\user\\.android\\avd\\phone1.avd"

Write-Host "Template AVD: $TemplateAvdPath" -ForegroundColor Gray
Write-Host "New AVD: $AvdName" -ForegroundColor Cyan

# Check template existence
if (!(Test-Path $TemplateAvdPath)) {
    Write-Host "ERROR: Template AVD not found: $TemplateAvdPath" -ForegroundColor Red
    exit 1
} else {
    Write-Host "SUCCESS: Template found!" -ForegroundColor Green
}

# Get template size
$TemplateSize = (Get-ChildItem -Path $TemplateAvdPath -Recurse | Measure-Object -Property Length -Sum).Sum
$TemplateSizeMB = [math]::Round($TemplateSize / 1MB, 2)
Write-Host "Template size: $TemplateSizeMB MB" -ForegroundColor Gray

# Determine target paths - check main directory first, then .HP
$UserProfilePath = "C:\\Users\\$LastValidUser"
$UserProfilePathHP = "C:\\Users\\$LastValidUser.HP"

# Check which directory has .android folder or use main directory
$MainAndroidDir = "$UserProfilePath\\.android"
$HPAndroidDir = "$UserProfilePathHP\\.android"

if (Test-Path $MainAndroidDir) {
    $ActualUserProfile = $UserProfilePath
    Write-Host "Using main profile (has .android): $ActualUserProfile" -ForegroundColor Gray
} elseif (Test-Path $HPAndroidDir) {
    $ActualUserProfile = $UserProfilePathHP
    Write-Host "Using HP profile (has .android): $ActualUserProfile" -ForegroundColor Gray
} elseif (Test-Path $UserProfilePath) {
    $ActualUserProfile = $UserProfilePath
    Write-Host "Using main profile (exists): $ActualUserProfile" -ForegroundColor Gray
} else {
    $ActualUserProfile = $UserProfilePathHP
    Write-Host "Using HP profile (fallback): $ActualUserProfile" -ForegroundColor Gray
}

$AndroidBaseDir = "$ActualUserProfile\\.android"
$TargetAndroidDir = "$AndroidBaseDir\\avd"
$TargetAvdPath = "$TargetAndroidDir\\$AvdName.avd"
$TargetIniPath = "$TargetAndroidDir\\$AvdName.ini"

try {
    # Create directories
    if (!(Test-Path $AndroidBaseDir)) {
        New-Item -ItemType Directory -Path $AndroidBaseDir -Force | Out-Null
        Write-Host "Created directory: $AndroidBaseDir" -ForegroundColor Gray
    }
    if (!(Test-Path $TargetAndroidDir)) {
        New-Item -ItemType Directory -Path $TargetAndroidDir -Force | Out-Null
        Write-Host "Created directory: $TargetAndroidDir" -ForegroundColor Gray
    }

    # Create lock files to prevent errors
    Write-Host "Creating lock files..." -ForegroundColor Yellow
    $LockFiles = @(
        "$AndroidBaseDir\\emu-last-feature-flags.protobuf",
        "$AndroidBaseDir\\emu-last-feature-flags.protobuf.lock",
        "$AndroidBaseDir\\emulator-check.exe.lock",
        "$AndroidBaseDir\\pid.lock",
        "$AndroidBaseDir\\cache.lock",
        "$AndroidBaseDir\\modem-nv-ram-5554",
        "$AndroidBaseDir\\modem-nv-ram-5556"
    )

    foreach ($LockFile in $LockFiles) {
        if (!(Test-Path $LockFile)) {
            New-Item -ItemType File -Path $LockFile -Force -ErrorAction SilentlyContinue | Out-Null
        }
    }

    # Remove existing AVD if exists
    if (Test-Path $TargetAvdPath) {
        Write-Host "Removing existing AVD..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force $TargetAvdPath -ErrorAction SilentlyContinue
    }
    if (Test-Path $TargetIniPath) {
        Remove-Item -Force $TargetIniPath -ErrorAction SilentlyContinue
    }

    # Copy AVD from template (main operation)
    Write-Host "Copying AVD from phone1 template..." -ForegroundColor Yellow
    $StartTime = Get-Date
    Copy-Item -Path $TemplateAvdPath -Destination $TargetAvdPath -Recurse -Force
    $EndTime = Get-Date
    $Duration = ($EndTime - $StartTime).TotalSeconds
    Write-Host "AVD copied in $([math]::Round($Duration, 1)) seconds" -ForegroundColor Green

    # Update config.ini with new paths
    $ConfigPath = "$TargetAvdPath\\config.ini"
    if (Test-Path $ConfigPath) {
        Write-Host "Updating config.ini..." -ForegroundColor Yellow
        $ConfigContent = Get-Content $ConfigPath
        $ConfigContent = $ConfigContent -replace "phone1", $AvdName
        $ConfigContent = $ConfigContent -replace "user", $LastValidUser
        $ConfigContent = $ConfigContent -replace "C:\\\\Users\\\\user", $ActualUserProfile
        
        # Add network settings for internet
        $NetworkSettings = @{
            "hw.gps" = "yes"
            "hw.gsmModem" = "yes"
            "hw.network" = "yes"
            "hw.wifi" = "yes"
            "netfast" = "yes"
            "netdelay" = "none"
            "netspeed" = "full"
        }
        
        $NewConfigContent = @()
        $SettingsAdded = @{}
        
        foreach ($line in $ConfigContent) {
            $NewConfigContent += $line
            # Mark which settings already exist
            foreach ($setting in $NetworkSettings.Keys) {
                if ($line -match "^$setting=") {
                    $SettingsAdded[$setting] = $true
                }
            }
        }
        
        # Add missing settings
        foreach ($setting in $NetworkSettings.Keys) {
            if (-not $SettingsAdded[$setting]) {
                $NewConfigContent += "$setting=$($NetworkSettings[$setting])"
            }
        }
        
        Set-Content -Path $ConfigPath -Value $NewConfigContent -Encoding UTF8
        Write-Host "config.ini updated" -ForegroundColor Green
    } else {
        Write-Host "WARNING: config.ini not found" -ForegroundColor Yellow
    }

    # Create .ini file
    $IniContent = @"
avd.ini.encoding=UTF-8
path=$TargetAvdPath
path.rel=avd\\$AvdName.avd
target=android-36
hw.audioInput=yes
hw.audioOutput=yes
"@
    Set-Content -Path $TargetIniPath -Value $IniContent -Encoding UTF8
    Write-Host ".ini file created" -ForegroundColor Green

    # Set permissions for RemoteApp
    Write-Host "Setting up permissions..." -ForegroundColor Yellow
    try {
        # Take ownership
        takeown /F "$AndroidBaseDir" /R /D Y 2>&1 | Out-Null
        
        # Set permissions using SIDs (more reliable)
        icacls "$AndroidBaseDir" /grant *S-1-1-0:(OI)(CI)F /T /C /Q 2>&1 | Out-Null      # Everyone
        icacls "$AndroidBaseDir" /grant *S-1-5-18:(OI)(CI)F /T /C /Q 2>&1 | Out-Null     # SYSTEM
        icacls "$AndroidBaseDir" /grant *S-1-5-32-545:(OI)(CI)F /T /C /Q 2>&1 | Out-Null # Users
        icacls "$AndroidBaseDir" /grant "$LastValidUser":(OI)(CI)F /T /C /Q 2>&1 | Out-Null
        
        # Set permissions on lock files specifically
        foreach ($LockFile in $LockFiles) {
            if (Test-Path $LockFile) {
                icacls "$LockFile" /grant *S-1-1-0:F /C /Q 2>&1 | Out-Null  # Everyone
                icacls "$LockFile" /grant *S-1-5-18:F /C /Q 2>&1 | Out-Null  # SYSTEM
            }
        }
        
        Write-Host "Permissions configured" -ForegroundColor Green
    } catch {
        Write-Host "WARNING: Could not set some permissions" -ForegroundColor Yellow
    }

    # Show results and quality control
    $AvdSize = (Get-ChildItem -Path $TargetAvdPath -Recurse | Measure-Object -Property Length -Sum).Sum
    $AvdSizeMB = [math]::Round($AvdSize / 1MB, 2)
    
    # Quality control - check file count
    $TemplateFileCount = (Get-ChildItem -Path $TemplateAvdPath -Recurse -File).Count
    $TargetFileCount = (Get-ChildItem -Path $TargetAvdPath -Recurse -File).Count

    Write-Host ""
    Write-Host "SUCCESS: AVD successfully copied from phone1 template!" -ForegroundColor Green
    Write-Host "AVD_NAME: $AvdName" -ForegroundColor Cyan
    Write-Host "AVD_PATH: $TargetAvdPath" -ForegroundColor Cyan
    Write-Host "AVD_SIZE: $AvdSizeMB MB (template: $TemplateSizeMB MB)" -ForegroundColor Cyan
    Write-Host "FILES: $TargetFileCount (template: $TemplateFileCount)" -ForegroundColor Cyan
    
    if ($TargetFileCount -eq $TemplateFileCount) {
        Write-Host "SUCCESS: File count matches - copy successful!" -ForegroundColor Green
    } else {
        Write-Host "WARNING: File count mismatch - possible issues" -ForegroundColor Yellow
    }
    
    Write-Host "COPY TIME: $([math]::Round($Duration, 1)) seconds" -ForegroundColor Gray
    Write-Host ""

} catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
    ''',
    
    
    'create_batch': r'''
# Шаг 3: Создание batch файла без BOM для запуска эмулятора
Write-Host "=== CREATING BATCH FILE (NO BOM) ===" -ForegroundColor Yellow

# Find last user via net user
$AllUsers = net user | Where-Object { $_ -match "User\d+" }
$UserNumbers = @()
foreach ($line in $AllUsers) {
    $users = $line -split '\s+' | Where-Object { $_ -match "^User\d+$" }
    foreach ($user in $users) {
        if ($user -match "^User(\d+)$") {
            $UserNumbers += [int]$matches[1]
        }
    }
}

if ($UserNumbers.Count -gt 0) {
    $MaxUserNumber = ($UserNumbers | Measure-Object -Maximum).Maximum
    $LastValidUser = "User$MaxUserNumber"
    Write-Host "Using user: $LastValidUser" -ForegroundColor Gray
} else {
    Write-Host "ERROR: Could not find User* users" -ForegroundColor Red
    exit 1
}

# Form names
$UserNum = $LastValidUser.Replace('User', '')
$EmulatorName = if ($env:EMULATOR_NAME) { $env:EMULATOR_NAME } else { "Emulator" }
$SafeEmulatorName = $EmulatorName -replace '[^a-zA-Z0-9_]', '_'
$AvdName = "User$UserNum`_$SafeEmulatorName"

# Determine paths - check main directory first, then .HP
$UserProfilePath = "C:\\Users\\$LastValidUser"
$UserProfilePathHP = "C:\\Users\\$LastValidUser.HP"

# Check which directory has .android folder or use main directory
$MainAndroidDir = "$UserProfilePath\\.android"
$HPAndroidDir = "$UserProfilePathHP\\.android"

if (Test-Path $MainAndroidDir) {
    $ActualUserProfile = $UserProfilePath
    Write-Host "Using main profile (has .android): $ActualUserProfile" -ForegroundColor Gray
} elseif (Test-Path $HPAndroidDir) {
    $ActualUserProfile = $UserProfilePathHP
    Write-Host "Using HP profile (has .android): $ActualUserProfile" -ForegroundColor Gray
} elseif (Test-Path $UserProfilePath) {
    $ActualUserProfile = $UserProfilePath
    Write-Host "Using main profile (exists): $ActualUserProfile" -ForegroundColor Gray
} else {
    $ActualUserProfile = $UserProfilePathHP
    Write-Host "Using HP profile (fallback): $ActualUserProfile" -ForegroundColor Gray
}

# Create batch file
$BatchFilePath = "C:\\Scripts\\$AvdName.bat"

Write-Host "Creating batch file: $BatchFilePath" -ForegroundColor Cyan

# Ensure Scripts directory exists
if (!(Test-Path "C:\\Scripts")) {
    New-Item -ItemType Directory -Path "C:\\Scripts" -Force | Out-Null
}

# Create batch content with proper encoding (NO BOM)
$BatchContent = @"
@echo off
REM ========================================
REM Android Emulator Launcher - $AvdName
REM Fixed version without BOM
REM ========================================

REM === Set user profile explicitly ===
set USERPROFILE=$ActualUserProfile
set JAVA_HOME=C:\\Program Files\\Microsoft\\jdk-17.0.16.8-hotspot

REM === Android SDK paths ===
set ANDROID_HOME=C:\\Program Files\\Android
set ANDROID_SDK_ROOT=%ANDROID_HOME%
set ANDROID_PREFS_ROOT=%USERPROFILE%\\.android
set ANDROID_AVD_HOME=%USERPROFILE%\\.android\\avd

REM === Update PATH ===
set PATH=%JAVA_HOME%\\bin;%ANDROID_HOME%\\platform-tools;%ANDROID_HOME%\\emulator;%ANDROID_HOME%\\cmdline-tools\\latest\\bin;%PATH%

echo ========================================
echo ANDROID EMULATOR LAUNCHER
echo ========================================
echo USERPROFILE=%USERPROFILE%
echo ANDROID_HOME=%ANDROID_HOME%
echo ANDROID_AVD_HOME=%ANDROID_AVD_HOME%
echo AVD_NAME=$AvdName
echo ========================================
echo.

REM === Create directories if needed ===
if not exist "%ANDROID_PREFS_ROOT%" mkdir "%ANDROID_PREFS_ROOT%"
if not exist "%ANDROID_AVD_HOME%" mkdir "%ANDROID_AVD_HOME%"

REM === Clean lock files ===
if exist "%ANDROID_PREFS_ROOT%\\*.lock" del /Q "%ANDROID_PREFS_ROOT%\\*.lock" 2>nul
if exist "%ANDROID_AVD_HOME%\\*.lock" del /Q "%ANDROID_AVD_HOME%\\*.lock" 2>nul

REM === Launch emulator ===
set AVD_NAME=$AvdName
set EMULATOR_ARGS=-avd "%AVD_NAME%" -no-snapshot -gpu host -memory 4096 -no-boot-anim -netdelay none -netspeed full -dns-server 8.8.8.8

echo Starting emulator: %AVD_NAME%
echo Command: emulator %EMULATOR_ARGS%
echo.

cd /d "%ANDROID_HOME%\\emulator"
emulator %EMULATOR_ARGS%

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Emulator failed to start
    echo Trying with -read-only flag...
    emulator %EMULATOR_ARGS% -read-only
)

echo.
echo [INFO] Emulator session ended
pause
"@

# Write batch file with ASCII encoding (NO BOM)
try {
    # Use .NET method to ensure no BOM
    [System.IO.File]::WriteAllText($BatchFilePath, $BatchContent, [System.Text.Encoding]::ASCII)
    
    Write-Host "SUCCESS: Batch file created without BOM!" -ForegroundColor Green
    Write-Host "BATCH_FILE: $BatchFilePath" -ForegroundColor Cyan
    
    # Check file size
    $FileInfo = Get-Item $BatchFilePath
    Write-Host "File size: $($FileInfo.Length) bytes" -ForegroundColor Gray
    
} catch {
    Write-Host "ERROR: Failed to create batch file: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
    ''',
    
    'convert_to_exe': r'''
# Шаг 4: Создание EXE файла через C# компиляцию
# Находим последнего созданного пользователя через net user
$AllUsers = net user | Where-Object { $_ -match "User\d+" }
$UserNumbers = @()
foreach ($line in $AllUsers) {
    $users = $line -split '\s+' | Where-Object { $_ -match "^User\d+$" }
    foreach ($user in $users) {
        if ($user -match "^User(\d+)$") {
            $UserNumbers += [int]$matches[1]
        }
    }
}

if ($UserNumbers.Count -gt 0) {
    $MaxUserNumber = ($UserNumbers | Measure-Object -Maximum).Maximum
    $LastValidUser = "User$MaxUserNumber"
} else {
    Write-Host "ERROR: Не удалось найти пользователей" -ForegroundColor Red
    exit 1
}

Write-Host "Найдены пользователи: $($UserNumbers -join ', ')" -ForegroundColor Gray
Write-Host "Используется пользователь: $LastValidUser" -ForegroundColor Gray

# Используем последнего созданного пользователя
$TestUser = $LastValidUser
$EmulatorName = if ($env:EMULATOR_NAME) { $env:EMULATOR_NAME } else { "Emulator" }
$SafeEmulatorName = $EmulatorName -replace '[^a-zA-Z0-9_]', '_'
$BatchFilePath = "C:\\Scripts\\$TestUser`_$SafeEmulatorName.bat"
$ExeFilePath = "C:\\Scripts\\$TestUser`_$SafeEmulatorName.exe"

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

    # Удаляем существующий EXE файл если он заблокирован
    if (Test-Path $ExeFilePath) {
        Write-Host "Удаление существующего EXE файла..." -ForegroundColor Yellow
        try {
            # Пытаемся завершить процессы, использующие файл
            $ProcessName = [System.IO.Path]::GetFileNameWithoutExtension($ExeFilePath)
            Get-Process -Name $ProcessName -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
            Start-Sleep -Milliseconds 500
            
            Remove-Item -Path $ExeFilePath -Force -ErrorAction Stop
            Write-Host "✅ Существующий EXE файл удален" -ForegroundColor Green
        } catch {
            Write-Host "⚠️ WARNING: Не удалось удалить существующий EXE: $($_.Exception.Message)" -ForegroundColor Yellow
            Write-Host "Попытка создания с уникальным именем..." -ForegroundColor Yellow
            $Timestamp = Get-Date -Format 'HHmmss'
            $ExeFilePath = $ExeFilePath -replace '\.exe$', ".$Timestamp.exe"
        }
    }
    
    # Компилируем C# код в EXE
    Write-Host "Компиляция C# кода в EXE..." -ForegroundColor Gray
    Write-Host "Путь к EXE: $ExeFilePath" -ForegroundColor Gray
    
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
    
    'configure_remoteapp': r'''
# Шаг 5: Настройка RemoteApp в реестре Windows
# Находим последнего созданного пользователя через net user
$AllUsers = net user | Where-Object { $_ -match "User\d+" }
$UserNumbers = @()
foreach ($line in $AllUsers) {
    $users = $line -split '\s+' | Where-Object { $_ -match "^User\d+$" }
    foreach ($user in $users) {
        if ($user -match "^User(\d+)$") {
            $UserNumbers += [int]$matches[1]
        }
    }
}

if ($UserNumbers.Count -gt 0) {
    $MaxUserNumber = ($UserNumbers | Measure-Object -Maximum).Maximum
    $LastValidUser = "User$MaxUserNumber"
} else {
    Write-Host "ERROR: Не удалось найти пользователей" -ForegroundColor Red
    exit 1
}

Write-Host "Найдены пользователи: $($UserNumbers -join ', ')" -ForegroundColor Gray
Write-Host "Используется пользователь: $LastValidUser" -ForegroundColor Gray

# Используем последнего созданного пользователя
$TestUser = $LastValidUser
$EmulatorName = if ($env:EMULATOR_NAME) { $env:EMULATOR_NAME } else { "Emulator" }
$SafeEmulatorName = $EmulatorName -replace '[^a-zA-Z0-9_]', '_'
$AppName = "$TestUser`_$SafeEmulatorName"
$BaseExePath = "C:\\Scripts\\$TestUser`_$SafeEmulatorName.exe"
$RemoteAppPath = "HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Terminal Server\\TSAppAllowList\\Applications"

Write-Host "🔄 Настройка RemoteApp в реестре..." -ForegroundColor Yellow

try {
    # Ищем EXE файл (может быть переименован из-за блокировки)
    $ExePath = $BaseExePath
    if (!(Test-Path $ExePath)) {
        # Ищем файлы с временными метками
        $ExePattern = "$TestUser`_$SafeEmulatorName.*.exe"
        $ExeFiles = Get-ChildItem -Path "C:\\Scripts" -Name $ExePattern -ErrorAction SilentlyContinue
        if ($ExeFiles.Count -gt 0) {
            $ExePath = "C:\\Scripts\\$($ExeFiles[0])"
            Write-Host "Найден переименованный EXE файл: $ExePath" -ForegroundColor Yellow
        } else {
            Write-Host "❌ ERROR: EXE файл не найден: $BaseExePath" -ForegroundColor Red
            Write-Host "Также проверены варианты: $ExePattern" -ForegroundColor Yellow
            Write-Host "Сначала выполните шаг 'convert_to_exe'" -ForegroundColor Yellow
            exit 1
        }
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
    
    'create_rdp': r'''
# Шаг 6: Создание RDP файла для подключения
# Находим последнего созданного пользователя через net user
$AllUsers = net user | Where-Object { $_ -match "User\d+" }
$UserNumbers = @()
foreach ($line in $AllUsers) {
    $users = $line -split '\s+' | Where-Object { $_ -match "^User\d+$" }
    foreach ($user in $users) {
        if ($user -match "^User(\d+)$") {
            $UserNumbers += [int]$matches[1]
        }
    }
}

if ($UserNumbers.Count -gt 0) {
    $MaxUserNumber = ($UserNumbers | Measure-Object -Maximum).Maximum
    $LastValidUser = "User$MaxUserNumber"
} else {
    Write-Host "ERROR: Не удалось найти пользователей" -ForegroundColor Red
    exit 1
}

Write-Host "Найдены пользователи: $($UserNumbers -join ', ')" -ForegroundColor Gray
Write-Host "Используется пользователь: $LastValidUser" -ForegroundColor Gray

# Используем последнего созданного пользователя
$TestUser = $LastValidUser
$Username = $TestUser
$EmulatorName = if ($env:EMULATOR_NAME) { $env:EMULATOR_NAME } else { "Emulator" }
$SafeEmulatorName = $EmulatorName -replace '[^a-zA-Z0-9_]', '_'
$AppName = "$TestUser`_$SafeEmulatorName"
$RdpFilePath = "C:\\Scripts\\$TestUser`_$SafeEmulatorName.rdp"
# Используем IP адрес из настроек (по умолчанию имя компьютера)
$ServerAddress = if ($env:RDP_IP) { $env:RDP_IP } else { $env:COMPUTERNAME }
$OperatorPassword = if ($env:OPERATOR_PASSWORD) { $env:OPERATOR_PASSWORD } else { "UniCo2022" }

Write-Host "🔄 Создание RDP файла..." -ForegroundColor Yellow

Write-Host "Создание RDP файла с запросом пароля при подключении" -ForegroundColor Gray

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
    Write-Host "Пароль: $OperatorPassword" -ForegroundColor Yellow
    Write-Host "При подключении введите указанный пароль" -ForegroundColor Yellow
    
} catch {
    Write-Host "❌ ERROR: Ошибка создания RDP файла: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
    ''',
    
    'delete_operator': r'''
# Удаление оператора и всех его эмуляторов
# Получаем имя оператора из переменных окружения
$OperatorUsername = if ($env:OPERATORUSERNAME) { $env:OPERATORUSERNAME } else { 
    Write-Host "❌ ERROR: Не указано имя оператора для удаления" -ForegroundColor Red
    exit 1
}

Write-Host "🗑️ Удаление оператора: $OperatorUsername" -ForegroundColor Red
Write-Host "Это действие удалит пользователя, все эмуляторы и файлы!" -ForegroundColor Yellow

try {
    # 1. Получаем список всех эмуляторов оператора из реестра RemoteApp
    $RemoteAppPath = "HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Terminal Server\\TSAppAllowList\\Applications"
    $EmulatorApps = @()
    
    if (Test-Path $RemoteAppPath) {
        $Apps = Get-ChildItem -Path $RemoteAppPath -ErrorAction SilentlyContinue
        foreach ($App in $Apps) {
            $AppName = $App.PSChildName
            if ($AppName -like "$OperatorUsername*") {
                $EmulatorApps += $AppName
                Write-Host "Найден эмулятор: $AppName" -ForegroundColor Gray
            }
        }
    }
    
    # 2. Удаляем все файлы эмуляторов (batch, exe, rdp)
    Write-Host "🗑️ Удаление файлов эмуляторов..." -ForegroundColor Yellow
    $FilesToDelete = @()
    
    # Ищем файлы по паттерну
    $Patterns = @(
        "$OperatorUsername*_*.bat",
        "$OperatorUsername*_*.exe", 
        "$OperatorUsername*_*.rdp",
        "$OperatorUsername*.bat",
        "$OperatorUsername*.exe",
        "$OperatorUsername*.rdp"
    )
    
    foreach ($Pattern in $Patterns) {
        $Files = Get-ChildItem -Path "C:\\Scripts" -Name $Pattern -ErrorAction SilentlyContinue
        foreach ($File in $Files) {
            $FilePath = "C:\\Scripts\\$File"
            $FilesToDelete += $FilePath
        }
    }
    
    # Удаляем найденные файлы
    foreach ($File in $FilesToDelete) {
        if (Test-Path $File) {
            try {
                # Завершаем процессы, использующие файл
                $FileName = [System.IO.Path]::GetFileNameWithoutExtension($File)
                Get-Process -Name $FileName -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
                Start-Sleep -Milliseconds 200
                
                Remove-Item -Path $File -Force -ErrorAction Stop
                Write-Host "Удален файл: $File" -ForegroundColor Gray
            } catch {
                Write-Host "⚠️ Не удалось удалить файл: $File - $($_.Exception.Message)" -ForegroundColor Yellow
            }
        }
    }
    
    # 3. Удаляем записи из реестра RemoteApp
    Write-Host "🗑️ Удаление записей RemoteApp из реестра..." -ForegroundColor Yellow
    foreach ($AppName in $EmulatorApps) {
        try {
            $AppKeyPath = "$RemoteAppPath\\$AppName"
            if (Test-Path $AppKeyPath) {
                Remove-Item -Path $AppKeyPath -Recurse -Force -ErrorAction Stop
                Write-Host "Удалена запись RemoteApp: $AppName" -ForegroundColor Gray
            }
        } catch {
            Write-Host "⚠️ Не удалось удалить запись RemoteApp: $AppName - $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }
    
    # 4. Удаляем AVD файлы пользователя
    Write-Host "🗑️ Удаление AVD файлов..." -ForegroundColor Yellow
    $UserProfilePaths = @(
        "C:\\Users\\$OperatorUsername",
        "C:\\Users\\$OperatorUsername.HP"
    )
    
    foreach ($ProfilePath in $UserProfilePaths) {
        if (Test-Path $ProfilePath) {
            $AndroidDir = "$ProfilePath\\.android"
            if (Test-Path $AndroidDir) {
                try {
                    Remove-Item -Path $AndroidDir -Recurse -Force -ErrorAction Stop
                    Write-Host "Удалена директория Android: $AndroidDir" -ForegroundColor Gray
                } catch {
                    Write-Host "⚠️ Не удалось удалить директорию Android: $AndroidDir - $($_.Exception.Message)" -ForegroundColor Yellow
                }
            }
        }
    }
    
    # 5. Завершаем все процессы пользователя
    Write-Host "🗑️ Завершение процессов пользователя..." -ForegroundColor Yellow
    try {
        # Завершаем процессы, запущенные от имени пользователя
        Get-WmiObject -Class Win32_Process | Where-Object { 
            $_.GetOwner().User -eq $OperatorUsername 
        } | ForEach-Object { 
            try {
                $_.Terminate()
                Write-Host "Завершен процесс: $($_.Name) (PID: $($_.ProcessId))" -ForegroundColor Gray
            } catch {
                Write-Host "⚠️ Не удалось завершить процесс: $($_.Name)" -ForegroundColor Yellow
            }
        }
    } catch {
        Write-Host "⚠️ Ошибка при завершении процессов: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    
    # Ждем завершения процессов
    Start-Sleep -Seconds 2
    
    # 6. Удаляем пользователя Windows
    Write-Host "🗑️ Удаление пользователя Windows..." -ForegroundColor Yellow
    try {
        # Проверяем существование пользователя через net user
        $UserCheck = net user $OperatorUsername 2>$null
        if ($LASTEXITCODE -eq 0) {
            Remove-LocalUser -Name $OperatorUsername -ErrorAction Stop
            Write-Host "Удален пользователь: $OperatorUsername" -ForegroundColor Gray
        } else {
            Write-Host "Пользователь $OperatorUsername не найден в системе" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "⚠️ Не удалось удалить пользователя: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    
    # 7. Удаляем профиль пользователя
    Write-Host "🗑️ Удаление профиля пользователя..." -ForegroundColor Yellow
    foreach ($ProfilePath in $UserProfilePaths) {
        if (Test-Path $ProfilePath) {
            try {
                # Снимаем атрибуты только для чтения
                Get-ChildItem -Path $ProfilePath -Recurse -Force -ErrorAction SilentlyContinue | ForEach-Object {
                    try {
                        $_.Attributes = 'Normal'
                    } catch {}
                }
                
                Remove-Item -Path $ProfilePath -Recurse -Force -ErrorAction Stop
                Write-Host "Удален профиль: $ProfilePath" -ForegroundColor Gray
            } catch {
                Write-Host "⚠️ Не удалось удалить профиль: $ProfilePath - $($_.Exception.Message)" -ForegroundColor Yellow
                Write-Host "Возможно, некоторые файлы заблокированы. Попробуйте перезагрузить систему." -ForegroundColor Yellow
            }
        }
    }
    
    Write-Host "✅ SUCCESS: Оператор $OperatorUsername удален" -ForegroundColor Green
    Write-Host "DELETED_USER: $OperatorUsername" -ForegroundColor Cyan
    Write-Host "DELETED_FILES: $($FilesToDelete.Count)" -ForegroundColor Cyan
    Write-Host "DELETED_REMOTEAPPS: $($EmulatorApps.Count)" -ForegroundColor Cyan
    
} catch {
    Write-Host "❌ ERROR: Ошибка удаления оператора: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "STACK_TRACE: $($_.ScriptStackTrace)" -ForegroundColor Red
    exit 1
}
''',
    
    'test_microphone': r'''
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
    'copy_template_avd': {
        'title': '2️⃣ Копирование готового AVD',
        'description': 'Копирует готовый AVD с предустановленными приложениями из шаблона phone1 (~11 ГБ)',
        'expected_output': 'AVD_NAME скопированного виртуального устройства'
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
    'delete_operator': {
        'title': '🗑️ Удаление оператора',
        'description': 'Полное удаление оператора: пользователь Windows, все эмуляторы, файлы и записи в реестре',
        'expected_output': 'DELETED_USER имя удаленного пользователя, DELETED_FILES количество удаленных файлов'
    },
    'test_microphone': {
        'title': '7️⃣ Тестирование микрофона',
        'description': 'Проверяет и настраивает все параметры для корректной работы микрофона в RemoteApp',
        'expected_output': 'MICROPHONE_STATUS статус настройки микрофона'
    }
}
