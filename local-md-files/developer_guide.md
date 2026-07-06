# PhotoBridge Developer Guide

This guide is intended for developers, contributors, and power users who want to modify PhotoBridge, run API tests, configure manual firewall profiles, or troubleshoot low-level backend configurations.

For high-level system details, see:
* 🗺️ **[System Architecture Diagram & Flow charts](file:///f:/CodeX/PyCharmProjects/my-photos-app/local-md-files/ARCHITECTURE.md)**
* 🤝 **[Contributing Guidelines & Coding Standards](file:///f:/CodeX/PyCharmProjects/my-photos-app/local-md-files/CONTRIBUTING.md)**

---

## 🛠️ Manual Installation & Packages

If you do not want to use the automated `run_control_center.bat` or `run_app.bat` launchers, you can set up Python dependencies manually:

```bash
pip install -r requirements.txt
```

### Key Dependencies Explained:
* **`fastapi`**: ASGI web framework serving our endpoints.
* **`uvicorn[standard]`**: High-performance ASGI server for hosting FastAPI.
* **`pillow`**: Image resizing and on-the-fly thumbnail caching.
* **`pillow-heif`**: Direct decoding of Apple's `.heic` and `.heif` files inside Python.
* **`python-multipart`**: Form payload handling (required by FastAPI endpoints).

---

## 🔒 Manual Firewall Rules & UAC Setup

If you prefer to configure the inbound rule manually instead of clicking **1. Configure Firewall** inside the Control Center GUI, you can run these commands:

### 1. Allow Port 8000 via PowerShell (Admin)
Open a UAC-elevated PowerShell command prompt and run:
```powershell
New-NetFirewallRule -DisplayName "PhotoBridge Port 8000" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow -Profile Private
```

### 2. Allow Port 8000 via netsh (Admin CMD)
Alternatively, from an elevated Command Prompt window:
```cmd
netsh advfirewall firewall add rule name="PhotoBridge Port 8000" dir=in action=allow protocol=TCP localport=8000 profile=private
```

---

## 🚀 Running via Command Line

### Standard Start:
```bash
python run.py
```

### Specifying a Custom Port:
To override the default port `8000`:
* **Windows Command Prompt (CMD)**:
  ```cmd
  set PORT=9000
  python run.py
  ```
* **PowerShell**:
  ```powershell
  $env:PORT = 9000
  python run.py
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

# 6. Stream Original Video Binary (with HTTP Range Seeking)
curl -r 0-999 -H "X-PhotoBridge-PIN: 1234" http://localhost:8000/api/full/YOUR_VIDEO_ID > partial.mp4
```

---

## ⚙️ Low-Level Module Architecture

* **`gui_app.py`**: Tkinter UI wrapper. Monitors processes, wraps PowerShell calls with hidden window flags (`Start-Process -WindowStyle Hidden`), and handles window state events (`<Configure>`) to size text layout containers.
* **`app/scanner.py`**: Handles directory walks. It parses EXIF tags using Pillow's `_getexif()` to query timestamp fields `36867` (DateTimeOriginal) and `306` (DateTime). If those fields are missing, it falls back to filesystem `mtime` records.
* **`app/media.py`**: Stream responses. Sets up chunked generators for serving standard media files and supports custom header range streaming (returning standard `206 Partial Content` with `Content-Range` bounds).

---

## 🩺 Developer Troubleshooting

### `pillow-heif` Installation Failures
On some Windows configurations, compiling `pillow-heif` fails if the Microsoft C++ Build Tools are missing.
* **Solution**: Ensure your pip is upgraded (`python -m pip install --upgrade pip`) to fetch the precompiled binary wheels. Alternatively, download the pre-built `.whl` files from PyPI.
* **PWA Fallback**: If HEIC thumbnail generation fails, Mobile Safari on iOS can still render HEIC files natively inside the fullscreen slider. Only grid thumbnails will display placeholder card graphics.

### Port Conflicts
If you receive a `[WinError 10048] Only one usage of each socket address is normally permitted` error:
* **Solution**: A previous uvicorn thread did not close cleanly or another application is listening on Port `8000`. Run the following command in cmd to locate the process and terminate it:
  ```cmd
  netstat -ano | findstr :8000
  taskkill /F /PID <PID_NUMBER>
  ```
