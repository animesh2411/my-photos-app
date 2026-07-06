# PhotoBridge — Local Network Photo Browser for iPhone

PhotoBridge is a local web application that runs on a Windows laptop and lets an iPhone on the same Wi-Fi network browse the laptop's photo/video folders in an interface styled like Apple Photos. It's a Progressive Web App (PWA) with no cloud accounts or complex setup needed.

---

## 📚 Documentation & Technical Guides

If you are a developer, want to contribute, or need advanced configurations, refer to these guides:
* 🛠️ **[Developer Guide](file:///f:/CodeX/PyCharmProjects/my-photos-app/local-md-files/developer_guide.md)**: Includes manual installation details, CLI execution ports, `curl` API endpoints tests, and manual firewall commands.
* 🗺️ **[System Architecture](file:///f:/CodeX/PyCharmProjects/my-photos-app/local-md-files/ARCHITECTURE.md)**: Module breakdowns, backend-frontend details, security designs, and Mermaid data flows.
* 🤝 **[Contributing Guidelines](file:///f:/CodeX/PyCharmProjects/my-photos-app/local-md-files/CONTRIBUTING.md)**: Project ownership rules, coding standard guides, and PR checklists.

---

## 🚀 How to Start (Quick Run)

1. **Download** or clone this project folder to your Windows laptop.
2. **Double-click `run_control_center.bat`** in the project folder. This will automatically create a safe virtual environment and install all packages.
3. In the PhotoBridge window:
   * Click **`1. Configure Firewall Rule`** (One-Time Setup). Click **Yes** on the Windows UAC security prompt that appears. This automatically secures your Wi-Fi port for phone access.
   * Click **`2. Start PhotoBridge Server`**.
4. The dashboard will instantly display the Wi-Fi connection addresses for your phone:
   * Example: `Phone: http://192.168.1.8:8000`

---

## 📱 First-Time Setup (From Your iPhone)

1. **Connect your iPhone to the same Wi-Fi network** as your laptop.
2. Open **Safari** on your phone and go to the address shown in the desktop dashboard (e.g. `http://192.168.1.8:8000`).
3. **Complete the setup wizard**:
   * Enter the path to the folder on your laptop you want to browse (e.g. `C:\Users\YourName\Pictures`).
   * (Optional) Set an **Access PIN** to protect your photos from other devices on the same network.
4. **Add to Home Screen**:
   * Tap Safari's Share button (↗️) and select **Add to Home Screen**.
   * Launch PhotoBridge from your home screen for a premium, fullscreen app experience.

---

## ✨ Features

* **🎛️ Windows Control Center**: Simple native desktop dashboard to check status, setup firewall rules, and start/stop the server windowlessly.
* **📸 Date-Grouped Grid**: Scroll through all photos grouped by capture date with smooth lazy-loading.
* **📂 Albums Card Grid**: Browse directories as album folders with Dynamic Cover Photos, total item counts, and smooth subnavigation back bars.
* **🎥 Video Scrubbing**: Play videos inside the fullscreen slider with full range scrubbing and seeking controls.
* **🔴 Live Photos Support**: Paired images and video clips (e.g. `.HEIC` + `.MOV`) show a "LIVE" badge in the viewer. Touch-and-hold to play the clip, and share them to your iPhone natively to merge them back into a Live Photo!
* **❤️ Mark Favorites**: Tap the heart button to save items to your favorites directory (saved locally).
* **🔒 Localhost & Path Traversal Security**: Settings can only be edited directly from the laptop. Files are resolved via URL-safe base64 memory IDs so folder hierarchies remain protected.

---

## 💻 Requirements
* **Python 3.11 or later** installed on your Windows laptop.
* **Windows 10 or 11** computer.
* **iPhone** running iOS 12 or newer.
