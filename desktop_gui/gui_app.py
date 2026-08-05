import sys
import os
import subprocess
import socket
import threading
import time
import tkinter as tk
from tkinter import messagebox, filedialog

# Setup system paths for backend imports (works in both dev and frozen mode)
if getattr(sys, "frozen", False):
    # PyInstaller frozen mode: bundled files are in sys._MEIPASS
    _base = sys._MEIPASS
    backend_path = os.path.join(_base, "backend")
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)
    if _base not in sys.path:
        sys.path.insert(0, _base)
else:
    # Development mode: navigate from desktop_gui/ to project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    backend_path = os.path.join(project_root, "backend")
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)

# ───────────────────────────────────────────────────
# Design Tokens — Premium Dark Navy Theme (v2)
# ───────────────────────────────────────────────────
BG_DEEP        = "#0b1929"
SIDEBAR_BG     = "#091422"
MAIN_BG        = "#0e1e35"
CARD_BG        = "#132d4f"
CARD_BORDER    = "#1c3d5e"
TEXT_WHITE     = "#ffffff"
TEXT_COLOR     = "#d4dde8"
TEXT_MUTED     = "#5d7a96"
GREEN_COLOR    = "#30d158"
GREEN_BTN      = "#2dd464"
GREEN_BTN_HVR  = "#28b857"
RED_COLOR      = "#ff453a"
YELLOW_COLOR   = "#ffd60a"
BLUE_COLOR     = "#0a84ff"
BTN_DARK_BG    = "#0f1d33"
BTN_DARK_HVR   = "#162a45"
DISABLED_BG    = "#1a2a3e"
DISABLED_FG    = "#3d5570"
ACCENT_BAR     = "#1478c8"


class PhotoBridgeGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PhotoBridge Control Center")

        # Set window icon
        try:
            from app.paths import resource_path
            icon_path = resource_path(os.path.join("desktop_gui", "icon.ico"))
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception:
            pass

        self.root.geometry("850x560")
        self.root.configure(bg=BG_DEEP)
        self.root.resizable(True, True)
        self.root.minsize(850, 560)

        self.center_window()

        self.server_process = None
        self.server_running = False
        self.firewall_active = False

        # URL values for copy-to-clipboard
        self.url_local = ""
        self.url_phone = ""
        self.url_easy = ""

        # Track which bottom-left button is showing
        self._showing_setup_btn = True

        self.create_widgets()

        # Intercept window close to clean up background processes
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Start periodic status checker loop
        self.update_status_loop()

    def center_window(self):
        self.root.update_idletasks()
        width = 850
        height = 560
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    # ──────────────────────────────────────────────
    # Widget Construction
    # ──────────────────────────────────────────────
    def create_widgets(self):
        # ═══════════════════════════════════════════
        # LEFT SIDEBAR
        # ═══════════════════════════════════════════
        sidebar = tk.Frame(self.root, bg=SIDEBAR_BG, width=165)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # ── Power Icon ──
        power_pad = tk.Frame(sidebar, bg=SIDEBAR_BG)
        power_pad.pack(fill="x", pady=(24, 14))

        self.power_canvas = tk.Canvas(
            power_pad, width=56, height=56,
            bg=SIDEBAR_BG, highlightthickness=0
        )
        self.power_canvas.pack(anchor="center")

        self.power_circle = self.power_canvas.create_oval(
            8, 8, 48, 48, outline=GREEN_COLOR, width=2.5
        )
        self.power_line = self.power_canvas.create_line(
            28, 4, 28, 24, fill=GREEN_COLOR, width=2.5
        )

        # ── Server Status ──
        srv_frame = tk.Frame(sidebar, bg=SIDEBAR_BG, padx=16)
        srv_frame.pack(fill="x", pady=(4, 0))

        srv_dot_row = tk.Frame(srv_frame, bg=SIDEBAR_BG)
        srv_dot_row.pack(anchor="w")

        self.srv_dot = tk.Canvas(
            srv_dot_row, width=10, height=10,
            bg=SIDEBAR_BG, highlightthickness=0
        )
        self.srv_dot.pack(side="left", padx=(0, 6), pady=3)
        self.srv_dot_id = self.srv_dot.create_oval(1, 1, 9, 9, fill=RED_COLOR, outline="")

        tk.Label(
            srv_dot_row, text="Server Status:",
            font=("Segoe UI", 8), fg=TEXT_MUTED, bg=SIDEBAR_BG
        ).pack(side="left")

        self.srv_val = tk.Label(
            srv_frame, text="Stopped",
            font=("Segoe UI", 9, "bold"), fg=RED_COLOR,
            bg=SIDEBAR_BG, anchor="w"
        )
        self.srv_val.pack(anchor="w", padx=(16, 0))

        # ── Firewall Status ──
        fw_frame = tk.Frame(sidebar, bg=SIDEBAR_BG, padx=16)
        fw_frame.pack(fill="x", pady=(12, 0))

        fw_dot_row = tk.Frame(fw_frame, bg=SIDEBAR_BG)
        fw_dot_row.pack(anchor="w")

        self.fw_dot = tk.Canvas(
            fw_dot_row, width=10, height=10,
            bg=SIDEBAR_BG, highlightthickness=0
        )
        self.fw_dot.pack(side="left", padx=(0, 6), pady=3)
        self.fw_dot_id = self.fw_dot.create_oval(1, 1, 9, 9, fill=YELLOW_COLOR, outline="")

        tk.Label(
            fw_dot_row, text="Firewall Rule:",
            font=("Segoe UI", 8), fg=TEXT_MUTED, bg=SIDEBAR_BG
        ).pack(side="left")

        self.fw_val = tk.Label(
            fw_frame, text="Checking...",
            font=("Segoe UI", 9, "bold"), fg=YELLOW_COLOR,
            bg=SIDEBAR_BG, anchor="w"
        )
        self.fw_val.pack(anchor="w", padx=(16, 0))

        # ── Spacer ──
        tk.Frame(sidebar, bg=SIDEBAR_BG).pack(fill="both", expand=True)

        # ── Sidebar Bottom Buttons ──
        sidebar_btns = tk.Frame(sidebar, bg=SIDEBAR_BG, padx=8, pady=12)
        sidebar_btns.pack(fill="x", side="bottom")

        # Check for Updates (with left accent bar)
        upd_wrap = tk.Frame(sidebar_btns, bg=ACCENT_BAR)
        upd_wrap.pack(fill="x", pady=(0, 6))

        self.btn_update = tk.Button(
            upd_wrap, text="\u21bb  Check for Updates",
            command=self.check_for_updates,
            bg=BTN_DARK_BG, fg=TEXT_COLOR,
            activebackground=BTN_DARK_HVR, activeforeground=TEXT_WHITE,
            font=("Segoe UI", 8), bd=0, relief="flat",
            cursor="hand2", pady=7, padx=10, anchor="w"
        )
        self.btn_update.pack(fill="both", expand=True, padx=(3, 0))
        self.btn_update.bind("<Enter>", lambda e: self.btn_update.configure(bg=BTN_DARK_HVR) if str(self.btn_update["state"]) != "disabled" else None)
        self.btn_update.bind("<Leave>", lambda e: self.btn_update.configure(bg=BTN_DARK_BG) if str(self.btn_update["state"]) != "disabled" else None)

        # View Server Logs (with left accent bar)
        log_wrap = tk.Frame(sidebar_btns, bg=ACCENT_BAR)
        log_wrap.pack(fill="x")

        self.btn_logs = tk.Button(
            log_wrap, text="View Server Logs",
            command=self.open_logs_window,
            bg=BTN_DARK_BG, fg=TEXT_COLOR,
            activebackground=BTN_DARK_HVR, activeforeground=TEXT_WHITE,
            font=("Segoe UI", 8), bd=0, relief="flat",
            cursor="hand2", pady=7, padx=10, anchor="w"
        )
        self.btn_logs.pack(fill="both", expand=True, padx=(3, 0))
        self.btn_logs.bind("<Enter>", lambda e: self.btn_logs.configure(bg=BTN_DARK_HVR))
        self.btn_logs.bind("<Leave>", lambda e: self.btn_logs.configure(bg=BTN_DARK_BG))

        # ═══════════════════════════════════════════
        # RIGHT MAIN CONTENT AREA
        # ═══════════════════════════════════════════
        main_frame = tk.Frame(self.root, bg=MAIN_BG)
        main_frame.pack(side="left", fill="both", expand=True)

        content = tk.Frame(main_frame, bg=MAIN_BG, padx=24, pady=18)
        content.pack(fill="both", expand=True)

        # ── Photos Folder Directory Card ──
        photos_card = tk.Frame(
            content, bg=CARD_BG,
            highlightbackground=CARD_BORDER, highlightthickness=1
        )
        photos_card.pack(fill="x", pady=(0, 14))

        photos_inner = tk.Frame(photos_card, bg=CARD_BG, padx=20, pady=16)
        photos_inner.pack(fill="x")

        tk.Label(
            photos_inner, text="Photos Folder Directory",
            font=("Segoe UI", 14, "bold"), fg=TEXT_WHITE, bg=CARD_BG
        ).pack(anchor="w", pady=(0, 12))

        dir_row = tk.Frame(photos_inner, bg=CARD_BG)
        dir_row.pack(fill="x")
        dir_row.bind("<Configure>", self._on_dir_row_configure)

        self.dir_val = tk.Label(
            dir_row, text="Not Configured",
            font=("Segoe UI", 10), fg=TEXT_COLOR, bg=CARD_BG,
            anchor="w", justify="left"
        )
        self.dir_val.pack(side="left", fill="x", expand=True)

        self.btn_change_dir = tk.Button(
            dir_row, text="Change",
            command=self.choose_directory,
            bg=BTN_DARK_BG, fg=TEXT_COLOR,
            activebackground=BTN_DARK_HVR, activeforeground=TEXT_WHITE,
            font=("Segoe UI", 9, "bold"), bd=1, relief="solid",
            padx=18, pady=5, cursor="hand2",
            highlightbackground=CARD_BORDER
        )
        self.btn_change_dir.pack(side="right", padx=(12, 0))
        self.btn_change_dir.bind("<Enter>", lambda e: self.btn_change_dir.configure(bg=BTN_DARK_HVR))
        self.btn_change_dir.bind("<Leave>", lambda e: self.btn_change_dir.configure(bg=BTN_DARK_BG))

        # ── Connection URLs Card ──
        urls_card = tk.Frame(
            content, bg=CARD_BG,
            highlightbackground=CARD_BORDER, highlightthickness=1
        )
        urls_card.pack(fill="x", pady=(0, 14))

        urls_inner = tk.Frame(urls_card, bg=CARD_BG, padx=20, pady=16)
        urls_inner.pack(fill="x")

        tk.Label(
            urls_inner, text="Connection URLs",
            font=("Segoe UI", 14, "bold"), fg=TEXT_WHITE, bg=CARD_BG
        ).pack(anchor="w", pady=(0, 12))

        # Placeholder text (visible when server is off)
        self.urls_placeholder = tk.Label(
            urls_inner,
            text="Launch the server to get local Wi\u2011Fi addresses.",
            font=("Segoe UI", 9, "italic"), fg=TEXT_MUTED, bg=CARD_BG,
            anchor="w", justify="left"
        )
        self.urls_placeholder.pack(anchor="w", fill="x")

        # URL rows frame (visible when server is running)
        self.urls_rows_frame = tk.Frame(urls_inner, bg=CARD_BG)
        # Not packed yet — shown by on_server_started

        self._make_url_row(self.urls_rows_frame, "Local:", 0)
        self._make_url_row(self.urls_rows_frame, "Phone:", 1)
        self._make_url_row(self.urls_rows_frame, "Easy:", 2)

        # Spacer to push bottom bar down
        tk.Frame(content, bg=MAIN_BG).pack(fill="both", expand=True)

        # ── Bottom Action Bar ──
        bottom_bar = tk.Frame(main_frame, bg=MAIN_BG, padx=24, pady=14)
        bottom_bar.pack(fill="x", side="bottom")

        # Left button area (setup / uninstall — only one shown at a time)
        self.left_btn_area = tk.Frame(bottom_bar, bg=MAIN_BG)
        self.left_btn_area.pack(side="left")

        self.btn_setup = tk.Button(
            self.left_btn_area, text="\U0001f6e1  Configure Firewall Rule",
            command=self.run_setup,
            bg=BTN_DARK_BG, fg=TEXT_COLOR,
            activebackground=BTN_DARK_HVR, activeforeground=TEXT_WHITE,
            font=("Segoe UI", 9, "bold"), bd=1, relief="solid",
            cursor="hand2", padx=14, pady=9,
            highlightbackground=CARD_BORDER
        )
        self.btn_setup.pack(fill="x")
        self.btn_setup.bind("<Enter>", lambda e: self.btn_setup.configure(bg=BTN_DARK_HVR) if str(self.btn_setup["state"]) != "disabled" else None)
        self.btn_setup.bind("<Leave>", lambda e: self.btn_setup.configure(bg=BTN_DARK_BG) if str(self.btn_setup["state"]) != "disabled" else None)

        self.btn_uninstall = tk.Button(
            self.left_btn_area, text="\U0001f5d1  Remove Firewall Rule",
            command=self.run_uninstall,
            bg=BTN_DARK_BG, fg=TEXT_COLOR,
            activebackground=BTN_DARK_HVR, activeforeground=TEXT_WHITE,
            font=("Segoe UI", 9, "bold"), bd=1, relief="solid",
            cursor="hand2", padx=14, pady=9,
            highlightbackground=CARD_BORDER
        )
        # Not packed — shown by update_status_loop when firewall is active
        self.btn_uninstall.bind("<Enter>", lambda e: self.btn_uninstall.configure(bg=BTN_DARK_HVR) if str(self.btn_uninstall["state"]) != "disabled" else None)
        self.btn_uninstall.bind("<Leave>", lambda e: self.btn_uninstall.configure(bg=BTN_DARK_BG) if str(self.btn_uninstall["state"]) != "disabled" else None)

        # Start / Stop server button (right side, large green)
        self.btn_run = tk.Button(
            bottom_bar, text="\u25b6  Start PhotoBridge Server",
            command=self.toggle_server,
            bg=GREEN_BTN, fg="#0a1628",
            activebackground=GREEN_BTN_HVR, activeforeground="#0a1628",
            font=("Segoe UI", 10, "bold"), bd=0, relief="flat",
            cursor="hand2", padx=24, pady=9
        )
        self.btn_run.pack(side="right", fill="x", expand=True, padx=(14, 0))
        self.btn_run.bind("<Enter>", lambda e: self.btn_run.configure(bg=GREEN_BTN_HVR) if str(self.btn_run["state"]) != "disabled" else None)
        self.btn_run.bind("<Leave>", lambda e: self._restore_run_btn_bg())

    # ──────────────────────────────────────────────
    # Widget Helpers
    # ──────────────────────────────────────────────
    def _make_url_row(self, parent, label_text, index):
        """Build a single URL row inside the urls_rows_frame."""
        if index > 0:
            tk.Frame(parent, bg=CARD_BORDER, height=1).pack(fill="x", pady=4)

        row = tk.Frame(parent, bg=CARD_BG)
        row.pack(fill="x", pady=2)

        tk.Label(
            row, text=label_text, font=("Segoe UI", 10),
            fg=TEXT_MUTED, bg=CARD_BG, width=7, anchor="w"
        ).pack(side="left")

        url_lbl = tk.Label(
            row, text="\u2014", font=("Segoe UI", 10),
            fg=TEXT_COLOR, bg=CARD_BG, anchor="w"
        )
        url_lbl.pack(side="left", fill="x", expand=True, padx=(4, 0))

        copy_btn = tk.Button(
            row, text="\u29c9", font=("Segoe UI", 12),
            bg=CARD_BG, fg=TEXT_MUTED,
            activebackground=CARD_BORDER, activeforeground=TEXT_WHITE,
            bd=0, relief="flat", cursor="hand2", padx=6, pady=0
        )
        copy_btn.pack(side="right")
        copy_btn.bind("<Enter>", lambda e: copy_btn.configure(fg=TEXT_WHITE))
        copy_btn.bind("<Leave>", lambda e: copy_btn.configure(fg=TEXT_MUTED))

        if index == 0:
            self.url_local_lbl = url_lbl
            copy_btn.configure(command=lambda: self.copy_to_clipboard(self.url_local))
        elif index == 1:
            self.url_phone_lbl = url_lbl
            copy_btn.configure(command=lambda: self.copy_to_clipboard(self.url_phone))
        else:
            self.url_easy_lbl = url_lbl
            copy_btn.configure(command=lambda: self.copy_to_clipboard(self.url_easy))

    def copy_to_clipboard(self, text):
        """Copy text to the system clipboard using tkinter's built-in API."""
        if text:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)

    def _on_dir_row_configure(self, event):
        """Adjust wraplength for directory label when the row resizes."""
        wrap_w = event.width - 110
        if wrap_w > 100:
            self.dir_val.configure(wraplength=wrap_w)

    def _restore_run_btn_bg(self):
        """Reset the run button colour on mouse leave."""
        if str(self.btn_run["state"]) == "disabled":
            return
        self.btn_run.configure(bg=GREEN_BTN)

    def _swap_left_btn(self, show_setup):
        """Toggle the left bottom-bar button between Configure and Remove."""
        if show_setup and not self._showing_setup_btn:
            self.btn_uninstall.pack_forget()
            self.btn_setup.pack(fill="x")
            self._showing_setup_btn = True
        elif not show_setup and self._showing_setup_btn:
            self.btn_setup.pack_forget()
            self.btn_uninstall.pack(fill="x")
            self._showing_setup_btn = False

    # ──────────────────────────────────────────────
    # Core logic methods
    # ──────────────────────────────────────────────
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
        if self.server_running:
            if getattr(sys, "frozen", False):
                if hasattr(self, 'server_thread') and self.server_thread and not self.server_thread.is_alive():
                    self.server_thread = None
                    self.server_running = False
                    self.on_server_stopped()
            else:
                if self.server_process and self.server_process.poll() is not None:
                    self.server_process = None
                    self.server_running = False
                    self.on_server_stopped()

        # Update Firewall Status GUI
        if self.firewall_active:
            self.fw_val.configure(text="Active", fg=GREEN_COLOR)
            self.fw_dot.itemconfigure(self.fw_dot_id, fill=GREEN_COLOR)

            # Show Remove button, hide Configure button
            self._swap_left_btn(show_setup=False)
            self.btn_uninstall.configure(state="normal")

            # If server isn't running, run button is ready
            if not self.server_running:
                self.btn_run.configure(
                    state="normal",
                    text="\u25b6  Start PhotoBridge Server",
                    bg=GREEN_BTN, fg="#0a1628"
                )
        else:
            self.fw_val.configure(text="Missing", fg=YELLOW_COLOR)
            self.fw_dot.itemconfigure(self.fw_dot_id, fill=YELLOW_COLOR)

            # Show Configure button, hide Remove button
            self._swap_left_btn(show_setup=True)
            self.btn_setup.configure(state="normal")

            # Server cannot be started safely without firewall rule
            if not self.server_running:
                self.btn_run.configure(
                    state="disabled",
                    text="Start Server (Setup Firewall First)",
                    bg=DISABLED_BG, fg=DISABLED_FG
                )

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
        self.btn_change_dir.configure(state="normal", text="Change")
        self.update_folder_label()
        messagebox.showinfo("Success", f"Photos folder updated:\n{selected_dir}")

    def _on_dir_update_failed(self, error_msg):
        """Called on main thread after a failed directory update."""
        self.btn_change_dir.configure(state="normal", text="Change")
        messagebox.showerror("Error", f"Failed to update folder:\n{error_msg}")

    def run_elevated_powershell(self, ps_command: str) -> bool:
        """Runs a PowerShell command elevated (RunAs) using ShellExecuteW."""
        import ctypes
        params = f"-NoProfile -NonInteractive -WindowStyle Hidden -Command \"{ps_command}\""
        try:
            ret = ctypes.windll.shell32.ShellExecuteW(
                None,
                "runas",
                "powershell.exe",
                params,
                None,
                0  # SW_HIDE
            )
            return ret > 32
        except Exception:
            return False

    def run_setup(self):
        """Execute elevated setup powershell command in background (window hidden)."""
        def run():
            ps_cmd = (
                "if (-not (Get-NetFirewallRule -DisplayName 'PhotoBridge Port 8000' -ErrorAction SilentlyContinue)) { "
                "New-NetFirewallRule -DisplayName 'PhotoBridge Port 8000' -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow -Profile Private "
                "}"
            )
            success = self.run_elevated_powershell(ps_cmd)
            if not success:
                messagebox.showerror("Error", "Failed to configure firewall: Permission denied or execution failed.")

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
                "if (Get-NetFirewallRule -DisplayName 'PhotoBridge Port 8000' -ErrorAction SilentlyContinue) { "
                "Remove-NetFirewallRule -DisplayName 'PhotoBridge Port 8000' "
                "}"
            )
            success = self.run_elevated_powershell(ps_cmd)
            if not success:
                messagebox.showerror("Error", "Failed to remove firewall: Permission denied or execution failed.")

        threading.Thread(target=run, daemon=True).start()

    def toggle_server(self):
        """Start or stop the server process."""
        if self.server_running:
            # Stop the server
            self.srv_val.configure(text="Stopping...", fg=YELLOW_COLOR)
            self.srv_dot.itemconfigure(self.srv_dot_id, fill=YELLOW_COLOR)
            self.btn_run.configure(state="disabled", bg=DISABLED_BG, fg=DISABLED_FG)

            def stop():
                try:
                    if hasattr(self, 'server_thread') and self.server_thread:
                        # Frozen mode: stop in-process uvicorn thread
                        self.server_thread.stop()
                        self.server_thread.join(timeout=5.0)
                        self.server_thread = None
                    elif self.server_process:
                        # Dev mode: send \n to run.py's stdin to stop uvicorn cleanly
                        self.server_process.communicate(input="\n", timeout=4)
                except Exception:
                    if self.server_process:
                        self.server_process.kill()
                finally:
                    self.server_process = None
                    self.server_running = False

                    try:
                        from app.media import clear_thumb_cache
                        clear_thumb_cache()
                    except Exception:
                        pass

                    # Run on main thread
                    self.root.after(0, self.on_server_stopped)

            threading.Thread(target=stop, daemon=True).start()
        else:
            # Start the server
            self.srv_val.configure(text="Starting...", fg=YELLOW_COLOR)
            self.srv_dot.itemconfigure(self.srv_dot_id, fill=YELLOW_COLOR)
            self.btn_run.configure(state="disabled", bg=DISABLED_BG, fg=DISABLED_FG)

            def start():
                try:
                    if getattr(sys, "frozen", False):
                        # Frozen mode: run uvicorn in-process as a thread
                        from app.config import get_port_from_env
                        port = get_port_from_env()
                        from run import UvicornServerThread
                        self.server_thread = UvicornServerThread("0.0.0.0", port)
                        self.server_thread.start()
                        time.sleep(1.5)

                        if self.server_thread.error:
                            self.server_running = False
                            self.server_thread = None
                            self.root.after(0, lambda: messagebox.showerror("Startup Error", "Server failed to start. Please wait a few seconds for port 8000 to clear, or check if another app is using port 8000."))
                            self.root.after(0, self.on_server_stopped)
                        else:
                            self.server_running = True
                            self.root.after(0, self.on_server_started)
                    else:
                        # Dev mode: spawn backend/run.py as subprocess
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
                        threading.Thread(target=self.drain_stream, args=(self.server_process.stdout, "STDOUT"), daemon=True).start()
                        threading.Thread(target=self.drain_stream, args=(self.server_process.stderr, "STDERR"), daemon=True).start()

                        # Give it 1.5 seconds to initialize
                        time.sleep(1.5)

                        if self.server_process.poll() is not None:
                            # Process exited due to startup error
                            self.server_running = False
                            self.server_process = None
                            self.root.after(0, lambda: messagebox.showerror("Startup Error", "Server failed to start. Please wait a few seconds for port 8000 to clear, or check if another app is using port 8000."))
                            self.root.after(0, self.on_server_stopped)
                        else:
                            self.server_running = True
                            self.root.after(0, self.on_server_started)
                except Exception as e:
                    self.server_running = False
                    self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to start server: {e}"))
                    self.root.after(0, self.on_server_stopped)

            threading.Thread(target=start, daemon=True).start()

    def drain_stream(self, stream, prefix: str):
        """Continuously reads from stream to keep buffers clear and logs output."""
        try:
            from app.logger import log_event
            while True:
                line = stream.readline()
                if not line:
                    break
                line = line.strip()
                if line:
                    log_event("INFO" if prefix == "STDOUT" else "ERROR", f"[{prefix}] {line}")
        except Exception:
            pass

    # ──────────────────────────────────────────────
    # Server state transitions
    # ──────────────────────────────────────────────
    def on_server_started(self):
        """Update interface when server starts running."""
        self.srv_val.configure(text="Running", fg=GREEN_COLOR)
        self.srv_dot.itemconfigure(self.srv_dot_id, fill=GREEN_COLOR)
        self.power_canvas.itemconfigure(self.power_circle, outline=GREEN_COLOR)
        self.power_canvas.itemconfigure(self.power_line, fill=GREEN_COLOR)

        self.btn_run.configure(
            state="normal",
            text="\u25a0  Stop PhotoBridge Server",
            bg=GREEN_BTN, fg="#0a1628"
        )

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

        try:
            hostname = socket.gethostname().lower()
        except Exception:
            hostname = "photobridge"

        # Populate URL values and labels
        self.url_local = f"http://localhost:{port}"
        self.url_phone = f"http://{lan_ip}:{port}"
        self.url_easy = f"http://{hostname}.local:{port}"

        self.url_local_lbl.configure(text=self.url_local)
        self.url_phone_lbl.configure(text=f"{self.url_phone}")
        self.url_easy_lbl.configure(text=self.url_easy)

        # Swap URL visibility
        self.urls_placeholder.pack_forget()
        self.urls_rows_frame.pack(fill="x")

        # Lock uninstall button while server runs
        self.btn_uninstall.configure(state="disabled")

    def on_server_stopped(self):
        """Update interface when server finishes stopping."""
        self.srv_val.configure(text="Stopped", fg=RED_COLOR)
        self.srv_dot.itemconfigure(self.srv_dot_id, fill=RED_COLOR)
        self.power_canvas.itemconfigure(self.power_circle, outline=RED_COLOR)
        self.power_canvas.itemconfigure(self.power_line, fill=RED_COLOR)

        self.btn_run.configure(
            state="normal",
            text="\u25b6  Start PhotoBridge Server",
            bg=GREEN_BTN, fg="#0a1628"
        )

        # Swap URL visibility
        self.urls_rows_frame.pack_forget()
        self.urls_placeholder.pack(anchor="w", fill="x")

        # Clear stored URLs
        self.url_local = ""
        self.url_phone = ""
        self.url_easy = ""

        if self.firewall_active:
            self.btn_uninstall.configure(state="normal")

    # ──────────────────────────────────────────────
    # Logs Window (themed)
    # ──────────────────────────────────────────────
    def open_logs_window(self):
        """Open a live log viewer window in Tkinter."""
        log_win = tk.Toplevel(self.root)
        log_win.title("PhotoBridge Server Logs")
        log_win.geometry("680x460")
        log_win.configure(bg=BG_DEEP)

        # Header
        hdr = tk.Frame(log_win, bg=CARD_BG, padx=15, pady=10)
        hdr.pack(fill="x", side="top")

        lbl = tk.Label(hdr, text="\U0001f4cb PhotoBridge Server Logs", font=("Segoe UI", 12, "bold"), fg=TEXT_WHITE, bg=CARD_BG)
        lbl.pack(side="left")

        # Text Widget
        import tkinter.scrolledtext as st
        log_text = st.ScrolledText(
            log_win,
            bg="#060e1a",
            fg="#d1d1d6",
            insertbackground="#ffffff",
            font=("Consolas", 10),
            padx=10,
            pady=10,
            relief="flat"
        )
        log_text.pack(fill="both", expand=True, padx=10, pady=10)

        log_text.tag_config("INFO", foreground=GREEN_COLOR)
        log_text.tag_config("WARN", foreground=YELLOW_COLOR)
        log_text.tag_config("ERROR", foreground=RED_COLOR)
        log_text.tag_config("TIME", foreground="#4a6278")

        def fetch_logs():
            log_text.configure(state="normal")
            log_text.delete("1.0", tk.END)

            try:
                from app.logger import get_logs
                logs = get_logs()
                if not logs:
                    log_text.insert(tk.END, "No logs recorded yet.\n", "TIME")
                else:
                    for entry in logs:
                        log_text.insert(tk.END, f"[{entry['timestamp']}] ", "TIME")
                        lvl = entry['level']
                        tag = "INFO"
                        if "WARN" in lvl: tag = "WARN"
                        if "ERR" in lvl: tag = "ERROR"
                        log_text.insert(tk.END, f"[{lvl}] ", tag)
                        log_text.insert(tk.END, f"{entry['message']}\n")
            except Exception as e:
                log_text.insert(tk.END, f"Failed to fetch logs: {e}\n", "ERROR")

            log_text.configure(state="disabled")
            log_text.see(tk.END)

        # Action Buttons
        btn_bar = tk.Frame(log_win, bg=BG_DEEP, padx=10, pady=8)
        btn_bar.pack(fill="x", side="bottom")

        btn_ref = tk.Button(btn_bar, text="\U0001f504 Refresh", command=fetch_logs, bg=CARD_BG, fg=TEXT_WHITE, relief="flat", padx=10, pady=5)
        btn_ref.pack(side="left", padx=5)

        def clear_logs_action():
            try:
                from app.logger import clear_logs
                clear_logs()
                fetch_logs()
            except Exception:
                pass

        btn_clr = tk.Button(btn_bar, text="\U0001f5d1\ufe0f Clear Logs", command=clear_logs_action, bg=CARD_BG, fg=TEXT_WHITE, relief="flat", padx=10, pady=5)
        btn_clr.pack(side="left", padx=5)

        win_active = True

        def auto_update():
            if win_active:
                try:
                    if log_win.winfo_exists():
                        fetch_logs()
                        log_win.after(1500, auto_update)
                except Exception:
                    pass

        def on_win_close():
            nonlocal win_active
            win_active = False
            log_win.destroy()

        log_win.protocol("WM_DELETE_WINDOW", on_win_close)
        auto_update()

    # ──────────────────────────────────────────────
    # Cleanup & Updates
    # ──────────────────────────────────────────────
    def on_closing(self):
        """Clean closure of application, terminating background server tasks & deleting .thumbcache."""
        if self.server_running:
            try:
                if hasattr(self, 'server_thread') and self.server_thread:
                    # Frozen mode: stop in-process uvicorn thread
                    self.server_thread.stop()
                    self.server_thread.join(timeout=3.0)
                elif self.server_process:
                    self.server_process.communicate(input="\n", timeout=2)
            except Exception:
                if self.server_process:
                    self.server_process.kill()

        try:
            from app.media import clear_thumb_cache
            clear_thumb_cache()
        except Exception:
            pass

        self.root.destroy()

    def check_for_updates(self):
        """Call GitHub Releases API, compare versions, and prompt if newer version is available."""
        import json
        import urllib.request
        from urllib.error import URLError
        import webbrowser
        from app.paths import get_app_version

        current_version = get_app_version()

        # Disable button during check to prevent double click
        self.btn_update.configure(state="disabled", text="Checking...")
        self.root.update_idletasks()

        def run_check():
            try:
                # Set a User-Agent header as GitHub API requires it
                req = urllib.request.Request(
                    "https://api.github.com/repos/animesh2411/my-photos-app/releases/latest",
                    headers={"User-Agent": "PhotoBridge-ControlCenter"}
                )
                with urllib.request.urlopen(req, timeout=5) as response:
                    data = json.loads(response.read().decode())

                tag_name = data.get("tag_name", "") # e.g., "v1.0.3"
                html_url = data.get("html_url", "https://github.com/animesh2411/my-photos-app/releases/latest")

                # Parse version strings to compare. E.g. clean "v1.0.3" to "1.0.3"
                clean_tag = tag_name.lstrip('v').strip()
                clean_current = current_version.lstrip('v').strip()

                # Compare versions using tuple representation of integers
                try:
                    tag_tuple = tuple(map(int, clean_tag.split('.')))
                    curr_tuple = tuple(map(int, clean_current.split('.')))
                except ValueError:
                    # Fallback to simple string comparison if split/int conversion fails
                    tag_tuple = (clean_tag,)
                    curr_tuple = (clean_current,)

                if tag_tuple > curr_tuple:
                    # New version available!
                    self.root.after(0, lambda: messagebox.showinfo(
                        "Update Available",
                        f"A new version ({tag_name}) of PhotoBridge is available!\n\n"
                        f"Current version: v{current_version}\n\n"
                        f"Click OK to open the download page in your browser.",
                        parent=self.root
                    ))
                    # Open browser with download page
                    webbrowser.open(html_url)
                else:
                    self.root.after(0, lambda: messagebox.showinfo(
                        "Up to Date",
                        f"PhotoBridge is up to date!\n\n"
                        f"Current version: v{current_version}\n"
                        f"Latest version: {tag_name or 'N/A'}",
                        parent=self.root
                    ))
            except URLError as e:
                self.root.after(0, lambda: messagebox.showerror(
                    "Connection Error",
                    f"Failed to check for updates.\n\nError: {e.reason}",
                    parent=self.root
                ))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror(
                    "Error",
                    f"An error occurred while checking for updates:\n\n{str(e)}",
                    parent=self.root
                ))
            finally:
                self.root.after(0, lambda: self.btn_update.configure(state="normal", text="\u21bb  Check for Updates"))

        # Run check in a background thread to keep GUI responsive
        threading.Thread(target=run_check, daemon=True).start()


if __name__ == "__main__":
    if getattr(sys, "frozen", False):
        # Frozen mode: working directory is beside the .exe
        os.chdir(os.path.dirname(sys.executable))
    else:
        # Dev mode: working directory is project root
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        os.chdir(project_root)

    # Clean leftover thumbnails on launch & register atexit hook
    import atexit
    try:
        from app.media import clear_thumb_cache
        clear_thumb_cache()
        atexit.register(clear_thumb_cache)
    except Exception:
        pass

    root = tk.Tk()
    gui = PhotoBridgeGUI(root)
    root.mainloop()
