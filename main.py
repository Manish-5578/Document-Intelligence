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
API_KEY = "Google_API_Key"
FOLDER_PATH = r"FOlder_Path"
INDEX_FILE = "domain_knowledge_index.json"

# Safety Settings
safety_settings = {
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}


class DocIntelliApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Document Intelligence System")
        self.root.geometry("800x700")
        self.root.configure(bg="#f0f0f0")

        # Logic State
        self.chat_session = None
        self.current_file = None
        self.configure_api()

        # --- UI LAYOUT BASED ON YOUR IMAGE ---

        # 1. TOP HEADER (Thick Border Box)
        header_frame = tk.Frame(root, bg="white", bd=2, relief="solid")
        header_frame.pack(fill="x", padx=20, pady=15)

        tk.Label(header_frame, text="DOCUMENT INTELLIGENCE AI",
                 font=("Segoe UI", 16, "bold"), bg="white", fg="black", pady=10).pack()

        # 2. OPTION BUTTONS (The 3 Boxes)
        btn_frame = tk.Frame(root, bg="#f0f0f0")
        btn_frame.pack(fill="x", padx=20, pady=5)

        # Helper to make styled buttons
        def make_btn(parent, text, cmd):
            return tk.Button(parent, text=text, command=cmd,
                             font=("Segoe UI", 10, "bold"), bg="white", fg="black",
                             bd=2, relief="solid", width=25, height=2)

        # Option 1: Indexing
        self.btn_index = make_btn(btn_frame, "Step 1: Scan & Index Docs", self.start_indexing)
        self.btn_index.pack(side="left", padx=(0, 10), expand=True, fill="x")

        # Option 2: Reset/Clear
        self.btn_reset = make_btn(btn_frame, "Reset / New Search", self.reset_session)
        self.btn_reset.pack(side="left", padx=10, expand=True, fill="x")

        # Option 3: Export
        self.btn_export = make_btn(btn_frame, "Export Chat Log", self.export_log)
        self.btn_export.pack(side="left", padx=(10, 0), expand=True, fill="x")

        # 3. QUERY BAR (Long Horizontal Box)
        query_frame = tk.Frame(root, bg="#f0f0f0")
        query_frame.pack(fill="x", padx=20, pady=15)

        tk.Label(query_frame, text="Query Input:", font=("Segoe UI", 10, "bold"), bg="#f0f0f0").pack(anchor="w")

        self.query_entry = tk.Entry(query_frame, font=("Segoe UI", 12), bd=2, relief="solid")
        self.query_entry.pack(fill="x", ipady=8)
        self.query_entry.bind("<Return>", self.handle_input)  # Press Enter to send

        # 4. OUTPUT AREA (Large Bottom Box)
        output_frame = tk.Frame(root, bg="white", bd=2, relief="solid")
        output_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        tk.Label(output_frame, text="Output / Logs:", font=("Segoe UI", 10, "bold"), bg="white", anchor="w").pack(
            fill="x", padx=5, pady=5)

        self.logs = scrolledtext.ScrolledText(output_frame, font=("Consolas", 10), state='disabled')
        self.logs.pack(fill="both", expand=True, padx=5, pady=5)

        # Log Tags for Colors
        self.logs.tag_config("user", foreground="blue")
        self.logs.tag_config("ai", foreground="green")
        self.logs.tag_config("sys", foreground="gray")
        self.logs.tag_config("err", foreground="red")

        # Initial Welcome Message
        self.log(
            "System Ready. \n1. Click 'Scan & Index' if adding new files.\n2. Type a document name/ID in 'Query' to start.",
            "sys")

    # ================= LOGIC & BACKEND =================

    def log(self, msg, tag="sys"):
        self.logs.config(state='normal')
        self.logs.insert(tk.END, f"{msg}\n", tag)
        self.logs.see(tk.END)
        self.logs.config(state='disabled')

    def configure_api(self):
        genai.configure(api_key=API_KEY)

    def handle_input(self, event=None):
        text = self.query_entry.get().strip()
        if not text: return
        self.query_entry.delete(0, tk.END)

        self.log(f"\nUser: {text}", "user")

        # Mode 1: If no chat active, treat input as SEARCH
        if self.chat_session is None:
            threading.Thread(target=self.run_search, args=(text,), daemon=True).start()
        # Mode 2: If chat active, treat input as QUESTION
        else:
            threading.Thread(target=self.run_chat, args=(text,), daemon=True).start()

    # --- INDEXING LOGIC ---
    def start_indexing(self):
        threading.Thread(target=self.run_indexing, daemon=True).start()

    def run_indexing(self):
        self.log("\n🚀 Starting Indexing Process...", "sys")
        if not os.path.exists(FOLDER_PATH):
            self.log(f"❌ Error: Folder '{FOLDER_PATH}' not found!", "err")
            return

        files = [f for f in os.listdir(FOLDER_PATH) if f.lower().endswith((".pdf", ".jpg", ".png"))]
        index_data = []
        model = genai.GenerativeModel("gemini-2.5-flash")

        for filename in files:
            file_path = os.path.join(FOLDER_PATH, filename)
            self.log(f"Scanning: {filename}...", "sys")
            try:
                uploaded = self.upload_file(file_path)
                prompt = 'Classify: {"category": "...", "doc_type": "...", "search_keywords": ["..."]}'
                response = model.generate_content([uploaded, prompt],
                                                  generation_config={"response_mime_type": "application/json"})
                data = json.loads(response.text)
                data['filename'] = filename
                data['search_keywords'] = [str(k).lower() for k in data.get('search_keywords', [])]
                index_data.append(data)
                self.log(f"✅ Identified: {data['doc_type']}", "ai")
            except Exception as e:
                self.log(f"❌ Error: {e}", "err")

        with open(INDEX_FILE, "w") as f:
            json.dump(index_data, f, indent=4)
        self.log("🎉 Indexing Complete!", "sys")

    # --- SEARCH LOGIC ---
    def run_search(self, query):
        self.log(f"🔎 Searching database for '{query}'...", "sys")

        if not os.path.exists(INDEX_FILE):
            self.log("⚠️ Index not found. Please click 'Scan & Index' first.", "err")
            return

        with open(INDEX_FILE, "r") as f:
            memory = json.load(f)

        found_doc = None
        q_lower = query.lower()

        for entry in memory:
            pool = entry['search_keywords'] + [entry['doc_type'].lower(), entry['filename'].lower()]
            for k in pool:
                k_str = str(k).lower()
                if (len(k_str) > 3 and k_str in q_lower) or (len(q_lower) > 3 and q_lower in k_str):
                    found_doc = entry
                    break
            if found_doc: break

        if found_doc:
            self.current_file = found_doc
            self.log(f"✅ Match Found: {found_doc['filename']}", "ai")
            self.init_chat(found_doc)
        else:
            self.log("❌ No matching document found. Try a different keyword.", "err")

    # --- CHAT LOGIC ---
    def init_chat(self, doc_data):
        self.log("🧠 Loading document into Gemini 2.5 Pro...", "sys")
        full_path = os.path.join(FOLDER_PATH, doc_data['filename'])

        try:
            uploaded = self.upload_file(full_path)
            model = genai.GenerativeModel("gemini-2.5-flash")  # Using Flash for speed/quota
            self.chat_session = model.start_chat(history=[])

            sys_prompt = f"You are analyzing {doc_data['filename']}. Be professional."
            self.chat_session.send_message([uploaded, sys_prompt])

            self.log(f"💬 CHAT STARTED with {doc_data['filename']}.", "ai")
            self.log("Type your question in the box above.", "sys")

        except Exception as e:
            self.log(f"❌ Connection Error: {e}", "err")

    def run_chat(self, msg):
        try:
            response = self.chat_session.send_message(msg, safety_settings=safety_settings)
            self.log(f"AI: {response.text}", "ai")
        except Exception as e:
            if "429" in str(e):
                self.log("⏳ Rate limit hit. Please wait 30s...", "err")
            else:
                self.log(f"❌ Error: {e}", "err")

    # --- UTILS ---
    def upload_file(self, path):
        mime = "application/pdf" if path.lower().endswith(".pdf") else "image/jpeg"
        file = genai.upload_file(path, mime_type=mime)
        while file.state.name == "PROCESSING":
            time.sleep(1)
            file = genai.get_file(file.name)
        return file

    def reset_session(self):
        self.chat_session = None
        self.current_file = None
        self.log("\n🔄 Session Reset. Enter a new search term.", "sys")

    def export_log(self):
        content = self.logs.get("1.0", tk.END)
        with open("exported_log.txt", "w", encoding="utf-8") as f:
            f.write(content)
        messagebox.showinfo("Export", "Logs saved to exported_log.txt")


if __name__ == "__main__":
    root = tk.Tk()
    app = DocIntelliApp(root)
    root.mainloop()

    root.mainloop()
