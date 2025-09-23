# Руководство по устранению неполадок

## 🔧 Общие проблемы и решения

### 1. Проблемы с созданием пользователя

#### Ошибка: "Превышена допустимая длина аргумента"
**Причина**: Слишком длинное имя пользователя или описание
**Решение**: 
- Имена пользователей ограничены 20 символами
- Описания ограничены 48 символами
- Используется формат User1, User2, User3...

#### Ошибка: "Группа не найдена"
**Причина**: Проблемы с локализацией Windows
**Решение**: Используются универсальные SID:
- Users: `S-1-5-32-545`
- Remote Desktop Users: `S-1-5-32-555`

### 2. Проблемы с Android SDK

#### Ошибка: "avdmanager не найден"
**Причина**: Android SDK не установлен или неправильный путь
**Решение**:
```powershell
# Проверить путь к SDK
$env:ANDROID_HOME = "C:\Program Files\Android"
$env:PATH += ";$env:ANDROID_HOME\cmdline-tools\latest\bin"
```

#### Ошибка: "Недостаточно места для AVD"
**Причина**: Мало места на диске
**Решение**:
- Освободить минимум 8GB для каждого AVD
- Переместить AVD на другой диск

### 3. Проблемы с микрофоном

#### Микрофон отключается через 3 секунды
**Причина**: Настройки групповой политики Windows
**Решение**:
```powershell
# Запустить скрипт исправления
.\scripts\ConfigureGroupPolicy.ps1
```

#### Микрофон не работает в RemoteApp
**Причина**: Неправильные настройки реестра
**Решение**:
```powershell
# Проверить настройки реестра
reg query "HKLM\SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp" /v fDisableAudioCapture
# Должно быть: 0x0 (0)
```

### 4. Проблемы с RemoteApp

#### RemoteApp не запускается
**Причина**: Неправильные права доступа к файлам
**Решение**:
```powershell
# Проверить права доступа
icacls "C:\Scripts\*.exe" /grant Users:RX
```

#### Ошибка: "Приложение не найдено"
**Причина**: Неправильный путь в реестре
**Решение**:
```powershell
# Проверить реестр RemoteApp
reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Terminal Server\TSAppAllowList\Applications"
```

### 5. Проблемы с веб-интерфейсом

#### Белый экран в браузере
**Причина**: React приложение требует сборки
**Решение**: Используется простой HTML интерфейс (`simple_interface.html`)

#### Ошибка кодировки в PowerShell
**Причина**: Конфликт кодировок Windows
**Решение**: Убраны эмодзи и специальные символы из скриптов

### 6. Проблемы с сетью

#### RDP соединение не устанавливается
**Причина**: Настройки брандмауэра
**Решение**:
```powershell
# Разрешить RDP в брандмауэре
netsh advfirewall firewall set rule group="remote desktop" new enable=Yes
```

#### Медленная работа эмулятора
**Причина**: Недостаточные ресурсы
**Решение**:
- Увеличить RAM до 2048MB
- Включить аппаратное ускорение GPU
- Использовать флаг `-gpu host`

## 🔍 Диагностические команды

### Проверка пользователей
```powershell
Get-LocalUser | Where-Object Name -like "User*"
```

### Проверка групп пользователя
```powershell
$Username = "User1"
Get-LocalGroup | ForEach-Object {
    $Members = Get-LocalGroupMember -Group $_.Name -ErrorAction SilentlyContinue
    if ($Members | Where-Object Name -like "*$Username*") {
        Write-Host $_.Name
    }
}
```

### Проверка AVD
```powershell
& "C:\Program Files\Android\cmdline-tools\latest\bin\avdmanager.bat" list avd
```

### Проверка процессов эмулятора
```powershell
Get-Process | Where-Object Name -like "*emulator*"
```

### Проверка логов
```powershell
Get-Content "C:\Scripts\log.txt" -Tail 50
Get-Content "C:\Scripts\web_log.txt" -Tail 50
```

## 📋 Контрольный список

### Перед началом работы:
- [ ] Windows Server/10 LTSC установлен
- [ ] Запуск от имени администратора
- [ ] Android SDK установлен
- [ ] Bat To Exe Converter установлен
- [ ] RDP Wrapper настроен
- [ ] Python 3.7+ установлен

### При создании пользователя:
- [ ] Имя не превышает 20 символов
- [ ] Пользователь добавлен в группы Users и RDP
- [ ] Пароль сгенерирован и сохранен
- [ ] Запрет смены пароля активен

### При создании AVD:
- [ ] Достаточно места на диске (8GB+)
- [ ] Android SDK доступен
- [ ] Системный образ загружен
- [ ] Настройки аудио включены

### При настройке RemoteApp:
- [ ] EXE файл создан
- [ ] Реестр настроен
- [ ] Права доступа установлены
- [ ] RDP файл сгенерирован

## 🆘 Экстренные решения

### Полная переустановка
```powershell
# Удалить всех тестовых пользователей
Get-LocalUser | Where-Object Name -like "User*" | Remove-LocalUser

# Очистить AVD
Remove-Item "$env:USERPROFILE\.android\avd\phone*" -Recurse -Force

# Очистить скрипты
Remove-Item "C:\Scripts\*" -Force

# Перезапустить установку
.\scripts\Install-EmulatorSystem.ps1
```

### Сброс настроек микрофона
```powershell
# Сбросить групповую политику
gpupdate /force

# Перезапустить службы аудио
Restart-Service -Name "AudioSrv"
Restart-Service -Name "AudioEndpointBuilder"
```

## 📞 Получение помощи

1. **Проверьте логи** в `C:\Scripts\log.txt`
2. **Запустите диагностические команды**
3. **Создайте issue** в репозитории GitHub
4. **Приложите информацию**:
   - Версия Windows
   - Текст ошибки
   - Логи операций
   - Скриншоты (если применимо)

## 🔄 Обновления

Регулярно проверяйте обновления:
- Android SDK
- PowerShell модули
- Системные обновления Windows
- Обновления репозитория

---

**Примечание**: Большинство проблем решается перезапуском от имени администратора и проверкой логов.
