import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import pyautogui
import keyboard
import os
import json
import urllib.request
import urllib.error
import webbrowser
import base64
from datetime import datetime
from collections import deque
from PIL import Image, ImageTk
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

matplotlib.use("TkAgg")

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1

HOTKEY = "f7"

# Dark theme palette
BG = "#1e1f22"
SURFACE = "#2b2d31"
FG = "#e6e6e6"
MUTED = "#a0a0a0"
ACCENT = "#3b82f6"
ACCENT_ACTIVE = "#2f6fd0"
BORDER = "#3a3d41"

CLICKING_COLOR = "#3fb950"
STOPPED_COLOR = "#e3b341"

ACCEPT_BUTTON_IMAGE = "accept_all_button.png"
DATA_FILE = "vibecode_data.json"
CONFIG_FILE = "vibecode_config.json"
LEADERBOARD_GITHUB_URL = "https://api.github.com/repos/kobel-studios/Kobel-vibecode-helper/contents/leaderboard_data.json"


class VibeCodeHelper:
    def __init__(self, root):
        self.root = root
        self.root.title("Vibe Code-Helper")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)
        
        # Position window on the right side of the screen
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        window_width = self.root.winfo_reqwidth()
        x_position = screen_width - window_width - 20
        self.root.geometry(f"+{x_position}+20")

        self.running = False
        self.stop_flag = threading.Event()
        self.worker = None
        self.accept_count = 0
        self.session_start_time = None
        self.total_clicks = 0
        
        # Graph data
        self.accept_rate_history = deque(maxlen=60)  # Store last 60 data points
        
        # Leaderboard configuration
        self.username = None
        self.participate_leaderboard = False
        self.github_token = None
        
        # Load user configuration
        self._load_config()

        self._apply_dark_theme()
        self._build_ui()

        keyboard.add_hotkey(HOTKEY, self._hotkey_pressed)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        # Bind click handler to entire window to remove focus from text boxes
        self.root.bind("<Button-1>", self._on_background_click)

    def _apply_dark_theme(self):
        self.root.configure(bg=BG)
        style = ttk.Style(self.root)
        style.theme_use("clam")

        style.configure(".", background=BG, foreground=FG, fieldbackground=SURFACE)
        style.configure("TFrame", background=BG)
        style.configure("TLabel", background=BG, foreground=FG)
        style.configure("TLabelframe", background=BG, foreground=FG, bordercolor=BORDER)
        style.configure("TLabelframe.Label", background=BG, foreground=MUTED)
        style.configure(
            "TButton",
            background=ACCENT,
            foreground="#ffffff",
            borderwidth=0,
            focuscolor=ACCENT,
            padding=8,
        )
        style.map(
            "TButton",
            background=[("active", ACCENT_ACTIVE), ("pressed", ACCENT_ACTIVE)],
        )
        style.configure(
            "TEntry",
            fieldbackground=SURFACE,
            foreground=FG,
            insertcolor=FG,
            bordercolor=BORDER,
            lightcolor=BORDER,
            darkcolor=BORDER,
        )

    def _build_ui(self):
        pad = {"padx": 8, "pady": 6}
        container = ttk.Frame(self.root, padding=16)
        container.grid(row=0, column=0, sticky="nsew")

        title = ttk.Label(container, text="Kobel-vibecode-helper", font=("Segoe UI", 16, "bold"))
        title.grid(row=0, column=0, columnspan=2, pady=(0, 12))

        # Check interval
        interval_frame = ttk.LabelFrame(container, text="Check interval (milliseconds)", padding=12)
        interval_frame.grid(row=1, column=0, columnspan=2, sticky="ew", **pad)

        self.interval_var = tk.StringVar(value="1000")
        interval_entry = ttk.Entry(interval_frame, textvariable=self.interval_var, width=10, justify="center")
        interval_entry.pack()

        # Status
        self.status_var = tk.StringVar(value="Idle")
        self.status_label = ttk.Label(
            container, textvariable=self.status_var, font=("Segoe UI", 11, "bold"), foreground=MUTED
        )
        self.status_label.grid(row=2, column=0, columnspan=2, pady=(10, 2))

        # Count
        self.count_var = tk.StringVar(value="Accepts performed: 0")
        ttk.Label(container, textvariable=self.count_var, foreground=MUTED).grid(row=3, column=0, columnspan=2, pady=(0, 4))
        
        # Statistics
        self.stats_var = tk.StringVar(value="Session: 0 clicks | 0.0 clicks/min")
        ttk.Label(container, textvariable=self.stats_var, foreground=MUTED, font=("Segoe UI", 9)).grid(row=4, column=0, columnspan=2, pady=(0, 8))

        # Setup instructions
        setup_frame = ttk.LabelFrame(container, text="Setup Instructions", padding=12)
        setup_frame.grid(row=5, column=0, columnspan=2, sticky="ew", **pad)

        setup_text = (
            "• Place accept_all_button.png in this folder\n"
            "• Screenshot of the Accept All button from Windsurf\n"
            "• The script will auto-detect and use it"
        )
        ttk.Label(setup_frame, text=setup_text, foreground=ACCENT, justify="left").pack()

        # Controls
        self.toggle_button = ttk.Button(container, text="Start (F7)", command=self._toggle)
        self.toggle_button.grid(row=6, column=0, columnspan=2, sticky="ew", padx=6, pady=(6, 2))

        # Settings buttons
        settings_frame = ttk.Frame(container)
        settings_frame.grid(row=7, column=0, columnspan=2, pady=(6, 0))
        
        ttk.Button(settings_frame, text="Save Settings", command=self._save_settings, width=12).pack(side="left", padx=2)
        ttk.Button(settings_frame, text="Load Settings", command=self._load_settings, width=12).pack(side="left", padx=2)

        hint = ttk.Label(
            container,
            text="Press F7 anywhere to start/stop. Press Esc to quit.\n"
                 "Fail-safe: slam mouse to a screen corner to abort.",
            foreground=MUTED,
            justify="center",
        )
        hint.grid(row=8, column=0, columnspan=2, pady=(8, 0))
        
        # Leaderboard and tools buttons
        tools_frame = ttk.Frame(container)
        tools_frame.grid(row=9, column=0, columnspan=2, pady=(6, 0))
        
        ttk.Button(tools_frame, text="View Leaderboard", command=self._view_leaderboard, width=12).pack(side="left", padx=2)
        ttk.Button(tools_frame, text="View Graph", command=self._view_graph, width=12).pack(side="left", padx=2)
        ttk.Button(tools_frame, text="Test Accept", command=self._test_accept, width=12).pack(side="left", padx=2)

    def _on_background_click(self, event):
        """Remove focus from text boxes when clicking on window background."""
        clicked_widget = event.widget
        
        if isinstance(clicked_widget, ttk.Entry):
            return
        
        current = clicked_widget
        while current:
            if isinstance(current, ttk.Entry):
                return
            if isinstance(current, (ttk.Button, ttk.Combobox, ttk.Checkbutton, ttk.Radiobutton)):
                return
            try:
                current = current.master
            except AttributeError:
                break
        
        self.root.focus_set()

    def _hotkey_pressed(self):
        self.root.after(0, self._toggle)

    def _toggle(self):
        if self.running:
            self.stop_running()
        else:
            self.start_running()

    def start_running(self):
        # Check if button image exists
        if not os.path.exists(ACCEPT_BUTTON_IMAGE):
            messagebox.showerror("Missing file", f"{ACCEPT_BUTTON_IMAGE} not found.\nPlease take a screenshot of the Accept All button and save it as {ACCEPT_BUTTON_IMAGE}")
            return

        try:
            interval = float(self.interval_var.get())
            if interval <= 0:
                raise ValueError("Interval must be greater than 0")
        except ValueError as exc:
            messagebox.showerror("Invalid input", str(exc))
            return

        self.running = True
        self.stop_flag.clear()
        self.accept_count = 0
        self.session_start_time = time.time()
        self.worker = threading.Thread(target=self._accept_loop, args=(interval,), daemon=True)
        self.worker.start()

        self.toggle_button.config(text="Stop (F7)")
        self._set_status("Running...", CLICKING_COLOR)

    def stop_running(self):
        self.stop_flag.set()
        self.running = False
        self.toggle_button.config(text="Start (F7)")
        self._set_status("Stopped", STOPPED_COLOR)
        # Ask if user wants to submit to leaderboard
        if self.participate_leaderboard and self.accept_count > 0:
            self._prompt_submit_leaderboard()

    def _accept_loop(self, interval):
        try:
            last_update = time.time()
            while not self.stop_flag.is_set():
                if self._click_accept_all():
                    self.accept_count += 1
                    self.total_clicks += 1
                    self.root.after(0, self._update_count, self.accept_count)
                    self.root.after(0, self._update_stats)
                    
                    # Record for graph
                    current_time = time.time()
                    if self.session_start_time:
                        elapsed = current_time - self.session_start_time
                        accepts_per_min = (self.accept_count / elapsed) * 60 if elapsed > 0 else 0
                        self.accept_rate_history.append((elapsed, accepts_per_min))

                # Update graph every second
                current_time = time.time()
                if current_time - last_update >= 1.0 and self.session_start_time:
                    elapsed = current_time - self.session_start_time
                    accepts_per_min = (self.accept_count / elapsed) * 60 if elapsed > 0 else 0
                    self.accept_rate_history.append((elapsed, accepts_per_min))
                    last_update = current_time

                slept = 0.0
                interval_seconds = interval / 1000.0  # Convert milliseconds to seconds
                while slept < interval_seconds and not self.stop_flag.is_set():
                    step = min(0.05, interval_seconds - slept)
                    time.sleep(step)
                    slept += step
        except Exception:
            pass
        finally:
            self.root.after(0, self._on_loop_done)

    def _click_accept_all(self):
        """Try to find and click the 'Accept All' button using image recognition."""
        
        try:
            button_location = pyautogui.locateOnScreen(ACCEPT_BUTTON_IMAGE, confidence=0.8)
            if button_location:
                button_center = pyautogui.center(button_location)
                
                # Save current mouse position
                original_pos = pyautogui.position()
                
                # Click the button
                pyautogui.click(button_center)
                
                # Restore mouse position without clicking
                pyautogui.move(original_pos[0] - button_center[0], original_pos[1] - button_center[1])
                
                return True
        except Exception as e:
            pass
        
        return False

    def _on_loop_done(self):
        self.running = False
        self.toggle_button.config(text="Start (F7)")
        self.count_var.set(f"Accepts performed: {self.accept_count}")
        self._set_status("Stopped", STOPPED_COLOR)

    def _set_status(self, text, color):
        self.status_var.set(text)
        self.status_label.config(foreground=color)

    def _update_count(self, count):
        self.count_var.set(f"Accepts performed: {count}")

    def _update_stats(self):
        """Update click statistics display."""
        if self.session_start_time:
            elapsed = time.time() - self.session_start_time
            if elapsed > 0:
                clicks_per_min = (self.accept_count / elapsed) * 60
                self.stats_var.set(f"Session: {self.accept_count} clicks | {clicks_per_min:.1f} clicks/min")
        else:
            self.stats_var.set(f"Session: {self.accept_count} clicks | 0.0 clicks/min")

    def _save_settings(self):
        """Save current settings to a JSON file."""
        settings = {
            "interval": self.interval_var.get()
        }
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save Settings"
        )
        
        if file_path:
            try:
                with open(file_path, "w") as f:
                    json.dump(settings, f, indent=4)
                messagebox.showinfo("Success", "Settings saved successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save settings: {e}")

    def _load_settings(self):
        """Load settings from a JSON file."""
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Load Settings"
        )
        
        if file_path:
            try:
                with open(file_path, "r") as f:
                    settings = json.load(f)
                
                if "interval" in settings:
                    self.interval_var.set(settings["interval"])
                
                messagebox.showinfo("Success", "Settings loaded successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load settings: {e}")

    def on_close(self):
        self.stop_running()
        self.root.destroy()

    # ---------- Leaderboard System ----------
    def _load_config(self):
        """Load user configuration or prompt for username on first launch."""
        self.username = None
        self.participate_leaderboard = False
        self.github_token = None

        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self.username = config.get("username")
                    self.participate_leaderboard = config.get("participate_leaderboard", False)
                    self.github_token = config.get("github_token")
            except Exception:
                pass

        if not self.username or not self.participate_leaderboard:
            self._prompt_username()

    def _save_config(self):
        """Save user configuration to file."""
        config = {
            "username": self.username,
            "participate_leaderboard": self.participate_leaderboard,
            "github_token": self.github_token
        }
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

    def _ask_github_token(self):
        """Ask user for GitHub token with clickable link."""
        dialog = tk.Toplevel(self.root)
        dialog.title("GitHub Token")
        dialog.geometry("500x400")
        dialog.configure(bg=BG)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Instructions
        instructions = tk.Label(
            dialog,
            text="WHAT THIS DOES:\n"
                   "This lets the app add your score to the leaderboard automatically.\n"
                   "It does NOT give us access to your GitHub account or repos.\n"
                   "You create the token yourself, so you control it.\n\n"
                   "STEP 1: Click the link below\n"
                   "STEP 2: Click 'Generate new token' (or 'Generate new token (classic)')\n"
                   "STEP 3: Type a name (like 'vibecode')\n"
                   "STEP 4: Check the box that says 'repo'\n"
                   "STEP 5: Click the green button\n"
                   "STEP 6: Copy the code it shows you\n"
                   "STEP 7: Paste it in the box below",
            fg=FG,
            bg=BG,
            font=("Segoe UI", 10),
            justify="left"
        )
        instructions.pack(pady=20, padx=20)
        
        # Clickable link
        def open_link():
            webbrowser.open("https://github.com/settings/tokens")
        
        link_label = tk.Label(
            dialog,
            text="https://github.com/settings/tokens",
            fg=ACCENT,
            bg=BG,
            font=("Segoe UI", 10, "underline"),
            cursor="hand2"
        )
        link_label.pack(pady=5)
        link_label.bind("<Button-1>", lambda e: open_link())
        
        # Safety note
        safety_note = tk.Label(
            dialog,
            text="This is NOT your GitHub password. It's a special code you create.\n"
                   "You can delete it anytime from GitHub settings.\n\n"
                   "(Leave empty to use manual submission instead)",
            fg=MUTED,
            bg=BG,
            font=("Segoe UI", 9),
            justify="left"
        )
        safety_note.pack(pady=10, padx=20)
        
        # Token input
        token_var = tk.StringVar()
        token_entry = tk.Entry(
            dialog,
            textvariable=token_var,
            show="*",
            font=("Segoe UI", 10),
            bg=SURFACE,
            fg=FG,
            insertbackground=FG
        )
        token_entry.pack(pady=10, padx=20, fill="x")
        token_entry.focus()
        
        # Buttons
        button_frame = tk.Frame(dialog, bg=BG)
        button_frame.pack(pady=20)
        
        result = [None]
        
        def on_ok():
            result[0] = token_var.get()
            dialog.destroy()
        
        def on_cancel():
            result[0] = ""
            dialog.destroy()
        
        ok_button = tk.Button(
            button_frame,
            text="OK",
            command=on_ok,
            bg=ACCENT,
            fg="white",
            font=("Segoe UI", 10),
            relief="flat",
            padx=20
        )
        ok_button.pack(side="left", padx=5)
        
        cancel_button = tk.Button(
            button_frame,
            text="Cancel",
            command=on_cancel,
            bg=SURFACE,
            fg=FG,
            font=("Segoe UI", 10),
            relief="flat",
            padx=20
        )
        cancel_button.pack(side="left", padx=5)
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Wait for dialog to close
        self.root.wait_window(dialog)
        
        return result[0]

    def _prompt_username(self):
        """Prompt user for leaderboard participation and username."""
        result = messagebox.askyesno(
            "Leaderboard",
            "Do you want to participate in the global leaderboard?\n\n"
            "Your accepts will be tracked and compared with other users."
        )

        if result:
            # Ask for username (loop until unique or cancelled)
            while True:
                username = simpledialog.askstring(
                    "Username",
                    "Enter your username for the leaderboard:",
                    parent=self.root
                )
                
                if not username or not username.strip():
                    # User cancelled or entered empty username
                    self.participate_leaderboard = False
                    self._save_config()
                    return
                
                username = username.strip()
                
                # Check if username already exists in leaderboard
                if self._username_exists(username):
                    messagebox.showerror(
                        "Username Taken",
                        f"The username '{username}' is already taken. Please choose a different username."
                    )
                    continue
                
                # Username is unique
                self.username = username
                self.participate_leaderboard = True
                # Ask for GitHub token for automatic submission
                token = self._ask_github_token()
                self.github_token = token.strip() if token else None
                self._save_config()
                if self.github_token:
                    messagebox.showinfo("Welcome", f"Welcome, {self.username}! Your sessions will be automatically submitted to the leaderboard.")
                else:
                    messagebox.showinfo("Welcome", f"Welcome, {self.username}! Your sessions will be saved to the leaderboard (manual submission via GitHub Issues).")
                break
        else:
            # User declined participation
            self.participate_leaderboard = False
            self._save_config()

    def _username_exists(self, username):
        """Check if username already exists in the leaderboard."""
        try:
            # Fetch current data from GitHub API
            response = urllib.request.urlopen(LEADERBOARD_GITHUB_URL)
            file_data = json.loads(response.read().decode('utf-8'))
            
            # Decode base64 content
            import base64
            content = file_data.get("content", "")
            if content:
                decoded_content = base64.b64decode(content).decode('utf-8')
                data = json.loads(decoded_content)
            else:
                data = {"sessions": []}
            
            sessions = data.get("sessions", [])
            
            # Check if any session has this username
            for session in sessions:
                if session.get("username") == username:
                    return True
            
            return False
        except urllib.error.URLError:
            # Can't connect to GitHub - warn user but allow
            messagebox.showwarning(
                "Connection Error",
                "Cannot check if username is taken (no internet connection).\n"
                "You can continue, but your username might already be taken."
            )
            return False
        except Exception as e:
            # Other error - warn user but allow
            messagebox.showwarning(
                "Error",
                f"Cannot check if username is taken: {e}\n"
                "You can continue, but your username might already be taken."
            )
            return False

    def _save_session(self):
        """Save session data to local file."""
        if not self.session_start_time or self.accept_count == 0:
            return
        
        session_data = {
            "username": self.username,
            "timestamp": datetime.now().isoformat(),
            "accepts": self.accept_count,
            "duration_seconds": time.time() - self.session_start_time,
            "accepts_per_minute": (self.accept_count / (time.time() - self.session_start_time)) * 60 if self.session_start_time else 0
        }
        
        # Load existing data
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    sessions = data.get("sessions", [])
            except Exception:
                sessions = []
        else:
            sessions = []
        
        # Add new session
        sessions.append(session_data)
        
        # Save back
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({"sessions": sessions}, f, indent=2)

    def _prompt_submit_leaderboard(self):
        """Prompt user to submit their session data to GitHub."""
        if self.github_token:
            # Automatic submission via GitHub API
            result = messagebox.askyesno(
                "Submit to Leaderboard",
                "Do you want to submit your session to the global leaderboard?\n\n"
                "This will automatically submit your data via GitHub API."
            )
            if result:
                # Save the session locally first
                self._save_session()
                # Then submit via GitHub API
                self._submit_to_github_api()
        else:
            # Manual submission via GitHub Issues
            result = messagebox.askyesno(
                "Submit to Leaderboard",
                "Do you want to submit your session to the global leaderboard?\n\n"
                "This will open a GitHub Issue where you can create your data."
            )
            if result:
                # Save the session locally first
                self._save_session()
                # Then open GitHub Issues
                self._submit_to_github()

    def _submit_to_github_api(self):
        """Submit session data to GitHub via API."""
        try:
            # Load the latest session data
            if not os.path.exists(DATA_FILE):
                messagebox.showerror("Error", "No session data found to submit.")
                return

            with open(DATA_FILE, "r", encoding="utf-8") as f:
                local_data = json.load(f)
            local_sessions = local_data.get("sessions", [])
            
            if not local_sessions:
                messagebox.showerror("Error", "No session data found to submit.")
                return

            # Get the most recent session
            latest_session = local_sessions[-1]

            # Fetch current data from GitHub API
            request = urllib.request.Request(
                LEADERBOARD_GITHUB_URL,
                headers={"Authorization": f"token {self.github_token}"}
            )
            response = urllib.request.urlopen(request)
            file_data = json.loads(response.read().decode('utf-8'))
            
            # Decode base64 content
            content = file_data.get("content", "")
            if content:
                decoded_content = base64.b64decode(content).decode('utf-8')
                remote_data = json.loads(decoded_content)
            else:
                remote_data = {"sessions": []}
            
            remote_sessions = remote_data.get("sessions", [])

            # Check if session already exists (by timestamp)
            if any(s.get("timestamp") == latest_session.get("timestamp") for s in remote_sessions):
                messagebox.showinfo("Info", "This session is already on the leaderboard.")
                return

            # Add new session
            remote_sessions.append(latest_session)
            remote_data["sessions"] = remote_sessions

            # Get the SHA of the current file (needed for updating)
            api_url = "https://api.github.com/repos/kobel-studios/Kobel-vibecode-helper/contents/leaderboard_data.json"
            request = urllib.request.Request(
                api_url,
                headers={"Authorization": f"token {self.github_token}"}
            )
            response = urllib.request.urlopen(request)
            file_info = json.loads(response.read().decode('utf-8'))
            sha = file_info.get("sha")

            # Update the file via GitHub API
            updated_content = json.dumps(remote_data, indent=2)
            encoded_content = base64.b64encode(updated_content.encode('utf-8')).decode('utf-8')

            put_data = {
                "message": f"Add session from {self.username}",
                "content": encoded_content,
                "sha": sha
            }

            request = urllib.request.Request(
                api_url,
                data=json.dumps(put_data).encode('utf-8'),
                headers={
                    "Authorization": f"token {self.github_token}",
                    "Content-Type": "application/json"
                },
                method="PUT"
            )
            response = urllib.request.urlopen(request)

            messagebox.showinfo("Success", "Your session has been successfully submitted to the leaderboard!")

        except urllib.error.HTTPError as e:
            if e.code == 401:
                messagebox.showerror("Error", "Invalid GitHub token. Please check your token and try again.")
            elif e.code == 403:
                messagebox.showerror("Error", "GitHub token doesn't have permission to modify the repository. Please ensure your token has 'repo' scope.")
            elif e.code == 404:
                messagebox.showerror("Error", "Repository or file not found. Please check the GitHub URL.")
            else:
                messagebox.showerror("Error", f"GitHub API error: {e.code} - {e.reason}")
        except urllib.error.URLError as e:
            messagebox.showerror("Error", f"Failed to connect to GitHub: {e}\n\nCheck your internet connection.")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")

    def _submit_to_github(self):
        """Open GitHub Issues with pre-filled leaderboard data."""
        try:
            if not os.path.exists(DATA_FILE):
                messagebox.showerror("Error", "No session data found to submit.")
                return

            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                sessions = data.get("sessions", [])
            
            if not sessions:
                messagebox.showerror("Error", "No session data found to submit.")
                return

            latest_session = sessions[-1]
            
            # Format the data for GitHub Issues
            issue_title = f"Leaderboard Submission: {self.username}"
            issue_body = f"""Username: {self.username}
Timestamp: {latest_session.get('timestamp')}
Accepts: {latest_session.get('accepts')}
Duration: {latest_session.get('duration_seconds', 0):.2f} seconds
Accepts per minute: {latest_session.get('accepts_per_minute', 0):.2f}

Please add this session to the leaderboard_data.json file."""

            # URL encode the body
            encoded_body = urllib.parse.quote(issue_body)
            
            # Open GitHub Issues
            issue_url = f"https://github.com/kobel-studios/Kobel-vibecode-helper/issues/new?title={urllib.parse.quote(issue_title)}&body={encoded_body}"
            webbrowser.open(issue_url)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open GitHub Issues: {e}")

    def _view_leaderboard(self):
        """Display the leaderboard in a new window."""
        try:
            # Fetch leaderboard data from GitHub API
            response = urllib.request.urlopen(LEADERBOARD_GITHUB_URL)
            file_data = json.loads(response.read().decode('utf-8'))
            
            # Decode base64 content
            content = file_data.get("content", "")
            if content:
                decoded_content = base64.b64decode(content).decode('utf-8')
                data = json.loads(decoded_content)
            else:
                data = {"sessions": []}
            
            sessions = data.get("sessions", [])
            
            if not sessions:
                messagebox.showinfo("Leaderboard", "No leaderboard data available yet.")
                return
            
            # Sort by accepts per minute (descending)
            sessions.sort(key=lambda x: x.get('accepts_per_minute', 0), reverse=True)
            
            # Create leaderboard window
            leaderboard_window = tk.Toplevel(self.root)
            leaderboard_window.title("Leaderboard")
            leaderboard_window.geometry("600x500")
            leaderboard_window.configure(bg=BG)
            leaderboard_window.transient(self.root)
            
            # Title
            title = tk.Label(
                leaderboard_window,
                text="Global Leaderboard - Accepts per Minute",
                fg=FG,
                bg=BG,
                font=("Segoe UI", 14, "bold")
            )
            title.pack(pady=20)
            
            # Create treeview for leaderboard
            tree = ttk.Treeview(leaderboard_window, columns=("rank", "username", "accepts", "apm"), show="headings")
            tree.heading("rank", text="Rank")
            tree.heading("username", text="Username")
            tree.heading("accepts", text="Accepts")
            tree.heading("apm", text="Accepts/min")
            
            tree.column("rank", width=50, anchor="center")
            tree.column("username", width=150, anchor="center")
            tree.column("accepts", width=100, anchor="center")
            tree.column("apm", width=100, anchor="center")
            
            tree.pack(fill="both", expand=True, padx=20, pady=10)
            
            # Add data
            for i, session in enumerate(sessions[:20], 1):  # Top 20
                tree.insert("", "end", values=(
                    i,
                    session.get("username", "Unknown"),
                    session.get("accepts", 0),
                    f"{session.get('accepts_per_minute', 0):.2f}"
                ))
            
            # Close button
            ttk.Button(leaderboard_window, text="Close", command=leaderboard_window.destroy).pack(pady=10)
            
            # Center window
            leaderboard_window.update_idletasks()
            x = (leaderboard_window.winfo_screenwidth() // 2) - (leaderboard_window.winfo_width() // 2)
            y = (leaderboard_window.winfo_screenheight() // 2) - (leaderboard_window.winfo_height() // 2)
            leaderboard_window.geometry(f"+{x}+{y}")
            
        except urllib.error.URLError:
            messagebox.showerror("Error", "Failed to fetch leaderboard data. Check your internet connection.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load leaderboard: {e}")

    def _view_graph(self):
        """Display the accepts per minute graph in a new window."""
        if not self.accept_rate_history:
            messagebox.showinfo("Graph", "No data available yet. Start a session to generate graph data.")
            return
        
        # Create graph window
        graph_window = tk.Toplevel(self.root)
        graph_window.title("Accepts Per Minute Graph")
        graph_window.geometry("800x600")
        graph_window.configure(bg=BG)
        graph_window.transient(self.root)
        
        # Create matplotlib figure with dark theme
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(8, 6), facecolor=BG)
        
        # Extract data
        times = [t[0] for t in self.accept_rate_history]
        rates = [t[1] for t in self.accept_rate_history]
        
        # Plot
        ax.plot(times, rates, color=ACCENT, linewidth=2)
        ax.set_xlabel('Time (seconds)', color=FG)
        ax.set_ylabel('Accepts per Minute', color=FG)
        ax.set_title('Accepts Per Minute Over Time', color=FG, fontsize=14, fontweight='bold')
        ax.tick_params(colors=FG)
        ax.grid(True, alpha=0.3)
        
        # Embed in tkinter
        canvas = FigureCanvasTkAgg(fig, master=graph_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=20)
        
        # Close button
        ttk.Button(graph_window, text="Close", command=graph_window.destroy).pack(pady=10)
        
        # Center window
        graph_window.update_idletasks()
        x = (graph_window.winfo_screenwidth() // 2) - (graph_window.winfo_width() // 2)
        y = (graph_window.winfo_screenheight() // 2) - (graph_window.winfo_height() // 2)
        graph_window.geometry(f"+{x}+{y}")

    def _test_accept(self):
        """Open a test window with an Accept All button to test the clicker."""
        test_window = tk.Toplevel(self.root)
        test_window.title("Accept Button Tester")
        test_window.geometry("400x300")
        test_window.configure(bg=BG)
        test_window.transient(self.root)
        
        # Title
        title = tk.Label(
            test_window,
            text="Accept Button Tester",
            fg=FG,
            bg=BG,
            font=("Segoe UI", 14, "bold")
        )
        title.pack(pady=20)
        
        # Instructions
        instructions = tk.Label(
            test_window,
            text="Click the Accept All button below to test\nif the clicker is working properly.",
            fg=MUTED,
            bg=BG,
            font=("Segoe UI", 10),
            justify="center"
        )
        instructions.pack(pady=10)
        
        # Accept All button (styled to look like Windsurf's button)
        accept_button = tk.Button(
            test_window,
            text="Accept All",
            bg=ACCENT,
            fg="white",
            font=("Segoe UI", 12, "bold"),
            relief="flat",
            padx=30,
            pady=10,
            cursor="hand2",
            command=lambda: self._on_test_accept_click(test_window)
        )
        accept_button.pack(pady=20)
        
        # Click counter
        test_window.test_clicks = 0
        test_window.clicks_label = tk.Label(
            test_window,
            text="Clicks detected: 0",
            fg=ACCENT,
            bg=BG,
            font=("Segoe UI", 12, "bold")
        )
        test_window.clicks_label.pack(pady=10)
        
        # Close button
        ttk.Button(test_window, text="Close", command=test_window.destroy).pack(pady=10)
        
        # Center window
        test_window.update_idletasks()
        x = (test_window.winfo_screenwidth() // 2) - (test_window.winfo_width() // 2)
        y = (test_window.winfo_screenheight() // 2) - (test_window.winfo_height() // 2)
        test_window.geometry(f"+{x}+{y}")

    def _on_test_accept_click(self, window):
        """Handle test button click."""
        window.test_clicks += 1
        window.clicks_label.config(text=f"Clicks detected: {window.test_clicks}")


def main():
    root = tk.Tk()
    app = VibeCodeHelper(root)
    root.mainloop()


if __name__ == "__main__":
    main()
