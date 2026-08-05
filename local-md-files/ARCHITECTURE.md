# PhotoBridge Architecture

PhotoBridge is a high-performance, lightweight, offline-first Progressive Web App (PWA) designed to stream and browse photos and videos directly from a Windows laptop (host/server) to an iPhone (client) over a local network (Wi-Fi).

This document details the system design, data flows, security mechanisms, and module structure of the application.

---

## 🗺️ High-Level System Architecture

### 1. Standalone Application Boundary
When packaged as a standalone application, all runtime components (Tkinter GUI, FastAPI, Uvicorn, Python runtime, and static web assets) are compiled into a single executable `PhotoBridge.exe`. Read-only files are extracted to `sys._MEIPASS` (temp path) upon startup, while user-writable files (configurations, logs, and caches) are stored in the user's local application data folder `%LOCALAPPDATA%\PhotoBridge`.

```mermaid
graph TD
    subgraph Client [iPhone / Client Device]
        PWA[PWA Home Screen Shell] <--> JS[Vanilla JS State Engine app.js]
        JS <--> CSS[Glassmorphic Styling style.css]
        JS <--> SW[Service Worker sw.js]
    end

    subgraph Host [Windows Laptop / PhotoBridge.exe]
        subgraph GUI [Tkinter GUI / gui_app.py]
            LogsView[Log Viewer Toplevel Window]
        end
        subgraph ServerThread [In-Process Server / UvicornServerThread]
            API[FastAPI Web Server main.py] <--> Sec[Security Middleware Host / PIN check]
            API <--> Config[Config Manager config.py]
            API <--> Media[Media Engine media.py]
            API <--> Scanner[Directory Scanner scanner.py]
        end
        
        AppData[%LOCALAPPDATA%/PhotoBridge]
        AppData <--> ConfigFile[(config.json)]
        AppData <--> Cache[(.thumbcache/)]
        AppData <--> AppLog[(app.log)]
        
        Media <--> Filesystem[(Laptop Photos Directory)]
    end

    JS -- HTTP API Request with PIN Header --> Sec
    JS -- Static Media Request with PIN Query --> Sec
    Sec -- Access Allowed --> API
    GUI -- Spawns / Checks Liveness --> ServerThread
```

---

## 📦 Module Breakdown

### 1. Backend Modules (Python / FastAPI)

* **`run.py`**: Spawns the Uvicorn web server. When running as a frozen executable, Uvicorn runs in-process as a background daemon thread (`UvicornServerThread`) with `log_config=None` to prevent crash-on-startup issues caused by console-less environments. Also queries the system's hostname to print a persistent host-based `.local` connection address.
* **`app/paths.py`**: Central path manager. Routes asset searches to `sys._MEIPASS` when frozen and relocates configurations, logs, and caches to `%LOCALAPPDATA%\PhotoBridge` to conform to Windows filesystem write privileges.
* **`app/main.py`**: FastAPI controller. Implements synchronous `def` endpoints to offload slow disk operations (such as recursive directory walking) to FastAPI's background thread pool, preventing main asyncio event loop blockages.
* **`app/logger.py`**: Process-safe, file-backed logger writing to `%LOCALAPPDATA%\PhotoBridge\app.log`. Logs API endpoints, timings, client IPs, and critical exceptions.
* **`app/config.py`**: Handles system configurations, directory locations, and access PIN values stored in `config.json`.
* **`app/scanner.py`**: Crawls local photos directory. Recursively pairs Live Photo items (`.HEIC`/`.JPG` + `.MOV`/`.MP4`) and caches album counts.
* **`app/media.py`**: Generates resized JPEG thumbnails, manages the disk cache (`.thumbcache/`), and handles range responses for video streaming.
* **`app/security.py`**: Handles Access PIN PBKDF2-HMAC-SHA256 hashing, symmetric local XOR obfuscations, and thread-safe client-IP sliding window rate limiting.
* **`backend/verify_api.py`**: Standalone API verification script to run manual integration queries.
* **`backend/diagnose.py`**: System diagnostics script to check ports, IPs, and configurations.

### 2. Windows Desktop Control Center & Launchers
* **`desktop_gui/gui_app.py`**: A native Tkinter desktop Control Center featuring a premium split-pane dark navy layout (v2):
  * **In-Process Monitor**: Spawns the server as a background thread and monitors thread liveness. If the thread crashes, it changes status indicators immediately to "Stopped".
  * **mDNS Connection Display**: Resolves system hostname using Python's `socket` library to show the easy-to-remember `.local` bookmark address alongside the numeric IP, with one-click copy buttons next to all URLs.
  * **UAC Firewall Automation**: Employs the Win32 `ShellExecuteW` API with the `"runas"` verb to run administrative PowerShell firewall scripts invisibly, safely handling path and quote escaping.
  * **Live Log Viewer Window**: Displays real-time logs fetched directly from the relocated `app.log` file.
  * **Update Checker**: Dynamically checks the latest releases via the GitHub API asynchronously on a background thread.
* **`PhotoBridge.spec`**: Configures the PyInstaller compile steps, bundling assets, icon configurations, metadata exclusions, and windowless execution binaries. Runs the version synchronizer script.
* **`installer/PhotoBridge.iss`**: Script for the Inno Setup compiler to generate the Windows installer. Automates adding/removing firewall rules. Resolves the application version dynamically from the root `VERSION` file at compile-time using Inno Setup Preprocessor (ISPP).

### 3. Frontend Modules (PWA Shell / Vanilla CSS & JS)
* **`frontend/index.html`**: Service template shell optimized for iOS Safari viewports (`viewport-fit=cover`).
* **`frontend/app.js`**: Single-page application state engine featuring request cancellations (`AbortController`) and dynamic video buffer cleanups to conserve iPhone hardware resources.
* **`frontend/style.css`**: Apple Photos style glassmorphic CSS styling.
* **`frontend/sw.js`**: Service Worker caching app shell assets only.

---

## 📂 Repository Structure & Directory Tree

```
my-photos-app/
├── .github/
│   └── workflows/
│       └── release.yml       # GitHub Actions CI/CD release workflow
├── backend/
│   ├── app/
│   │   ├── __init__.py       # Package marker
│   │   ├── main.py           # FastAPI routes & thread-pool controllers
│   │   ├── config.py         # Configuration manager (config.json I/O)
│   │   ├── scanner.py        # Filesystem scanner & metadata generator
│   │   ├── paths.py          # AppData / sys._MEIPASS paths manager
│   │   ├── media.py          # HEIC decoder & seekable range streaming
│   │   └── security.py       # PBKDF2 hashing, XOR local cipher, rate limiter
│   ├── run.py                # Server entry point & thread daemon
│   ├── verify_api.py         # Standalone API verification script
│   └── diagnose.py           # Diagnostics utility
├── frontend/
│   ├── index.html            # PWA template HTML
│   ├── app.js                # Vanilla JS state engine
│   ├── style.css             # Glassmorphic dark styling
│   ├── manifest.json         # PWA app registry
│   ├── sw.js                 # Service worker
│   └── icons/                # Home screen icon graphics
├── desktop_gui/
│   ├── gui_app.py            # Laptop controller GUI (Tkinter)
│   └── icon.ico              # Windows app icon file
├── installer/
│   └── PhotoBridge.iss       # Inno Setup compiler configuration
├── PhotoBridge.spec          # PyInstaller compilation specification
├── requirements.txt          # Unified runtime/build dependencies list
├── VERSION                   # Root version number source of truth
└── pyproject.toml            # Python package build specifications
```

---

## 🔒 Security Architecture

```mermaid
sequenceDiagram
    autonumber
    actor Client as Remote Phone
    participant Server as FastAPI Server
    
    Client->>Server: GET /api/config
    Server-->>Client: Returns Config (configured=True, pin_required=True)
    Note over Client: Phone checks local storage for pb_pin
    
    alt PIN is Missing or Incorrect
        Client->>Server: GET /api/media (No PIN Header)
        Server-->>Client: HTTP 401 Unauthorized
        Note over Client: app.js intercepts 401, shows Lock Screen
        Client->>Client: User enters PIN
    end
    
    Client->>Server: GET /api/media (X-PhotoBridge-PIN Header)
    Server-->>Client: HTTP 200 OK (Media JSON List)
    Note over Client: Render grid. Append ?pin=PIN to image URLs
    
    Client->>Server: GET /api/thumb/ID?pin=PIN
    Server-->>Client: Returns JPEG Thumbnail
```

### 0. Request Access Control Flow
Every incoming request to the media library goes through strict sequence checks, verifying directory liveness, lockout limits, and credential correctness.

```mermaid
graph TD
    Client[Remote PWA Client] -->|API Request| Dep{verify_access_pin}
    Dep -->|1. Get Config| Config[config.py]
    Config -->|Reads config.json & os.path.isdir| DiskCheck{Directory exists?}
    DiskCheck -->|No| Reject400[HTTP 400 Bad Request: Path Missing]
    DiskCheck -->|Yes| PinCheck{PIN Required?}
    PinCheck -->|No| Allow[Proceed to Endpoint]
    PinCheck -->|Yes| RateLimitCheck{Client IP locked out?}
    RateLimitCheck -->|Yes| Reject429[HTTP 429 Too Many Requests]
    RateLimitCheck -->|No| AuthCheck{Header PIN matches hash?}
    AuthCheck -->|No| RecordFailure[Record Failure] --> Reject401[HTTP 401 Unauthorized]
    AuthCheck -->|Yes| RecordSuccess[Record Success] --> Allow
```

### 1. Localhost Setup Lock
Any actions altering directories or displaying local dialogues (`POST /api/config` and `POST /api/select-folder`) check if the incoming connection is originating from the host machine loopback address (`127.0.0.1`, `localhost`). Remote calls are rejected with a `403 Forbidden` error.

### 2. Access PIN Authentication
When a security PIN is configured, all media endpoints require validation. 
* **Salted PBKDF2 Hash**: The PIN is stored as a salted PBKDF2-HMAC-SHA256 hash (`salt$hash` with 100,000 iterations) inside `config.json` for server authentication.
* **XOR Local Obfuscation**: The local host GUI stores and retrieves the PIN using a local XOR-obfuscation key (`access_pin_local`), permitting secure unmasked viewing within the laptop console while hiding raw plaintext from casual text-editor views.
* **Client-IP Sliding Window Rate Limiting**: The server tracks failed PIN attempts by client IP. If a client records 5 consecutive failed attempts, it is locked out for 60 seconds. Subsequent requests return a `429 Too Many Requests` status code with a retry timer.
* **Local GUI Isolation**: PIN setup and editing is restricted entirely to the host laptop GUI. Remote web app clients cannot set, modify, or delete the PIN, and API POST calls attempting to submit PIN configurations are blocked.
* **Client Transport**: Authorized JavaScript web requests transmit the PIN inside the `X-PhotoBridge-PIN` header, while native page elements (`<img>`/`<video>`) attach the PIN via the `?pin=XXXX` query string.

### 3. Path Traversal Defense
No absolute or relative file paths are exposed or accepted by the client. Files are mapped to in-memory URL-safe base64 indices generated during the scanner sweep.

### 4. mDNS & Hostname Diagnostics
To ensure that local hostname resolution (`http://<hostname>.local:8000`) functions reliably over the LAN:
* **Firewall Coverage**: During setup or installation, both TCP Port 8000 (app server) and UDP Port 5353 (standard Multicast DNS client port) exceptions are registered.
* **Test Action Diagnostics**: The Control Center displays a **Test** button next to the easy hostname row. When clicked, it spawns a background thread attempting to resolve the `.local` hostname using local DNS services (`socket.gethostbyname`). If resolution fails, it prints diagnostic logs pointing to firewall rules, network profiles (must be private), and the DNS Client service liveness.

### 5. Scan Progress Tracking
During folder rescans or directory re-indexing, the walker can process hundreds of files.
* **SCAN_STATUS State**: The `scanner.py` file declares a global tracker dictionary (`SCAN_STATUS`) containing `"status"` (scanning, idle, completed) and `"files_found"` metrics.
* **Exposed API**: A GET `/api/scan-status` route serves the current state to verified clients.
* **Frontend Toast Polling**: The PWA client polls `/api/scan-status` recursively every 1 second during a scan, rendering dynamic, non-stacking toast alerts (`Scanning library... Found X files`) and cleanups once completed.

### 6. Per-Request Path Re-Validation
If a network directory or USB flash card containing the photos library is unplugged mid-session:
* **FastAPI Dependency**: The FastAPI security dependency `verify_access_pin` executes on every media endpoint call.
* **Directory Liveness Check**: It checks the dynamically calculated `configured` state of `get_config()` on every request, immediately throwing an `HTTP 400 Bad Request` if the photo directory goes missing or becomes inaccessible on disk.
