# PhotoBridge — Local Network Photo Browser for iPhone

PhotoBridge is a local web application that runs on a Windows laptop and lets an iPhone on the same Wi-Fi network browse the laptop's photo/video folders in an interface styled like Apple Photos. It's a Progressive Web App (PWA) with no cloud accounts or complex setup needed.

---

## 📚 Documentation & Technical Guides

If you are a developer, want to contribute, or need advanced configurations, refer to these guides:
* 🛠️ **[Developer Guide](local-md-files/developer_guide.md)**: Includes manual installation details, CLI execution ports, `curl` API endpoints tests, and manual firewall commands.
* 🗺️ **[System Architecture](local-md-files/ARCHITECTURE.md)**: Module breakdowns, backend-frontend details, security designs, and Mermaid data flows.
* 🤝 **[Contributing Guidelines](local-md-files/CONTRIBUTING.md)**: Project ownership rules, coding standard guides, and PR checklists.

---

## 🚀 How to Start (Quick Run)

1. **Download** or clone this project folder to your Windows laptop.
2. **Double-click `run_control_center.bat`** in the `local-batch-files/` folder. This will automatically create a safe virtual environment and install all packages.
3. In the PhotoBridge window:
   * Click **`1. Configure Firewall Rule`** (One-Time Setup). Click **Yes** on the Windows UAC security prompt that appears. This automatically secures your Wi-Fi port for phone access.
   * Click **`2. Start PhotoBridge Server`**.
4. The dashboard will instantly display the Wi-Fi connection addresses for your phone:
   * **Numeric IP**: `Phone: http://192.168.1.8:8000`
   * **Easy Hostname**: `Easy: http://mylaptop.local:8000` (Bookmark this! It uses mDNS so it stays valid even if your numeric IP changes).

---

## 📱 First-Time Setup (From Your iPhone)

1. **Connect your iPhone to the same Wi-Fi network** as your laptop.
2. Open **Safari** on your phone and go to the easy hostname address shown in the desktop dashboard (e.g. `http://mylaptop.local:8000`).
3. **Complete the setup wizard**:
   * Enter the path to the folder on your laptop you want to browse (e.g. `C:\Users\YourName\Pictures`).
   * (Optional) Set an **Access PIN** to protect your photos from other devices on the same network.
4. **Add to Home Screen**:
   * Tap Safari's Share button (↗️) and select **Add to Home Screen**.
   * Launch PhotoBridge from your home screen for a premium, fullscreen app experience.

---

## ✨ Features

* **📦 Standalone Packaging & Zero-Dependency Portability (No Python Needed!)**: Can be compiled into a standalone directory distribution (`PhotoBridge.exe`) and packaged into a one-click Windows installer (`PhotoBridgeSetup.exe`). End users do not need Python or any development libraries installed to run the application.
* **🌐 mDNS Hostname Resolution (`.local` URL)**: Exposes a persistent host-based address (e.g. `http://<your-device-name>.local:8000`) for easy bookmarking, keeping connections active when the laptop's numeric IP changes.
* **🛡️ Elevated Inbound Firewalling (Auto-Managed)**: The installer and Control Center automatically manage Windows Firewall exceptions for Port 8000 on private Wi-Fi profiles, handling setup and clean removal on uninstall.
* **📂 User Data Relocation (Write-Safe)**: Stores configuration (`config.json`), log files (`app.log`), and thumbnail caches under `%LOCALAPPDATA%\PhotoBridge` instead of the project folder, complying with Windows security policies and bypassing permission issues in `Program Files`.
* **🚀 Automated GitHub Actions Releases**: Fully configured CI/CD pipeline (`.github/workflows/release.yml`) builds the standalone installer automatically on every master push and publishes tagged releases (`v*`) to GitHub.
* **🎛️ Windows Control Center GUI**: Native desktop dashboard to check server status, configure/remove firewall rules, launch windowless servers, and inspect **live real-time server logs** (`📋 View Server Logs`).
* **📸 Date-Grouped Grid**: Scroll through all photos grouped by capture date with smooth lazy-loading and shimmer placeholders.
* **📂 Albums Grid & Cover Art**: Browse directory albums with automatic cover art selection (prioritizes image files over video clips) and persistent cover caching.
* **🎥 Video Badging & Scrubbing**: Video tiles display an iOS Photos style glassmorphism video badge (`▶ VIDEO`). Fullscreen video player supports range scrubbing and instant first-frame preview.
* **🧵 ThreadPool Offloaded Processing**: Fast API endpoints offload PIL decoding and EXIF reads to background worker threads, preventing event loop blocking.
* **🛑 Request Cancellation Controller**: Aborts pending thumbnail downloads when switching tabs or clicking a photo, dedicating 100% pipeline to requested media.
* **🧹 Automatic Cache Cleanup & Teardown**: `backend/.thumbcache/` is automatically purged on server shutdown/launch to keep laptop hard drives clean.
* **📱 Strict Mobile Privacy**: Headers set to `Cache-Control: private, no-store, must-revalidate` — phone browsers are strictly forbidden from writing media to phone disk storage.
* **🔴 Live Photos Support**: Paired images and video clips (e.g. `.HEIC` + `.MOV`) show a "LIVE" badge in the viewer. Touch-and-hold to play the clip.
* **❤️ Mark Favorites**: Tap the heart button to save items to your favorites directory (saved locally).
* **🔒 Localhost & Path Traversal Security**: Folder picker and settings can only be edited directly from the host laptop. Files are resolved via URL-safe base64 memory IDs.

---

## 💻 Requirements
* **Windows 10 or 11** computer.
* **iPhone** running iOS 12 or newer.
* **Python 3.12 or later** (Only required for running from source code/development; not needed when using the standalone `PhotoBridgeSetup.exe` installer).

---

## 📚 Technical Documentation & Guides

Below is the complete list of developer guides, system architectures, and completed roadmap tracking:

| Document | Description |
|---|---|
| 🗺️ **[System Architecture](local-md-files/ARCHITECTURE.md)** | Module breakdown, static file mapping, data structures, and Mermaid diagrams |
| 🛠️ **[Developer Guide](local-md-files/developer_guide.md)** | Executable compilation manual, manual firewall commands, and troubleshooting |
| 📋 **[Release Notes](RELEASE_NOTES.md)** | Full history of released versions, new features, and bug fixes |
| 🤝 **[Contributing Guidelines](local-md-files/CONTRIBUTING.md)** | Coding style standards and PR submission rules |
| 📝 **[Implementation Summary](local-md-files/IMPLEMENTATION.md)** | Code maps, completed tasks check-off list, and extension instructions |
| 📊 **[Completion Report](local-md-files/COMPLETION_REPORT.md)** | Final validation states, testing logs, and performance metrics |
| 📌 **[Requirements Specification](local-md-files/requirement.md)** | Functional and technical system design goals |

---

Made with ❤️ by Animesh
