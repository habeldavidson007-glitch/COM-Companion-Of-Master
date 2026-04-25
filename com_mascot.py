"""
COM (Companion Of Master) — Floating Mascot UI
Clippy-style: COM floats on screen, click to open chat bubble.
Chat bubble auto-hides after inactivity.
Matches COM mascot: navy/gold/white aesthetic.
"""

import tkinter as tk
from tkinter import font as tkfont
import threading
import requests
import json
import time
import math
import os
import sys
from datetime import datetime

# ── Try importing PIL for mascot image ──────────────────────────
try:
    from PIL import Image, ImageTk, ImageDraw, ImageFilter
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════
# CONSTANTS & THEME
# ═══════════════════════════════════════════════════════════════

MASCOT_SIZE   = 140          # px — floating sprite size
CHAT_WIDTH    = 360          # chat bubble width
CHAT_HEIGHT   = 480          # chat bubble height
HIDE_DELAY    = 8            # seconds of inactivity before chat hides
FLOAT_MARGIN  = 20           # margin from screen edges

# Navy / gold / white — pulled from mascot image
C_NAVY        = "#0A0F2C"
C_NAVY_MID    = "#111736"
C_NAVY_LIGHT  = "#1A2355"
C_GOLD        = "#C9A84C"
C_GOLD_LIGHT  = "#E8C96A"
C_WHITE       = "#F0F4FF"
C_MUTED       = "#7A8BB5"
C_ACCENT_BLUE = "#4A7FD4"
C_BUBBLE_BG   = "#0D1435"
C_INPUT_BG    = "#080D28"
C_SUCCESS     = "#4ADE80"
C_ERROR       = "#F87171"
C_USER_BUBBLE = "#1A2F6E"

OLLAMA_URL  = "http://localhost:11434/api/chat"
MODEL_NAME  = "qwen2.5:0.5b-instruct-q4_K_M"


# ═══════════════════════════════════════════════════════════════
# FALLBACK MASCOT DRAWING (when no image is present)
# ═══════════════════════════════════════════════════════════════

def draw_com_mascot(size=110):
    """Draw COM mascot using PIL if available, else return None."""
    if not PIL_AVAILABLE:
        return None
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2 + 10

    # Body — white ghost teardrop
    d.ellipse([cx-28, cy-32, cx+28, cy+22], fill=(240, 244, 255, 255))
    # Flame hair — blue glow (simplified)
    for i, (ox, oy, r, alpha) in enumerate([
        (-8, -40, 18, 180), (0, -48, 14, 200), (10, -42, 16, 170),
        (-14, -34, 12, 140), (16, -36, 10, 140),
    ]):
        col = (80 + i*10, 140 + i*8, 240, alpha)
        d.ellipse([cx+ox-r, cy+oy-r, cx+ox+r, cy+oy+r], fill=col)
    # Eyes — deep blue
    d.ellipse([cx-12, cy-14, cx-4,  cy-6],  fill=(20, 60, 180, 255))
    d.ellipse([cx+4,  cy-14, cx+12, cy-6],  fill=(20, 60, 180, 255))
    d.ellipse([cx-10, cy-12, cx-7,  cy-9],  fill=(180, 210, 255, 200))
    d.ellipse([cx+6,  cy-12, cx+9,  cy-9],  fill=(180, 210, 255, 200))
    # Gold crown gem
    d.polygon([cx-4, cy-34, cx, cy-42, cx+4, cy-34], fill=(201, 168, 76, 255))
    # Blush
    d.ellipse([cx-24, cy-4, cx-14, cy+2], fill=(255, 180, 180, 100))
    d.ellipse([cx+14, cy-4, cx+24, cy+2], fill=(255, 180, 180, 100))
    # Smile
    d.arc([cx-8, cy+2, cx+8, cy+12], 0, 180, fill=(100, 120, 180, 200), width=2)
    # Tuxedo jacket suggestion
    d.ellipse([cx-20, cy+18, cx+20, cy+46], fill=(15, 20, 60, 230))
    d.line([cx, cy+20, cx, cy+44], fill=(240, 235, 210, 200), width=3)

    # Soft glow blur pass
    img = img.filter(ImageFilter.SMOOTH)
    return ImageTk.PhotoImage(img)


# ═══════════════════════════════════════════════════════════════
# MASCOT SPRITE LOADER
# ═══════════════════════════════════════════════════════════════

def load_mascot_image(path, size=MASCOT_SIZE):
    """Load and resize the actual mascot PNG."""
    if not PIL_AVAILABLE:
        print("[COM] PIL not installed. Run: pip install Pillow")
        return None
    if not path or not os.path.exists(path):
        print(f"[COM] Image file not found: {path}")
        return None
    try:
        img = Image.open(path).convert("RGBA")
        # If image has black background (like the mascot PNG), make it transparent
        data = img.getdata()
        new_data = []
        for r, g, b, a in data:
            # Black or near-black pixels -> transparent
            if r < 20 and g < 20 and b < 20:
                new_data.append((0, 0, 0, 0))
            else:
                new_data.append((r, g, b, a))
        img.putdata(new_data)
        img = img.resize((size, size), Image.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception as e:
        print(f"[COM] Image load error: {e}")
        return None


# ═══════════════════════════════════════════════════════════════
# MAIN APP
# ═══════════════════════════════════════════════════════════════

class COMApp:
    def __init__(self):
        # ── Root (invisible anchor) ──────────────────────────
        self.root = tk.Tk()
        self.root.withdraw()          # hidden anchor window
        self.root.title("COM")

        # ── State ────────────────────────────────────────────
        self.chat_visible    = False
        self.is_streaming    = False
        self.last_activity   = time.time()
        self.drag_x          = 0
        self.drag_y          = 0
        self._drag_moved     = False
        self.anim_tick       = 0
        self.hide_job        = None
        self.messages        = []     # conversation history

        # ── Screen geometry ──────────────────────────────────
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.mascot_x = sw - MASCOT_SIZE - FLOAT_MARGIN - 40
        self.mascot_y = sh - MASCOT_SIZE - FLOAT_MARGIN - 60

        # ── Build windows ────────────────────────────────────
        self._build_mascot_window()
        self._build_chat_window()

        # ── Load mascot image ────────────────────────────────
        # Search multiple locations — handles Windows path quirks
        _known = "ChatGPT_Image_Apr_25__2026__11_20_52_PM.png"
        _dirs = [
            os.path.dirname(os.path.abspath(__file__)),
            os.getcwd(),
        ]
        img_path = None
        # Try known filename first
        for _d in _dirs:
            _c = os.path.join(_d, _known)
            if os.path.exists(_c):
                img_path = _c
                break
        # Fallback: grab ANY .png in script folder
        if not img_path:
            _sd = os.path.dirname(os.path.abspath(__file__))
            for _f in os.listdir(_sd):
                if _f.lower().endswith(".png"):
                    img_path = os.path.join(_sd, _f)
                    break
        print(f"[COM] Looking for image in: {_dirs}")
        print(f"[COM] Found: {img_path}")
        print(f"[COM] PIL available: {PIL_AVAILABLE}")
        self.mascot_photo = load_mascot_image(img_path) if img_path else None
        if self.mascot_photo:
            self.mascot_canvas.delete("fallback")
            self.mascot_canvas.itemconfig(self.mascot_img_id,
                                          image=self.mascot_photo)
            print("[COM] Mascot image loaded successfully")
        else:
            print("[COM] No image found — using drawn fallback")
            self.mascot_photo = draw_com_mascot(MASCOT_SIZE)
            if self.mascot_photo:
                self.mascot_canvas.delete("fallback")
                self.mascot_canvas.itemconfig(self.mascot_img_id,
                                              image=self.mascot_photo)

        # ── Start loops ──────────────────────────────────────
        self._animate()
        self._auto_hide_loop()

    # ═══════════════════════════════════════════════════════
    # MASCOT WINDOW
    # ═══════════════════════════════════════════════════════

    def _build_mascot_window(self):
        self.mascot_win = tk.Toplevel(self.root)
        self.mascot_win.overrideredirect(True)
        self.mascot_win.attributes("-topmost", True)
        self.mascot_win.attributes("-transparentcolor", "#010101")
        self.mascot_win.configure(bg="#010101")
        self.mascot_win.geometry(
            f"{MASCOT_SIZE}x{MASCOT_SIZE}+{self.mascot_x}+{self.mascot_y}"
        )

        self.mascot_canvas = tk.Canvas(
            self.mascot_win,
            width=MASCOT_SIZE, height=MASCOT_SIZE,
            bg="#010101", highlightthickness=0
        )
        self.mascot_canvas.pack()

        # Glow ring FIRST (bottom layer)
        self.glow_ring = self.mascot_canvas.create_oval(
            4, 4, MASCOT_SIZE-4, MASCOT_SIZE-4,
            outline=C_ACCENT_BLUE, width=0,
            tags="glow"
        )

        # Fallback shape SECOND (shown only if no image)
        self.mascot_canvas.create_oval(
            10, 10, MASCOT_SIZE-10, MASCOT_SIZE-10,
            fill=C_NAVY_LIGHT, outline=C_GOLD, width=2,
            tags="fallback"
        )
        self.mascot_canvas.create_text(
            MASCOT_SIZE//2, MASCOT_SIZE//2,
            text="COM", fill=C_GOLD,
            font=("Segoe UI", 14, "bold"),
            tags="fallback"
        )

        # Image item LAST — always on top
        self.mascot_img_id = self.mascot_canvas.create_image(
            MASCOT_SIZE // 2, MASCOT_SIZE // 2, anchor="center"
        )

        # Drag bindings
        self.mascot_canvas.bind("<ButtonPress-1>",   self._drag_start)
        self.mascot_canvas.bind("<B1-Motion>",       self._drag_motion)
        self.mascot_canvas.bind("<ButtonRelease-1>", self._drag_end)
        self.mascot_canvas.bind("<Double-Button-1>", self._toggle_chat)
        self.mascot_canvas.bind("<Enter>",           self._on_hover_enter)
        self.mascot_canvas.bind("<Leave>",           self._on_hover_leave)

        # Tooltip
        self._tooltip_label = None

    # ═══════════════════════════════════════════════════════
    # CHAT BUBBLE WINDOW
    # ═══════════════════════════════════════════════════════

    def _build_chat_window(self):
        self.chat_win = tk.Toplevel(self.root)
        self.chat_win.overrideredirect(True)
        self.chat_win.attributes("-topmost", True)
        self.chat_win.attributes("-alpha", 0.0)   # start hidden
        self.chat_win.configure(bg=C_NAVY)
        self.chat_win.withdraw()

        # Rounded appearance via outer frame
        outer = tk.Frame(self.chat_win, bg=C_GOLD, padx=1, pady=1)
        outer.pack(fill="both", expand=True)

        inner = tk.Frame(outer, bg=C_BUBBLE_BG)
        inner.pack(fill="both", expand=True)

        # ── Header ──────────────────────────────────────────
        header = tk.Frame(inner, bg=C_NAVY_MID, height=44)
        header.pack(fill="x")
        header.pack_propagate(False)

        # COM dot indicator
        dot_canvas = tk.Canvas(header, width=10, height=10,
                               bg=C_NAVY_MID, highlightthickness=0)
        dot_canvas.pack(side="left", padx=(12, 6), pady=17)
        self.status_dot = dot_canvas.create_oval(0, 0, 9, 9, fill=C_SUCCESS)
        self.dot_canvas = dot_canvas

        tk.Label(header, text="COM", font=("Segoe UI", 12, "bold"),
                 bg=C_NAVY_MID, fg=C_GOLD).pack(side="left")
        tk.Label(header, text="Companion Of Master",
                 font=("Segoe UI", 8), bg=C_NAVY_MID, fg=C_MUTED).pack(
                 side="left", padx=(6, 0), pady=(4, 0))

        close_btn = tk.Label(header, text="✕", font=("Segoe UI", 11),
                             bg=C_NAVY_MID, fg=C_MUTED, cursor="hand2")
        close_btn.pack(side="right", padx=10)
        close_btn.bind("<Button-1>", lambda e: self._hide_chat())
        close_btn.bind("<Enter>",    lambda e: close_btn.config(fg=C_ERROR))
        close_btn.bind("<Leave>",    lambda e: close_btn.config(fg=C_MUTED))

        # Drag header
        header.bind("<ButtonPress-1>",   self._chat_drag_start)
        header.bind("<B1-Motion>",       self._chat_drag_motion)

        # ── Chat history ─────────────────────────────────────
        history_frame = tk.Frame(inner, bg=C_BUBBLE_BG)
        history_frame.pack(fill="both", expand=True, padx=8, pady=(6, 4))

        self.chat_history = tk.Text(
            history_frame,
            bg=C_BUBBLE_BG, fg=C_WHITE,
            font=("Segoe UI", 10),
            wrap="word", border=0,
            highlightthickness=0,
            cursor="arrow",
            state="disabled",
            padx=4, pady=4
        )
        scroll = tk.Scrollbar(history_frame, command=self.chat_history.yview,
                              bg=C_NAVY_MID, troughcolor=C_BUBBLE_BG,
                              width=6)
        self.chat_history.config(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.chat_history.pack(side="left", fill="both", expand=True)

        # Text tags
        self.chat_history.tag_configure("com_name",  foreground=C_GOLD,
                                        font=("Segoe UI", 9, "bold"))
        self.chat_history.tag_configure("com_text",  foreground=C_WHITE,
                                        font=("Segoe UI", 10),
                                        lmargin1=8, lmargin2=8)
        self.chat_history.tag_configure("user_name", foreground=C_ACCENT_BLUE,
                                        font=("Segoe UI", 9, "bold"))
        self.chat_history.tag_configure("user_text", foreground=C_WHITE,
                                        font=("Segoe UI", 10),
                                        lmargin1=8, lmargin2=8)
        self.chat_history.tag_configure("system",    foreground=C_MUTED,
                                        font=("Segoe UI", 8, "italic"),
                                        justify="center")
        self.chat_history.tag_configure("tool_ok",   foreground=C_SUCCESS,
                                        font=("Segoe UI", 9))
        self.chat_history.tag_configure("tool_err",  foreground=C_ERROR,
                                        font=("Segoe UI", 9))

        # Welcome
        self._append_system("✦  COM is ready. Double-click the mascot to toggle.  ✦")

        # ── Typing indicator ─────────────────────────────────
        self.typing_frame = tk.Frame(inner, bg=C_BUBBLE_BG, height=20)
        self.typing_frame.pack(fill="x", padx=12)
        self.typing_label = tk.Label(self.typing_frame, text="",
                                     bg=C_BUBBLE_BG, fg=C_MUTED,
                                     font=("Segoe UI", 8, "italic"))
        self.typing_label.pack(side="left")

        # ── Separator ────────────────────────────────────────
        tk.Frame(inner, bg=C_GOLD, height=1).pack(fill="x", padx=8)

        # ── Input area ───────────────────────────────────────
        input_frame = tk.Frame(inner, bg=C_NAVY_MID, pady=8)
        input_frame.pack(fill="x")

        self.input_var = tk.StringVar()
        self.input_field = tk.Entry(
            input_frame,
            textvariable=self.input_var,
            bg=C_INPUT_BG, fg=C_WHITE,
            insertbackground=C_GOLD,
            font=("Segoe UI", 10),
            border=0, highlightthickness=1,
            highlightbackground=C_NAVY_LIGHT,
            highlightcolor=C_GOLD,
            relief="flat"
        )
        self.input_field.pack(side="left", fill="x", expand=True,
                              padx=(10, 6), ipady=6)
        self.input_field.bind("<Return>",    self._send_message)
        self.input_field.bind("<Key>",       self._on_keypress)

        send_btn = tk.Label(
            input_frame, text="▶", font=("Segoe UI", 13),
            bg=C_NAVY_MID, fg=C_GOLD, cursor="hand2", padx=10
        )
        send_btn.pack(side="right", padx=(0, 8))
        send_btn.bind("<Button-1>", self._send_message)
        send_btn.bind("<Enter>",    lambda e: send_btn.config(fg=C_GOLD_LIGHT))
        send_btn.bind("<Leave>",    lambda e: send_btn.config(fg=C_GOLD))

        # Store inner for positioning
        self._inner = inner
        self._chat_drag_ox = 0
        self._chat_drag_oy = 0

        # Position chat relative to mascot
        self._reposition_chat()

    # ═══════════════════════════════════════════════════════
    # ANIMATION
    # ═══════════════════════════════════════════════════════

    def _animate(self):
        """Idle float + glow breath animation. Runs every 40ms."""
        self.anim_tick += 1
        t = self.anim_tick

        # Floating bob (slow sine)
        bob = math.sin(t * 0.04) * 5
        self.mascot_win.geometry(
            f"{MASCOT_SIZE}x{MASCOT_SIZE}"
            f"+{self.mascot_x}+{int(self.mascot_y + bob)}"
        )

        # Glow ring pulse (blue halo)
        pulse = (math.sin(t * 0.06) + 1) / 2   # 0→1
        width = int(pulse * 3)
        glow_col = "#{}{}D4".format(
            format(int(74), '02x'),
            format(int(100 + pulse * 80), '02x')
        )
        self.mascot_canvas.itemconfig(self.glow_ring,
                                      width=width, outline=glow_col)

        self.root.after(40, self._animate)

    # ═══════════════════════════════════════════════════════
    # AUTO-HIDE
    # ═══════════════════════════════════════════════════════

    def _auto_hide_loop(self):
        """Check inactivity every second. Hide chat after HIDE_DELAY."""
        if self.chat_visible and not self.is_streaming:
            idle = time.time() - self.last_activity
            if idle > HIDE_DELAY:
                self._fade_out_chat()
        self.root.after(1000, self._auto_hide_loop)

    def _reset_activity(self):
        self.last_activity = time.time()

    # ═══════════════════════════════════════════════════════
    # CHAT SHOW / HIDE
    # ═══════════════════════════════════════════════════════

    def _toggle_chat(self, event=None):
        if self.chat_visible:
            self._hide_chat()
        else:
            self._show_chat()

    def _show_chat(self):
        if self.chat_visible:
            return
        self.chat_visible = True
        self._reset_activity()
        self._reposition_chat()
        self.chat_win.deiconify()
        self._fade_in_chat()
        self.chat_win.lift()
        # Force focus to input field after fade completes
        self.root.after(300, self._focus_input)

    def _focus_input(self):
        """Ensure input field gets focus."""
        if self.chat_visible:
            self.input_field.focus_force()
            self.input_field.icursor(tk.END)

    def _hide_chat(self):
        self.chat_visible = False
        self._fade_out_chat()

    def _fade_in_chat(self, alpha=0.0):
        if not self.chat_visible:
            return
        alpha = min(alpha + 0.08, 0.96)
        self.chat_win.attributes("-alpha", alpha)
        if alpha < 0.96:
            self.root.after(20, lambda: self._fade_in_chat(alpha))

    def _fade_out_chat(self, alpha=None):
        if alpha is None:
            alpha = float(self.chat_win.attributes("-alpha"))
        alpha = max(alpha - 0.08, 0.0)
        self.chat_win.attributes("-alpha", alpha)
        if alpha > 0:
            self.root.after(20, lambda: self._fade_out_chat(alpha))
        else:
            self.chat_win.withdraw()
            self.chat_visible = False

    def _reposition_chat(self):
        """Position chat bubble to the left of the mascot."""
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        cx = self.mascot_x - CHAT_WIDTH - 12
        cy = self.mascot_y - CHAT_HEIGHT + MASCOT_SIZE
        # Keep on screen
        cx = max(FLOAT_MARGIN, min(cx, sw - CHAT_WIDTH - FLOAT_MARGIN))
        cy = max(FLOAT_MARGIN, min(cy, sh - CHAT_HEIGHT - FLOAT_MARGIN))
        self.chat_win.geometry(f"{CHAT_WIDTH}x{CHAT_HEIGHT}+{cx}+{cy}")

    # ═══════════════════════════════════════════════════════
    # DRAGGING — MASCOT
    # ═══════════════════════════════════════════════════════

    def _drag_start(self, event):
        self.drag_x = event.x
        self.drag_y = event.y
        self._drag_moved = False

    def _drag_motion(self, event):
        dx = event.x - self.drag_x
        dy = event.y - self.drag_y
        if abs(dx) > 2 or abs(dy) > 2:
            self._drag_moved = True
        self.mascot_x += dx
        self.mascot_y += dy
        self.mascot_win.geometry(
            f"{MASCOT_SIZE}x{MASCOT_SIZE}+{self.mascot_x}+{self.mascot_y}"
        )
        if self.chat_visible:
            self._reposition_chat()

    def _drag_end(self, event):
        if not self._drag_moved:
            self._toggle_chat()

    def _on_hover_enter(self, event):
        # Show tooltip hint if chat is closed
        if not self.chat_visible:
            self.mascot_canvas.itemconfig(self.glow_ring, width=4)

    def _on_hover_leave(self, event):
        self.mascot_canvas.itemconfig(self.glow_ring, width=1)

    # ═══════════════════════════════════════════════════════
    # DRAGGING — CHAT WINDOW
    # ═══════════════════════════════════════════════════════

    def _chat_drag_start(self, event):
        self._chat_drag_ox = event.x_root - self.chat_win.winfo_x()
        self._chat_drag_oy = event.y_root - self.chat_win.winfo_y()

    def _chat_drag_motion(self, event):
        x = event.x_root - self._chat_drag_ox
        y = event.y_root - self._chat_drag_oy
        self.chat_win.geometry(f"{CHAT_WIDTH}x{CHAT_HEIGHT}+{x}+{y}")

    # ═══════════════════════════════════════════════════════
    # INPUT
    # ═══════════════════════════════════════════════════════

    def _on_keypress(self, event):
        self._reset_activity()

    # ═══════════════════════════════════════════════════════
    # MESSAGING
    # ═══════════════════════════════════════════════════════

    def _send_message(self, event=None):
        query = self.input_var.get().strip()
        if not query or self.is_streaming:
            return

        self._reset_activity()
        self.input_field.delete(0, "end")

        # Display user message
        self._append_message("user", query)

        # Add to history
        self.messages.append({"role": "user", "content": query})

        # Start generation thread
        self.is_streaming = True
        self._set_status("thinking", C_GOLD)
        self.typing_label.config(text="COM is thinking…")

        thread = threading.Thread(target=self._generate, args=(query,), daemon=True)
        thread.start()

    def _generate(self, query):
        """Runs in background thread."""
        try:
            payload = {
                "model": MODEL_NAME,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are COM (Companion Of Master). "
                            "Answer concisely in 1-3 sentences max. "
                            "No greetings. No filler."
                        )
                    }
                ] + self.messages[-8:],   # sliding window
                "stream": True,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 256,
                    "num_ctx": 2048
                }
            }

            resp = requests.post(OLLAMA_URL, json=payload,
                                 stream=True, timeout=30)

            # Prepare response bubble
            self.root.after(0, self._start_com_bubble)

            full_response = ""
            for line in resp.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        chunk = data.get("message", {}).get("content", "")
                        if chunk:
                            full_response += chunk
                            self.root.after(0, lambda c=chunk: self._stream_chunk(c))
                    except json.JSONDecodeError:
                        continue

            self.messages.append({"role": "assistant", "content": full_response})
            self.root.after(0, self._finish_response)

        except requests.exceptions.ConnectionError:
            self.root.after(0, lambda: self._append_system(
                "⚠  Cannot reach Ollama. Is it running?"
            ))
            self.root.after(0, self._finish_response)
        except Exception as e:
            self.root.after(0, lambda: self._append_system(f"⚠  Error: {e}"))
            self.root.after(0, self._finish_response)

    # ═══════════════════════════════════════════════════════
    # CHAT HISTORY HELPERS
    # ═══════════════════════════════════════════════════════

    def _append_message(self, role, text):
        self.chat_history.config(state="normal")
        if role == "user":
            self.chat_history.insert("end", "\nYou  ", "user_name")
            self.chat_history.insert("end", f"{text}\n", "user_text")
        else:
            self.chat_history.insert("end", "\nCOM  ", "com_name")
            self.chat_history.insert("end", f"{text}\n", "com_text")
        self.chat_history.config(state="disabled")
        self.chat_history.see("end")

    def _start_com_bubble(self):
        """Insert COM label before streaming starts."""
        self.chat_history.config(state="normal")
        self.chat_history.insert("end", "\nCOM  ", "com_name")
        self.chat_history.config(state="disabled")
        self.chat_history.see("end")
        self.typing_label.config(text="")

    def _stream_chunk(self, chunk):
        self.chat_history.config(state="normal")
        self.chat_history.insert("end", chunk, "com_text")
        self.chat_history.config(state="disabled")
        self.chat_history.see("end")

    def _finish_response(self):
        self.chat_history.config(state="normal")
        self.chat_history.insert("end", "\n", "com_text")
        self.chat_history.config(state="disabled")
        self.is_streaming = False
        self._set_status("ready", C_SUCCESS)
        self.typing_label.config(text="")
        self._reset_activity()
        # Refocus input after response
        self.root.after(100, self._focus_input)

    def _append_system(self, text):
        self.chat_history.config(state="normal")
        self.chat_history.insert("end", f"\n{text}\n", "system")
        self.chat_history.config(state="disabled")
        self.chat_history.see("end")

    def _set_status(self, state, color):
        self.dot_canvas.itemconfig(self.status_dot, fill=color)

    # ═══════════════════════════════════════════════════════
    # RUN
    # ═══════════════════════════════════════════════════════

    def run(self):
        self.root.mainloop()


# ═══════════════════════════════════════════════════════════════
# ENTRY
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = COMApp()
    app.run()
