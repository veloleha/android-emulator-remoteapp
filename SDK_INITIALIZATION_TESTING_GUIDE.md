# 🧪 Руководство по тестированию SDK инициализации

## 📋 Обзор

Это руководство описывает процесс тестирования автоматической инициализации Android SDK для новых пользователей в системе Android Emulator RemoteApp.

**Дата создания**: 25.09.2025  
**Версия**: 1.0  
**Статус**: Готово к тестированию

---

## 🎯 Цели тестирования

### **Основные цели:**
1. Проверить автоматическую настройку Android SDK для нового пользователя
2. Убедиться в корректной установке переменных окружения
3. Проверить создание необходимых директорий и файлов
4. Протестировать установку недостающих SDK компонентов
5. Проверить работоспособность SDK инструментов

### **Критерии успеха:**
- ✅ SDK инициализируется без ошибок
- ✅ Все необходимые директории созданы
- ✅ Переменные окружения установлены корректно
- ✅ SDK инструменты (sdkmanager, avdmanager, emulator) работают
- ✅ Можно создать тестовый AVD
- ✅ Процесс логируется для отладки

---

## 🛠️ Предварительные требования

### **Системные требования:**
- Windows Server с установленным Android SDK
- Java JDK 17+ установлен в `C:\Program Files\Microsoft\jdk-17.0.16.8-hotspot`
- Android SDK установлен в `C:\Program Files\Android`
- PowerShell 5.1+
- Права администратора

### **Необходимые компоненты SDK:**
- `system-images;android-36;google_apis_playstore;x86_64`
- `platforms;android-36`
- `build-tools;34.0.0`
- `platform-tools`
- `emulator`
- `cmdline-tools;latest`

---

## 🧪 Методы тестирования

### **1. Автоматическое тестирование через Flask API**

#### **Шаг 1: Запуск Flask приложения**
```powershell
cd C:\Users\admin\CascadeProjects\android-emulator-remoteapp\web
python app.py
```

#### **Шаг 2: Создание тестового пользователя через API**
```powershell
# Логин в API
$login = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5000/api/login -ContentType application/json -Body '{"username":"admin","password":"admin123"}'
$headers = @{ Authorization = "Bearer " + $login.token }

# Создание пользователя (SDK инициализация произойдет автоматически)
$response = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5000/api/test_step -Headers $headers -ContentType application/json -Body '{"step":"create_user"}'

# Проверка результата
$response | ConvertTo-Json -Depth 3
```

#### **Ожидаемый результат:**
```json
{
  "success": true,
  "step": "create_user",
  "output": "Содержит логи SDK инициализации",
  "timestamp": "2025-09-25T01:30:00.000000"
}
```

### **2. Ручное тестирование через PowerShell скрипт**

#### **Шаг 1: Создание тестового пользователя**
```powershell
# Создаем тестового пользователя
$TestUser = "TestUser2"
$Password = "TestPass123!"
New-LocalUser -Name $TestUser -Password (ConvertTo-SecureString $Password -AsPlainText -Force) -FullName "Test User 2" -Description "Тестовый пользователь для SDK"
```

#### **Шаг 2: Запуск тестового скрипта**
```powershell
# Запуск тестирования SDK инициализации
C:\Scripts\test_sdk_initialization.ps1 -TestUsername $TestUser
```

#### **Шаг 3: Анализ результатов**
```powershell
# Просмотр лог файла
Get-Content C:\Scripts\sdk_init_test_log.txt | Select-Object -Last 20

# Проверка созданных директорий
Get-ChildItem "C:\Users\$TestUser\.android" -Recurse
```

### **3. Интеграционное тестирование**

#### **Шаг 1: Полный цикл создания пользователя и AVD**
```powershell
# 1. Создание пользователя через API
$createUserResponse = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5000/api/test_step -Headers $headers -ContentType application/json -Body '{"step":"create_user"}'

# 2. Создание AVD через API
$createAvdResponse = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5000/api/test_step -Headers $headers -ContentType application/json -Body '{"step":"create_avd"}'

# 3. Создание batch файла
$createBatchResponse = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5000/api/test_step -Headers $headers -ContentType application/json -Body '{"step":"create_batch"}'
```

---

## 📊 Проверочные точки

### **1. Проверка директорий**
```powershell
$TestUser = "User1"  # Замените на имя тестового пользователя
$AndroidUserDir = "C:\Users\$TestUser\.android"

# Основная директория
Test-Path $AndroidUserDir  # Должно быть True

# Поддиректории
Test-Path "$AndroidUserDir\avd"    # Должно быть True
Test-Path "$AndroidUserDir\cache"  # Должно быть True
Test-Path "$AndroidUserDir\temp"   # Должно быть True

# Конфигурационные файлы
Test-Path "$AndroidUserDir\repositories.cfg"  # Должно быть True
```

### **2. Проверка переменных окружения**
```powershell
# В PowerShell сессии после инициализации
$env:ANDROID_HOME      # Должно быть: C:\Program Files\Android
$env:ANDROID_SDK_ROOT  # Должно быть: C:\Program Files\Android
$env:JAVA_HOME         # Должно быть: C:\Program Files\Microsoft\jdk-17.0.16.8-hotspot
$env:ANDROID_AVD_HOME  # Должно быть: C:\Users\[User]\.android\avd
```

### **3. Проверка SDK инструментов**
```powershell
# Проверка доступности инструментов
$AndroidHome = "C:\Program Files\Android"

# sdkmanager
& "$AndroidHome\cmdline-tools\latest\bin\sdkmanager.bat" --version

# avdmanager
& "$AndroidHome\cmdline-tools\latest\bin\avdmanager.bat" list avd

# emulator
& "$AndroidHome\emulator\emulator.exe" -version
```

### **4. Проверка установленных пакетов**
```powershell
$SdkManager = "C:\Program Files\Android\cmdline-tools\latest\bin\sdkmanager.bat"
& $SdkManager --list_installed | Select-String "system-images;android-36;google_apis_playstore;x86_64"
& $SdkManager --list_installed | Select-String "platforms;android-36"
& $SdkManager --list_installed | Select-String "build-tools"
& $SdkManager --list_installed | Select-String "platform-tools"
& $SdkManager --list_installed | Select-String "emulator"
```

---

## 📄 Анализ логов

### **Лог файлы:**
- **Основной лог**: `C:\Scripts\sdk_init_log.txt`
- **Тестовый лог**: `C:\Scripts\sdk_init_test_log.txt`
- **Flask лог**: Вывод в консоли Flask приложения

### **Ключевые сообщения в логах:**

#### **Успешная инициализация:**
```
[2025-09-25 01:30:00] [INFO] Начало инициализации SDK для пользователя: User1
[2025-09-25 01:30:01] [INFO] Android SDK найден: C:\Program Files\Android
[2025-09-25 01:30:01] [INFO] Java найден: C:\Program Files\Microsoft\jdk-17.0.16.8-hotspot
[2025-09-25 01:30:02] [INFO] Создана директория: C:\Users\User1\.android
[2025-09-25 01:30:03] [INFO] Все необходимые SDK компоненты установлены
[2025-09-25 01:30:04] [INFO] SDK инициализация завершена успешно для User1
```

#### **Ошибки инициализации:**
```
[2025-09-25 01:30:00] [ERROR] Android SDK не найден по пути: C:\Program Files\Android
[2025-09-25 01:30:01] [ERROR] sdkmanager не доступен
[2025-09-25 01:30:02] [WARN] Отсутствует пакет: system-images;android-36;google_apis_playstore;x86_64
```

---

## 🔧 Устранение неполадок

### **Проблема 1: Android SDK не найден**
```
Ошибка: Android SDK не найден по пути: C:\Program Files\Android
```
**Решение:**
1. Проверить установку Android SDK
2. Убедиться в правильности пути
3. Проверить права доступа к директории

### **Проблема 2: Java не найден**
```
Ошибка: Java не найден по пути: C:\Program Files\Microsoft\jdk-17.0.16.8-hotspot
```
**Решение:**
1. Установить Java JDK 17+
2. Обновить путь в скрипте
3. Проверить переменную JAVA_HOME

### **Проблема 3: sdkmanager недоступен**
```
Ошибка: sdkmanager не доступен
```
**Решение:**
1. Проверить установку cmdline-tools
2. Обновить Android SDK
3. Проверить права выполнения

### **Проблема 4: Отсутствуют SDK пакеты**
```
Предупреждение: Отсутствует пакет: system-images;android-36;google_apis_playstore;x86_64
```
**Решение:**
1. Запустить установку вручную:
```powershell
$SdkManager = "C:\Program Files\Android\cmdline-tools\latest\bin\sdkmanager.bat"
& $SdkManager "system-images;android-36;google_apis_playstore;x86_64"
```

### **Проблема 5: Права доступа**
```
Ошибка: Не удалось создать директорию
```
**Решение:**
1. Запустить PowerShell от имени администратора
2. Проверить права пользователя
3. Настроить ACL вручную

---

## ✅ Чек-лист тестирования

### **Перед тестированием:**
- [ ] Android SDK установлен и доступен
- [ ] Java JDK установлен
- [ ] PowerShell запущен от имени администратора
- [ ] Flask приложение работает
- [ ] Интернет соединение доступно (для загрузки пакетов)

### **Во время тестирования:**
- [ ] Создание пользователя завершается успешно
- [ ] SDK инициализация не вызывает критических ошибок
- [ ] Все директории создаются
- [ ] Переменные окружения устанавливаются
- [ ] SDK инструменты работают
- [ ] Логи записываются корректно

### **После тестирования:**
- [ ] Проверить лог файлы на наличие ошибок
- [ ] Убедиться в создании всех необходимых файлов
- [ ] Протестировать создание AVD
- [ ] Очистить тестовые данные (при необходимости)

---

## 📈 Метрики успеха

### **Количественные метрики:**
- **Время инициализации**: < 60 секунд
- **Успешность создания директорий**: 100%
- **Успешность установки пакетов**: ≥ 90%
- **Доступность SDK инструментов**: 100%

### **Качественные метрики:**
- **Стабильность**: Процесс не прерывается критическими ошибками
- **Логирование**: Все действия записываются в лог
- **Восстановимость**: При ошибках пользователь все равно создается
- **Совместимость**: Работает с существующим workflow

---

## 🚀 Автоматизация тестирования

### **Создание тестового набора:**
```powershell
# Скрипт для автоматического тестирования
$TestUsers = @("TestUser1", "TestUser2", "TestUser3")

foreach ($User in $TestUsers) {
    Write-Host "Тестирование пользователя: $User" -ForegroundColor Yellow
    
    # Создание пользователя
    New-LocalUser -Name $User -Password (ConvertTo-SecureString "Test123!" -AsPlainText -Force) -ErrorAction SilentlyContinue
    
    # Тестирование SDK инициализации
    C:\Scripts\test_sdk_initialization.ps1 -TestUsername $User
    
    # Пауза между тестами
    Start-Sleep -Seconds 10
}
```

### **Интеграция с CI/CD:**
Этот процесс может быть интегрирован в систему непрерывной интеграции для автоматического тестирования при изменениях в коде.

---

**Последнее обновление**: 25.09.2025 01:35  
**Автор**: Android Emulator RemoteApp Project Team
