# 🔧 ИСПРАВЛЕНИЕ ПРОБЛЕМЫ LOCK FILES ЭМУЛЯТОРА

## ❌ **Проблема:**
```
ERROR | Unexpected error while creating: C:\Users\User28.HP\.android\emu-last-feature-flags.protobuf.lock (error: 3)
```

## 🔍 **Причина:**
1. **Неправильная логика определения директории пользователя** - скрипты искали `.HP` директорию вместо основной
2. **Отсутствие lock файлов** в правильной директории
3. **Неправильные права доступа** на файлы эмулятора

## ✅ **Решение:**

### **1. Исправлена логика определения директории:**
```powershell
# БЫЛО (неправильно):
$ActualUserProfile = if (Test-Path $UserProfilePathHP) { $UserProfilePathHP } else { $UserProfilePath }

# СТАЛО (правильно):
if (Test-Path "$UserProfilePath\.android") {
    $ActualUserProfile = $UserProfilePath  # Используем основную директорию
} elseif (Test-Path "$UserProfilePathHP\.android") {
    $ActualUserProfile = $UserProfilePathHP  # Используем .HP только если там есть .android
}
```

### **2. Созданы необходимые lock файлы:**
- `emu-last-feature-flags.protobuf`
- `emu-last-feature-flags.protobuf.lock`
- `emulator-check.exe.lock`
- `pid.lock`
- `cache.lock`

### **3. Исправлены права доступа:**
```powershell
# Взятие владения
takeown /F "C:\Users\User28\.android" /R /D Y

# Установка полных прав
icacls "C:\Users\User28\.android" /grant Everyone:(OI)(CI)F /T /Q
```

## 📊 **Результаты тестирования:**

### **✅ User28 - ИСПРАВЛЕНО:**
- **Директория:** `C:\Users\User28\.android` (правильная)
- **AVD:** `User28_bobik.avd` (найден)
- **Lock файлы:** Созданы и настроены права
- **Эмулятор:** ✅ Запущен успешно (PID 40764)

### **🔧 Обновленные скрипты:**
- `copy_template_avd_fixed.ps1` - исправлена логика определения директории
- `create_batch_fixed.ps1` - исправлена логика определения директории
- `fix_permissions_simple.ps1` - создание lock файлов и настройка прав

## 🎯 **Ключевые изменения:**

### **Приоритет директорий:**
1. **Основная директория** `C:\Users\UserXX` (если есть `.android`)
2. **HP директория** `C:\Users\UserXX.HP` (если есть `.android`)
3. **Основная директория** (если существует)
4. **HP директория** (fallback)

### **Автоматическое исправление:**
- Создание недостающих lock файлов
- Установка правильных прав доступа
- Взятие владения файлами эмулятора

## 🚀 **Статус:**
**✅ ПРОБЛЕМА РЕШЕНА!**

- Эмулятор User28_bobik запущен без ошибок
- Lock файлы созданы в правильной директории
- Права доступа настроены корректно
- Логика скриптов исправлена для будущих пользователей

**Система готова к работе!** 🎉
