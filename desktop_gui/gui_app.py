import sys
import os
import subprocess
import socket
import threading
import time
import tkinter as tk
from tkinter import messagebox, filedialog

# Setup system paths for backend imports
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
backend_path = os.path.join(project_root, "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Design Tokens (Harmonious Dark Theme)
BG_COLOR = "#000000"
CARD_BG = "#1c1c1e"
TEXT_COLOR = "#ffffff"
TEXT_MUTED = "#8e8e93"
BLUE_COLOR = "#0a84ff"
BLUE_HOVER = "#359aff"
RED_COLOR = "#ff453a"
RED_HOVER = "#ff6961"
GREEN_COLOR = "#30d158"
YELLOW_COLOR = "#ffd60a"
BORDER_COLOR = "#2c2c2e"

class PhotoBridgeGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PhotoBridge Control Center")
        self.root.geometry("480x620")
        self.root.configure(bg=BG_COLOR)
        self.root.resizable(True, True)
        self.root.minsize(440, 560)
        
        # Center the window on screen
        self.center_window()

        self.server_process = None
        self.server_running = False
        self.firewall_active = False

        self.create_widgets()
        
        # Intercept window close to clean up background processes
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Start periodic status checker loop
        self.update_status_loop()

    def center_window(self):
        self.root.update_idletasks()
        width = 480
        height = 620
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def create_widgets(self):
        # 1. Header Section
        header_frame = tk.Frame(self.root, bg=BG_COLOR, padx=20, pady=10)
        header_frame.pack(fill="x")
        header_frame.bind("<Configure>", self.on_configure_header)
        
        title_label = tk.Label(
            header_frame, 
            text="PhotoBridge", 
            font=("Segoe UI", 18, "bold"), 
            fg=TEXT_COLOR, 
            bg=BG_COLOR
        )
        title_label.pack(anchor="w")
        
        self.subtitle_label = tk.Label(
            header_frame, 
            text="Local Network Photo Browser for iOS", 
            font=("Segoe UI", 10), 
            fg=TEXT_MUTED, 
            bg=BG_COLOR
        )
        self.subtitle_label.pack(anchor="w")

        # 2. Status Dashboard Card
        self.status_card = tk.Frame(self.root, bg=CARD_BG, bd=1, highlightbackground=BORDER_COLOR, highlightthickness=1)
        self.status_card.pack(fill="both", expand=True, padx=20, pady=5)
        
        # Inner padding frame
        self.status_inner = tk.Frame(self.status_card, bg=CARD_BG, padx=15, pady=15)
        self.status_inner.pack(fill="both", expand=True)
        self.status_inner.bind("<Configure>", self.on_configure_status_inner)

        # Firewall status line
        fw_title = tk.Label(self.status_inner, text="Windows Firewall Inbound Rule", font=("Segoe UI", 9), fg=TEXT_MUTED, bg=CARD_BG)
        fw_title.pack(anchor="w", pady=(0, 2))
        
        self.fw_val = tk.Label(self.status_inner, text="Checking...", font=("Segoe UI", 11, "bold"), fg=YELLOW_COLOR, bg=CARD_BG)
        self.fw_val.pack(anchor="w", pady=(0, 12))

        # Server status line
        srv_title = tk.Label(self.status_inner, text="PhotoBridge Server Status", font=("Segoe UI", 9), fg=TEXT_MUTED, bg=CARD_BG)
        srv_title.pack(anchor="w", pady=(0, 2))
        
        self.srv_val = tk.Label(self.status_inner, text="Stopped", font=("Segoe UI", 11, "bold"), fg=RED_COLOR, bg=CARD_BG)
        self.srv_val.pack(anchor="w", pady=(0, 12))

        # Photos folder line
        dir_title = tk.Label(self.status_inner, text="Photos Folder Directory", font=("Segoe UI", 9), fg=TEXT_MUTED, bg=CARD_BG)
        dir_title.pack(anchor="w", pady=(0, 2))

        # Horizontal row containing the folder path and a Change button
        dir_row = tk.Frame(self.status_inner, bg=CARD_BG)
        dir_row.pack(anchor="w", fill="x", pady=(0, 12))

        self.dir_val = tk.Label(dir_row, text="Not Configured", font=("Segoe UI", 10, "bold"), fg=TEXT_COLOR, bg=CARD_BG, justify="left", anchor="w")
        self.dir_val.pack(side="left", fill="x", expand=True)

        self.btn_change_dir = tk.Button(
            dir_row,
            text="Change...",
            command=self.choose_directory,
            bg=BORDER_COLOR,
            fg=TEXT_COLOR,
            activebackground="#3a3a3c",
            activeforeground=TEXT_COLOR,
            font=("Segoe UI", 8, "bold"),
            bd=0,
            relief="flat",
            padx=8,
            pady=2,
            cursor="hand2"
        )
        self.btn_change_dir.pack(side="right", padx=(10, 0))
        self.btn_change_dir.bind("<Enter>", lambda e: self.btn_change_dir.configure(bg="#3a3a3c"))
        self.btn_change_dir.bind("<Leave>", lambda e: self.btn_change_dir.configure(bg=BORDER_COLOR))

        # Connection URLs Info
        self.url_label = tk.Label(
            self.status_inner, 
            text="Launch the server to get local Wi-Fi addresses.", 
            font=("Segoe UI", 9, "italic"), 
            fg=TEXT_MUTED, 
            bg=CARD_BG,
            justify="left"
        )
        self.url_label.pack(anchor="w", fill="x", pady=(8, 0))

        # 3. Control Panel Buttons Frame (anchored to bottom)
        btn_frame = tk.Frame(self.root, bg=BG_COLOR, padx=20, pady=10)
        btn_frame.pack(fill="x", side="bottom")

        # Custom Hover Action Buttons Helper
        def make_flat_btn(parent, text, command, bg_color, hover_color):
            btn = tk.Button(
                parent, 
                text=text, 
                command=command,
                bg=bg_color, 
                fg="#ffffff", 
                activebackground=hover_color, 
                activeforeground="#ffffff",
                font=("Segoe UI", 10, "bold"),
                bd=0, 
                relief="flat", 
                cursor="hand2",
                pady=8
            )
            btn.bind("<Enter>", lambda e: btn.configure(bg=hover_color) if btn["state"] != "disabled" else None)
            btn.bind("<Leave>", lambda e: btn.configure(bg=bg_color) if btn["state"] != "disabled" else None)
            return btn

        # Setup rule button
        self.btn_setup = make_flat_btn(btn_frame, "1. Configure Firewall Rule (One-Time)", self.run_setup, BLUE_COLOR, BLUE_HOVER)
        self.btn_setup.pack(fill="x", pady=6)

        # Run server button
        self.btn_run = make_flat_btn(btn_frame, "2. Start PhotoBridge Server", self.toggle_server, GREEN_COLOR, "#34c759")
        self.btn_run.pack(fill="x", pady=6)

        # Uninstall rule button
        self.btn_uninstall = make_flat_btn(btn_frame, "3. Remove Firewall Rule", self.run_uninstall, CARD_BG, "#2c2c2e")
        self.btn_uninstall.pack(fill="x", pady=6)

    def on_configure_header(self, event):
        wrap_width = event.width - 40
        if wrap_width > 100:
            self.subtitle_label.configure(wraplength=wrap_width)

    def on_configure_status_inner(self, event):
        wrap_width = event.width - 30
        if wrap_width > 100:
            self.url_label.configure(wraplength=wrap_width)
            self.dir_val.configure(wraplength=wrap_width - 80)

    def check_firewall(self) -> bool:
        """Query firewall database for Port 8000 rule using netsh (non-admin friendly)."""
        try:
            res = subprocess.run(
                'netsh advfirewall firewall show rule name="PhotoBridge Port 8000"',
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return res.returncode == 0
        except Exception:
            return False

    def update_status_loop(self):
        """Periodically runs in the GUI thread to verify state and update buttons."""
        self.firewall_active = self.check_firewall()

        # Detect externally-killed server (e.g. taskkill or crash)
        if self.server_running and self.server_process and self.server_process.poll() is not None:
            self.server_process = None
            self.server_running = False
            self.on_server_stopped()

        # Update Firewall Status GUI
        if self.firewall_active:
            self.fw_val.configure(text="ACTIVE (Port 8000)", fg=GREEN_COLOR)
            self.btn_setup.configure(state="disabled", text="1. Configured Successfully ✓", bg=BORDER_COLOR)
            self.btn_uninstall.configure(state="normal", bg=CARD_BG)

            # If server isn't running, run button is ready
            if not self.server_running:
                self.btn_run.configure(state="normal", text="2. Start PhotoBridge Server", bg=GREEN_COLOR)
        else:
            self.fw_val.configure(text="MISSING (Inbound Blocked)", fg=YELLOW_COLOR)
            self.btn_setup.configure(state="normal", text="1. Configure Firewall Rule (One-Time)", bg=BLUE_COLOR)
            self.btn_uninstall.configure(state="disabled", bg=BORDER_COLOR)

            # Server cannot be started safely without firewall rule
            if not self.server_running:
                self.btn_run.configure(state="disabled", text="2. Start Server (Setup Firewall First)", bg=BORDER_COLOR)

        # Update photos directory label
        self.update_folder_label()

        # Reschedule check in 1.5 seconds
        self.root.after(1500, self.update_status_loop)

    def update_folder_label(self):
        """Read config.json and update the directory label text in the GUI."""
        try:
            from app.config import get_config
            config = get_config()
            folder = config.get("photos_dir")
            if folder:
                self.dir_val.configure(text=folder, fg=TEXT_COLOR)
            else:
                self.dir_val.configure(text="Not Configured", fg=RED_COLOR)
        except Exception:
            self.dir_val.configure(text="Error Loading Config", fg=RED_COLOR)

    def choose_directory(self):
        """Open a native Windows folder selector, write the path to config, and sync the server."""
        selected_dir = filedialog.askdirectory(title="Select Photos Folder")
        if not selected_dir:
            return

        selected_dir = os.path.abspath(selected_dir)

        # Disable the button immediately so the user can't double-click
        self.btn_change_dir.configure(state="disabled", text="Updating...")

        if self.server_running:
            # Run the HTTP call in a background thread so the UI stays responsive
            def update_via_api():
                import urllib.request
                import json
                from app.config import get_port_from_env, get_config
                port = get_port_from_env()
                try:
                    config = get_config()
                    headers = {'Content-Type': 'application/json'}
                    if config.get("pin_required") and config.get("access_pin"):
                        headers['X-PhotoBridge-PIN'] = config["access_pin"]

                    payload = json.dumps({"photos_dir": selected_dir}).encode()
                    req = urllib.request.Request(
                        f"http://localhost:{port}/api/config",
                        data=payload,
                        headers=headers,
                        method='POST'
                    )
                    with urllib.request.urlopen(req, timeout=5) as resp:
                        pass
                    # Back on main thread: update UI
                    self.root.after(0, lambda: self._on_dir_updated(selected_dir))
                except OSError:
                    # Connection refused — server died externally, fall back to direct write
                    try:
                        from app.config import set_photos_dir
                        set_photos_dir(selected_dir)
                        self.root.after(0, lambda: self._on_dir_updated(selected_dir))
                    except Exception as e2:
                        self.root.after(0, lambda: self._on_dir_update_failed(str(e2)))
                except Exception as e:
                    self.root.after(0, lambda: self._on_dir_update_failed(str(e)))

            threading.Thread(target=update_via_api, daemon=True).start()
        else:
            # Run the file write in a background thread too, for safety
            def save_to_config():
                try:
                    from app.config import set_photos_dir
                    set_photos_dir(selected_dir)
                    self.root.after(0, lambda: self._on_dir_updated(selected_dir))
                except Exception as e:
                    self.root.after(0, lambda: self._on_dir_update_failed(str(e)))

            threading.Thread(target=save_to_config, daemon=True).start()

    def _on_dir_updated(self, selected_dir):
        """Called on main thread after a successful directory update."""
        self.btn_change_dir.configure(state="normal", text="Change...")
        self.update_folder_label()
        messagebox.showinfo("Success", f"Photos folder updated:\n{selected_dir}")

    def _on_dir_update_failed(self, error_msg):
        """Called on main thread after a failed directory update."""
        self.btn_change_dir.configure(state="normal", text="Change...")
        messagebox.showerror("Error", f"Failed to update folder:\n{error_msg}")

    def run_setup(self):
        """Execute elevated setup powershell command in background (window hidden)."""
        def run():
            ps_cmd = (
                "if (-not (Get-NetFirewallRule -DisplayName ''PhotoBridge Port 8000'' -ErrorAction SilentlyContinue)) { "
                "New-NetFirewallRule -DisplayName ''PhotoBridge Port 8000'' -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow -Profile Private "
                "}"
            )
            cmd = [
                "powershell",
                "-Command",
                f"Start-Process powershell -ArgumentList '-NoProfile -WindowStyle Hidden -Command \"{ps_cmd}\"' -Verb RunAs -Wait"
            ]
            try:
                subprocess.run(cmd, check=True)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to configure firewall: {e}")
        
        threading.Thread(target=run, daemon=True).start()

    def run_uninstall(self):
        """Execute elevated uninstall powershell command in background (window hidden)."""
        if self.server_running:
            if messagebox.askyesno("Confirmation", "Server is running. Stopping the server first is recommended. Proceed?"):
                self.toggle_server()
            else:
                return

        def run():
            ps_cmd = (
                "if (Get-NetFirewallRule -DisplayName ''PhotoBridge Port 8000'' -ErrorAction SilentlyContinue) { "
                "Remove-NetFirewallRule -DisplayName ''PhotoBridge Port 8000'' "
                "}"
            )
            cmd = [
                "powershell",
                "-Command",
                f"Start-Process powershell -ArgumentList '-NoProfile -WindowStyle Hidden -Command \"{ps_cmd}\"' -Verb RunAs -Wait"
            ]
            try:
                subprocess.run(cmd, check=True)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to remove firewall: {e}")
        
        threading.Thread(target=run, daemon=True).start()

    def toggle_server(self):
        """Start or stop the server process."""
        if self.server_running:
            # Stop the server
            self.srv_val.configure(text="Stopping...", fg=YELLOW_COLOR)
            self.btn_run.configure(state="disabled")
            
            def stop():
                try:
                    if self.server_process:
                        # Send \n to run.py's stdin to stop uvicorn cleanly
                        self.server_process.communicate(input="\n", timeout=4)
                except Exception:
                    if self.server_process:
                        self.server_process.kill()
                finally:
                    self.server_process = None
                    self.server_running = False
                    
                    # Run on main thread
                    self.root.after(0, self.on_server_stopped)
            
            threading.Thread(target=stop, daemon=True).start()
        else:
            # Start the server
            self.srv_val.configure(text="Starting...", fg=YELLOW_COLOR)
            self.btn_run.configure(state="disabled")
            
            def start():
                try:
                    python_exe = os.path.join(".venv", "Scripts", "python.exe")
                    if not os.path.exists(python_exe):
                        python_exe = "python"
                        
                    creationflags = 0
                    if sys.platform == "win32":
                        creationflags = subprocess.CREATE_NO_WINDOW

                    self.server_process = subprocess.Popen(
                        [python_exe, os.path.join("backend", "run.py")],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        creationflags=creationflags
                    )
                    
                    # Start stdout/stderr drain threads to prevent OS buffer locks
                    threading.Thread(target=self.drain_stream, args=(self.server_process.stdout,), daemon=True).start()
                    threading.Thread(target=self.drain_stream, args=(self.server_process.stderr,), daemon=True).start()
                    
                    # Give it a second to start
                    time.sleep(1.2)
                    
                    self.server_running = True
                    self.root.after(0, self.on_server_started)
                except Exception as e:
                    self.server_running = False
                    self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to start server: {e}"))
                    self.root.after(0, self.on_server_stopped)
            
            threading.Thread(target=start, daemon=True).start()

    def drain_stream(self, stream):
        """Continuously reads from stream to keep buffers clear."""
        try:
            while True:
                line = stream.readline()
                if not line:
                    break
        except Exception:
            pass

    def on_server_started(self):
        """Update interface when server starts running."""
        self.srv_val.configure(text="RUNNING", fg=GREEN_COLOR)
        self.btn_run.configure(state="normal", text="2. Stop PhotoBridge Server", bg=RED_COLOR)
        
        # Get LAN IP
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            lan_ip = s.getsockname()[0]
            s.close()
        except Exception:
            lan_ip = "127.0.0.1"

        from app.config import get_port_from_env
        port = get_port_from_env()

        self.url_label.configure(
            text=f"Local:   http://localhost:{port}\nPhone:  http://{lan_ip}:{port}   (same Wi-Fi)",
            fg=TEXT_COLOR
        )
        # Lock uninstall button when server runs
        self.btn_uninstall.configure(state="disabled", bg=BORDER_COLOR)

    def on_server_stopped(self):
        """Update interface when server finishes stopping."""
        self.srv_val.configure(text="Stopped", fg=RED_COLOR)
        self.btn_run.configure(state="normal", text="2. Start PhotoBridge Server", bg=GREEN_COLOR)
        self.url_label.configure(
            text="Server is offline.",
            fg=TEXT_MUTED
        )
        if self.firewall_active:
            self.btn_uninstall.configure(state="normal", bg=CARD_BG)

    def on_closing(self):
        """Clean closure of application, terminating background server tasks."""
        if self.server_running:
            # Stop server synchronously on close
            try:
                if self.server_process:
                    self.server_process.communicate(input="\n", timeout=2)
            except Exception:
                if self.server_process:
                    self.server_process.kill()
        self.root.destroy()

if __name__ == "__main__":
    # Ensure working directory is the project directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    os.chdir(project_root)

    root = tk.Tk()
    app = PhotoBridgeGUI(root)
    root.mainloop()
