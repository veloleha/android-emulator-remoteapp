# 🚀 Руководство по новым функциям

## 📋 Обзор новых возможностей

Версия включает следующие улучшения:
- ✅ SQLite база данных для постоянного хранения
- ✅ Настройка IP адреса для RemoteApp
- ✅ Единый пароль UniCo2022 для всех операторов  
- ✅ Автоматическое сохранение пароля в RDP файлах
- ✅ Удаление эмуляторов с полной очисткой

## 🗄️ SQLite База данных

### Описание
Все данные теперь сохраняются в SQLite базе данных `C:\Scripts\emulator_manager.db`

### Структура таблиц
```sql
-- Настройки системы
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- Операторы (пользователи Windows)
CREATE TABLE operators (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Эмуляторы Android
CREATE TABLE emulators (
    id TEXT PRIMARY KEY,
    operator_id TEXT NOT NULL,
    name TEXT NOT NULL,
    device TEXT NOT NULL,
    api_level TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    rdp_file TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (operator_id) REFERENCES operators (id)
);
```

### Преимущества
- 📊 Данные сохраняются после перезагрузки сервера
- 🔒 Потокобезопасность через `db_lock`
- 🚀 Быстрый доступ к данным
- 📈 Масштабируемость

## 🌐 Настройка IP адреса

### Как использовать
1. Войдите как администратор
2. Нажмите кнопку **"Настройки IP"**
3. Введите IP адрес или имя сервера
4. Нажмите **"Сохранить"**

### Применение
- IP используется в RDP файлах вместо имени компьютера
- Позволяет подключаться к эмуляторам по сети
- Настройка сохраняется в базе данных

### API
```http
GET /api/settings/rdp_ip    # Получить текущий IP
POST /api/settings/rdp_ip   # Установить новый IP
```

## 🔑 Единый пароль UniCo2022

### Описание
Все операторы создаются с единым паролем `UniCo2022`

### Преимущества
- 🔐 Упрощенное управление паролями
- 🚀 Быстрый доступ для операторов
- 💾 Автоматическое сохранение в RDP файлах
- 🔄 Отключен запрос пароля при подключении

### Настройки RDP
```ini
prompt for credentials on client:i:0  # Отключен запрос пароля
username:s:UserX                      # Имя пользователя
password 51:b:[hex-encoded]           # Зашифрованный пароль
```

## 🗑️ Удаление эмуляторов

### Как использовать
1. Войдите как оператор
2. В списке эмуляторов нажмите **"Удалить"**
3. Подтвердите удаление в диалоге
4. Дождитесь завершения операции

### Что удаляется
- 📱 AVD файлы из директории пользователя
- 📄 Batch и EXE файлы из `C:\Scripts\`
- 📋 RDP файл
- 🗂️ Запись в реестре RemoteApp
- 💾 Запись в базе данных

### Поддержка .HP директорий
Автоматически обрабатывает как обычные директории `C:\Users\UserX\`, так и с суффиксом `C:\Users\UserX.HP\`

### API
```http
DELETE /api/delete_emulator/<emulator_id>
```

## 🔧 Технические детали

### Переменные окружения
Контекст передается в PowerShell скрипты через переменные окружения:
- `RDP_IP` - IP адрес для RDP подключений
- `OPERATOR_PASSWORD` - Пароль оператора
- `USERNAME` - Имя пользователя
- `EMULATOR_NAME` - Название эмулятора

### Новые API эндпоинты
```http
GET /api/settings/rdp_ip           # Получить IP настройки
POST /api/settings/rdp_ip          # Установить IP настройки
DELETE /api/delete_emulator/<id>   # Удалить эмулятор
```

### Функции базы данных
```python
init_database()                    # Инициализация БД
get_setting(key, default)          # Получить настройку
set_setting(key, value)            # Установить настройку
create_operator_db(username, pwd)  # Создать оператора
get_all_operators_db()             # Получить всех операторов
create_emulator_db(...)            # Создать эмулятор
get_operator_emulators_db(op_id)   # Получить эмуляторы оператора
delete_emulator_db(emulator_id)    # Удалить эмулятор
```

## 🚀 Запуск системы

### Требования
- Python 3.7+
- Flask
- SQLite3 (встроен в Python)
- Права администратора

### Запуск
```bash
cd C:\Users\admin\CascadeProjects\android-emulator-remoteapp\web
python app.py
```

### Доступ
- **URL:** http://127.0.0.1:5000
- **Админ:** admin / admin123
- **Операторы:** UserX / UniCo2022

## 📊 Мониторинг

### Логи
- **Flask логи:** `C:\Scripts\web_log.txt`
- **PowerShell логи:** `C:\Scripts\debug_last_step.ps1`

### База данных
- **Файл:** `C:\Scripts\emulator_manager.db`
- **Просмотр:** Любой SQLite клиент

### Файлы системы
- **Scripts:** `C:\Scripts\`
- **AVD:** `C:\Users\UserX\.android\avd\` или `C:\Users\UserX.HP\.android\avd\`

## 🎯 Результат

Полнофункциональная система управления Android эмуляторами с:
- 💾 Постоянным хранением данных
- 🌐 Настраиваемым сетевым доступом
- 🔐 Упрощенной аутентификацией
- 🗑️ Удобным управлением эмуляторами

**Система готова к продуктивному использованию!** 🎉
