import os
import re

def sync():
    # 1. Read VERSION file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    version_file = os.path.join(project_root, "VERSION")
    
    if not os.path.exists(version_file):
        with open(version_file, "w") as f:
            f.write("1.0.2\n")
            
    with open(version_file, "r") as f:
        version = f.read().strip()
        
    print(f"Syncing version: {version}")
    
    # 2. Update pyproject.toml
    toml_path = os.path.join(project_root, "pyproject.toml")
    if os.path.exists(toml_path):
        with open(toml_path, "r", encoding="utf-8") as f:
            content = f.read()
        content = re.sub(r'version\s*=\s*["\'][^"\']+["\']', f'version = "{version}"', content)
        with open(toml_path, "w", encoding="utf-8", newline='\n') as f:
            f.write(content)
            
    # 3. Update installer/PhotoBridge.iss
    iss_path = os.path.join(project_root, "installer", "PhotoBridge.iss")
    if os.path.exists(iss_path):
        with open(iss_path, "r", encoding="utf-8") as f:
            content = f.read()
        content = re.sub(r'#define\s+MyAppVersion\s+["\'][^"\']+["\']', f'#define MyAppVersion "{version}"', content)
        with open(iss_path, "w", encoding="utf-8", newline='\r\n') as f:
            f.write(content)

if __name__ == "__main__":
    sync()
