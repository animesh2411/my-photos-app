# Contributing to PhotoBridge

Thank you for your interest in contributing to PhotoBridge! We welcome contributions to make this local PWA photo browser even better, faster, and more secure.

This project is owned and maintained by [@animesh2411](https://github.com/animesh2411).

---

## 🛠️ Code of Conduct & Ownership

* **Repository Owner**: [@animesh2411](https://github.com/animesh2411)
* **Code Owners**: Please refer to the [.github/CODEOWNERS](../.github/CODEOWNERS) file. All Pull Requests and code modifications require approval from the owner.

---

## 🚀 How to Contribute

### 1. Report Bugs & Request Features
If you find a bug or have a suggestion for improvement:
- Open an Issue in the repository.
- Describe the problem clearly, including steps to reproduce, client device info (e.g., iPhone iOS version, Safari), and any server-side logs.

### 2. Submit Pull Requests
If you want to contribute code:
1. Fork the repository and create your branch from `main`.
2. Implement your changes.
3. Verify your changes (see the [Testing & Verification](#-testing--verification) section below).
4. Submit a Pull Request (PR) targeting the `main` branch.

---

## 💻 Coding Guidelines

To maintain the project's performance and design consistency, please adhere to these guidelines:

### Backend (Python/FastAPI)
- Keep dependencies minimal. Current dependencies include `fastapi`, `uvicorn`, `pillow`, `pillow-heif`, and `python-multipart`.
- Ensure all file operations are secure against path traversal (always resolve paths through index IDs).
- Enforce that configuration endpoints remain restricted to `localhost` requests only.

### Frontend (Vanilla JS & CSS)
- **No JS Frameworks**: Do not introduce React, Vue, or other heavy frameworks. Keep the codebase lightweight using vanilla JavaScript.
- **Glassmorphism Aesthetic**: Follow Apple's iOS Photos dark mode styling (dark background, translucent headers/modals with `backdrop-filter`, and clean circular button controls).
- **Responsive Layout**: Ensure all views are optimized for mobile touch interaction (specifically Mobile Safari on iPhone).
- **PWA Integrity**: Maintain service worker caching rules. If you modify static assets, increment `CACHE_NAME` in [sw.js](../frontend/sw.js) to force client cache eviction.

---

## 🧪 Testing & Verification

Before submitting any code changes, verify your work:

1. **Verify Python Syntax**:
   ```bash
   python -m py_compile backend/app/main.py backend/app/config.py backend/app/scanner.py backend/app/media.py backend/run.py desktop_gui/gui_app.py
   ```
2. **Run the API Test Suite**:
   ```bash
   python backend/verify_api.py
   ```
3. **Launch the Server**:
   Double-click `local-batch-files/run_app.bat` or run:
   ```bash
   python backend/run.py
   ```
4. **Manual UI Checks**:
   Open the app on your mobile Safari browser and verify:
   - Date-grouped photo grids and fullscreen viewing.
   - Live Photo playback (touch-and-hold) and saving.
   - Album folder grid navigation and back options.
   - Settings configurations and localhost connection locks.

---

## 🚀 Release Management & Branching Strategy

We follow a structured branching and release workflow to avoid release pollution and code debt on major branches.

### 1. Continuous Integration (CI) on `master`
- Daily development is merged into the `master` branch.
- Every push to `master` triggers the CI workflow, which builds the standalone installer and uploads it as a workflow artifact on GitHub Actions for testing.
- **No Git tag is pushed and no public GitHub Release is created on master commits.**

### 2. Continuous Deployment (CD) on `release/v*`
- When the codebase on `master` is stable and ready for a public release:
  1. Create a release branch named `release/v<version>` from `master` (e.g., `release/v1.0.0`):
     ```bash
     git checkout master
     git pull origin master
     git checkout -b release/v1.0.0
     git push origin release/v1.0.0
     ```
  2. The push to the `release/v*` branch automatically triggers the CD pipeline:
     - Extracts the version (e.g. `v1.0.0`) from the branch name.
     - Compiles the PyInstaller build and packages `PhotoBridgeSetup.exe` via Inno Setup.
     - Tags the commit with the extracted version and pushes it back to GitHub.
     - Creates a public GitHub Release for the tag, attaching the installer asset.
