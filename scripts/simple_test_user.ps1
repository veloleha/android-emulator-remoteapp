# Простой тест создания пользователя Windows
# Без сложных конструкций try-catch

Write-Host "=== ПРОСТОЙ ТЕСТ СОЗДАНИЯ ПОЛЬЗОВАТЕЛЯ ===" -ForegroundColor Cyan

# Поиск следующего доступного номера пользователя
$UserNumber = 1
do {
    $Username = "User$UserNumber"
    $UserExists = Get-LocalUser -Name $Username -ErrorAction SilentlyContinue
    if ($UserExists) {
        $UserNumber++
    }
} while ($UserExists)

Write-Host "Создаем пользователя: $Username" -ForegroundColor Yellow

# Генерация пароля
$Password = [System.Guid]::NewGuid().ToString().Replace("-", "").Substring(0, 16)
Write-Host "Пароль: $Password" -ForegroundColor Yellow

# Создание пользователя
$SecurePassword = ConvertTo-SecureString $Password -AsPlainText -Force
New-LocalUser -Name $Username -Password $SecurePassword -FullName "Android Emulator User" -Description "Android Emulator User" -PasswordNeverExpires -UserMayNotChangePassword

# Проверка создания
$CreatedUser = Get-LocalUser -Name $Username -ErrorAction SilentlyContinue
if ($CreatedUser) {
    Write-Host "SUCCESS: Пользователь $Username создан" -ForegroundColor Green
} else {
    Write-Host "ERROR: Не удалось создать пользователя" -ForegroundColor Red
    exit 1
}

# Добавление в группы
Write-Host "Добавляем в группы..." -ForegroundColor Yellow

# Группа Users
$UsersGroup = Get-LocalGroup -SID "S-1-5-32-545" -ErrorAction SilentlyContinue
if ($UsersGroup) {
    Add-LocalGroupMember -Group $UsersGroup.Name -Member $Username -ErrorAction SilentlyContinue
    Write-Host "Добавлен в группу Users: $($UsersGroup.Name)" -ForegroundColor Green
} else {
    Write-Host "Группа Users не найдена" -ForegroundColor Red
}

# Группа Remote Desktop Users
$RDPGroup = Get-LocalGroup -SID "S-1-5-32-555" -ErrorAction SilentlyContinue
if ($RDPGroup) {
    Add-LocalGroupMember -Group $RDPGroup.Name -Member $Username -ErrorAction SilentlyContinue
    Write-Host "Добавлен в группу RDP: $($RDPGroup.Name)" -ForegroundColor Green
} else {
    Write-Host "Группа Remote Desktop Users не найдена" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== РЕЗУЛЬТАТ ===" -ForegroundColor Cyan
Write-Host "USERNAME: $Username" -ForegroundColor White
Write-Host "PASSWORD: $Password" -ForegroundColor White
Write-Host "SUCCESS: Пользователь создан успешно!" -ForegroundColor Green
