# -*- coding: utf-8 -*-
"""
Скрипты для пошагового тестирования Android Emulator RemoteApp
Каждый шаг можно тестировать отдельно для диагностики проблем
"""

# Словарь со всеми шагами тестирования
STEP_SCRIPTS = {
    'create_user': r'''
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
# Шаг 2: Копирование готового AVD с предустановленными приложениями
# Копирует готовый образ C:\\Users\\user\\.android\\avd\\phone1.avd

Write-Host "📱 Копирование готового AVD с предустановленными приложениями..." -ForegroundColor Yellow

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

Write-Host "Последний пользователь: $LastValidUser" -ForegroundColor Gray

if (-not $LastValidUser -or $LastValidUser -eq "") {
    Write-Host "ERROR: Не удалось найти последнего пользователя" -ForegroundColor Red
    exit 1
}

$UserNum = $LastValidUser.Replace('User', '')
$EmulatorName = if ($env:EMULATOR_NAME) { $env:EMULATOR_NAME } else { "Emulator" }
$SafeEmulatorName = $EmulatorName -replace '[^a-zA-Z0-9_]', '_'
$AvdName = "User$UserNum`_$SafeEmulatorName"

Write-Host "UserNum: $UserNum" -ForegroundColor Gray
Write-Host "EmulatorName: $EmulatorName" -ForegroundColor Gray
Write-Host "SafeEmulatorName: $SafeEmulatorName" -ForegroundColor Gray

# Настройки шаблона
$TemplateAvdPath = "C:\\Users\\user\\.android\\avd\\phone1.avd"

Write-Host "Шаблон AVD: $TemplateAvdPath" -ForegroundColor Gray
Write-Host "Новый AVD: $AvdName" -ForegroundColor Cyan

# Проверяем существование шаблона
if (!(Test-Path $TemplateAvdPath)) {
    Write-Host "ERROR: Шаблон AVD не найден: $TemplateAvdPath" -ForegroundColor Red
    exit 1
}

# Определяем целевые пути
$UserProfilePath = "C:\\Users\\$LastValidUser"
$UserProfilePathHP = "C:\\Users\\$LastValidUser.HP"
$ActualUserProfile = if (Test-Path $UserProfilePathHP) { $UserProfilePathHP } else { $UserProfilePath }

$TargetAndroidDir = "$ActualUserProfile\\.android\\avd"
$TargetAvdPath = "$TargetAndroidDir\\$AvdName.avd"
$TargetIniPath = "$TargetAndroidDir\\$AvdName.ini"

try {
    # Создаем директории
    $AndroidBaseDir = "$ActualUserProfile\\.android"
    if (!(Test-Path $AndroidBaseDir)) {
        New-Item -ItemType Directory -Path $AndroidBaseDir -Force | Out-Null
    }
    if (!(Test-Path $TargetAndroidDir)) {
        New-Item -ItemType Directory -Path $TargetAndroidDir -Force | Out-Null
    }
    
    # Удаляем существующий AVD
    if (Test-Path $TargetAvdPath) {
        Remove-Item -Recurse -Force $TargetAvdPath -ErrorAction SilentlyContinue
    }
    if (Test-Path $TargetIniPath) {
        Remove-Item -Force $TargetIniPath -ErrorAction SilentlyContinue
    }
    
    # Копируем AVD
    Copy-Item -Path $TemplateAvdPath -Destination $TargetAvdPath -Recurse -Force
    
    # Обновляем config.ini
    $ConfigPath = "$TargetAvdPath\\config.ini"
    if (Test-Path $ConfigPath) {
        Write-Host "Обновление config.ini..." -ForegroundColor Yellow
        $ConfigContent = Get-Content $ConfigPath
        
        # Безопасная замена путей
        if ($AvdName -and $AvdName -ne "") {
            $ConfigContent = $ConfigContent -replace "phone1", $AvdName
        }
        if ($LastValidUser -and $LastValidUser -ne "") {
            $ConfigContent = $ConfigContent -replace "user", $LastValidUser
        }
        if ($ActualUserProfile -and $ActualUserProfile -ne "") {
            # Простая замена без сложного экранирования
            $ConfigContent = $ConfigContent.Replace("C:\Users\user", $ActualUserProfile)
            $ConfigContent = $ConfigContent.Replace("C:\\Users\\user", $ActualUserProfile)
        }
        
        Set-Content -Path $ConfigPath -Value $ConfigContent -Encoding UTF8
        Write-Host "config.ini обновлен" -ForegroundColor Green
    }
    
    # Создаем .ini файл
    $IniContent = @"
avd.ini.encoding=UTF-8
path=$TargetAvdPath
path.rel=avd\\$AvdName.avd
target=android-36
hw.audioInput=yes
hw.audioOutput=yes
"@
    Set-Content -Path $TargetIniPath -Value $IniContent -Encoding UTF8
    
    # Настраиваем права доступа для RDP
    icacls $ActualUserProfile /grant "Everyone:(OI)(CI)F" /T /Q | Out-Null
    icacls $AndroidBaseDir /grant "Everyone:(OI)(CI)F" /T /Q | Out-Null
    icacls $AndroidBaseDir /grant "Users:(OI)(CI)F" /T /Q | Out-Null
    icacls $AndroidBaseDir /grant "SYSTEM:(OI)(CI)F" /T /Q | Out-Null
    icacls $TargetAvdPath /grant "Everyone:(OI)(CI)F" /T /Q | Out-Null
    icacls $TargetIniPath /grant "Everyone:F" /Q | Out-Null
    
    Write-Host "SUCCESS: AVD скопирован из готового шаблона: $AvdName" -ForegroundColor Green
    Write-Host "AVD_NAME: $AvdName" -ForegroundColor Cyan
    Write-Host "AVD_PATH: $TargetAvdPath" -ForegroundColor Cyan
    
} catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
    ''',
            }
            
            # Создаем символическую ссылку
            cmd.exe /c mklink /D "$LinkPath" "$TargetPath" | Out-Null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Создана символическая ссылка: $LinkPath -> $TargetPath" -ForegroundColor Green
            } else {
                Write-Host "⚠️ Не удалось создать символическую ссылку, копируем файлы" -ForegroundColor Yellow
                # Если симлинк не удался, создаем обычную директорию
                if (!(Test-Path $LinkPath)) {
                    New-Item -ItemType Directory -Path $LinkPath -Force | Out-Null
                    icacls $LinkPath /grant "Everyone:(OI)(CI)F" /T /Q | Out-Null
                }
            }
        } catch {
            Write-Host "⚠️ Ошибка создания символической ссылки: $($_.Exception.Message)" -ForegroundColor Yellow
            # Создаем обычную директорию как fallback
            if (!(Test-Path $LinkPath)) {
                New-Item -ItemType Directory -Path $LinkPath -Force | Out-Null
                icacls $LinkPath /grant "Everyone:(OI)(CI)F" /T /Q | Out-Null
            }
        }
    }
} else {
    Write-Host "Используется обычный профиль: $UserProfilePath" -ForegroundColor Yellow
}

# Используем фактический профиль для создания AVD
$UserProfilePath = $ActualUserProfile

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
    $AndroidBaseDir = "$UserProfilePath\\.android"
    $AndroidDir = "$AndroidBaseDir\\avd"
    
    if (!(Test-Path $AndroidBaseDir)) {
        New-Item -ItemType Directory -Path $AndroidBaseDir -Force
        Write-Host "Создана базовая директория: $AndroidBaseDir" -ForegroundColor Gray
    }
    
    if (!(Test-Path $AndroidDir)) {
        New-Item -ItemType Directory -Path $AndroidDir -Force
        Write-Host "Создана директория AVD: $AndroidDir" -ForegroundColor Gray
    }
    
    # Создаем дополнительные директории для эмулятора
    $CacheDir = "$AndroidBaseDir\\cache"
    $TempDir = "$AndroidBaseDir\\temp"
    
    if (!(Test-Path $CacheDir)) {
        New-Item -ItemType Directory -Path $CacheDir -Force
        Write-Host "Создана директория cache: $CacheDir" -ForegroundColor Gray
    }
    
    if (!(Test-Path $TempDir)) {
        New-Item -ItemType Directory -Path $TempDir -Force
        Write-Host "Создана директория temp: $TempDir" -ForegroundColor Gray
    }
    
    # Настраиваем права доступа для RemoteApp совместимости
    Write-Host "🔐 Настройка прав доступа для RemoteApp..." -ForegroundColor Yellow
    try {
        icacls $AndroidBaseDir /grant "Everyone:(OI)(CI)F" /T /Q | Out-Null
        icacls $AndroidBaseDir /grant "Users:(OI)(CI)F" /T /Q | Out-Null
        icacls $AndroidBaseDir /grant "Administrators:(OI)(CI)F" /T /Q | Out-Null
        icacls $AndroidBaseDir /grant "SYSTEM:(OI)(CI)F" /T /Q | Out-Null
        
        # Создаем пустые lock файлы для предотвращения ошибок эмулятора
        $LockFiles = @(
            "$AndroidBaseDir\\emu-last-feature-flags.protobuf",
            "$AndroidBaseDir\\emu-last-feature-flags.protobuf.lock",
            "$AndroidBaseDir\\emulator-check.exe.lock"
        )
        
        foreach ($LockFile in $LockFiles) {
            if (!(Test-Path $LockFile)) {
                try {
                    New-Item -ItemType File -Path $LockFile -Force | Out-Null
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
        
        Write-Host "✅ Права доступа и lock файлы настроены на: $AndroidBaseDir" -ForegroundColor Green
    } catch {
        Write-Host "⚠️ WARNING: Не удалось настроить права доступа: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    
    # Удаляем существующий AVD если есть
    $ExistingAvdPath = "$AndroidDir\\$AvdName.avd"
    $ExistingIniPath = "$AndroidDir\\$AvdName.ini"
    
    # Сначала очищаем все lock файлы
    Write-Host "🔄 Очистка lock файлов..." -ForegroundColor Yellow
    Get-ChildItem -Path $AndroidBaseDir -Filter "*.lock" -Recurse -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
    if (Test-Path $ExistingAvdPath) {
        Get-ChildItem -Path $ExistingAvdPath -Filter "*.lock" -Recurse -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
    }
    
    if (Test-Path $ExistingAvdPath) {
        Remove-Item -Recurse -Force $ExistingAvdPath -ErrorAction SilentlyContinue
        Write-Host "Удален существующий AVD: $AvdName" -ForegroundColor Gray
    }
    if (Test-Path $ExistingIniPath) {
        Remove-Item -Force $ExistingIniPath -ErrorAction SilentlyContinue
    }
    
    # Создаем AVD через avdmanager с правильными параметрами устройства
    Write-Host "Создание AVD через avdmanager..." -ForegroundColor Gray
    Write-Host "AVD Name: $AvdName" -ForegroundColor Cyan
    Write-Host "ANDROID_AVD_HOME: $env:ANDROID_AVD_HOME" -ForegroundColor Cyan
    
    # Используем параметр -p для явного указания пути к AVD
    $CreateAvdCmd = "`"$AvdManagerPath`" create avd -n `"$AvdName`" -k `"system-images;android-36;google_apis_playstore;x86_64`" -d `"small_phone`" -c `"512M`" -p `"$AndroidDir\\$AvdName.avd`" --force"
    Write-Host "Команда: $CreateAvdCmd" -ForegroundColor Gray
    
    # Устанавливаем переменные окружения для avdmanager
    $env:ANDROID_AVD_HOME = $AndroidDir
    $result = cmd.exe /c $CreateAvdCmd
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ SUCCESS: AVD $AvdName создан успешно" -ForegroundColor Green
        Write-Host "AVD_NAME: $AvdName" -ForegroundColor Cyan
        
        # Проверяем, что AVD действительно создался
        $AvdPath = "$AndroidDir\\$AvdName.avd"
        if (Test-Path $AvdPath) {
            Write-Host "AVD_PATH: $AvdPath" -ForegroundColor Cyan
            
            # Создаем дополнительные lock файлы в директории AVD
            $AvdLockFiles = @(
                "$AvdPath\\hardware-qemu.ini.lock",
                "$AvdPath\\config.ini.lock"
            )
            
            foreach ($LockFile in $AvdLockFiles) {
                try {
                    New-Item -ItemType File -Path $LockFile -Force | Out-Null
                    icacls $LockFile /grant "Everyone:F" /Q | Out-Null
                    icacls $LockFile /grant "SYSTEM:F" /Q | Out-Null
                    Write-Host "Создан AVD lock файл: $LockFile" -ForegroundColor Gray
                } catch {
                    Write-Host "⚠️ Не удалось создать AVD lock файл: $LockFile" -ForegroundColor Yellow
                }
            }
            
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
            
            # Назначаем полные права на созданный AVD
            Write-Host "🔐 Настройка прав доступа на AVD..." -ForegroundColor Yellow
            try {
                icacls $AvdPath /grant "Everyone:(OI)(CI)F" /T /Q | Out-Null
                icacls $AvdPath /grant "Users:(OI)(CI)F" /T /Q | Out-Null
                icacls $AvdPath /grant "Administrators:(OI)(CI)F" /T /Q | Out-Null
                icacls $AvdPath /grant "SYSTEM:(OI)(CI)F" /T /Q | Out-Null
                
                if (Test-Path $IniPath) {
                    icacls $IniPath /grant "Everyone:F" /Q | Out-Null
                    icacls $IniPath /grant "Users:F" /Q | Out-Null
                    icacls $IniPath /grant "Administrators:F" /Q | Out-Null
                    icacls $IniPath /grant "SYSTEM:F" /Q | Out-Null
                }
                
                Write-Host "✅ Права доступа на AVD настроены" -ForegroundColor Green
            } catch {
                Write-Host "⚠️ Не удалось настроить права на AVD: $($_.Exception.Message)" -ForegroundColor Yellow
            }
            
            # Если используется .HP профиль, создаем копию AVD в обычной директории для совместимости
            if ($ActualUserProfile -like "*.HP") {
                $NormalProfilePath = $ActualUserProfile -replace "\\.HP$", ""
                $NormalAndroidDir = "$NormalProfilePath\\.android\\avd"
                $NormalAvdPath = "$NormalAndroidDir\\$AvdName.avd"
                $NormalIniPath = "$NormalAndroidDir\\$AvdName.ini"
                
                Write-Host "🔄 Создание копии AVD в обычной директории для совместимости..." -ForegroundColor Yellow
                
                try {
                    # Создаем директории
                    if (!(Test-Path $NormalAndroidDir)) {
                        New-Item -ItemType Directory -Path $NormalAndroidDir -Force | Out-Null
                        icacls $NormalAndroidDir /grant "Everyone:(OI)(CI)F" /T /Q | Out-Null
                        Write-Host "Создана директория: $NormalAndroidDir" -ForegroundColor Gray
                    }
                    
                    # Копируем AVD директорию
                    if (Test-Path $AvdPath) {
                        Copy-Item -Path $AvdPath -Destination $NormalAvdPath -Recurse -Force
                        icacls $NormalAvdPath /grant "Everyone:(OI)(CI)F" /T /Q | Out-Null
                        Write-Host "Скопирована AVD директория: $NormalAvdPath" -ForegroundColor Gray
                    }
                    
                    # Копируем .ini файл
                    if (Test-Path $IniPath) {
                        Copy-Item -Path $IniPath -Destination $NormalIniPath -Force
                        icacls $NormalIniPath /grant "Everyone:F" /Q | Out-Null
                        Write-Host "Скопирован .ini файл: $NormalIniPath" -ForegroundColor Gray
                    }
                    
                    Write-Host "✅ Копия AVD создана в обычной директории" -ForegroundColor Green
                } catch {
                    Write-Host "⚠️ Не удалось создать копию AVD: $($_.Exception.Message)" -ForegroundColor Yellow
                }
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
    
    'create_batch': r'''
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
$EmulatorName = if ($env:EMULATOR_NAME) { $env:EMULATOR_NAME } else { "Emulator" }
$SafeEmulatorName = $EmulatorName -replace '[^a-zA-Z0-9_]', '_'
$AvdName = "User$UserNum`_$SafeEmulatorName"
$BatchFilePath = "C:\\Scripts\\$TestUser`_$SafeEmulatorName.bat"

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

echo Проверка существования AVD...
if exist "%ANDROID_AVD_HOME%\\$AvdName.avd" (
    echo ✅ AVD найден: %ANDROID_AVD_HOME%\\$AvdName.avd
) else (
    echo ❌ AVD НЕ найден: %ANDROID_AVD_HOME%\\$AvdName.avd
    echo Содержимое директории %ANDROID_AVD_HOME%:
    if exist "%ANDROID_AVD_HOME%" (
        dir "%ANDROID_AVD_HOME%" /b
    ) else (
        echo Директория %ANDROID_AVD_HOME% не существует!
    )
    echo.
    echo Попробуем найти AVD в других местах:
    if exist "C:\\Users\\$TestUser\\.android\\avd\\$AvdName.avd" (
        echo Найден в: C:\\Users\\$TestUser\\.android\\avd\\$AvdName.avd
        set ANDROID_AVD_HOME=C:\\Users\\$TestUser\\.android\\avd
        echo Переключаемся на: %ANDROID_AVD_HOME%
    )
    if exist "C:\\Users\\$TestUser.HP\\.android\\avd\\$AvdName.avd" (
        echo Найден в: C:\\Users\\$TestUser.HP\\.android\\avd\\$AvdName.avd
        set ANDROID_AVD_HOME=C:\\Users\\$TestUser.HP\\.android\\avd
        echo Переключаемся на: %ANDROID_AVD_HOME%
    )
)
echo.

echo Очистка блокировок эмулятора...
REM Удаляем lock файлы перед запуском
if exist "%ANDROID_AVD_HOME%\\$AvdName.avd\\*.lock" (
    del /Q "%ANDROID_AVD_HOME%\\$AvdName.avd\\*.lock"
    echo Удалены lock файлы AVD
)
if exist "%USERPROFILE%\\.android\\*.lock" (
    del /Q "%USERPROFILE%\\.android\\*.lock"
    echo Удалены общие lock файлы
)

echo Запуск эмулятора $AvdName...
echo Команда: emulator -avd "$AvdName" -no-snapshot -gpu host -memory 4096 -no-boot-anim -netdelay none -netspeed full -verbose -wipe-data
echo.

REM Пробуем запустить эмулятор с очисткой данных
emulator -avd "$AvdName" -no-snapshot -gpu host -memory 4096 -no-boot-anim -netdelay none -netspeed full -verbose -wipe-data

REM Если первый запуск не удался, пробуем в режиме только для чтения
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Первый запуск не удался, пробуем режим только для чтения...
    echo Команда: emulator -avd "$AvdName" -no-snapshot -gpu host -memory 4096 -no-boot-anim -netdelay none -netspeed full -verbose -read-only
    echo.
    emulator -avd "$AvdName" -no-snapshot -gpu host -memory 4096 -no-boot-anim -netdelay none -netspeed full -verbose -read-only
)

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
    
    'convert_to_exe': r'''
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
authentication level:i:2
username:s:$Username
domain:s:
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
        $User = Get-LocalUser -Name $OperatorUsername -ErrorAction SilentlyContinue
        if ($User) {
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
