# PhotoBridge — Local Network Photo Browser for iPhone

PhotoBridge is a local web app that runs on a Windows laptop and lets an iPhone on the same WiFi network browse the laptop's photo/video folder in an interface styled like Apple Photos. It's a Progressive Web App (PWA) with no login required — just type your folder path on the setup screen.

## Documentation

- 🗺️ **[System Architecture](file:///f:/CodeX/PyCharmProjects/my-photos-app/ARCHITECTURE.md)**: Details modules, data flow, and security design.
- 🤝 **[Contributing Guidelines](file:///f:/CodeX/PyCharmProjects/my-photos-app/CONTRIBUTING.md)**: Describes codebase structure, coding guidelines, and testing.

## Features

- **🎛️ Windows Control Center** — Desktop GUI dashboard to setup firewall rules, start/stop the server, and monitor connection URLs natively.
- **📱 No App Installation** — Works as a Progressive Web App (PWA) added to home screen via Safari
- **📸 Grid View** — Date-grouped grid just like Apple Photos, with lazy loading
- **🎥 Video Support** — Full-screen viewer with scrubbing and seeking support
- **🔍 Search & Albums** — Filter by filename and browse by album  
- **❤️ Favorites** — Mark favorites (stored in browser localStorage)
- **💾 Save to Photos** — Press a button to save directly into the phone's native Photos app
- **🔄 No Cloud** — Everything stays on your local network
- **🖼️ HEIC Support** — Native iPhone photo format handled via `pillow-heif`
- **📴 No Setup Needed** — Just run the server and enter your folder path from the phone
- **📴 Optional PIN for security** — Configure a PIN to restrict access to your photos from other devices on the same WiFi

## Requirements

- **Python 3.11 or later** (tested on Python 3.14)
- **Windows 10 or later** laptop on the same WiFi as your iPhone
- **iPhone** with Safari (iOS 12+)

## Installation

1. **Clone or download** this project folder.

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

   On Windows, this installs:
   - `fastapi` — web framework
   - `uvicorn[standard]` — ASGI server
   - `pillow` — image resizing & thumbnail generation
   - `pillow-heif` — HEIC/HEIF image format support
   - `python-multipart` — file upload handling

## Running the App

### Option 1: Double-Click Launcher (Recommended for Non-Technical Users)

Simply **double-click the `run_app.bat` file** in the project root folder.
This batch script will automatically:
1. Verify Python is installed.
2. Create an isolated Python Virtual Environment (`.venv`) so it doesn't clutter your system.
3. Automatically install all required dependencies from `requirements.txt`.
4. Start the PhotoBridge server.
5. Provide a simple prompt: **Press [ENTER] in the window to stop the server cleanly.**

### Option 2: Command Line Quick Start

If you prefer using the command line:
```bash
python run.py
```

The server will start and print:

```
======================================================================
PhotoBridge running!
Local:  http://localhost:8000
Phone:  http://192.168.1.8:8000   (same WiFi)
Photos folder: not yet configured — open the app and complete setup
======================================================================
```

### Option 2: Custom Port

Set the `PORT` environment variable:

```bash
set PORT=9000
python run.py
```

Or on PowerShell:
```powershell
$env:PORT = 9000
python run.py
```

## First-Time Setup (from Your iPhone)

1. **Find your laptop's LAN IP**:
   - Run `ipconfig` on Windows
   - Look for the "IPv4 Address" under your WiFi adapter (usually looks like `192.168.x.x`)

2. **Configure Windows Firewall (Required for phone access)**:
   By default, Windows blocks incoming connections from other devices on the network. Before trying to connect:
   - **Switch Network Profile to Private**:
     1. Open **Settings** on your laptop (`Win + I`).
     2. Go to **Network & Internet** > **Wi-Fi**.
     3. Click on your active Wi-Fi connection.
     4. Change the Network profile type to **Private**.
   - **Allow Port 8000 through Firewall**:
     1. Right-click the Start menu and select **Terminal (Admin)** or **PowerShell (Admin)**.
     2. Run the following command:
        ```powershell
        New-NetFirewallRule -DisplayName "PhotoBridge Port 8000" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
        ```

3. **Open Safari on your iPhone** and go to:
   ```
   http://<your-laptop-ip>:8000
   ```
   (e.g., `http://192.168.1.8:8000`)

4. **You'll see the setup screen**:
   - Enter the full path to your photos folder on the laptop
   - Example: `C:\Users\YourName\Pictures` or `D:\Photos\2024`
   - The server validates the path and starts scanning

5. **Your photos appear** in a grid, grouped by date (newest first)

6. **Add to Home Screen** (optional but recommended):
   - Tap the Share button (↗️) in Safari's menu bar
   - Tap "Add to Home Screen"
   - Name it "PhotoBridge" and tap Add
   - PhotoBridge now appears as a full-screen app icon on your home screen

## Changing the Photos Folder

Click the ⚙️ gear icon in the top-right corner at any time to change the folder. The app will rescan and update.

## Features in Detail

### Grid & Navigation

- **All Photos tab** — all media sorted by date
- **Albums tab** — browse subfolders as albums
- **Favorites tab** — only media you've marked with a heart
- **Search** — type to filter by filename (case-insensitive)

### Full-Screen Viewer

- **Swipe left/right** — previous/next photo
- **Arrow keys** (desktop) — prev/next
- **Heart icon** — toggle favorite
- **⬇️ Download/Save** — save to your phone's Photos app
- **Close (✕)** — exit viewer

### Save to Photos

Tap the download button to save a photo or video:
- **iPhone** — opens the native share sheet; tap "Save Image" or "Save Video"
- **Other devices** — downloads the file normally

### Rescan

**Pull-to-refresh** the grid when you've added new files to your laptop's photos folder. The server doesn't need to be restarted.

## Architecture

### Backend

- **`app/main.py`** — FastAPI routes and config endpoints
- **`app/config.py`** — reads/writes `config.json` with the photos folder path
- **`app/scanner.py`** — filesystem walk, EXIF date extraction, in-memory media index
- **`app/media.py`** — thumbnail generation (Pillow), file streaming with HTTP range support
- **`run.py`** — entry point; starts uvicorn server

### Frontend

- **`static/index.html`** — HTML structure
- **`static/app.js`** — vanilla JavaScript (no framework)
- **`static/style.css`** — dark theme CSS (iOS Photos aesthetic)
- **`static/manifest.json`** — PWA manifest (display: standalone, dark theme)
- **`static/sw.js`** — service worker (caches static files, never caches API)
- **`static/icons/`** — app icons for home screen

### Configuration

- **`config.json`** (created on first run)
  ```json
  {
    "photos_dir": "C:\\Users\\You\\Pictures",
    "port": 8000
  }
  ```
  - `photos_dir` — only set through the app setup screen, never hardcoded
  - `port` — can be overridden by the `PORT` environment variable
  - Add `config.json` to `.gitignore` since it's machine-specific

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/api/config` | Get current config (photos_dir, port, configured) |
| `POST` | `/api/config` | Set photos directory (validates path exists) |
| `POST` | `/api/select-folder` | Open native folder picker on server (returns selected path) |
| `GET` | `/api/media` | Get list of all media objects |
| `POST` | `/api/rescan` | Rescan photos folder and rebuild index |
| `GET` | `/api/thumb/{id}?w=300` | Get JPEG thumbnail (width in px, default 300) |
| `GET` | `/api/full/{id}` | Stream original file (supports HTTP Range requests for video seeking) |
| `GET` | `/api/download/{id}` | Download with attachment disposition (for Save to Photos) |

All endpoints on paths like `/api/thumb/...` use URL-safe base64 IDs derived from relative paths on disk.

## File Formats Supported

### Images
- `.jpg`, `.jpeg` (JPEG)
- `.png` (PNG)
- `.heic`, `.heif` (Apple formats, requires `pillow-heif`)
- `.gif` (GIF)
- `.webp` (WebP)

### Videos
- `.mp4` (MPEG-4)
- `.mov` (QuickTime)
- `.m4v` (iTunes video)

Other files are skipped.

## Metadata & Dates

- **Images** — tries to read EXIF `DateTimeOriginal`, falls back to `DateTime`, then to file modified time
- **Videos** — uses file modified time (no EXIF parsing)
- All dates stored as ISO 8601 strings

## Troubleshooting

### Server won't start

- Make sure Python 3.11+ is installed: `python --version`
- Dependencies installed? Run: `pip install -r requirements.txt`
- Port 8000 already in use? Set `PORT=9000 && python run.py`

### Photos don't appear after setup

- Double-check the folder path is correct (must be absolute path like `C:\Users\You\Pictures`)
- Make sure the folder actually exists on your laptop
- Try the gear icon → change the folder again or pull-to-refresh in the app

### HEIC thumbnails fail

- `pillow-heif` installation can fail if build tools aren't available
- The app still works! Mobile Safari can display HEIC natively — only thumbnail generation is affected
- To fix: install build tools or use pre-built wheels

### iPhone can't reach the laptop

- **Are you on the same WiFi?** Both the phone and laptop must be connected to the exact same Wi-Fi network.
- **Did you type the IP correctly?** Run `ipconfig` on the laptop to find the correct active IPv4 address (usually `192.168.1.x`).
- **Is your network profile set to Public?** Windows Firewall blocks inbound traffic on Public networks. Switch it to **Private**:
  1. Open Windows **Settings** (`Win + I`) -> **Network & Internet** -> **Wi-Fi**.
  2. Click your Wi-Fi name.
  3. Select **Private** under Network Profile Type.
- **Is Windows Firewall blocking Port 8000?** Add an inbound firewall rule by opening **PowerShell (as Administrator)** and running:
  ```powershell
  New-NetFirewallRule -DisplayName "PhotoBridge Port 8000" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
  ```

### Folder changes don't show up

- Use pull-to-refresh gesture or tap the gear icon and reselect the folder
- Server doesn't need to restart; rescan is on-demand

## Running as a Background Service (Windows)

To keep PhotoBridge running even when you close the terminal:

### Using Task Scheduler

1. Open Task Scheduler
2. Create Basic Task → name it "PhotoBridge"
3. Trigger: "At startup"
4. Action: Start program `python.exe` with arguments:
   ```
   C:\path\to\PhotoBridge\run.py
   ```
   (use absolute path)
5. Check "Run whether user is logged in or not"
6. Finish

### Using NSSM (Non-Sucking Service Manager)

```bash
nssm install PhotoBridge "C:\Python\python.exe" "C:\path\to\PhotoBridge\run.py"
nssm start PhotoBridge
```

See [NSSM documentation](https://nssm.cc/) for details.

## Known Limitations

- **No cloud sync** — everything local only
- **No user login** — assumes trusted local network
- **Mobile Safari only** — tested on iOS 14+; Chrome/other browsers on Android not tested
- **HEIC thumbnails** — depend on `pillow-heif` building correctly; app works fine without it (uses native format)
- **Subfolders only** — only immediate subfolders become albums; deeply nested folders are not treated as albums
- **No metadata editing** — viewing and favorite-marking only

## Example Folder Structure

```
C:\Users\You\Pictures/
├── 2024/
│   ├── vacation-001.jpg
│   ├── vacation-002.mov
├── 2023/
│   ├── family-photo.heic
├── screenshot.png
└── meme.gif
```

When you point PhotoBridge to `C:\Users\You\Pictures`:
- Files directly in that folder belong to album **"All Photos"**
- Each subfolder (2024, 2023) becomes an album
- You can filter to see only one album's photos

## Security & Privacy

PhotoBridge is designed to run locally on your network. To protect your private files and settings, the following security measures are implemented:

* 🔒 **Localhost Settings Protection**: Configuration adjustments (like changing the photos folder path or opening the native Windows folder selector dialog) can **only** be performed directly from the host laptop (`localhost`). Remote devices on your WiFi trying to make configuration changes will receive a `403 Forbidden` error.
* 🔑 **Optional Access PIN**: You can set a connection **Access PIN** during initial setup or inside Settings. 
  * If a PIN is configured, any device accessing the app from your Wi-Fi network must enter this PIN on a secure lock screen before they can see or download any photos.
  * API requests are secured via an `X-PhotoBridge-PIN` header, while inline elements (`<img>` and `<video>`) append it as a query parameter (`?pin=XXXX`).
* 🛡️ **Directory Traversal Protection**: All media files are accessed via secure, URL-safe base64 IDs mapped in memory. Users cannot request arbitrary files on your system by trying to load relative paths (e.g. `..\..\Windows`).

## Development

### Project Structure

```
photobridge/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app
│   ├── config.py        # config.json I/O
│   ├── scanner.py       # filesystem walk + EXIF
│   └── media.py         # thumbnails + streaming
├── static/
│   ├── index.html
│   ├── app.js
│   ├── style.css
│   ├── manifest.json
│   ├── sw.js
│   └── icons/
│       ├── icon-180.png
│       └── icon-512.png
├── .github/
│   └── CODEOWNERS       # github repository ownership config
├── run.py               # entry point
├── run_app.bat          # windows server launcher
├── gui_app.py           # desktop control center GUI (Tkinter)
├── run_control_center.bat # double-clickable launcher for the GUI Control Center
├── setup.bat            # admin setup script (adds private network firewall rule)
├── uninstall.bat        # admin cleanup script (removes firewall rule)
├── requirements.txt
├── config.json          # generated on first run
├── README.md
├── CONTRIBUTING.md
└── ARCHITECTURE.md
```

### Testing the API

```bash
# Get config
curl http://localhost:8000/api/config

# Set photos folder
curl -X POST http://localhost:8000/api/config \
  -H "Content-Type: application/json" \
  -d "{\"photos_dir\": \"C:\\\\Users\\\\You\\\\Pictures\"}"

# Get media list
curl http://localhost:8000/api/media

# Rescan
curl -X POST http://localhost:8000/api/rescan

# Get thumbnail
curl http://localhost:8000/api/thumb/YOUR_MEDIA_ID?w=300 > thumb.jpg

# Stream full video with range request
curl -r 0-999 http://localhost:8000/api/full/YOUR_VIDEO_ID > partial.mp4
```

## License

This project is provided as-is for personal use on trusted local networks. No warranty is provided.

---

**Enjoy browsing your photos from your iPhone! 📱📸**

