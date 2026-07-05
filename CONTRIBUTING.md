# Contributing to PhotoBridge

Thank you for your interest in contributing to PhotoBridge! We welcome contributions to make this local PWA photo browser even better, faster, and more secure.

This project is owned and maintained by [@animesh2411](https://github.com/animesh2411).

---

## 🛠️ Code of Conduct & Ownership

* **Repository Owner**: [@animesh2411](https://github.com/animesh2411)
* **Code Owners**: Please refer to the [.github/CODEOWNERS](file:///f:/CodeX/PyCharmProjects/my-photos-app/.github/CODEOWNERS) file. All Pull Requests and code modifications require approval from the owner.

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
- **PWA Integrity**: Maintain service worker caching rules. If you modify static assets, increment `CACHE_NAME` in [sw.js](file:///f:/CodeX/PyCharmProjects/my-photos-app/static/sw.js) to force client cache eviction.

---

## 🧪 Testing & Verification

Before submitting any code changes, verify your work:

1. **Verify Python Syntax**:
   ```bash
   python -m py_compile app/main.py app/config.py app/scanner.py app/media.py run.py
   ```
2. **Run the API Test Suite**:
   ```bash
   python test_api.py
   ```
3. **Launch the Server**:
   Double-click `run_app.bat` or run:
   ```bash
   python run.py
   ```
4. **Manual UI Checks**:
   Open the app on your mobile Safari browser and verify:
   - Date-grouped photo grids and fullscreen viewing.
   - Live Photo playback (touch-and-hold) and saving.
   - Album folder grid navigation and back options.
   - Settings configurations and localhost connection locks.
