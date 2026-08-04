# PhotoBridge Developer & Packaging Guide

This guide is intended for developers, contributors, and power users who want to modify PhotoBridge, run API tests, configure manual firewall profiles, build standalone executables, or troubleshoot low-level backend configurations.

For high-level system details, see:
* 🗺️ **[System Architecture Diagram & Flow charts](file:///f:/CodeX/PyCharmProjects/my-photos-app/local-md-files/ARCHITECTURE.md)**
* 🤝 **[Contributing Guidelines & Coding Standards](file:///f:/CodeX/PyCharmProjects/my-photos-app/local-md-files/CONTRIBUTING.md)**

---

## 🛠️ Installation & Dependency Management

### 1. Development Mode (Running from Source)
Set up Python dependencies in your virtual environment:
```bash
pip install -r requirements.txt
```

#### Key Dependencies:
* **`fastapi`**: ASGI web framework serving our endpoints.
* **`uvicorn[standard]`**: High-performance ASGI server for hosting FastAPI.
* **`pillow`**: Image resizing and on-the-fly thumbnail caching.
* **`pillow-heif`**: Direct decoding of Apple's `.heic` and `.heif` files inside Python.
* **`pyinstaller`**: Packs the code and assets into a standalone distribution.

### 2. Standalone Windows Executable
No Python installation is required when running from the compiled executable.
- Run the packaged exe directly: `dist\PhotoBridge\PhotoBridge.exe`
- Or use the one-click installer: `dist\PhotoBridgeSetup.exe` (generated via Inno Setup).

---

## 📦 Building and Packaging Standalone Builds

### 1. PyInstaller Executable Compilation
The compilation is managed via the version-controlled PyInstaller spec file:
```bash
pyinstaller PhotoBridge.spec --noconfirm
```
This bundles the Tkinter desktop GUI, backend FastAPI server, and static frontend assets into a single distribution directory under `dist/PhotoBridge/`. 

*Note: In frozen mode, read-only assets are extracted to `sys._MEIPASS` at runtime, while user-writable assets (configurations, logs, and caches) are relocated to `%LOCALAPPDATA%\PhotoBridge` to bypass protected directory write restrictions.*

### 2. Creating the Inno Setup Windows Installer
The installer script packages the PyInstaller output directory into a single `PhotoBridgeSetup.exe` file.
Compile it locally using the Inno Setup Compiler (`iscc`):
```cmd
"C:\Program Files (x86)\Inno Setup 6\iscc.exe" installer\PhotoBridge.iss
```
This installer automatically configures the Windows Defender Firewall inbound rule for Port 8000 and registers an uninstaller under Windows Add/Remove Programs.

---

## 🔒 Windows Firewall & UAC Automation

### 1. Auto-Managed (Recommended)
Click **`1. Configure Firewall Rule`** inside the Control Center GUI. It uses the native Windows `ShellExecuteW` API with the `"runas"` verb to launch PowerShell elevated in the background. The UAC prompt appears cleanly without terminal console wraps.

### 2. Manual Command Line
If you prefer to configure the inbound rule manually:
* **PowerShell (Elevated Admin)**:
  ```powershell
  New-NetFirewallRule -DisplayName "PhotoBridge Port 8000" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow -Profile Private
  ```
* **Command Prompt (Elevated Admin CMD)**:
  ```cmd
  netsh advfirewall firewall add rule name="PhotoBridge Port 8000" dir=in action=allow protocol=TCP localport=8000 profile=private
  ```

---

## 🚀 Running via Command Line (Dev Mode)

### Standard Start:
```bash
python backend/run.py
```

### Specifying a Custom Port:
* **Windows Command Prompt (CMD)**:
  ```cmd
  set PORT=9000
  python backend/run.py
  ```
* **PowerShell**:
  ```powershell
  $env:PORT = 9000
  python backend/run.py
  ```

---

## 🧪 Testing the REST API

You can test all endpoints manually using `curl` or any API client. Note: If a PIN is configured, you must send the `X-PhotoBridge-PIN` header (or append `?pin=XXXX` query parameters for media routes).

```bash
# 1. Query Current Configuration
curl http://localhost:8000/api/config

# 2. Configure Directory Path (restricted to localhost)
curl -X POST http://localhost:8000/api/config \
  -H "Content-Type: application/json" \
  -d "{\"photos_dir\": \"C:\\\\Users\\\\YourName\\\\Pictures\", \"access_pin\": \"1234\"}"

# 3. Request Scanned Media JSON Index
curl -H "X-PhotoBridge-PIN: 1234" http://localhost:8000/api/media

# 4. Trigger Filesystem Rescan
curl -X POST -H "X-PhotoBridge-PIN: 1234" http://localhost:8000/api/rescan

# 5. Fetch Resized Image Thumbnail (300px width limit)
curl -H "X-PhotoBridge-PIN: 1234" http://localhost:8000/api/thumb/YOUR_MEDIA_ID?w=300 > thumb.jpg
```

---

## ⚙️ Low-Level Module Architecture

* **`desktop_gui/gui_app.py`**: Tkinter UI wrapper. Tracks liveness of the in-process server thread when frozen and routes subprocess streams (STDOUT/STDERR) directly to `app.log` in development mode.
* **`backend/run.py`**: Launches `UvicornServerThread` in-process. Passes `log_config=None` in frozen mode to prevent Uvicorn console logger initialization failures when standard IO streams are detached (`sys.stdout = None` in windowed mode).
* **`backend/app/paths.py`**: Central path resolution manager. Directs static assets to `sys._MEIPASS` when frozen and resolves user directories (configurations, logs, caches) to `%LOCALAPPDATA%\PhotoBridge`.
* **`backend/app/main.py`**: FastAPI controller. Implements standard synchronous `def` endpoints to offload slow disk operations (like recursive filesystem directory walking) to FastAPI's background thread pool, keeping the main asyncio event loop responsive.

---

## 🩺 Developer Troubleshooting

### `pillow-heif` Installation Failures
On some Windows configurations, compiling `pillow-heif` fails if the Microsoft C++ Build Tools are missing.
* **Solution**: Ensure your pip is upgraded (`python -m pip install --upgrade pip`) to fetch the precompiled binary wheels. Alternatively, download the pre-built `.whl` files from PyPI.

### Port Conflicts
If you receive a `[WinError 10048] Only one usage of each socket address is normally permitted` error:
* **Solution**: An orphaned `PhotoBridge.exe` background thread did not close cleanly or another application is listening on Port `8000`. Run the following command in cmd to locate the process and terminate it:
  ```cmd
  netstat -ano | findstr :8000
  taskkill /F /PID <PID_NUMBER>
  ```
