# Android Emulator RemoteApp Automation

Automated solution for creating and managing Android emulator RemoteApp sessions on Windows Server with microphone support.

## 🎯 Features

- **Automated User Creation**: Sequential user creation (User1, User2, User3...)
- **Android Virtual Device (AVD) Setup**: Optimized emulator configuration
- **RemoteApp Integration**: Seamless RDP access to Android emulators
- **Microphone Support**: Fixed 3-second cutoff issue in RemoteApp sessions
- **Web Interface**: Flask-based management interface
- **Step-by-Step Testing**: Individual component testing and validation

## 🛠️ System Requirements

- **OS**: Windows 10 LTSC (version 1809 or later) / Windows Server
- **Android SDK**: Installed at `C:\Program Files\Android`
- **Bat To Exe Converter**: For batch file conversion
- **RDP Wrapper**: For multi-session RDP support
- **Python 3.7+**: For Flask web interface
- **PowerShell 5.1+**: For automation scripts

## 📁 Project Structure

```
android-emulator-remoteapp/
├── scripts/
│   ├── AndroidEmulatorSetup.ps1      # Main automation script
│   ├── ConfigureGroupPolicy.ps1      # Microphone fix configuration
│   └── Install-EmulatorSystem.ps1    # System installation script
├── web/
│   ├── app.py                        # Flask web application
│   ├── step_scripts.py               # Step-wise testing scripts
│   ├── simple_interface.html         # Web interface
│   └── requirements.txt              # Python dependencies
├── docs/
│   ├── SETUP.md                      # Setup instructions (Russian)
│   ├── TESTING.md                    # Testing guide (Russian)
│   └── TROUBLESHOOTING.md            # Troubleshooting guide
└── README.md                         # This file
```

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/YOUR_USERNAME/android-emulator-remoteapp.git
cd android-emulator-remoteapp
```

### 2. Install Dependencies
```bash
# Install Python dependencies
pip install -r web/requirements.txt

# Install Android SDK (if not already installed)
# Download from: https://developer.android.com/studio
```

### 3. Run System Installation
```powershell
# Run as Administrator
.\scripts\Install-EmulatorSystem.ps1
```

### 4. Start Web Interface
```bash
cd web
python app.py
```

### 5. Access Web Interface
Open http://localhost:5000 in your browser

**Default credentials:**
- Username: `admin`
- Password: `admin123`

## 📋 Step-by-Step Testing

The web interface provides 7 testing steps:

1. **Create Windows User** - Creates User1, User2, etc. with RDP access
2. **Create Android AVD** - Sets up phone1, phone2, etc. virtual devices
3. **Create Batch File** - Generates emulator launch scripts
4. **Convert to EXE** - Converts batch files to executables
5. **Configure RemoteApp** - Sets up Windows Registry for RemoteApp
6. **Create RDP File** - Generates connection files for clients
7. **Test Microphone** - Validates audio input functionality

## 🎤 Microphone Fix

The solution addresses the common 3-second microphone cutoff issue in RemoteApp sessions through:

- **AVD Configuration**: `hw.audioInput=yes`, `hw.audioOutput=yes`
- **Registry Tweaks**: `MaxConnectionTime=0`, `fDisableAudioCapture=0`
- **Emulator Flags**: `-audio-in on -audio-out on`
- **Group Policy**: Disabled session timeouts

## 🔧 Configuration

### Main Script Parameters
- **User naming**: User1, User2, User3... (sequential)
- **Phone naming**: phone1, phone2, phone3... (matching user numbers)
- **Password policy**: 16-character GUID, no expiration, user cannot change
- **Groups**: Automatically added to Users and Remote Desktop Users

### Security Features
- Admin authentication for web interface
- Unique user/password generation
- File permission restrictions with `icacls`
- Comprehensive logging for audit trail

## 📝 Logging

All operations are logged to:
- `C:\Scripts\log.txt` - Main automation log
- `C:\Scripts\web_log.txt` - Web interface log

## 🐛 Troubleshooting

Common issues and solutions:

1. **User creation fails**: Check if running as Administrator
2. **Groups not found**: System uses SID-based group detection
3. **AVD creation fails**: Verify Android SDK installation path
4. **Microphone not working**: Run `ConfigureGroupPolicy.ps1`
5. **RemoteApp not launching**: Check Registry settings and file permissions

See [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for detailed solutions.

## 📚 Documentation

- [SETUP.md](docs/SETUP.md) - Detailed setup instructions (Russian)
- [TESTING.md](docs/TESTING.md) - Testing procedures (Russian)
- [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) - Problem resolution

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Android SDK team for emulator tools
- Microsoft for RemoteApp technology
- Community contributors for troubleshooting solutions

## 📞 Support

For support and questions:
- Create an issue in this repository
- Check the troubleshooting guide
- Review the documentation

---

**Note**: This solution is designed for Windows Server environments and requires administrative privileges for proper operation.
