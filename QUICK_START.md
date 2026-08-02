# PhotoBridge Build Quick Start

## Local Build & Test (5 minutes)

### Prerequisites
- Python 3.14+
- Windows 10/11
- Git

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Build Executable
```bash
pyinstaller PhotoBridge.spec
```
Output: `dist\PhotoBridge\PhotoBridge.exe`

### Step 3: Test Executable
```bash
.\dist\PhotoBridge\PhotoBridge.exe
```
- GUI should launch
- Config creates in `%LOCALAPPDATA%\PhotoBridge\config.json`
- Frontend loads correctly

### Step 4: Build Installer (Optional)
Install Inno Setup first:
```bash
choco install innosetup
# OR download from: https://jrsoftware.org/isdl.php
```

Then compile:
```bash
"C:\Program Files (x86)\Inno Setup 6\iscc.exe" "installer\PhotoBridge.iss"
```
Output: `installer-output\PhotoBridgeSetup.exe`

### Step 5: Test Installer (Optional)
```bash
.\installer-output\PhotoBridgeSetup.exe
```
- Follow prompts
- Check Start Menu for shortcut
- Firewall rule should be created

---

## Automated Release (GitHub Actions)

**No additional steps needed!**

1. Commit and push to `master`:
```bash
git add .
git commit -m "Your changes"
git push origin master
```

2. GitHub Actions automatically:
   - ✓ Builds `PhotoBridge.exe`
   - ✓ Builds `PhotoBridgeSetup.exe`
   - ✓ Creates Release with auto-generated version tag
   - ✓ Uploads installer for download

3. Monitor progress at: `Actions` tab in GitHub

---

## Troubleshooting

**"PhotoBridge.exe not created?"**
```bash
# Check for errors
pyinstaller PhotoBridge.spec --debug all
```

**"Module not found?" when running frozen .exe**
- Add module to `PhotoBridge.spec` → `hiddenimports` list
- Re-run: `pyinstaller PhotoBridge.spec`

**"Config file not found?"**
- Verify `backend/app/paths.py` exists
- Check: `%LOCALAPPDATA%\PhotoBridge\` folder

**Need to adjust version?**
- Edit: `pyproject.toml` → `version = "0.1.0"`
- Edit: `installer/PhotoBridge.iss` → `#define MyAppVersion "0.1.0"`

---

## Files Modified/Created

- ✓ `backend/app/paths.py` — Resource path helper (NEW)
- ✓ `backend/app/config.py` — Uses %LOCALAPPDATA% (UPDATED)
- ✓ `backend/app/main.py` — Uses resource_path() (UPDATED)
- ✓ `requirements.txt` — Added pyinstaller (UPDATED)
- ✓ `PhotoBridge.spec` — PyInstaller config (NEW)
- ✓ `installer/PhotoBridge.iss` — Inno Setup script (NEW)
- ✓ `.github/workflows/release.yml` — CI/CD workflow (NEW)
- ✓ `BUILD.md` — Full documentation (NEW)

See `BUILD.md` for detailed information.

