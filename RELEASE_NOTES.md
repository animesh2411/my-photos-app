# PhotoBridge Release Notes

This document tracks all version releases of PhotoBridge, highlighting new features, enhancements, and bug fixes for each build.

---

## [v1.0.4] — 2026-08-06 (Current Release)

### 🚀 Update Checker
- **Control Center Update Checking**: Added a **"Check for Updates"** button to the Control Center desktop GUI wrapper. When clicked, it executes a secure, asynchronous background request to the GitHub Releases API to verify if a newer version exists.
- **Auto-Comparison & Prompt**: Compares the latest release tag on GitHub against the version baked into the local binary. If a newer build is detected, it prompts the user with an alert dialog and opens the official release download page in their default web browser.

---

## [v1.0.3] — 2026-08-05

### 🚀 Versioning & Mobile Enhancements
- **Unified Version Management**: Consolidated version numbers into a single root `VERSION` file. Created `local-batch-files/sync_version.py` (which runs automatically during PyInstaller builds) to propagate versions to `pyproject.toml` and Inno Setup `PhotoBridge.iss`.
- **Dynamic Service Worker Cache-Busting**: Configured `sw.js` and `app.js` to dynamically parse and register the service worker using a version query parameter (`/sw.js?v=1.0.3`), forcing immediate cache flushes on the client side whenever a new version is built.
- **iOS Safari Download Guidance**: Configured the fullscreen download action to trigger Safari's native download prompt while showing a helpful toast instruction: *"Tip: Tap 'View', then long-press the image to save to Photos."* This bypasses confusing Files app storage defaults.
- **Lazy Preload of High-Resolution Assets**: Automatically preloads the original image in the background of the fullscreen viewer and swaps it inline (zero-flicker), ensuring long-presses save full-resolution photos.
- **HEIC Browser Compatibility**: Restricts original HEIC file swapping to Safari/iOS browsers that support it natively, maintaining high-res JPEG previews on other browsers (Chrome, Brave, Firefox) to prevent broken image renders.

---

## [v1.0.2] — 2026-08-05

### 🚀 CI/CD & Documentation Improvements
- **Branch-Based CD Strategy**: Decoupled continuous integration from continuous deployment. Commits on `master` now run CI test builds, while creating/pushing a release branch matching `release/v*` (e.g. `release/v1.0.2`) automatically tags the commit and publishes the public GitHub Release.
- **Relative Path Link Refactoring**: Replaced all local `file:///` absolute paths in `README.md` and developers guides with relative repository paths so clicking documents opens them seamlessly in both local editors and on GitHub.
- **Removed Duplicate Guides List**: Cleaned up the landing screen in `README.md` by removing the duplicate top links section.
- **Created TESTING.md Guide**: Added `local-md-files/TESTING.md` to detail test runners, code coverage reports, and testing instructions.

---

## [v1.0.1] — 2026-08-05

### 🧪 Testing & Code Quality
- **Backend Unit Testing Suite**: Developed a comprehensive Python testing suite (66 test cases in the `tests/` folder) using `pytest` and `pytest-cov`, achieving **90% code coverage** for the backend FastAPI application, media processing, configurations, and scanner algorithms.
- **Test Runner automation**: Added `local-batch-files/run_tests.bat` to easily run all test cases and check code coverage locally with a single click.
- **Test Asset Reorganization**: Relocated the untracked root-level test photo to the isolated `tests/resources/` directory.

---

## [v1.0.0] — 2026-08-05

### 🚀 New Features & Enhancements
- **mDNS Hostname Resolution (`.local` URL)**: Expose system hostname as an easy-to-remember, case-insensitive `.local` address (e.g., `http://<your-device-name>.local:8000`) on both the desktop GUI dashboard and the server console. This allows mobile devices to connect and bookmark a single persistent address that remains valid even when your router changes the laptop's IP address.
- **Upgraded GUI Layout**: Increased the default window dimensions of the Control Center dashboard to `520x680` (minimum size locked to `480x600`) to neatly display all three server access URLs (Local, Wi-Fi IP, and Hostname) without text clipping or layout wrapping.
- **Launcher Relocation**: Moved the `run_control_center.bat` launcher into the `local-batch-files/` directory, resolving path execution dependencies relative to the project root.
- **Root Release Notes**: Introduced root-level release notes tracking for public repository visibility.

---

## [v0.1.3] — 2026-08-05

### 🐛 Bug Fixes & Automation
- **Import Crash Hotfix**: Fixed a `NameError: name 'Request' is not defined` crash on server startup in compiled/frozen environments by moving the FastAPI `Request` import to the very top of `backend/app/main.py`.
- **Release Automation**: Integrated GitHub Actions CI/CD workflow to auto-compile, auto-tag, and publish installer executable assets automatically.

---

## [v0.1.2] — 2026-08-04

### 📦 Standalone Packaging & Portability
- **PyInstaller Executable Compilation**: Added `PhotoBridge.spec` to package the Python runtime, Tkinter GUI, FastAPI server, and web frontend assets into a standalone `PhotoBridge.exe` distribution requiring no pre-installed Python interpreter or runtime environments on end-user PCs.
- **Relocated Data Directories**: Implemented write-safe path resolution via `backend/app/paths.py`. Stores configurations (`config.json`), logs (`app.log`), and caches (`.thumbcache/`) under `%LOCALAPPDATA%\PhotoBridge` to conform to Windows user privilege models and bypass folder write access failures under `Program Files`.
- **Zero-Subprocess Server Thread**: Configured Uvicorn to run as an in-process thread daemon (`UvicornServerThread`) when frozen, passing `log_config=None` to prevent logger initialization crashes in windowed, console-less environments.
- **FastAPI Event-Loop Concurrency**: Converted recursive file-scanning, EXIF parsing, and media listing endpoints from `async def` to regular synchronous `def` routes, permitting FastAPI to route these CPU/disk-heavy processes to a background worker pool and keep the main asyncio event loop responsive.

### 🛡️ Windows Firewall & UAC Automation
- **Win32 ShellExecuteW Integration**: Refactored the control center's manual firewall exceptions setup to use the native Win32 `ShellExecuteW` API utilizing the `"runas"` verb. This triggers the standard Windows UAC prompt directly, avoiding nested PowerShell escaping errors and console flashes.
- **Inno Setup Installer (`PhotoBridgeSetup.exe`)**: Built `installer/PhotoBridge.iss` to package the PyInstaller output into a single, user-friendly setup file. Automatically registers inbound TCP Port 8000 exceptions on Private Wi-Fi profiles during installation, and cleans up rules on uninstallation.

---

## [v0.1.1] — 2026-08-02

### ⚙️ Minor Adjustments
- Initial packaging configurations and environment parameters setup.

---

## [v0.1.0] — 2026-07-06

### ✨ Initial Release
- **Tkinter GUI Control Center**: Initial native Windows Control Center GUI to check server status, open firewall ports, view logs, and launch windowless servers.
- **Responsive PWA Grid Layout**: Apple Photos styled dark-themed progressive web application with date-grouped photo/video lists, iOS Photos-style glassmorphic video tiles, and swipe/arrow navigation.
- **EXIF Extraction**: Directory scanner crawling photos and extracting capture dates using Pillow EXIF tags, with automatic file mtime fallbacks.
- **Video Scrubbing**: FastAPI HTTP range-seeking response streaming allowing videos to play and scrub in Safari.
- **Strict Privacy Headers**: Appended `Cache-Control: private, no-store, must-revalidate` to all media streams, preventing mobile devices from cache-writing photos to device storage.
- **Favorites & Search**: LocalStorage persistent favorites and live filename search filtering.
