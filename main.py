import os
import json
import time
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# ======================================================
# CONFIGURATION
# ======================================================
# ⚠️ API KEY - Ensure this is correct
API_KEY = "Google_API_Key"
FOLDER_PATH = r"Your path "
INDEX_FILE = "domain_knowledge_index.json"

# ======================================================
# AESTHETIC COLOR PALETTE (Minimalist Light Theme)
# ======================================================
COLOR_BG = "#F4F7F6"  # Soft Cloud Blue-Grey (Main Background)
COLOR_PANEL = "#FFFFFF"  # Pure White (Cards/Panels)
COLOR_PRIMARY = "#5C6BC0"  # Soft Indigo (Buttons/Accents)
COLOR_HOVER = "#3949AB"  # Darker Indigo (Hover)
COLOR_TEXT = "#37474F"  # Dark Blue-Grey (Main Text)
COLOR_SUBTEXT = "#78909C"  # Muted Gray (Subtitles)
COLOR_USER_TAG = "#1565C0"  # Blue (User Messages)
COLOR_AI_TAG = "#00695C"  # Teal (AI Messages)
COLOR_ERR_TAG = "#D32F2F"  # Soft Red (Errors)

# Configure API
genai.configure(api_key=API_KEY)
safety_settings = {
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}


class AestheticDocApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Document Intelligence AI")
        self.root.geometry("1100x800")
        self.root.configure(bg=COLOR_BG)

        # State
        self.chat_session = None

        # --- FONTS ---
        self.font_header = ("Segoe UI", 18, "bold")
        self.font_btn = ("Segoe UI", 10, "bold")
        self.font_main = ("Segoe UI", 11)
        self.font_mono = ("Consolas", 10)

        # --- BUILD UI ---
        self.build_layout()
        self.start_up_sequence()

    def build_layout(self):
        # 1. HEADER (Floating Card Style)
        header_frame = tk.Frame(self.root, bg=COLOR_PANEL, padx=20, pady=15)
        header_frame.pack(fill="x", padx=30, pady=(30, 15))

        # Add a subtle shadow border effect using a bottom frame
        shadow = tk.Frame(self.root, bg="#E0E0E0", height=2)
        shadow.place(in_=header_frame, relx=0, rely=1, relwidth=1, y=0)

        tk.Label(header_frame, text="Document Intelligence Agent",
                 font=self.font_header, bg=COLOR_PANEL, fg=COLOR_TEXT).pack(anchor="w")

        self.status_lbl = tk.Label(header_frame, text="System Ready",
                                   font=("Segoe UI", 10), bg=COLOR_PANEL, fg=COLOR_SUBTEXT)
        self.status_lbl.pack(anchor="w")

        # 2. CONTROL BAR (Minimalist Buttons)
        control_frame = tk.Frame(self.root, bg=COLOR_BG)
        control_frame.pack(fill="x", padx=30, pady=5)

        self.btn_index = self.create_aesthetic_btn(control_frame, "📂 Scan & Index", self.start_indexing)
        self.btn_index.pack(side="left", padx=(0, 15))

        self.btn_reset = self.create_aesthetic_btn(control_frame, "🔄 Reset Chat", self.reset_session)
        self.btn_reset.pack(side="left", padx=(0, 15))

        self.btn_export = self.create_aesthetic_btn(control_frame, "💾 Export Log", self.export_log)
        self.btn_export.pack(side="right")

        # 3. MAIN WORKSPACE (Split View)
        workspace = tk.Frame(self.root, bg=COLOR_BG)
        workspace.pack(fill="both", expand=True, padx=30, pady=15)

        # Left Side: Query Input
        input_panel = tk.Frame(workspace, bg=COLOR_PANEL, padx=15, pady=15)
        input_panel.pack(side="top", fill="x", pady=(0, 15))

        tk.Label(input_panel, text="QUERY / COMMAND", font=("Segoe UI", 9, "bold"),
                 bg=COLOR_PANEL, fg=COLOR_SUBTEXT).pack(anchor="w", pady=(0, 5))

        self.query_entry = tk.Entry(input_panel, font=("Segoe UI", 14),
                                    bg="#FAFAFA", fg=COLOR_TEXT,
                                    relief="flat", bd=0, highlightthickness=1, highlightbackground="#E0E0E0")
        self.query_entry.pack(fill="x", ipady=10, padx=2)
        self.query_entry.bind("<Return>", self.handle_input)

        # Bottom Side: Logs (The "Paper" look)
        log_panel = tk.Frame(workspace, bg=COLOR_PANEL, padx=2, pady=2)
        log_panel.pack(side="bottom", fill="both", expand=True)

        self.logs = scrolledtext.ScrolledText(log_panel, font=self.font_main,
                                              bg=COLOR_PANEL, fg=COLOR_TEXT,
                                              bd=0, state='disabled', padx=15, pady=15)
        self.logs.pack(fill="both", expand=True)

        # Tags for beautiful text formatting
        self.logs.tag_config("user", foreground=COLOR_USER_TAG, font=("Segoe UI", 11, "bold"))
        self.logs.tag_config("ai", foreground=COLOR_AI_TAG)
        self.logs.tag_config("sys", foreground=COLOR_SUBTEXT, font=("Segoe UI", 10, "italic"))
        self.logs.tag_config("err", foreground=COLOR_ERR_TAG)
        self.logs.tag_config("header", font=("Segoe UI", 12, "bold", "underline"), spacing3=10)

    def create_aesthetic_btn(self, parent, text, cmd):
        """Creates a modern, flat button with hover effects"""
        btn = tk.Button(parent, text=text, command=cmd,
                        bg=COLOR_PANEL, fg=COLOR_PRIMARY,
                        font=self.font_btn,
                        relief="flat", bd=0, padx=20, pady=8,
                        cursor="hand2", activebackground=COLOR_BG)

        # Rounded corner simulation via border (optional, kept simple for Tkinter)
        btn.config(highlightbackground=COLOR_PRIMARY, highlightthickness=1)

        def on_enter(e):
            btn['bg'] = COLOR_PRIMARY
            btn['fg'] = "#FFFFFF"

        def on_leave(e):
            btn['bg'] = COLOR_PANEL
            btn['fg'] = COLOR_PRIMARY

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    def start_up_sequence(self):
        self.log_message("System Initialized.", "sys")
        self.log_message("Please ensure your documents are in the folder.", "sys")
        self.log_message("1. Click 'Scan & Index' to build memory.", "sys")
        self.log_message("2. Type 'Invoices' or a specific ID to search.", "sys")

    # ================= LOGIC =================

    def log_message(self, msg, tag="sys", animate=True):
        self.logs.config(state='normal')
        self.logs.insert(tk.END, "\n")

        if animate and tag == "ai":
            # Typing effect for AI
            for char in msg:
                self.logs.insert(tk.END, char, tag)
                self.logs.see(tk.END)
                self.logs.update()
                time.sleep(0.005)  # Fast typing
        else:
            self.logs.insert(tk.END, f"{msg}", tag)

        self.logs.see(tk.END)
        self.logs.config(state='disabled')

    def handle_input(self, event=None):
        text = self.query_entry.get().strip()
        if not text: return
        self.query_entry.delete(0, tk.END)

        self.log_message(f"You: {text}", "user", animate=False)

        if self.chat_session is None:
            threading.Thread(target=self.run_search, args=(text,), daemon=True).start()
        else:
            threading.Thread(target=self.run_chat, args=(text,), daemon=True).start()

    # --- FIXED ROBUST INDEXING ---
    def start_indexing(self):
        threading.Thread(target=self.run_indexing, daemon=True).start()

    def run_indexing(self):
        self.status_lbl.config(text="Status: Indexing... (Please wait)")
        self.log_message("🚀 Starting Indexing Sequence...", "sys")

        if not os.path.exists(FOLDER_PATH):
            self.log_message(f"❌ Error: Folder not found: {FOLDER_PATH}", "err")
            return

        files = [f for f in os.listdir(FOLDER_PATH) if f.lower().endswith((".pdf", ".jpg", ".png", ".jpeg"))]

        if not files:
            self.log_message("⚠️ No supported files found in folder.", "err")
            self.status_lbl.config(text="Status: Idle")
            return

        index_data = []
        model = genai.GenerativeModel("gemini-2.5-flash")

        for filename in files:
            self.status_lbl.config(text=f"Status: Scanning {filename}...")
            file_path = os.path.join(FOLDER_PATH, filename)

            try:
                # Robust Upload
                uploaded = self.upload_file_robust(file_path)
                if not uploaded: continue

                # Generate Metadata
                prompt = 'Classify this document. Return JSON: {"category": "...", "doc_type": "...", "search_keywords": ["..."]}'
                response = model.generate_content(
                    [uploaded, prompt],
                    generation_config={"response_mime_type": "application/json"}
                )

                data = json.loads(response.text)
                data['filename'] = filename
                data['search_keywords'] = [str(k).lower() for k in data.get('search_keywords', [])]
                index_data.append(data)

                self.log_message(f"✅ Indexed: {filename} [{data['doc_type']}]", "sys", animate=False)
                time.sleep(1)  # Prevent Rate Limit

            except Exception as e:
                self.log_message(f"❌ Failed: {filename} ({e})", "err")

        with open(INDEX_FILE, "w") as f:
            json.dump(index_data, f, indent=4)

        self.log_message(f"🎉 Indexing Complete. {len(index_data)} files saved.", "ai")
        self.status_lbl.config(text="Status: Ready")

    def upload_file_robust(self, path):
        """Handles timeouts and failed states correctly"""
        mime = "application/pdf" if path.lower().endswith(".pdf") else "image/jpeg"
        try:
            file = genai.upload_file(path, mime_type=mime)
            # Wait loop with timeout
            for _ in range(30):
                if file.state.name == "ACTIVE":
                    return file
                elif file.state.name == "FAILED":
                    return None
                time.sleep(1)
                file = genai.get_file(file.name)
            return None
        except:
            return None

    # --- MULTI-FILE SEARCH LOGIC ---
    def run_search(self, query):
        self.status_lbl.config(text=f"Status: Searching for '{query}'...")

        if not os.path.exists(INDEX_FILE):
            self.log_message("⚠️ Database empty. Click 'Scan & Index' first.", "err")
            return

        with open(INDEX_FILE, "r") as f:
            memory = json.load(f)

        matches = []
        q_lower = query.lower()

        # Find ALL matches
        for entry in memory:
            pool = entry['search_keywords'] + [entry['doc_type'].lower(), entry['category'].lower(),
                                               entry['filename'].lower()]
            for k in pool:
                k_str = str(k).lower()
                if (len(k_str) > 3 and k_str in q_lower) or (len(q_lower) > 3 and q_lower in k_str):
                    matches.append(entry)
                    break

        if not matches:
            self.log_message("❌ No matches found.", "err")
            self.status_lbl.config(text="Status: Idle")

        elif len(matches) == 1:
            # Single match - Auto start
            self.log_message(f"✅ Match: {matches[0]['filename']}", "ai")
            self.init_chat(matches[0])

        else:
            # Multiple matches - List them
            self.log_message(f"📚 Found {len(matches)} documents:", "header")
            for doc in matches:
                self.log_message(f" • {doc['filename']} ({doc['doc_type']})", "sys", animate=False)
            self.log_message("👉 Please type the specific filename to chat.", "ai")
            self.status_lbl.config(text="Status: Multiple matches found")

    def init_chat(self, doc_data):
        self.status_lbl.config(text=f"Status: Loading {doc_data['filename']}...")
        full_path = os.path.join(FOLDER_PATH, doc_data['filename'])

        try:
            uploaded = self.upload_file_robust(full_path)
            model = genai.GenerativeModel("gemini-2.5-flash")
            self.chat_session = model.start_chat(history=[])

            sys_prompt = f"You are analyzing {doc_data['filename']}. Be professional and concise."
            self.chat_session.send_message([uploaded, sys_prompt])

            self.log_message(f"💬 Chat Active with {doc_data['filename']}.", "ai")
            self.status_lbl.config(text="Status: Chat Active")

        except Exception as e:
            self.log_message(f"❌ Connection Error: {e}", "err")

    def run_chat(self, msg):
        self.status_lbl.config(text="Status: AI Thinking...")
        try:
            response = self.chat_session.send_message(msg, safety_settings=safety_settings)
            self.log_message(response.text, "ai")
            self.status_lbl.config(text="Status: Chat Active")
        except Exception as e:
            if "429" in str(e):
                self.log_message("⏳ Rate limit. Please wait...", "err")
            else:
                self.log_message(f"❌ Error: {e}", "err")

    def reset_session(self):
        self.chat_session = None
        self.log_message("🔄 Session Reset.", "sys")
        self.status_lbl.config(text="Status: Idle")

    def export_log(self):
        content = self.logs.get("1.0", tk.END)
        with open("exported_log.txt", "w", encoding="utf-8") as f:
            f.write(content)
        messagebox.showinfo("Export", "Logs saved.")


if __name__ == "__main__":
    root = tk.Tk()
    app = AestheticDocApp(root)
    root.mainloop()
