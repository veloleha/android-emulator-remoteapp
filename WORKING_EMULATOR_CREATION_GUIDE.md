# 🎯 Рабочая цепочка создания нового эмулятора Android RemoteApp

## ✅ Проверенная и работающая методология

**Дата создания**: 25.09.2025  
**Статус**: ✅ ПРОТЕСТИРОВАНО И РАБОТАЕТ  
**Пример**: User1_Phone3 (small_phone) - успешно запущен

---

## 📋 Пошаговая инструкция

### **Шаг 1: Создание AVD через avdmanager**

```powershell
# Настройка переменных окружения
$AndroidHome = "C:\Program Files\Android"
$env:ANDROID_HOME = $AndroidHome
$env:ANDROID_SDK_ROOT = $AndroidHome
$env:JAVA_HOME = "C:\Program Files\Microsoft\jdk-17.0.16.8-hotspot"
$env:Path = "$env:JAVA_HOME\bin;$AndroidHome\platform-tools;$AndroidHome\emulator;$AndroidHome\cmdline-tools\latest\bin;" + $env:Path

# Создание AVD
$AvdName = "User1_Phone3"  # Уникальное имя
$UserAndroidDir = "C:\Users\User1\.android\avd"
$env:ANDROID_AVD_HOME = $UserAndroidDir
$AvdManagerPath = "$AndroidHome\cmdline-tools\latest\bin\avdmanager.bat"

# Команда создания (БЕЗ аудио параметров!)
$CreateAvdCmd = "`"$AvdManagerPath`" create avd -n `"$AvdName`" -k `"system-images;android-36;google_apis_playstore;x86_64`" -d `"small_phone`" -c `"512M`" --force"
cmd.exe /c $CreateAvdCmd
```

**⚠️ ВАЖНО**: НЕ трогать config.ini после создания! Оставить как есть.

### **Шаг 2: Создание Batch файла**

```powershell
$BatchFilePath = "C:\Scripts\User1_Phone3_emulator.bat"
$BatchContent = @"
@echo off
title User1 Android Emulator - Phone3

echo ========================================
echo Android Emulator - User1_Phone3
echo Small Phone Device
echo ========================================

REM Переменные окружения
set ANDROID_HOME=C:\Program Files\Android
set ANDROID_SDK_ROOT=C:\Program Files\Android
set JAVA_HOME=C:\Program Files\Microsoft\jdk-17.0.16.8-hotspot
set PATH=%JAVA_HOME%\bin;%ANDROID_HOME%\platform-tools;%ANDROID_HOME%\emulator;%ANDROID_HOME%\cmdline-tools\latest\bin;%PATH%
set ANDROID_AVD_HOME=C:\Users\User1\.android\avd

echo Проверка наличия AVD...
if not exist "%ANDROID_AVD_HOME%\User1_Phone3.avd" (
    echo ОШИБКА: AVD не найден!
    pause
    exit /b 1
)

echo Переход в директорию эмулятора...
cd /d "%ANDROID_HOME%\emulator"

echo Запуск эмулятора...
REM БЕЗ -audio-in и -audio-out параметров!
emulator -avd "User1_Phone3" -no-snapshot -gpu host -memory 4096 -no-boot-anim -netdelay none -netspeed full -verbose

pause
"@

Set-Content -Path $BatchFilePath -Value $BatchContent -Encoding ASCII
```

### **Шаг 3: Создание EXE файла**

```powershell
$ExeFilePath = "C:\Scripts\User1Phone3AndroidEmulator.exe"

$CSharpCode = @"
using System;
using System.Diagnostics;
using System.IO;

public class EmulatorLauncher
{
    public static void Main()
    {
        try
        {
            string batchFile = @"C:\Scripts\User1_Phone3_emulator.bat";
            
            if (!File.Exists(batchFile))
            {
                Console.WriteLine("ОШИБКА: Batch файл не найден: " + batchFile);
                Console.ReadKey();
                return;
            }
            
            ProcessStartInfo psi = new ProcessStartInfo();
            psi.FileName = batchFile;
            psi.UseShellExecute = true;
            psi.WindowStyle = ProcessWindowStyle.Normal;
            psi.WorkingDirectory = @"C:\Scripts";
            
            Process process = Process.Start(psi);
            if (process != null)
            {
                process.WaitForExit();
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine("ОШИБКА: " + ex.Message);
            Console.ReadKey();
        }
    }
}
"@

Add-Type -TypeDefinition $CSharpCode -OutputAssembly $ExeFilePath -OutputType ConsoleApplication
```

### **Шаг 4: Регистрация в RemoteApp**

```powershell
$AppName = "User1Phone3AndroidEmulator"
$RemoteAppRegPath = "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Terminal Server\TSAppAllowList\Applications"
$AppRegPath = "$RemoteAppRegPath\$AppName"

# Создание записи в реестре
New-Item -Path $AppRegPath -Force | Out-Null
Set-ItemProperty -Path $AppRegPath -Name "Name" -Value "User1 Android Emulator - Phone3"
Set-ItemProperty -Path $AppRegPath -Name "Path" -Value $ExeFilePath
Set-ItemProperty -Path $AppRegPath -Name "CommandLineSetting" -Value 1
Set-ItemProperty -Path $AppRegPath -Name "RequiredCommandLine" -Value ""
Set-ItemProperty -Path $AppRegPath -Name "IconPath" -Value $ExeFilePath
Set-ItemProperty -Path $AppRegPath -Name "IconIndex" -Value 0
Set-ItemProperty -Path $AppRegPath -Name "ShowInTSWA" -Value 1
Set-ItemProperty -Path $AppRegPath -Name "VPath" -Value $AppName

# Включение RemoteApp
$TSAppAllowListPath = "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Terminal Server\TSAppAllowList"
Set-ItemProperty -Path $TSAppAllowListPath -Name "fDisabledAllowList" -Value 0
```

### **Шаг 5: Создание RDP файла**

```powershell
$RdpFilePath = "C:\Scripts\User1_Phone3_RemoteApp.rdp"
$ServerAddress = $env:COMPUTERNAME

$RdpContent = @"
full address:s:$ServerAddress`:3389
remoteapplicationmode:i:1
remoteapplicationname:s:User1 Android Emulator - Phone3
remoteapplicationprogram:s:||$AppName
alternate shell:s:rdpinit.exe
disableremoteappcapscheck:i:1
prompt for credentials on client:i:1
username:s:User1
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

Set-Content -Path $RdpFilePath -Value $RdpContent -Encoding UTF8
```

### **Шаг 6: Создание ярлыка**

```powershell
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = "$DesktopPath\User1 Android Phone3.lnk"

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $RdpFilePath
$Shortcut.Description = "User1 Android Emulator - Phone3 (RemoteApp)"
$Shortcut.WorkingDirectory = "C:\Scripts"
$Shortcut.Save()
```

---

## 🔑 Ключевые моменты успеха

### **✅ ЧТО РАБОТАЕТ:**

1. **Использование avdmanager** вместо копирования файлов
2. **Устройство small_phone** - стабильно работает
3. **НЕ трогать config.ini** после создания через avdmanager
4. **Убрать -audio-in и -audio-out** из команды эмулятора
5. **Создание EXE через C# компиляцию** вместо внешних конверторов

### **❌ ЧТО НЕ РАБОТАЕТ:**

1. ~~Копирование готовых AVD директорий~~ - проблемы с .ini файлами
2. ~~Использование -audio-in -audio-out~~ - неподдерживаемые параметры
3. ~~Ручное редактирование config.ini~~ - ломает AVD
4. ~~Pixel 6 устройство~~ - не всегда стабильно

---

## 📁 Результирующие файлы

После выполнения всех шагов должны быть созданы:

```
C:\Scripts\
├── User1_Phone3_emulator.bat          # Batch файл
├── User1Phone3AndroidEmulator.exe     # EXE файл
└── User1_Phone3_RemoteApp.rdp         # RDP файл

C:\Users\User1\.android\avd\
├── User1_Phone3.avd\                  # AVD директория
└── User1_Phone3.ini                   # AVD конфигурация

Desktop\
└── User1 Android Phone3.lnk           # Ярлык RemoteApp
```

---

## 🧪 Тестирование

### **Проверка работоспособности:**

1. **AVD Manager**: `avdmanager list avd` - должен показать AVD без ошибок
2. **Batch файл**: Запуск должен открыть эмулятор без ошибок аудио
3. **EXE файл**: Должен запускать batch файл корректно
4. **RemoteApp**: RDP подключение должно открыть эмулятор
5. **Ярлык**: Двойной клик должен запустить RemoteApp

### **Ожидаемый результат:**
- ✅ Эмулятор запускается без ошибок
- ✅ Отображается Android интерфейс
- ✅ Разрешение: 720x1280 (small_phone)
- ✅ RAM: 4096MB
- ✅ RemoteApp работает стабильно

---

## 🔄 Автоматизация

Эта методология может быть интегрирована в `step_scripts.py` для автоматического создания эмуляторов через Flask API.

**Статус интеграции**: ✅ Частично реализовано в step_scripts.py

---

## 📞 Поддержка

При возникновении проблем проверьте:

1. **Переменные окружения** Android SDK
2. **Права доступа** пользователя на .android директорию
3. **Наличие системных образов** android-36
4. **Статус RemoteApp** в реестре Windows

**Последнее обновление**: 25.09.2025 01:30  
**Протестировано на**: Windows Server с Android SDK 36.1.9
