import os
import pytest
from unittest.mock import patch
from app.logger import log_event, get_logs, clear_logs

@pytest.fixture
def mock_log_file(tmp_path):
    log_path = str(tmp_path / "app.log")
    with patch("app.logger.LOG_FILE", log_path):
        # Initialize the mock file
        if os.path.exists(log_path):
            os.remove(log_path)
        yield log_path

def test_log_event_creation(mock_log_file):
    assert not os.path.exists(mock_log_file)
    
    log_event("INFO", "Test message")
    assert os.path.exists(mock_log_file)
    
    with open(mock_log_file, "r", encoding="utf-8") as f:
        content = f.read()
    assert "[INFO] Test message" in content

def test_get_logs_empty(mock_log_file):
    logs = get_logs()
    assert logs == []

def test_get_logs_populated(mock_log_file):
    log_event("INFO", "Hello Info")
    log_event("WARN", "Hello Warn")
    log_event("ERROR", "Hello Error")
    
    logs = get_logs()
    assert len(logs) == 3
    assert logs[0]["level"] == "INFO"
    assert logs[0]["message"] == "Hello Info"
    assert logs[1]["level"] == "WARN"
    assert logs[1]["message"] == "Hello Warn"
    assert logs[2]["level"] == "ERROR"
    assert logs[2]["message"] == "Hello Error"

def test_get_logs_max_lines(mock_log_file):
    for i in range(10):
        log_event("INFO", f"Msg {i}")
        
    logs = get_logs(max_lines=5)
    assert len(logs) == 5
    assert logs[0]["message"] == "Msg 5"
    assert logs[4]["message"] == "Msg 9"

def test_get_logs_malformed_lines(mock_log_file):
    with open(mock_log_file, "w", encoding="utf-8") as f:
        f.write("Malformed_line_no_spaces\n")
        f.write("[12:00:00] [INFO] Clean line\n")
        
    logs = get_logs()
    assert len(logs) == 2
    assert logs[0]["message"] == "Malformed_line_no_spaces"
    assert logs[1]["level"] == "INFO"
    assert logs[1]["message"] == "Clean line"

def test_clear_logs(mock_log_file):
    log_event("INFO", "Log message 1")
    log_event("INFO", "Log message 2")
    
    clear_logs()
    
    logs = get_logs()
    assert len(logs) == 1
    assert "Logs cleared." in logs[0]["message"]
