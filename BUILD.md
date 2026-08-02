<!-- build.md -->

# PhotoBridge Build and Release Documentation

This document describes how PhotoBridge is packaged as a standalone Windows installer with automated CI/CD through GitHub Actions.

## Architecture Overview

The build process consists of three main stages:

1. **PyInstaller Packaging** — Bundles Python code + frontend assets into `PhotoBridge.exe`
2. **Inno Setup Installer** — Packages the exe into a Windows installer (`PhotoBridgeSetup.exe`)
3. **GitHub Actions CI/CD** — Automatically builds and releases on every push to `master`

---

## Part 1: PyInstaller Packaging

### How It Works

PyInstaller converts the Python desktop GUI application into a standalone `.exe` file that:
- Includes all Python dependencies
- Bundles the frontend assets (`frontend/` folder)
- Requires **no external Python installation**
- Handles resource paths via `sys._MEIPASS` at runtime

### Key Components

#### `backend/app/paths.py` — Resource Path Helper

This module provides two critical functions:

```python
def resource_path(relative_path: str) -> str:
    """
    Resolves paths for bundled resources in both dev and frozen contexts.
    - Dev mode: returns paths relative to project root
    - Frozen mode: returns paths relative to sys._MEIPASS (PyInstaller temp folder)
    """

def get_user_data_dir() -> str:
    """
    Returns %LOCALAPPDATA%\PhotoBridge on Windows.
    Used for storing config.json so the app has write permissions (Program Files is read-only).
    """
```

#### Updated `backend/app/config.py`

The config file location was changed from the current working directory to:
```
%LOCALAPPDATA%\PhotoBridge\config.json
```

This ensures:
- **Config persists** across app updates (not in Program Files)
- **Write permissions** guaranteed (LOCALAPPDATA is user-writable)
- **Isolation** from other apps' data

#### Updated `backend/app/main.py`

The frontend static directory is now resolved using the helper:
```python
from app.paths import resource_path

static_dir = resource_path("frontend")  # Works in both dev and frozen modes
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
```

#### `PhotoBridge.spec` — PyInstaller Configuration

This reproducible spec file defines:
- **Entry point**: `desktop_gui/gui_app.py`
- **Data to bundle**: `frontend/` folder, icons, etc.
- **Hidden imports**: Explicit listing of backend modules
- **Output**: `dist/PhotoBridge/PhotoBridge.exe` (with deps bundled)

### Building Locally

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run PyInstaller
pyinstaller PhotoBridge.spec

# 3. Output: dist\PhotoBridge\PhotoBridge.exe
```

#### Testing the Frozen Executable

```bash
# Run directly
.\dist\PhotoBridge\PhotoBridge.exe

# Note: First run will create %LOCALAPPDATA%\PhotoBridge\config.json
```

---

## Part 2: Inno Setup Installer

### What It Does

`installer/PhotoBridge.iss` is an **Inno Setup** script that:

1. **Installs files** to `Program Files\PhotoBridge\`
2. **Creates shortcuts**:
   - Start Menu: `Start → PhotoBridge → PhotoBridge`
   - Desktop (optional): User can choose during setup
3. **Configures Windows Firewall**:
   - Adds inbound rule for port 8000 (Private network only)
   - Rule is only created once, never duplicated
   - Runs elevated (user sees UAC prompt)
4. **Registers uninstaller**:
   - Appears in Settings → Apps & Features
   - Removes firewall rule on uninstall
5. **Output**: `installer-output/PhotoBridgeSetup.exe`

### Key Script Sections

#### Task: Firewall Configuration

```ini
[Tasks]
Name: "firewallrule"; Description: "Configure Windows Firewall inbound rule (Port 8000)"

[Run]
Filename: "powershell.exe"; 
Parameters: "-NoProfile -WindowStyle Hidden -Command ""if (-not (Get-NetFirewallRule ...
```

This runs PowerShell elevated to:
- Check if rule already exists (prevent duplicates)
- Create rule if missing
- Only affects Private networks (safe for home/work networks)

#### Uninstall Cleanup

```ini
[UninstallRun]
Filename: "powershell.exe";
Parameters: "... Remove-NetFirewallRule -DisplayName 'PhotoBridge Port 8000' ..."
```

On uninstall, the firewall rule is automatically removed.

### Building the Installer Locally

```bash
# 1. First, build PhotoBridge.exe
pyinstaller PhotoBridge.spec

# 2. Install Inno Setup from: https://jrsoftware.org/isdl.php

# 3. Compile the installer
# Via GUI: Open installer\PhotoBridge.iss in Inno Setup IDE, then Build → Compile
# Via CLI:
"C:\Program Files (x86)\Inno Setup 6\iscc.exe" "installer\PhotoBridge.iss"

# 4. Output: installer-output\PhotoBridgeSetup.exe
```

#### Customizing Installer Settings

Edit `installer/PhotoBridge.iss`:
- `#define MyAppVersion`: Update version number
- `DefaultDirName`: Change installation directory
- `SetupIconFile`: Change installer icon
- `LicenseFile`: Point to your license

---

## Part 3: GitHub Actions Workflow

### Trigger

The workflow `.github/workflows/release.yml` is triggered on:
```yaml
on:
  push:
    branches:
      - master
```

**Every push to `master`** automatically:
1. Builds `PhotoBridge.exe`
2. Builds `PhotoBridgeSetup.exe`
3. Creates a GitHub Release with the installer attached

### Workflow Steps

#### 1. Setup
- Checks out code
- Sets up Python 3.14
- Installs dependencies from `requirements.txt`

#### 2. Build PyInstaller

```bash
pyinstaller PhotoBridge.spec
```

Produces: `dist/PhotoBridge/PhotoBridge.exe` (with all dependencies bundled)

#### 3. Install Inno Setup

```bash
choco install innosetup
```

The `windows-latest` GitHub Actions runner includes Chocolatey.

#### 4. Compile Inno Setup

```bash
iscc.exe installer\PhotoBridge.iss
```

Produces: `installer-output/PhotoBridgeSetup.exe`

#### 5. Version Generation

```bash
# Extract first 7 chars of commit SHA
$shortSha = "abc1234567..."  →  "abc1234"
$version = "v0.1.0-abc1234"
```

This ensures **every push produces a distinct version tag**, preventing conflicts.

#### 6. Create GitHub Release

Using `softprops/action-gh-release@v1`:
- **Tag**: `v0.1.0-<commit-sha>` (auto-generated)
- **Release name**: `PhotoBridge v0.1.0-<commit-sha>`
- **Asset**: `installer-output/PhotoBridgeSetup.exe`
- **Visibility**: Public (visible in Releases tab)

#### 7. Upload Artifacts

Build artifacts are retained for 30 days:
- `dist/PhotoBridge/` (exe + dependencies)
- `installer-output/` (installer exe)

Available under Actions → specific run → Artifacts.

### How Releases Appear

In your GitHub repo:
- **Releases tab** shows new release for each push
- **Release name and tag**: `v0.1.0-<short-sha>`
- **Download**: Click release → download `PhotoBridgeSetup.exe`

Example:
```
v0.1.0-abc1234  (commit abc1234567...)
  ↳ PhotoBridgeSetup.exe (5.2 MB)

v0.1.0-def5678  (commit def5678901...)
  ↳ PhotoBridgeSetup.exe (5.2 MB)
```

### Customizing Versioning

To change version strategy, edit `.github/workflows/release.yml`:

**Current (Auto-generate per push):**
```bash
$version = "v0.1.0-$shortSha"  # Every push = new release
```

**Alternative (Only on tags):**
```yaml
on:
  push:
    tags:
      - 'v*'
```
Then version from tag: `$version = ${{ github.ref_name }}`

### Secrets & Permissions

The workflow includes:
```yaml
permissions:
  contents: write
```

This grants `GITHUB_TOKEN` permission to:
- Create releases
- Upload release assets

**No additional secrets needed** — `GITHUB_TOKEN` is auto-provisioned.

---

## File Structure

```
my-photos-app/
├── .github/
│   └── workflows/
│       └── release.yml                 # ← GitHub Actions workflow
├── backend/
│   └── app/
│       ├── paths.py                    # ← NEW: Resource path helper
│       ├── config.py                   # ← UPDATED: Use %LOCALAPPDATA%
│       └── main.py                     # ← UPDATED: Use resource_path()
├── desktop_gui/
│   ├── gui_app.py
│   └── icon.ico
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── ...
├── installer/
│   └── PhotoBridge.iss                 # ← NEW: Inno Setup script
├── PhotoBridge.spec                    # ← NEW: PyInstaller spec
├── requirements.txt                    # ← UPDATED: Added pyinstaller
└── README.md
```

---

## Troubleshooting

### PyInstaller Issues

**"Module not found" when running frozen exe:**
- Add to `PhotoBridge.spec` → `hiddenimports` list
- Run: `pyinstaller PhotoBridge.spec --debug all`

**Config.json not found in frozen exe:**
- Verify `backend/app/paths.py` is imported
- Check `%LOCALAPPDATA%\PhotoBridge\` directory exists

### Inno Setup Issues

**"iscc.exe not found":**
- Install Inno Setup: https://jrsoftware.org/isdl.php
- Or run: `choco install innosetup`
- Ensure it's in PATH

**Firewall rule not created during install:**
- Check UAC prompt appeared
- Verify user has admin rights
- Manually test: `powershell -Command "Get-NetFirewallRule -DisplayName 'PhotoBridge Port 8000'"`

### GitHub Actions Issues

**Workflow doesn't trigger:**
- Verify push is to `master` branch (not a draft)
- Check `.github/workflows/release.yml` syntax

**"PhotoBridge.exe not created":**
- Check build logs in Actions tab
- Verify `desktop_gui/gui_app.py` exists
- Run locally: `pyinstaller PhotoBridge.spec`

---

## Development Workflow

### Normal Development

```bash
# 1. Desktop GUI dev
python desktop_gui/gui_app.py

# 2. Backend dev
cd backend
python run.py

# 3. Frontend dev
# Edit frontend/index.html, app.js, etc.
# Auto-reloaded by uvicorn in development
```

### Testing Build Chain

```bash
# 1. Local PyInstaller build (30-60 seconds)
pyinstaller PhotoBridge.spec

# 2. Local Inno Setup build (15 seconds)
iscc.exe installer\PhotoBridge.iss

# 3. Test the installer
.\installer-output\PhotoBridgeSetup.exe
```

### Releasing

```bash
# 1. Edit version in pyproject.toml (optional)
# 2. Commit changes
git add .
git commit -m "Feature: Add new photos view"

# 3. Push to master
git push origin master

# 4. GitHub Actions automatically builds and releases
# Monitor at: https://github.com/youruser/my-photos-app/actions
```

---

## Performance & Size

| Artifact | Size | Build Time |
|----------|------|-----------|
| `PhotoBridge.exe` | ~40 MB | ~30 sec |
| `PhotoBridgeSetup.exe` | ~5 MB | ~15 sec |
| Full CI/CD run | — | ~3-4 min |

- PyInstaller bundles all Python dependencies
- LZMA compression used in Inno Setup
- File sizes are typical for Python/PyQt apps

---

## License & Attribution

- **PyInstaller**: GNU General Public License (GPLv2)
- **Inno Setup**: Zlib License
- **PhotoBridge**: [Your License]

Ensure compliance when distributing `PhotoBridgeSetup.exe`.

---

## Next Steps

1. **Test locally**: `pyinstaller PhotoBridge.spec`
2. **Push to master**: GitHub Actions will build and release automatically
3. **Share installer**: Link users to GitHub Releases tab
4. **Updates**: Each push to master generates a new downloadable version


