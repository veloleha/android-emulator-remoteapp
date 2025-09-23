#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Android Emulator RemoteApp Flask API
Автор: Система автоматизации
Дата: 2025-09-23
Назначение: API для работы с React фронтендом и пошаговое тестирование RemoteApp
"""

import os
import re
import json
import logging
import subprocess
import hashlib
import uuid
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

# Конфигурация приложения
app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
CORS(app)  # Разрешаем CORS для React фронтенда

# Настройки
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD_HASH = generate_password_hash('admin123')  # Измените пароль!
POWERSHELL_SCRIPT_PATH = r'C:\emulator\AndroidEmulatorSetup.ps1'
LOG_FILE = r'C:\Scripts\web_log.txt'
DOWNLOAD_DIR = r'C:\Scripts\downloads'

# Убедимся, что директории существуют
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Хранилище сессий и телефонов в памяти (в продакшене использовать базу данных)
sessions = {}
phones_db = {}

def write_log(message, level='INFO'):
    """Функция для записи логов"""
    if level == 'ERROR':
        logging.error(message)
    elif level == 'WARNING':
        logging.warning(message)
    else:
        logging.info(message)

def is_authenticated(token):
    """Проверка аутентификации по токену"""
    return token in sessions and sessions[token]['authenticated']

def get_user_from_token(token):
    """Получение пользователя по токену"""
    if token in sessions:
        return sessions[token].get('user')
    return None

def execute_powershell_step(step_name, script_content, user_context=None):
    """Выполнение отдельного шага PowerShell скрипта"""
    try:
        write_log(f"Выполнение шага: {step_name}")
        
        # Подставляем контекст пользователя в скрипт если нужно
        if user_context:
            for key, value in user_context.items():
                script_content = script_content.replace(f"{{{{ {key} }}}}", str(value))
        
        # Создаем временный скрипт для шага
        temp_script = f"C:\\Scripts\\temp_{step_name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ps1"
        with open(temp_script, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        # Выполняем скрипт
        cmd = f'powershell.exe -ExecutionPolicy Bypass -File "{temp_script}" 2>&1'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='cp866', timeout=300)
        
        # Удаляем временный файл
        try:
            os.remove(temp_script)
        except:
            pass
        
        success = result.returncode == 0
        output = result.stdout + result.stderr
        
        write_log(f"Шаг '{step_name}' {'выполнен успешно' if success else 'завершился с ошибкой'}")
        
        return {
            'success': success,
            'output': output,
            'step': step_name,
            'timestamp': datetime.now().isoformat()
        }
    except subprocess.TimeoutExpired:
        write_log(f"Тайм-аут выполнения шага '{step_name}'", 'ERROR')
        return {
            'success': False,
            'output': 'Тайм-аут выполнения (превышено 5 минут)',
            'step': step_name,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        write_log(f"Ошибка выполнения шага '{step_name}': {str(e)}", 'ERROR')
        return {
            'success': False,
            'output': str(e),
            'step': step_name,
            'timestamp': datetime.now().isoformat()
        }

# API эндпоинты для React фронтенда

@app.route('/api/login', methods=['POST'])
def api_login():
    """API для входа в систему"""
    data = request.get_json()
    username = data.get('username', '')
    password = data.get('password', '')
    
    if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
        # Создаем токен сессии
        token = str(uuid.uuid4())
        sessions[token] = {
            'authenticated': True,
            'user': {
                'id': '1',
                'telegramUsername': username,
                'balance': 100.0,
                'totalPhones': 0,
                'totalSpent': 0.0
            },
            'created_at': datetime.now()
        }
        
        write_log(f"Успешный вход администратора с IP: {request.remote_addr}")
        return jsonify({
            'success': True,
            'token': token,
            'user': sessions[token]['user']
        })
    else:
        write_log(f"Неудачная попытка входа с IP: {request.remote_addr}, имя пользователя: {username}", 'WARNING')
        return jsonify({
            'success': False,
            'error': 'Неверные учетные данные'
        }), 401

@app.route('/api/logout', methods=['POST'])
def api_logout():
    """API для выхода из системы"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if token in sessions:
        del sessions[token]
        write_log("Пользователь вышел из системы")
    return jsonify({'success': True})

@app.route('/api/phones', methods=['GET'])
def api_get_phones():
    """Получение списка телефонов пользователя"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not is_authenticated(token):
        return jsonify({'error': 'Не авторизован'}), 401
    
    user = get_user_from_token(token)
    user_phones = [phone for phone in phones_db.values() if phone.get('owner_id') == user['id']]
    
    return jsonify({
        'success': True,
        'phones': user_phones
    })

@app.route('/api/create_phone', methods=['POST'])
def api_create_phone():
    """API для создания нового телефона (эмулятора)"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not is_authenticated(token):
        return jsonify({'error': 'Не авторизован'}), 401
    
    data = request.get_json()
    phone_data = {
        'name': data.get('name', 'Android Phone'),
        'model': data.get('model', 'Pixel 6'),
        'apiLevel': data.get('apiLevel', 'API 33')
    }
    
    user = get_user_from_token(token)
    write_log(f"Создание нового телефона для пользователя {user['telegramUsername']}: {phone_data}")
    
    try:
        # Выполняем полную настройку через PowerShell
        cmd = f'powershell.exe -ExecutionPolicy Bypass -File "{POWERSHELL_SCRIPT_PATH}" 2>&1'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='cp866', timeout=600)
        
        if result.returncode == 0:
            # Парсим результат
            parsed = parse_full_setup_output(result.stdout + result.stderr)
            
            # Создаем запись телефона в базе
            phone_id = str(uuid.uuid4())
            new_phone = {
                'id': phone_id,
                'name': phone_data['name'],
                'status': 'active',
                'timeRemaining': 24.0,  # 24 часа
                'model': phone_data['model'],
                'apiLevel': phone_data['apiLevel'],
                'createdAt': datetime.now().isoformat(),
                'lastPayment': datetime.now().isoformat(),
                'owner_id': user['id'],
                'username': parsed.get('username', ''),
                'password': parsed.get('password', ''),
                'rdp_file': parsed.get('rdp_file', '')
            }
            
            phones_db[phone_id] = new_phone
            
            # Обновляем статистику пользователя
            sessions[token]['user']['totalPhones'] += 1
            
            write_log(f"Телефон создан успешно: {phone_id}")
            return jsonify({
                'success': True,
                'phone': new_phone,
                'setup_output': result.stdout + result.stderr
            })
        else:
            error_msg = f"Ошибка создания телефона: {result.stdout + result.stderr}"
            write_log(error_msg, 'ERROR')
            return jsonify({
                'success': False,
                'error': error_msg
            }), 500
    
    except Exception as e:
        error_msg = f"Исключение при создании телефона: {str(e)}"
        write_log(error_msg, 'ERROR')
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500

@app.route('/api/test_step', methods=['POST'])
def api_test_step():
    """API для тестирования отдельных шагов"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not is_authenticated(token):
        return jsonify({'error': 'Не авторизован'}), 401
    
    data = request.get_json()
    step_name = data.get('step')
    
    user = get_user_from_token(token)
    write_log(f"Запрос на тестирование шага: {step_name} от пользователя {user['telegramUsername']}")
    
    # Импортируем скрипты шагов
    from step_scripts import STEP_SCRIPTS, STEP_DESCRIPTIONS
    
    if step_name not in STEP_SCRIPTS:
        return jsonify({
            'success': False,
            'error': f'Неизвестный шаг: {step_name}',
            'available_steps': list(STEP_SCRIPTS.keys())
        })
    
    # Выполняем шаг
    result = execute_powershell_step(step_name, STEP_SCRIPTS[step_name])
    
    # Парсим результат для извлечения полезной информации
    parsed_result = parse_step_output(result['output'], step_name)
    result.update(parsed_result)
    
    return jsonify(result)

@app.route('/api/steps_info', methods=['GET'])
def api_get_steps_info():
    """Получение информации о всех доступных шагах тестирования"""
    from step_scripts import STEP_DESCRIPTIONS
    return jsonify({
        'success': True,
        'steps': STEP_DESCRIPTIONS
    })

@app.route('/api/download_rdp/<phone_id>', methods=['GET'])
def api_download_rdp(phone_id):
    """Скачивание RDP файла для конкретного телефона"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not is_authenticated(token):
        return jsonify({'error': 'Не авторизован'}), 401
    
    if phone_id not in phones_db:
        return jsonify({'error': 'Телефон не найден'}), 404
    
    phone = phones_db[phone_id]
    rdp_file = phone.get('rdp_file')
    
    if not rdp_file or not os.path.exists(rdp_file):
        return jsonify({'error': 'RDP файл не найден'}), 404
    
    write_log(f"Скачивание RDP файла для телефона {phone_id}: {os.path.basename(rdp_file)}")
    return send_file(rdp_file, as_attachment=True, download_name=f"{phone['name']}.rdp")

def parse_step_output(output, step_name):
    """Парсинг вывода шага для извлечения полезной информации"""
    result = {}
    
    if 'SUCCESS:' in output or '✅ SUCCESS:' in output:
        result['success'] = True
        
        # Извлекаем специфичную для шага информацию
        if step_name == 'create_user':
            username_match = re.search(r'USERNAME: (.+)', output)
            password_match = re.search(r'PASSWORD: (.+)', output)
            if username_match and password_match:
                result['username'] = username_match.group(1).strip()
                result['password'] = password_match.group(1).strip()
        
        elif step_name == 'create_avd':
            avd_match = re.search(r'AVD_NAME: (.+)', output)
            if avd_match:
                result['avd_name'] = avd_match.group(1).strip()
        
        elif step_name == 'create_batch':
            batch_match = re.search(r'BATCH_FILE: (.+)', output)
            if batch_match:
                result['batch_file'] = batch_match.group(1).strip()
        
        elif step_name == 'convert_to_exe':
            exe_match = re.search(r'EXE_FILE: (.+)', output)
            if exe_match:
                result['exe_file'] = exe_match.group(1).strip()
        
        elif step_name == 'configure_remoteapp':
            app_match = re.search(r'APP_NAME: (.+)', output)
            path_match = re.search(r'APP_PATH: (.+)', output)
            if app_match and path_match:
                result['app_name'] = app_match.group(1).strip()
                result['app_path'] = path_match.group(1).strip()
        
        elif step_name == 'create_rdp':
            rdp_match = re.search(r'RDP_FILE: (.+)', output)
            if rdp_match:
                result['rdp_file'] = rdp_match.group(1).strip()
        
        elif step_name == 'test_microphone':
            mic_match = re.search(r'MICROPHONE_STATUS: (.+)', output)
            if mic_match:
                result['microphone_status'] = mic_match.group(1).strip()
    
    else:
        result['success'] = False
        if 'ERROR:' in output or '❌ ERROR:' in output:
            error_match = re.search(r'(?:❌ )?ERROR: (.+)', output)
            if error_match:
                result['error'] = error_match.group(1).strip()
    
    return result

def parse_full_setup_output(output):
    """Парсинг вывода полной настройки"""
    result = {}
    
    # Извлекаем информацию о пользователе
    username_match = re.search(r'Username: (.+)', output)
    password_match = re.search(r'Password: (.+)', output)
    rdp_match = re.search(r'RDP File: (.+)', output)
    
    if username_match:
        result['username'] = username_match.group(1).strip()
    if password_match:
        result['password'] = password_match.group(1).strip()
    if rdp_match:
        result['rdp_file'] = rdp_match.group(1).strip()
    
    return result

# Статический контент для простого HTML интерфейса
@app.route('/')
def serve_main_interface():
    """Обслуживание главной страницы"""
    # Получаем абсолютный путь к файлу в текущей директории
    html_file = os.path.join(os.path.dirname(__file__), 'simple_interface.html')
    return send_file(html_file)

@app.route('/<path:filename>')
def serve_static_files(filename):
    """Обслуживание статических файлов"""
    try:
        # Получаем абсолютный путь к файлу
        file_path = os.path.join(os.path.dirname(__file__), filename)
        return send_file(file_path)
    except:
        # Если файл не найден, возвращаем главную страницу
        html_file = os.path.join(os.path.dirname(__file__), 'simple_interface.html')
        return send_file(html_file)

if __name__ == '__main__':
    write_log("Запуск Flask API для Android Emulator Manager")
    print("")
    print("Android Emulator RemoteApp API запущен!")
    print("")
    print("Доступные эндпоинты:")
    print("  POST /api/login - Вход в систему")
    print("  POST /api/logout - Выход из системы")
    print("  GET  /api/phones - Получение списка телефонов")
    print("  POST /api/create_phone - Создание нового телефона")
    print("  POST /api/test_step - Пошаговое тестирование")
    print("  GET  /api/steps_info - Информация о шагах")
    print("  GET  /api/download_rdp/<id> - Скачивание RDP файла")
    print("")
    print("Веб-интерфейс: http://localhost:5000")
    print("API Base URL: http://localhost:5000/api")
    print("")
    print("Не забудьте:")
    print("  1. Изменить пароль администратора в коде")
    print("  2. Установить Android SDK")
    print("  3. Установить Bat To Exe Converter")
    print("  4. Запустить от имени администратора")
    print("")
    
    app.run(host='0.0.0.0', port=5000, debug=True)

# Очистка старых сессий (запускается периодически)
def cleanup_old_sessions():
    """Очистка старых сессий (старше 24 часов)"""
    current_time = datetime.now()
    expired_tokens = []
    
    for token, session_data in sessions.items():
        if current_time - session_data['created_at'] > timedelta(hours=24):
            expired_tokens.append(token)
    
    for token in expired_tokens:
        del sessions[token]
        write_log(f"Удалена устаревшая сессия: {token[:8]}...")
    
    return len(expired_tokens)
