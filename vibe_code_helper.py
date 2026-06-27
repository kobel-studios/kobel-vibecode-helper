import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pyautogui
import keyboard
import os
from PIL import Image, ImageTk

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
        interval_frame = ttk.LabelFrame(container, text="Check interval (seconds)", padding=12)
        interval_frame.grid(row=1, column=0, columnspan=2, sticky="ew", **pad)

        self.interval_var = tk.StringVar(value="1")
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
        ttk.Label(container, textvariable=self.count_var, foreground=MUTED).grid(row=3, column=0, columnspan=2, pady=(0, 8))

        # Setup instructions
        setup_frame = ttk.LabelFrame(container, text="Setup Instructions", padding=12)
        setup_frame.grid(row=4, column=0, columnspan=2, sticky="ew", **pad)

        setup_text = (
            "• Place accept_all_button.png in this folder\n"
            "• Screenshot of the Accept All button from Windsurf\n"
            "• The script will auto-detect and use it"
        )
        ttk.Label(setup_frame, text=setup_text, foreground=ACCENT, justify="left").pack()

        # Controls
        self.toggle_button = ttk.Button(container, text="Start (F7)", command=self._toggle)
        self.toggle_button.grid(row=5, column=0, columnspan=2, sticky="ew", padx=6, pady=(6, 2))

        hint = ttk.Label(
            container,
            text="Press F7 anywhere to start/stop. Press Esc to quit.\n"
                 "Fail-safe: slam mouse to a screen corner to abort.",
            foreground=MUTED,
            justify="center",
        )
        hint.grid(row=6, column=0, columnspan=2, pady=(8, 0))

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
        self.worker = threading.Thread(target=self._accept_loop, args=(interval,), daemon=True)
        self.worker.start()

        self.toggle_button.config(text="Stop (F7)")
        self._set_status("Running...", CLICKING_COLOR)

    def stop_running(self):
        self.stop_flag.set()
        self.running = False
        self.toggle_button.config(text="Start (F7)")
        self._set_status("Stopped", STOPPED_COLOR)

    def _accept_loop(self, interval):
        try:
            while not self.stop_flag.is_set():
                if self._click_accept_all():
                    self.accept_count += 1
                    self.root.after(0, self._update_count, self.accept_count)

                slept = 0.0
                while slept < interval and not self.stop_flag.is_set():
                    step = min(0.05, interval - slept)
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

    def on_close(self):
        self.stop_running()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = VibeCodeHelper(root)
    root.mainloop()


if __name__ == "__main__":
    main()
