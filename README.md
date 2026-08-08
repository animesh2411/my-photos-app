# PhotoBridge — Cross-Platform Local Network Photo Browser

PhotoBridge is a lightweight, local web application that runs on a Windows host laptop and allows any device (iPhones, Android phones, iPads, tablets, smart TVs, or other laptops) on the same Wi-Fi[...]

---

Live on the Microsoft Store now:
https://aka.ms/AA132oh6

## 🚀 How to Start (Quick Run)

1. **Download the Installer**: Go to the [Releases](https://github.com/animesh2411/my-photos-app/releases) page on GitHub and download the latest `PhotoBridgeSetup.exe`.
2. **Install**: Double-click the downloaded setup file to install the application. This will automatically set up a desktop shortcut.
3. **Launch**: Open the **PhotoBridge** app from your desktop or Start Menu.
4. **Configure & Start**:
   * Click **Configure Firewall Rule** (One-Time Setup) to allow phone traffic. Click **Yes** on the Windows UAC prompt.
   * Click **Start PhotoBridge Server**.
5. The dashboard will instantly display the Wi-Fi connection addresses for your mobile devices:
   * **Numeric IP**: `Phone: http://192.168.1.8:8000`
   * **Easy Hostname**: `Easy: http://mylaptop.local:8000` (Bookmark this! It uses mDNS so it stays valid even if your numeric IP changes).

---

## 📱 First-Time Setup (From Your Phone, Tablet, or TV)

1. **Connect your phone, tablet, or device to the same Wi-Fi network** as your laptop.
2. Open **any web browser** (Safari, Chrome, Firefox, etc.) on your device and go to the easy hostname address shown in the desktop dashboard (e.g. `http://mylaptop.local:8000`).
3. **Complete the setup wizard**:
   * Enter the path to the folder on your laptop you want to browse (e.g. `C:\Users\YourName\Pictures`).
   * *(Note: To secure your connections, you can configure an **Access PIN** locally inside the Windows desktop GUI sidebar).* 
4. **Add to Home Screen**:
    * Tap Safari's Share button (↗️) and select **Add to Home Screen**.
    * Launch PhotoBridge from your home screen for a premium, fullscreen app experience.

---

## ✨ Features

* **📱 Universal Cross-Platform Compatibility**: Fully compatible with any modern browser. Open and browse photos on iPhones, iPads, Android phones/tablets, smart TVs, or other laptops on the sa[...]
* **📦 Standalone Packaging & Zero-Dependency Portability (No Python Needed!)**: Can be compiled into a standalone directory distribution (`PhotoBridge.exe`) and packaged into a one-click Window[...]
* **🌐 mDNS Hostname Resolution & Diagnostics (`.local` URL)**: Exposes a persistent host-based address (e.g. `http://<your-device-name>.local:8000`) for easy bookmarking. Includes a built-in **[...]
* **🛡️ Elevated Inbound Firewalling (Auto-Managed)**: The installer and Control Center automatically manage Windows Firewall exceptions for both TCP Port 8000 (app server) and UDP Port 5353 ([...]
* **📂 User Data Relocation (Write-Safe)**: Stores configuration (`config.json`), log files (`app.log`), and thumbnail caches under `%LOCALAPPDATA%\PhotoBridge` instead of the project folder, co[...]
* **🎛️ Windows Control Center GUI**: Native desktop dashboard to check server status, configure/remove firewall rules, launch windowless servers, and inspect **live real-time server logs** (`[...]
* **📸 Date-Grouped Grid**: Scroll through all photos grouped by capture date with smooth lazy-loading and shimmer placeholders.
* **📂 Albums Grid & Cover Art**: Browse directory albums with automatic cover art selection (prioritizes image files over video clips) and persistent cover caching.
* **🎥 Video Badging & Scrubbing**: Video tiles display an iOS Photos style glassmorphism video badge (`▶ VIDEO`). Fullscreen video player supports range scrubbing and instant first-frame prev[...]
* **⚡ High-Performance Background Loading**: Engineered to decode heavy photos and EXIF data in the background, keeping the host laptop responsive and media loading fast.
* **🚀 Instant Page Transitions**: Instantly cancels previous loading queues when switching albums, dedicating 100% network bandwidth to the media you are currently viewing.
* **🧹 Automatic Cache Cleanup & Teardown**: The thumbnail cache directory under `%LOCALAPPDATA%\PhotoBridge` is automatically managed and cleared on server shutdown/launch to keep laptop hard d[...]
* **🔄 Real-Time Scan Progress Feedback**: Exposes a `/api/scan-status` polling API to show real-time progress indicators (`Scanning library... Found X files`) in the PWA client during recursive[...]
* **📱 Strict Mobile Privacy**: Headers set to `Cache-Control: private, no-store, must-revalidate` — phone browsers are strictly forbidden from writing media to phone disk storage.
* **🔴 Live Photos Support**: Paired images and video clips (e.g. `.HEIC` + `.MOV`) show a "LIVE" badge in the viewer. Touch-and-hold to play the clip.
* **❤️ Mark Favorites**: Tap the heart button to save items to your favorites directory (saved locally).
* **🔒 Localhost, Access PIN & Path Re-Validation Security**: Folder picker, settings, and PIN management can only be edited directly from the host laptop GUI. Access PINs are stored as secure, [...]

---

## 💻 Requirements
* **Windows 10 or 11** computer.
* **Mobile device, tablet, or smart TV** running a modern web browser (e.g. Safari, Chrome, Firefox).

---

## 📚 Technical Documentation & Guides

Below is the complete list of developer guides, system architectures, and completed roadmap tracking:

| Document | Description |
|---|---|
| 🗺️ **[System Architecture](local-md-files/ARCHITECTURE.md)** | Module breakdown, static file mapping, data structures, and Mermaid diagrams |
| 🛠️ **[Developer Guide](local-md-files/developer_guide.md)** | Executable compilation manual, manual firewall commands, and troubleshooting |
| 📋 **[Release Notes](RELEASE_NOTES.md)** | Full history of released versions, new features, and bug fixes |
| 🤝 **[Contributing Guidelines](local-md-files/CONTRIBUTING.md)** | Coding style standards and PR submission rules |
| 🧪 **[Testing Guide](local-md-files/TESTING.md)** | Unit test structures, coverage reporting, and test runner configurations |
| 📝 **[Implementation Summary](local-md-files/IMPLEMENTATION.md)** | Code maps, completed tasks check-off list, and extension instructions |
| 📊 **[Completion Report](local-md-files/COMPLETION_REPORT.md)** | Final validation states, testing logs, and performance metrics |
| 📌 **[Requirements Specification](local-md-files/requirement.md)** | Functional and technical system design goals |

---

Made with ❤️ by Animesh
