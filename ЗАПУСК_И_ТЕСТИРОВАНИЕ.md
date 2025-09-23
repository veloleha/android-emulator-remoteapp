# 🚀 Инструкция по запуску и тестированию системы Android Emulator RemoteApp

## 📋 Краткое описание

Создана полная система автоматизации для Android эмулятора с RemoteApp поддержкой:
- **Flask API** для пошагового тестирования и управления
- **React фронтенд** (уже готов в папке `сайт`)
- **PowerShell скрипты** для автоматизации всех этапов
- **Решение проблемы микрофона** (3-секундный обрыв)

## 🛠️ Предварительные требования

### 1. Установите необходимое ПО:
- **Android SDK** в `C:\Program Files\Android`
- **Bat To Exe Converter** в `C:\Program Files\BatToExe\BatToExeConverter.exe`
- **Python 3.8+** с pip
- **PowerShell** (уже есть в Windows)

### 2. Настройте права администратора:
- Запускайте все команды от имени администратора
- Включите выполнение PowerShell скриптов:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope LocalMachine
```

## 🚀 Быстрый запуск

### Шаг 1: Установка Python зависимостей
```cmd
cd C:\emulator\сайт
pip install -r requirements.txt
```

### Шаг 2: Запуск Flask API
```cmd
cd C:\emulator\сайт
python app.py
```

### Шаг 3: Доступ к системе
- **API**: http://localhost:5000/api
- **Веб-интерфейс**: http://localhost:5000
- **Логин**: admin / admin123 ⚠️ (измените пароль!)

## 🧪 Пошаговое тестирование

### Через API (рекомендуется для диагностики)

1. **Авторизация**:
```bash
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

2. **Получение списка шагов**:
```bash
curl -X GET http://localhost:5000/api/steps_info \
  -H "Authorization: Bearer YOUR_TOKEN"
```

3. **Тестирование отдельного шага**:
```bash
curl -X POST http://localhost:5000/api/test_step \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"step":"create_user"}'
```

### Доступные шаги для тестирования:

| Шаг | Описание | Ожидаемый результат |
|-----|----------|-------------------|
| `create_user` | Создание пользователя Windows | USERNAME и PASSWORD |
| `create_avd` | Создание Android Virtual Device | AVD_NAME |
| `create_batch` | Создание batch файла (исправлен cd /c → cd /d) | BATCH_FILE |
| `convert_to_exe` | Конвертация в EXE | EXE_FILE |
| `configure_remoteapp` | Настройка RemoteApp в реестре | APP_NAME и APP_PATH |
| `create_rdp` | Создание RDP файла | RDP_FILE |
| `test_microphone` | Тестирование настроек микрофона | MICROPHONE_STATUS |

## 🎯 Полная настройка системы

### Через API:
```bash
curl -X POST http://localhost:5000/api/create_phone \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"name":"Test Phone","model":"Pixel 6","apiLevel":"API 33"}'
```

### Через PowerShell напрямую:
```powershell
C:\emulator\AndroidEmulatorSetup.ps1
```

## 🔧 Диагностика проблем

### Проблема 1: Ошибка выполнения PowerShell
**Решение:**
```powershell
# Проверьте политику выполнения
Get-ExecutionPolicy
# Установите разрешающую политику
Set-ExecutionPolicy RemoteSigned -Scope LocalMachine
```

### Проблема 2: Android SDK не найден
**Решение:**
- Установите Android SDK в `C:\Program Files\Android`
- Или измените путь в скриптах

### Проблема 3: Bat To Exe Converter не найден
**Решение:**
- Скачайте с официального сайта
- Установите в `C:\Program Files\BatToExe\`

### Проблема 4: Микрофон обрывается через 3 секунды
**Решение (автоматически применяется):**
```powershell
# Запустите скрипт настройки микрофона
C:\emulator\ConfigureGroupPolicy.ps1
```

## 📊 Мониторинг и логи

### Просмотр логов:
```powershell
# Логи Flask API
Get-Content "C:\Scripts\web_log.txt" -Wait

# Логи PowerShell скриптов
Get-Content "C:\Scripts\log.txt" -Wait
```

### Проверка созданных файлов:
```powershell
# Проверка пользователей
Get-LocalUser | Where-Object {$_.Name -like "User*"}

# Проверка AVD
Get-ChildItem "$env:USERPROFILE\.android\avd\"

# Проверка RemoteApp в реестре
Get-ChildItem "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Terminal Server\TSAppAllowList\Applications"
```

## 🔐 Безопасность

### Обязательные изменения для продакшена:

1. **Смените пароль администратора** в `app.py`:
```python
ADMIN_PASSWORD_HASH = generate_password_hash('ваш_новый_пароль')
```

2. **Настройте HTTPS** для веб-интерфейса

3. **Ограничьте доступ к API** по IP адресам

4. **Регулярно очищайте** временные пользователи и файлы

## 📱 Подключение к эмулятору

### После успешной настройки:

1. **Скачайте RDP файл** через веб-интерфейс или API
2. **Запустите RDP файл** - откроется подключение
3. **Введите учетные данные** пользователя
4. **Android эмулятор** запустится в RemoteApp режиме
5. **Микрофон** должен работать без обрывов

## 🆘 Техническая поддержка

### Частые ошибки и решения:

| Ошибка | Причина | Решение |
|--------|---------|---------|
| "AVD Manager не найден" | Android SDK не установлен | Установите Android SDK |
| "Bat To Exe Converter не найден" | Конвертер не установлен | Установите конвертер |
| "Доступ запрещен к реестру" | Нет прав администратора | Запустите как администратор |
| "Микрофон не работает" | Неправильные настройки RDP | Запустите test_microphone шаг |
| "RDP подключение отклонено" | RDP Wrapper не настроен | Настройте RDP Wrapper |

### Контакты для поддержки:
- **Логи системы**: `C:\Scripts\log.txt`
- **Веб-логи**: `C:\Scripts\web_log.txt`
- **Тестирование**: http://localhost:5000/api/steps_info

## 📈 Производительность

### Рекомендуемые характеристики сервера:
- **CPU**: 4+ ядра
- **RAM**: 8+ GB
- **Диск**: SSD, 50+ GB свободного места
- **Сеть**: Гигабитное подключение

### Оптимизация:
- Используйте аппаратное ускорение GPU
- Настройте Intel HAXM или Hyper-V
- Ограничьте количество одновременных AVD

---

## ✅ Чек-лист готовности системы

- [ ] Android SDK установлен
- [ ] Bat To Exe Converter установлен  
- [ ] Python зависимости установлены
- [ ] PowerShell политика настроена
- [ ] Flask API запущен
- [ ] Тестовые шаги выполняются успешно
- [ ] Пароль администратора изменен
- [ ] RDP Wrapper настроен
- [ ] Микрофон протестирован

**Система готова к работе! 🎉**
