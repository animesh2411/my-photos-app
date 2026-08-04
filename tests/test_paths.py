import os
import sys
import unittest
from unittest.mock import patch
from app.paths import is_frozen, resource_path, user_data_dir, project_root

class TestPaths(unittest.TestCase):
    def test_is_frozen_false_by_default(self):
        # By default in testing, we are not running as a frozen executable
        with patch.object(sys, "frozen", False, create=True):
            self.assertFalse(is_frozen())

    def test_is_frozen_true(self):
        with patch.object(sys, "frozen", True, create=True):
            self.assertTrue(is_frozen())

    def test_resource_path_dev(self):
        with patch.object(sys, "frozen", False, create=True):
            path = resource_path("frontend/index.html")
            self.assertTrue(path.endswith("frontend/index.html") or path.endswith("frontend\\index.html"))
            # Dev mode resource path resolves relative to project root
            self.assertIn("my-photos-app", path)

    def test_resource_path_frozen(self):
        mock_meipass = "/mock/meipass/dir"
        with patch.object(sys, "frozen", True, create=True), \
             patch.object(sys, "_MEIPASS", mock_meipass, create=True):
            path = resource_path("frontend/index.html")
            expected = os.path.join(mock_meipass, "frontend/index.html")
            self.assertEqual(path, expected)

    def test_user_data_dir_win32(self):
        with patch("sys.platform", "win32"), \
             patch.dict(os.environ, {"LOCALAPPDATA": "/mock/localappdata"}):
            path = user_data_dir()
            self.assertTrue(path.startswith("/mock/localappdata"))
            self.assertIn("PhotoBridge", path)

    def test_user_data_dir_non_win32(self):
        with patch("sys.platform", "darwin"), \
             patch("os.path.expanduser", return_value="/mock/home"):
            path = user_data_dir()
            self.assertTrue(path.startswith("/mock/home"))
            self.assertIn("PhotoBridge", path)

    def test_project_root_dev(self):
        with patch.object(sys, "frozen", False, create=True):
            root = project_root()
            self.assertTrue(os.path.isdir(root))
            self.assertTrue(os.path.exists(os.path.join(root, "requirements.txt")))

    def test_project_root_frozen(self):
        mock_exe = os.path.abspath("/mock/install/dir/PhotoBridge.exe")
        with patch.object(sys, "frozen", True, create=True), \
             patch.object(sys, "executable", mock_exe, create=True):
            root = project_root()
            self.assertEqual(root, os.path.dirname(mock_exe))
