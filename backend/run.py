"""
Entry point for PhotoBridge.
Starts uvicorn server bound to 0.0.0.0 in a background thread
so phones on the LAN can reach it, while allowing the user to
stop the server easily by pressing ENTER.
"""

import threading
import uvicorn
import time
import sys
from app.config import get_port_from_env, get_config
from app.main import get_lan_ip

class UvicornServerThread(threading.Thread):
    def __init__(self, host: str, port: int):
        super().__init__()
        self.daemon = True
        self.config = uvicorn.Config(
            "app.main:app",
            host=host,
            port=port,
            reload=False,
            log_level="warning"
        )
        self.server = uvicorn.Server(self.config)

    def run(self):
        try:
            self.server.run()
        except Exception as e:
            print(f"\n[ERROR] Server error: {e}")

    def stop(self):
        self.server.should_exit = True

if __name__ == "__main__":
    port = get_port_from_env()
    config = get_config()
    lan_ip = get_lan_ip()

    # Create and start server in background thread
    server_thread = UvicornServerThread("0.0.0.0", port)
    server_thread.start()

    # Small delay to let uvicorn initialize
    time.sleep(1.5)

    photos_folder_status = (
        "not yet configured — open the app and complete setup"
        if not config["configured"]
        else f"{config['photos_dir']}"
    )

    print("\n" + "=" * 70)
    print("PhotoBridge running!")
    print(f"Local:  http://localhost:{port}")
    print(f"Phone:  http://{lan_ip}:{port}   (same WiFi)")
    print(f"Photos folder: {photos_folder_status}")
    print("=" * 70 + "\n")

    print(">>> TO STOP THE SERVER: Press [ENTER] key in this window at any time. <<<\n")
    
    try:
        # Block main thread until user presses Enter
        input()
    except (KeyboardInterrupt, EOFError):
        # Handle Ctrl+C or closed stdin streams
        pass

    print("\nStopping PhotoBridge server...")
    server_thread.stop()
    server_thread.join(timeout=5.0)
    print("PhotoBridge stopped. You can close this window now.")
