<?php
/**
 * Android Emulator RemoteApp Web Interface
 * Author: Automated Setup System
 * Date: 2025-09-23
 * Purpose: Web interface for creating Android emulator RemoteApp sessions
 */

session_start();

// Configuration
define('ADMIN_USERNAME', 'admin');
define('ADMIN_PASSWORD_HASH', password_hash('admin123', PASSWORD_DEFAULT)); // Change this!
define('POWERSHELL_SCRIPT_PATH', 'C:\emulator\AndroidEmulatorSetup.ps1');
define('LOG_FILE', 'C:\Scripts\web_log.txt');
define('DOWNLOAD_DIR', 'C:\Scripts\downloads');

// Ensure download directory exists
if (!is_dir(DOWNLOAD_DIR)) {
    mkdir(DOWNLOAD_DIR, 0755, true);
}

// Logging function
function writeLog($message, $level = 'INFO') {
    $timestamp = date('Y-m-d H:i:s');
    $logEntry = "[$timestamp] [$level] $message" . PHP_EOL;
    file_put_contents(LOG_FILE, $logEntry, FILE_APPEND | LOCK_EX);
}

// Authentication check
function isAuthenticated() {
    return isset($_SESSION['authenticated']) && $_SESSION['authenticated'] === true;
}

// Handle login
if ($_POST['action'] === 'login') {
    $username = $_POST['username'] ?? '';
    $password = $_POST['password'] ?? '';
    
    if ($username === ADMIN_USERNAME && password_verify($password, ADMIN_PASSWORD_HASH)) {
        $_SESSION['authenticated'] = true;
        writeLog("Admin login successful from IP: " . $_SERVER['REMOTE_ADDR']);
        header('Location: ' . $_SERVER['PHP_SELF']);
        exit;
    } else {
        $loginError = 'Invalid credentials';
        writeLog("Failed login attempt from IP: " . $_SERVER['REMOTE_ADDR'] . " with username: $username", 'WARNING');
    }
}

// Handle logout
if ($_GET['action'] === 'logout') {
    session_destroy();
    header('Location: ' . $_SERVER['PHP_SELF']);
    exit;
}

// Handle emulator setup
if ($_POST['action'] === 'setup_emulator' && isAuthenticated()) {
    writeLog("Starting emulator setup request from admin");
    
    try {
        // Execute PowerShell script
        $command = 'powershell.exe -ExecutionPolicy Bypass -File "' . POWERSHELL_SCRIPT_PATH . '" 2>&1';
        writeLog("Executing command: $command");
        
        $output = shell_exec($command);
        writeLog("PowerShell output: " . $output);
        
        // Parse output to extract user information
        $setupResult = parseSetupOutput($output);
        
        if ($setupResult['success']) {
            $setupSuccess = true;
            $userInfo = $setupResult;
            writeLog("Emulator setup completed successfully for user: " . $setupResult['username']);
        } else {
            $setupError = $setupResult['error'] ?? 'Unknown error occurred';
            writeLog("Emulator setup failed: $setupError", 'ERROR');
        }
    } catch (Exception $e) {
        $setupError = 'Failed to execute setup: ' . $e->getMessage();
        writeLog("Exception during setup: " . $e->getMessage(), 'ERROR');
    }
}

// Parse PowerShell output
function parseSetupOutput($output) {
    $result = ['success' => false];
    
    if (strpos($output, 'Setup completed successfully!') !== false) {
        $result['success'] = true;
        
        // Extract username
        if (preg_match('/Username: ([^\r\n]+)/', $output, $matches)) {
            $result['username'] = trim($matches[1]);
        }
        
        // Extract password
        if (preg_match('/Password: ([^\r\n]+)/', $output, $matches)) {
            $result['password'] = trim($matches[1]);
        }
        
        // Extract RDP file path
        if (preg_match('/RDP File: ([^\r\n]+)/', $output, $matches)) {
            $result['rdp_file'] = trim($matches[1]);
        }
    } else {
        // Extract error message
        if (preg_match('/Setup failed: ([^\r\n]+)/', $output, $matches)) {
            $result['error'] = trim($matches[1]);
        } else {
            $result['error'] = 'Unknown error - check logs for details';
        }
    }
    
    return $result;
}

// Handle RDP file download
if ($_GET['action'] === 'download_rdp' && isAuthenticated() && isset($_GET['file'])) {
    $rdpFile = $_GET['file'];
    
    if (file_exists($rdpFile) && strpos($rdpFile, 'C:\Scripts') === 0) {
        $filename = basename($rdpFile);
        
        header('Content-Type: application/rdp');
        header('Content-Disposition: attachment; filename="' . $filename . '"');
        header('Content-Length: ' . filesize($rdpFile));
        
        readfile($rdpFile);
        writeLog("RDP file downloaded: $filename");
        exit;
    } else {
        writeLog("Invalid RDP file download request: $rdpFile", 'WARNING');
        $downloadError = 'File not found or access denied';
    }
}

?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Android Emulator RemoteApp Manager</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .container {
            background: white;
            border-radius: 10px;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
            padding: 2rem;
            width: 100%;
            max-width: 500px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 2rem;
        }
        
        .header h1 {
            color: #333;
            margin-bottom: 0.5rem;
        }
        
        .header p {
            color: #666;
            font-size: 0.9rem;
        }
        
        .form-group {
            margin-bottom: 1rem;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            color: #333;
            font-weight: 500;
        }
        
        .form-group input {
            width: 100%;
            padding: 0.75rem;
            border: 2px solid #e1e5e9;
            border-radius: 5px;
            font-size: 1rem;
            transition: border-color 0.3s;
        }
        
        .form-group input:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .btn {
            width: 100%;
            padding: 0.75rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
        }
        
        .btn:hover {
            transform: translateY(-2px);
        }
        
        .btn:active {
            transform: translateY(0);
        }
        
        .btn-secondary {
            background: #6c757d;
            margin-top: 1rem;
        }
        
        .btn-success {
            background: #28a745;
            margin-top: 1rem;
        }
        
        .alert {
            padding: 1rem;
            border-radius: 5px;
            margin-bottom: 1rem;
        }
        
        .alert-danger {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .alert-success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .user-info {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 5px;
            margin: 1rem 0;
        }
        
        .user-info h3 {
            color: #333;
            margin-bottom: 1rem;
        }
        
        .user-info p {
            margin-bottom: 0.5rem;
            color: #555;
        }
        
        .user-info strong {
            color: #333;
        }
        
        .logout-link {
            text-align: center;
            margin-top: 1rem;
        }
        
        .logout-link a {
            color: #667eea;
            text-decoration: none;
        }
        
        .logout-link a:hover {
            text-decoration: underline;
        }
        
        .loading {
            display: none;
            text-align: center;
            margin: 1rem 0;
        }
        
        .loading.show {
            display: block;
        }
        
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 1rem;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Android Emulator Manager</h1>
            <p>RemoteApp Automation System</p>
        </div>

        <?php if (!isAuthenticated()): ?>
            <!-- Login Form -->
            <?php if (isset($loginError)): ?>
                <div class="alert alert-danger">
                    <?php echo htmlspecialchars($loginError); ?>
                </div>
            <?php endif; ?>
            
            <form method="post">
                <input type="hidden" name="action" value="login">
                
                <div class="form-group">
                    <label for="username">Username</label>
                    <input type="text" id="username" name="username" required>
                </div>
                
                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" name="password" required>
                </div>
                
                <button type="submit" class="btn">Login</button>
            </form>
            
        <?php else: ?>
            <!-- Admin Dashboard -->
            <div class="logout-link">
                <a href="?action=logout">Logout</a>
            </div>
            
            <?php if (isset($setupError)): ?>
                <div class="alert alert-danger">
                    <strong>Setup Failed:</strong> <?php echo htmlspecialchars($setupError); ?>
                </div>
            <?php endif; ?>
            
            <?php if (isset($downloadError)): ?>
                <div class="alert alert-danger">
                    <strong>Download Error:</strong> <?php echo htmlspecialchars($downloadError); ?>
                </div>
            <?php endif; ?>
            
            <?php if (isset($setupSuccess) && $setupSuccess): ?>
                <div class="alert alert-success">
                    <strong>Success!</strong> Android emulator RemoteApp has been configured successfully.
                </div>
                
                <div class="user-info">
                    <h3>📋 Connection Details</h3>
                    <p><strong>Username:</strong> <?php echo htmlspecialchars($userInfo['username']); ?></p>
                    <p><strong>Password:</strong> <?php echo htmlspecialchars($userInfo['password']); ?></p>
                    <?php if (isset($userInfo['rdp_file'])): ?>
                        <p><strong>RDP File:</strong> Ready for download</p>
                        <a href="?action=download_rdp&file=<?php echo urlencode($userInfo['rdp_file']); ?>" class="btn btn-success">
                            📥 Download RDP File
                        </a>
                    <?php endif; ?>
                </div>
            <?php endif; ?>
            
            <form method="post" id="setupForm">
                <input type="hidden" name="action" value="setup_emulator">
                
                <div class="form-group">
                    <label>🚀 Create New Android Emulator Session</label>
                    <p style="color: #666; font-size: 0.9rem; margin-top: 0.5rem;">
                        This will create a new Windows user, configure an Android Virtual Device, 
                        and generate a RemoteApp connection with microphone support.
                    </p>
                </div>
                
                <div class="loading" id="loading">
                    <div class="spinner"></div>
                    <p>Setting up Android emulator... This may take several minutes.</p>
                </div>
                
                <button type="submit" class="btn" id="setupBtn">
                    🎯 Create Emulator Session
                </button>
            </form>
            
        <?php endif; ?>
    </div>

    <script>
        document.getElementById('setupForm')?.addEventListener('submit', function() {
            document.getElementById('loading').classList.add('show');
            document.getElementById('setupBtn').disabled = true;
            document.getElementById('setupBtn').textContent = 'Setting up...';
        });
    </script>
</body>
</html>
