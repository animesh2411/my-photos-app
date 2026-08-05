# PhotoBridge Testing Guide

This guide describes the unit testing setup, test runner scripts, and coverage goals for the PhotoBridge backend.

---

## 🚀 How to Run Tests

### 1. Simple Run (Batch Script)
You can run the entire test suite and generate a console coverage report by double-clicking:
`local-batch-files/run_tests.bat`

### 2. Manual CLI Run
Ensure you have the virtual environment activated, set the `PYTHONPATH` to include the `backend/` directory, and run `pytest`:
```bash
# Set environment path
set PYTHONPATH=backend

# Run all tests
pytest

# Run tests with coverage summary
pytest --cov=backend/app --cov-report=term-missing tests/
```

---

## 🧪 Test Suite Structure

Unit tests are located in the `tests/` directory:

*   **`test_paths.py`**: Verifies path resolution in both development mode and frozen PyInstaller modes (simulating `sys.frozen` and `sys._MEIPASS`).
*   **`test_config.py`**: Verifies JSON read/write configuration, folder path validations, access PIN pbkdf2 hashing, legacy config auto-migration, and XOR local obfuscation.
*   **`test_logger.py`**: Verifies logging processes, parsing log lines, and log clearing.
*   **`test_scanner.py`**: Verifies filesystem recursive walking, base64 ID parsing, EXIF date metadata extractions, and Live Photo video/image group pairing.
*   **`test_media.py`**: Verifies thumbnail resizing caches, RGBA alpha channels, and seekable HTTP 206 Range Response video stream chunks.
*   **`test_main.py`**: Verifies all FastAPI server endpoints, access authentication, client IP rate limiting lockouts, loopback locks, and lifecycle startup/shutdown handlers.

---

## 📊 Code Coverage Goals

We maintain a strict coverage threshold of **>90%** for all backend logic modules.

To generate an interactive HTML coverage report on your local machine:
```bash
set PYTHONPATH=backend
pytest --cov=backend/app --cov-report=html tests/
```
Open `htmlcov/index.html` in your web browser to inspect line-by-line coverage analysis.
