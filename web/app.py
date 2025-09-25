#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Android Emulator RemoteApp Flask API
Автор: Система автоматизации
Дата: 2025-09-23
Назначение: API для работы с React фронтендом и пошаговое тестирование RemoteApp
"""

import os
import tempfile
import ctypes
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
import sqlite3
import threading

# Конфигурация приложения
app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
CORS(app)  # Разрешаем CORS для React фронтенда

# Настройки
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD_HASH = generate_password_hash('admin123')  # Измените пароль!
OPERATOR_PASSWORD = 'UniCo2022'  # Единый пароль для всех операторов
POWERSHELL_SCRIPT_PATH = r'C:\emulator\AndroidEmulatorSetup.ps1'
LOG_FILE = r'C:\Scripts\web_log.txt'
DOWNLOAD_DIR = r'C:\Scripts\downloads'
DATABASE_PATH = r'C:\Scripts\emulator_manager.db'
DEFAULT_RDP_IP = '127.0.0.1'  # IP по умолчанию для RemoteApp

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

# Хранилище сессий в памяти (временные данные)
sessions = {}

# Блокировка для потокобезопасности базы данных
db_lock = threading.Lock()

def init_database():
    """Инициализация SQLite базы данных"""
    with db_lock:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Таблица настроек
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        ''')
        
        # Таблица операторов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS operators (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица эмуляторов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS emulators (
                id TEXT PRIMARY KEY,
                operator_id TEXT NOT NULL,
                name TEXT NOT NULL,
                device TEXT NOT NULL,
                api_level TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                rdp_file TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (operator_id) REFERENCES operators (id)
            )
        ''')
        
        # Устанавливаем IP по умолчанию если не установлен
        cursor.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', 
                      ('rdp_ip', DEFAULT_RDP_IP))
        
        conn.commit()
        conn.close()

def get_setting(key, default=None):
    """Получить настройку из базы данных"""
    with db_lock:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else default

def set_setting(key, value):
    """Установить настройку в базе данных"""
    with db_lock:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, value))
        conn.commit()
        conn.close()

# Инициализация базы данных при запуске
init_database()

def write_log(message, level='INFO'):
    """Функция для записи логов"""
    if level == 'ERROR':
        logging.error(message)
    elif level == 'WARNING':
        logging.warning(message)
    else:
        logging.info(message)

# Функции для работы с операторами
def create_operator_db(username, password=OPERATOR_PASSWORD):
    """Создать оператора в базе данных"""
    with db_lock:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        operator_id = str(uuid.uuid4())
        try:
            cursor.execute('''
                INSERT INTO operators (id, username, password, status)
                VALUES (?, ?, ?, 'active')
            ''', (operator_id, username, password))
            conn.commit()
            conn.close()
            return operator_id
        except sqlite3.IntegrityError:
            conn.close()
            return None  # Пользователь уже существует

def get_operator_db(username):
    """Получить оператора из базы данных"""
    with db_lock:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM operators WHERE username = ?', (username,))
        result = cursor.fetchone()
        conn.close()
        if result:
            return {
                'id': result[0],
                'username': result[1],
                'password': result[2],
                'status': result[3],
                'created_at': result[4]
            }
        return None

def get_all_operators_db():
    """Получить всех операторов из базы данных"""
    with db_lock:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM operators ORDER BY created_at DESC')
        results = cursor.fetchall()
        conn.close()
        operators = []
        for row in results:
            operators.append({
                'id': row[0],
                'username': row[1],
                'password': row[2],
                'status': row[3],
                'created_at': row[4]
            })
        return operators

# Функции для работы с эмуляторами
def create_emulator_db(operator_id, name, device, api_level, rdp_file=None):
    """Создать эмулятор в базе данных"""
    with db_lock:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        emulator_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO emulators (id, operator_id, name, device, api_level, rdp_file, status)
            VALUES (?, ?, ?, ?, ?, ?, 'active')
        ''', (emulator_id, operator_id, name, device, api_level, rdp_file))
        conn.commit()
        conn.close()
        return emulator_id

def get_emulator_by_id_db(emulator_id):
    """Получить эмулятор по его ID из базы данных"""
    with db_lock:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM emulators WHERE id = ?', (emulator_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        return {
            'id': row[0],
            'operator_id': row[1],
            'name': row[2],
            'device': row[3],
            'api_level': row[4],
            'status': row[5],
            'rdp_file': row[6],
            'created_at': row[7]
        }

def get_operator_emulators_db(operator_id):
    """Получить эмуляторы оператора из базы данных"""
    with db_lock:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM emulators WHERE operator_id = ? ORDER BY created_at DESC', (operator_id,))
        results = cursor.fetchall()
        conn.close()
        emulators = []
        for row in results:
            emulators.append({
                'id': row[0],
                'operator_id': row[1],
                'name': row[2],
                'device': row[3],
                'api_level': row[4],
                'status': row[5],
                'rdp_file': row[6],
                'created_at': row[7]
            })
        return emulators

def delete_emulator_db(emulator_id):
    """Удалить эмулятор из базы данных"""
    with db_lock:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM emulators WHERE id = ?', (emulator_id,))
        conn.commit()
        conn.close()

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
        
        # Проверяем права администратора для шагов, требующих повышенных прав
        admin_required_steps = {
            'create_user',
            'create_avd',
            'create_batch',
            'convert_to_exe',
            'configure_remoteapp',
            'create_rdp',
            'test_microphone'
        }
        try:
            is_admin = bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:
            is_admin = False
        if step_name in admin_required_steps and not is_admin:
            msg = (
                "Требуются права администратора для выполнения шага '"
                + step_name + "'. Запустите сервер Flask/PowerShell от имени администратора."
            )
            write_log(msg, 'ERROR')
            return {
                'success': False,
                'output': msg,
                'step': step_name,
                'needs_admin': True,
                'timestamp': datetime.now().isoformat()
            }
        
        # Подставляем контекст пользователя в скрипт если нужно
        env_vars = {}
        if user_context:
            for key, value in user_context.items():
                script_content = script_content.replace(f"{{{{ {key} }}}}", str(value))
                # Также устанавливаем переменные окружения для PowerShell
                env_vars[key.upper()] = str(value)
        
        # Создаем временный скрипт для шага с правильной кодировкой
        temp_script = f"C:\\Scripts\\temp_{step_name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ps1"
        transcripts_dir = os.path.join(tempfile.gettempdir(), 'emulator_transcripts')
        os.makedirs(transcripts_dir, exist_ok=True)
        transcript_path = os.path.join(transcripts_dir, f"transcript_{step_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        
        # Принудительно устанавливаем UTF-8 для корректной кодировки вывода
        utf8_preamble = (
            "$ErrorActionPreference = 'Continue'\n"
            "$PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'\n"
            "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8\n"
            "$OutputEncoding = [System.Text.Encoding]::UTF8\n"
        )
        # Оборачиваем в транскрипцию, чтобы перехватить Write-Host/хост-вывод
        wrapped = (
            f"Write-Output '[[STEP {step_name} START]]'\n" 
            f"Start-Transcript -Path '{transcript_path}' -Append | Out-Null\n" 
            + script_content +
            "\nStop-Transcript | Out-Null\n"
            "Write-Output '[[STEP END]]'\n"
            "exit 0\n"
        )
        final_script_content = utf8_preamble + wrapped

        # Записываем файл с BOM для корректного чтения PowerShell
        with open(temp_script, 'w', encoding='utf-8-sig') as f:
            f.write(final_script_content)
        
        # Выполняем скрипт с правильной кодировкой
        # Use -NoProfile, enable Information stream, and merge all streams to stdout so Write-Host is captured
        # PowerShell stream redirection: *>&1 merges all streams (success, error, warning, verbose, debug, information) into stdout
        cmd = (
            f'powershell.exe -NoProfile -NonInteractive -NoLogo -ExecutionPolicy Bypass '
            f'-File "{temp_script}" -InformationAction Continue'
        )
        write_log(f"Запуск PowerShell: temp_script={temp_script}, transcript={transcript_path}")
        
        # Подготавливаем окружение с дополнительными переменными
        env = os.environ.copy()
        env.update(env_vars)
        
        # Увеличиваем таймаут до 900 секунд, т.к. установка SDK может занять время
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', timeout=900, env=env)
        
        # Не удаляем временный файл сразу — полезно для отладки. Оставим копию.
        try:
            debug_copy = os.path.join(os.path.dirname(LOG_FILE), 'debug_last_step.ps1')
            os.makedirs(os.path.dirname(debug_copy), exist_ok=True)
            with open(debug_copy, 'w', encoding='utf-8-sig') as df:
                with open(temp_script, 'r', encoding='utf-8-sig', errors='ignore') as sf:
                    df.write(sf.read())
        except Exception:
            pass
        
        success = result.returncode == 0
        # Safely handle potential None values for stdout/stderr
        stdout_text = result.stdout if result.stdout is not None else ''
        stderr_text = result.stderr if result.stderr is not None else ''
        output = stdout_text + stderr_text

        # Всегда добавляем содержимое транскрипта к выводу для надежного парсинга
        try:
            if os.path.exists(transcript_path):
                try:
                    sz = os.path.getsize(transcript_path)
                    write_log(f"Обнаружен транскрипт: {transcript_path} ({sz} bytes)")
                except Exception:
                    pass
                with open(transcript_path, 'r', encoding='utf-8', errors='ignore') as tf:
                    transcript_text = tf.read()
                    # Избегаем дублирования
                    if transcript_text and transcript_text not in output:
                        output = (output or '') + "\n" + transcript_text
        except Exception:
            pass

        # Диагностика: записываем полный вывод шага в файл для отладки
        try:
            os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
            debug_out_path = os.path.join(os.path.dirname(LOG_FILE), f"last_step_output_{step_name}.txt")
            with open(debug_out_path, 'w', encoding='utf-8') as df:
                df.write(output)
        except Exception:
            pass
        
        # Логируем превью вывода (первые 500 символов) и статус
        try:
            preview = (output[:500] + '...') if len(output) > 500 else output
            write_log(f"Вывод шага '{step_name}': {preview}")
        except Exception:
            pass
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
            stdout_text = result.stdout if result.stdout is not None else ''
            stderr_text = result.stderr if result.stderr is not None else ''
            parsed = parse_full_setup_output(stdout_text + stderr_text)
            
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
            stdout_text = result.stdout if result.stdout is not None else ''
            stderr_text = result.stderr if result.stderr is not None else ''
            error_msg = f"Ошибка создания телефона: {stdout_text + stderr_text}"
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

# Состояние прав администратора процесса Flask
@app.route('/api/admin_status', methods=['GET'])
def api_admin_status():
    try:
        is_admin = False
        try:
            is_admin = bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:
            is_admin = False
        return jsonify({'success': True, 'is_admin': is_admin})
    except Exception as e:
        write_log(f"Ошибка в admin_status: {e}", 'ERROR')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/download_rdp/<emulator_id>', methods=['GET'])
def api_download_rdp(emulator_id):
    """Скачивание RDP файла для конкретного эмулятора"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not is_authenticated(token):
        return jsonify({'error': 'Не авторизован'}), 401

    # Получаем данные сессии, чтобы ограничить доступ операторов только своими эмуляторами
    session_data = sessions.get(token, {})
    user_type = session_data.get('user_type')

    emulator = get_emulator_by_id_db(emulator_id)
    if not emulator:
        return jsonify({'error': 'Эмулятор не найден'}), 404

    # Если это оператор, проверяем, что эмулятор принадлежит ему
    if user_type == 'operator':
        operator_id = session_data.get('operator_id')
        if not operator_id or emulator.get('operator_id') != operator_id:
            return jsonify({'error': 'Доступ запрещен'}), 403

    rdp_file = emulator.get('rdp_file')
    if not rdp_file or not os.path.exists(rdp_file):
        return jsonify({'error': 'RDP файл не найден'}), 404

    write_log(f"Скачивание RDP файла для эмулятора {emulator_id}: {os.path.basename(rdp_file)}")
    return send_file(rdp_file, as_attachment=True, download_name=f"{emulator['name']}.rdp")

# === API для управления операторами ===

@app.route('/api/operators', methods=['GET'])
def api_get_operators():
    """Получение списка всех операторов"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not is_authenticated(token):
        return jsonify({'error': 'Не авторизован'}), 401
    
    operators = get_all_operators_db()
    operators_list = []
    for operator in operators:
        # Подсчитываем количество эмуляторов для каждого оператора
        emulators = get_operator_emulators_db(operator['id'])
        operators_list.append({
            'id': operator['id'],
            'username': operator['username'],
            'password': operator['password'],
            'status': operator['status'],
            'created_at': operator['created_at'],
            'emulator_count': len(emulators)
        })
    
    return jsonify({
        'success': True,
        'operators': operators_list
    })

@app.route('/api/settings/rdp_ip', methods=['GET', 'POST'])
def api_rdp_ip_settings():
    """Настройка IP адреса для RemoteApp"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not is_authenticated(token):
        return jsonify({'error': 'Не авторизован'}), 401
    
    if request.method == 'GET':
        # Получить текущий IP
        current_ip = get_setting('rdp_ip', DEFAULT_RDP_IP)
        return jsonify({
            'success': True,
            'rdp_ip': current_ip
        })
    
    elif request.method == 'POST':
        # Установить новый IP
        data = request.get_json()
        if not data or 'rdp_ip' not in data:
            return jsonify({'error': 'IP адрес не указан'}), 400
        
        new_ip = data['rdp_ip'].strip()
        if not new_ip:
            return jsonify({'error': 'IP адрес не может быть пустым'}), 400
        
        set_setting('rdp_ip', new_ip)
        write_log(f"IP адрес для RemoteApp изменен на: {new_ip}")
        
        return jsonify({
            'success': True,
            'message': 'IP адрес обновлен',
            'rdp_ip': new_ip
        })

@app.route('/api/create_operator', methods=['POST'])
def api_create_operator():
    """Создание нового оператора (пользователя Windows + SDK)"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not is_authenticated(token):
        return jsonify({'error': 'Не авторизован'}), 401
    
    write_log("Запуск создания нового оператора...")
    
    try:
        # Импортируем скрипты шагов
        from step_scripts import STEP_SCRIPTS
        
        # Выполняем создание пользователя
        result = execute_powershell_step('create_user', STEP_SCRIPTS['create_user'])
        
        if result['success']:
            # Парсим результат для получения данных пользователя
            parsed_result = parse_step_output(result['output'], 'create_user')
            
            if 'username' in parsed_result:
                # Создаем запись оператора в базе данных с единым паролем
                operator_id = create_operator_db(parsed_result['username'], OPERATOR_PASSWORD)
                
                if operator_id:
                    new_operator = {
                        'id': operator_id,
                        'username': parsed_result['username'],
                        'password': OPERATOR_PASSWORD,  # Единый пароль для всех
                        'status': 'active',
                        'created_at': datetime.now().isoformat(),
                        'sdk_initialized': True
                    }
                
                write_log(f"Оператор создан успешно: {parsed_result['username']}")
                return jsonify({
                    'success': True,
                    'operator': new_operator,
                    'setup_output': result['output']
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Не удалось получить данные созданного пользователя',
                    'output': result['output']
                }), 500
        else:
            return jsonify({
                'success': False,
                'error': 'Ошибка создания пользователя',
                'output': result['output']
            }), 500
    
    except Exception as e:
        error_msg = f"Исключение при создании оператора: {str(e)}"
        write_log(error_msg, 'ERROR')
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500

@app.route('/api/operator_login', methods=['POST'])
def api_operator_login():
    """Вход в систему под оператором"""
    data = request.get_json()
    username = data.get('username', '')
    password = data.get('password', '')
    
    # Ищем оператора в базе данных
    operator = get_operator_db(username)
    if operator and operator['password'] == password:
        # Создаем токен сессии для оператора
        token = str(uuid.uuid4())
        sessions[token] = {
            'authenticated': True,
            'user_type': 'operator',
            'operator_id': operator['id'],
            'user': {
                'id': operator['id'],
                'username': operator['username'],
                'type': 'operator'
            },
            'created_at': datetime.now()
        }
        
        write_log(f"Успешный вход оператора {username} с IP: {request.remote_addr}")
        return jsonify({
            'success': True,
            'token': token,
            'operator': operator
        })
    else:
        write_log(f"Неудачная попытка входа оператора с IP: {request.remote_addr}, имя: {username}", 'WARNING')
        return jsonify({
            'success': False,
            'error': 'Неверные учетные данные оператора'
        }), 401

@app.route('/api/operator_emulators', methods=['GET'])
def api_get_operator_emulators():
    """Получение списка эмуляторов конкретного оператора"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not is_authenticated(token):
        return jsonify({'error': 'Не авторизован'}), 401
    
    session_data = sessions.get(token, {})
    if session_data.get('user_type') != 'operator':
        return jsonify({'error': 'Доступ только для операторов'}), 403
    
    operator_id = session_data.get('operator_id')
    operator_emulators = get_operator_emulators_db(operator_id)
    
    return jsonify({
        'success': True,
        'emulators': operator_emulators
    })

@app.route('/api/create_emulator', methods=['POST'])
def api_create_emulator():
    """Создание нового эмулятора для оператора"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not is_authenticated(token):
        return jsonify({'error': 'Не авторизован'}), 401
    
    session_data = sessions.get(token, {})
    if session_data.get('user_type') != 'operator':
        return jsonify({'error': 'Доступ только для операторов'}), 403
    
    data = request.get_json()
    emulator_data = {
        'name': data.get('name', 'Android Emulator'),
        'device': data.get('device', 'small_phone'),
        'api_level': data.get('api_level', 'android-36')
    }
    
    operator_id = session_data.get('operator_id')
    operator = get_operator_db(session_data['user']['username'])
    
    if not operator:
        return jsonify({'error': 'Оператор не найден'}), 404
    
    write_log(f"Создание эмулятора для оператора {operator['username']}: {emulator_data}")
    
    try:
        # Импортируем скрипты шагов
        from step_scripts import STEP_SCRIPTS
        
        # Контекст для подстановки в скрипты
        rdp_ip = get_setting('rdp_ip', DEFAULT_RDP_IP)
        user_context = {
            'username': operator['username'],
            'emulator_name': emulator_data['name'],
            'device_type': emulator_data['device'],
            'rdp_ip': rdp_ip,
            'operator_password': OPERATOR_PASSWORD
        }
        
        # Выполняем полную цепочку создания эмулятора
        steps = ['create_avd', 'create_batch', 'convert_to_exe', 'configure_remoteapp', 'create_rdp']
        results = {}
        
        for step in steps:
            write_log(f"Выполнение шага: {step}")
            result = execute_powershell_step(step, STEP_SCRIPTS[step], user_context)
            results[step] = result
            
            if not result['success']:
                write_log(f"Ошибка на шаге {step}: {result.get('output', 'Неизвестная ошибка')}", 'ERROR')
                return jsonify({
                    'success': False,
                    'error': f'Ошибка на шаге {step}',
                    'step_results': results
                }), 500
        
        # Парсим результаты для получения путей к файлам
        parsed_results = {}
        for step, result in results.items():
            parsed_results[step] = parse_step_output(result['output'], step)
        
        # Создаем запись эмулятора в базе данных
        rdp_file = parsed_results.get('create_rdp', {}).get('rdp_file', '')
        emulator_id = create_emulator_db(
            operator_id=operator_id,
            name=emulator_data['name'],
            device=emulator_data['device'],
            api_level=emulator_data['api_level'],
            rdp_file=rdp_file
        )
        
        new_emulator = {
            'id': emulator_id,
            'name': emulator_data['name'],
            'device': emulator_data['device'],
            'api_level': emulator_data['api_level'],
            'status': 'active',
            'created_at': datetime.now().isoformat(),
            'operator_id': operator_id,
            'operator_username': operator['username'],
            'avd_name': parsed_results.get('create_avd', {}).get('avd_name', ''),
            'batch_file': parsed_results.get('create_batch', {}).get('batch_file', ''),
            'exe_file': parsed_results.get('convert_to_exe', {}).get('exe_file', ''),
            'rdp_file': rdp_file,
            'app_name': parsed_results.get('configure_remoteapp', {}).get('app_name', '')
        }
        
        write_log(f"Эмулятор создан успешно: {emulator_id}")
        return jsonify({
            'success': True,
            'emulator': new_emulator,
            'step_results': results
        })
    
    except Exception as e:
        error_msg = f"Исключение при создании эмулятора: {str(e)}"
        write_log(error_msg, 'ERROR')
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500

@app.route('/api/delete_emulator/<emulator_id>', methods=['DELETE'])
def api_delete_emulator(emulator_id):
    """Удаление эмулятора с очисткой реестра RemoteApp"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not is_authenticated(token):
        return jsonify({'error': 'Не авторизован'}), 401
    
    session_data = sessions.get(token, {})
    if session_data.get('user_type') != 'operator':
        return jsonify({'error': 'Доступ только для операторов'}), 403
    
    operator_id = session_data.get('operator_id')
    
    # Получаем эмулятор из базы данных
    emulators = get_operator_emulators_db(operator_id)
    emulator = next((e for e in emulators if e['id'] == emulator_id), None)
    
    if not emulator:
        return jsonify({'error': 'Эмулятор не найден'}), 404
    
    write_log(f"Удаление эмулятора {emulator['name']} (ID: {emulator_id})")
    
    try:
        # Импортируем скрипт удаления
        from step_scripts import STEP_SCRIPTS
        
        # Создаем скрипт удаления эмулятора
        delete_script = f'''
# Удаление эмулятора {emulator['name']}
Write-Host "🗑️ Удаление эмулятора {emulator['name']}..." -ForegroundColor Yellow

# Получаем имя пользователя из имени эмулятора
$EmulatorName = "{emulator['name']}"
$Username = $EmulatorName -replace "_.*", ""

Write-Host "Пользователь: $Username" -ForegroundColor Cyan

try {{
    # 1. Удаляем RemoteApp из реестра
    $AppName = "$Username`AndroidEmulator"
    $RemoteAppPath = "HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Terminal Server\\TSAppAllowList\\Applications"
    $AppKeyPath = "$RemoteAppPath\\$AppName"
    
    if (Test-Path $AppKeyPath) {{
        Remove-Item -Path $AppKeyPath -Recurse -Force
        Write-Host "✅ RemoteApp удален из реестра: $AppName" -ForegroundColor Green
    }} else {{
        Write-Host "⚠️ RemoteApp не найден в реестре: $AppName" -ForegroundColor Yellow
    }}
    
    # 2. Удаляем файлы эмулятора
    $FilesToDelete = @(
        "C:\\Scripts\\$Username`_emulator.bat",
        "C:\\Scripts\\$Username`AndroidEmulator.exe", 
        "C:\\Scripts\\$Username`_emulator.rdp"
    )
    
    foreach ($File in $FilesToDelete) {{
        if (Test-Path $File) {{
            Remove-Item -Path $File -Force
            Write-Host "✅ Удален файл: $File" -ForegroundColor Green
        }} else {{
            Write-Host "⚠️ Файл не найден: $File" -ForegroundColor Yellow
        }}
    }}
    
    # 3. Удаляем AVD файлы
    $UserProfilePath = "C:\\Users\\$Username"
    $UserProfilePathHP = "C:\\Users\\$Username.HP"
    
    # Проверяем обе возможные директории
    $AvdDirs = @()
    if (Test-Path $UserProfilePathHP) {{
        $AvdDirs += "$UserProfilePathHP\\.android\\avd"
    }}
    if (Test-Path $UserProfilePath) {{
        $AvdDirs += "$UserProfilePath\\.android\\avd"
    }}
    
    foreach ($AvdDir in $AvdDirs) {{
        if (Test-Path $AvdDir) {{
            $AvdFiles = Get-ChildItem -Path $AvdDir -Filter "$Username`_*" -ErrorAction SilentlyContinue
            foreach ($AvdFile in $AvdFiles) {{
                Remove-Item -Path $AvdFile.FullName -Recurse -Force
                Write-Host "✅ Удален AVD файл: $($AvdFile.Name)" -ForegroundColor Green
            }}
        }}
    }}
    
    Write-Host "✅ SUCCESS: Эмулятор $EmulatorName полностью удален" -ForegroundColor Green
    
}} catch {{
    Write-Host "❌ ERROR: Ошибка удаления эмулятора: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}}
        '''
        
        # Выполняем скрипт удаления
        result = execute_powershell_step('delete_emulator', delete_script)
        
        if result['success']:
            # Удаляем эмулятор из базы данных
            delete_emulator_db(emulator_id)
            
            write_log(f"Эмулятор {emulator['name']} успешно удален")
            return jsonify({
                'success': True,
                'message': f'Эмулятор {emulator["name"]} успешно удален',
                'cleanup_output': result['output']
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Ошибка при удалении файлов эмулятора',
                'output': result['output']
            }), 500
    
    except Exception as e:
        error_msg = f"Исключение при удалении эмулятора: {str(e)}"
        write_log(error_msg, 'ERROR')
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500

def parse_step_output(output, step_name):
    """Парсинг вывода шага для извлечения полезной информации."""
    result = {}

    # Определяем успех по наличию SUCCESS: в выводе
    has_success = ('SUCCESS:' in output) or ('✅ SUCCESS:' in output)
    has_error = ('ERROR:' in output) or ('❌ ERROR:' in output)
    
    # Приоритет SUCCESS над ERROR (т.к. могут быть предупреждения)
    if has_success:
        result['success'] = True
    elif has_error:
        result['success'] = False
    else:
        # Если нет явных маркеров, считаем успехом
        result['success'] = True

    # Общий парсинг ошибок
    if has_error:
        error_match = re.search(r'(?:❌ )?ERROR: (.+)', output)
        if error_match:
            result['error'] = error_match.group(1).strip()

    # Специфичные поля
    if step_name == 'create_user':
        username_match = re.search(r'USERNAME: (.+)', output)
        password_match = re.search(r'PASSWORD: (.+)', output)
        if username_match:
            result['username'] = username_match.group(1).strip()
        if password_match:
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
        if app_match:
            result['app_name'] = app_match.group(1).strip()
        if path_match:
            result['app_path'] = path_match.group(1).strip()

    elif step_name == 'create_rdp':
        rdp_match = re.search(r'RDP_FILE: (.+)', output)
        if rdp_match:
            result['rdp_file'] = rdp_match.group(1).strip()

    elif step_name == 'test_microphone':
        mic_match = re.search(r'MICROPHONE_STATUS: (.+)', output)
        if mic_match:
            result['microphone_status'] = mic_match.group(1).strip()

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
    print("  === Администратор ===")
    print("  POST /api/login - Вход администратора")
    print("  POST /api/logout - Выход из системы")
    print("  GET  /api/operators - Список всех операторов")
    print("  POST /api/create_operator - Создание нового оператора")
    print("  === Операторы ===")
    print("  POST /api/operator_login - Вход оператора")
    print("  GET  /api/operator_emulators - Эмуляторы оператора")
    print("  POST /api/create_emulator - Создание эмулятора")
    print("  GET  /api/download_rdp/<id> - Скачивание RDP файла")
    print("  === Тестирование ===")
    print("  POST /api/test_step - Пошаговое тестирование")
    print("  GET  /api/steps_info - Информация о шагах")
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
