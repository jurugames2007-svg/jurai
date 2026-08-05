import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox


class BuusFuryEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Buu's Fury Studio (Clean Text Engine)")
        self.root.geometry("900x680")

        self.text_entries = []
        self.table = {}
        self.reverse_table = {}
        self.rom_path = ""

        self.setup_ui()

    def browse_rom(self):
        filepath = filedialog.askopenfilename(title="Select ROM",
                                              filetypes=[("GBA ROM", "*.gba"), ("All Files", "*.*")])
        if filepath:
            self.rom_entry.delete(0, tk.END)
            self.rom_entry.insert(0, filepath)

    def browse_tbl(self):
        filepath = filedialog.askopenfilename(title="Select Table",
                                              filetypes=[("Table File", "*.tbl"), ("All Files", "*.*")])
        if filepath:
            self.tbl_entry.delete(0, tk.END)
            self.tbl_entry.insert(0, filepath)

    def process_files(self):
        self.rom_path = self.rom_entry.get().strip()
        tbl_path = self.tbl_entry.get().strip()

        try:
            self.start_offset = int(self.offset_entry.get().strip(), 16)
        except ValueError:
            messagebox.showerror("Error", "Invalid Hex Offset! Defaulting to 50000.")
            self.offset_entry.delete(0, tk.END)
            self.offset_entry.insert(0, "50000")
            self.start_offset = 0x50000

        if not os.path.exists(self.rom_path) or not os.path.exists(tbl_path):
            messagebox.showerror("Error", "Please select valid files.")
            return

        self.table.clear()
        self.reverse_table.clear()
        self.text_entries.clear()

        self.load_table(tbl_path)
        self.scan_rom()

    def load_table(self, tbl_path):
        try:
            with open(tbl_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.replace('\n', '').replace('\r', '')
                    if '=' in line:
                        parts = line.split('=', 1)
                        if len(parts) == 2:
                            self.table[parts[0].upper()] = parts[1]
                            self.reverse_table[parts[1]] = parts[0].upper()

            self.table['20'] = ' '
            self.reverse_table[' '] = '20'
            self.table['0A'] = '\n'
            self.reverse_table['\n'] = '0A'

            if '00' in self.table:
                del self.table['00']

        except Exception as e:
            messagebox.showerror("Table Error", f"Could not read the table file:\n{e}")

    def scan_rom(self):
        self.listbox.delete(0, tk.END)
        self.listbox.insert(tk.END, "Applying Linguistic Filters... Please wait...")
        self.root.update()

        with open(self.rom_path, 'rb') as f:
            data = f.read()

        current_str = ""
        start_addr = 0
        in_string = False

        # Start at the custom offset to bypass the engine!
        i = self.start_offset

        def save_current_string(end_index):
            nonlocal current_str, in_string

            if in_string:
                clean_str = re.sub(r'(\[[0-9A-F]{2}\])+$', '', current_str).strip()

                # --- THE LINGUISTICS FILTER ---
                # 1. Count how many normal letters/punctuation it has vs bracket tags
                readable_chars = sum(1 for c in clean_str if c.isalnum() or c in ' .,!?\'"-')
                brackets = clean_str.count('[')

                # 2. Vowel Check (Machine code rarely forms words with vowels)
                vowels = sum(1 for c in clean_str.lower() if c in 'aeiouy')

                # 3. Known UI elements that bypass the vowel rule
                is_ui = any(ui in clean_str for ui in ['HP', 'EP', 'XP', 'LVL', 'No'])

                # 4. The Execution:
                # Must have at least 2 real letters. Must have a vowel or be UI. Brackets can't completely outnumber text.
                if readable_chars >= 2 and (vowels > 0 or is_ui) and (brackets <= readable_chars + 2):
                    byte_len = self.calculate_physical_bytes(clean_str)
                    self.text_entries.append({
                        'address': start_addr,
                        'text': clean_str,
                        'max_bytes': byte_len
                    })

            in_string = False
            current_str = ""

        while i < len(data) - 1:
            b1 = data[i]
            b2 = data[i + 1]

            if b2 == 0x00:
                hex1 = f"{b1:02X}"

                if hex1 == "00":
                    save_current_string(i)  # Single Null string termination
                else:
                    if not in_string:
                        in_string = True
                        start_addr = i

                    if hex1 in self.table:
                        current_str += self.table[hex1]
                    else:
                        current_str += f"[{hex1}]"
                i += 2
            else:
                save_current_string(i)
                i += 1

        self.populate_list()

    def calculate_physical_bytes(self, text):
        bytes_count = 0
        i = 0
        while i < len(text):
            if text[i] == '[' and i + 3 < len(text) and text[i + 3] == ']':
                bytes_count += 2
                i += 4
            else:
                bytes_count += 2
                i += 1
        return bytes_count

    def populate_list(self):
        self.listbox.delete(0, tk.END)
        self.listbox.insert(0, f"--- Scan Complete: Found {len(self.text_entries)} clean strings ---")
        self.listbox.itemconfig(0, {'fg': 'green'})

        for entry in self.text_entries:
            gba_ptr = entry['address'] + 0x08000000
            preview_text = entry['text'].replace('\n', ' ↵ ')
            self.listbox.insert(tk.END, f"[{gba_ptr:08X}] {preview_text}")

    def on_select(self, event):
        selection = self.listbox.curselection()
        if not selection:
            return

        index = selection[0]
        if index == 0 or "--- Scan Complete" in self.listbox.get(index):
            return
        if "--- Scan Complete" in self.listbox.get(0):
            index -= 1

        self.current_entry = self.text_entries[index]
        self.max_bytes = self.current_entry['max_bytes']

        self.text_editor.delete(1.0, tk.END)
        self.text_editor.insert(tk.END, self.current_entry['text'])
        self.update_char_count()

    def update_char_count(self, event=None):
        raw_text = self.text_editor.get(1.0, tk.END).strip()
        current_bytes = self.calculate_physical_bytes(raw_text)

        self.lbl_status.config(text=f"ROM Space: {current_bytes} / {self.max_bytes} Bytes")

        if current_bytes > self.max_bytes:
            self.lbl_status.config(fg="red")
            self.btn_save.config(state=tk.DISABLED)
        else:
            self.lbl_status.config(fg="black")
            self.btn_save.config(state=tk.NORMAL)

    def save_to_rom(self):
        new_text = self.text_editor.get(1.0, tk.END).strip('\n')

        if self.calculate_physical_bytes(new_text) > self.max_bytes:
            messagebox.showerror("Error", "Text requires too much space! Cannot inject.")
            return

        compiled_bytes = bytearray()
        i = 0

        while i < len(new_text):
            char = new_text[i]

            if char == '[' and i + 3 < len(new_text) and new_text[i + 3] == ']':
                hex_code = new_text[i + 1:i + 3]
                try:
                    compiled_bytes.append(int(hex_code, 16))
                    compiled_bytes.append(0x00)
                    i += 4
                    continue
                except ValueError:
                    pass

            hex_val = self.reverse_table.get(char, "20")
            compiled_bytes.append(int(hex_val, 16))
            compiled_bytes.append(0x00)
            i += 1

        while len(compiled_bytes) < self.max_bytes:
            compiled_bytes.append(0x00)

        try:
            with open(self.rom_path, 'r+b') as f:
                f.seek(self.current_entry['address'])
                f.write(compiled_bytes)

            messagebox.showinfo("Success", f"Injected perfectly at {hex(self.current_entry['address'])}!")
            self.current_entry['text'] = new_text
            self.populate_list()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to write to ROM:\n{e}")

    def export_to_txt(self):
        if not self.text_entries:
            return
        filepath = filedialog.asksaveasfilename(title="Export Dialogue", defaultextension=".txt",
                                                filetypes=[("Text File", "*.txt"), ("All Files", "*.*")])
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    for entry in self.text_entries:
                        gba_ptr = entry['address'] + 0x08000000
                        f.write(f"[{gba_ptr:08X}] {entry['text']}\n")
                messagebox.showinfo("Success", f"Exported to:\n{filepath}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export:\n{e}")

    def setup_ui(self):
        top_frame = tk.LabelFrame(self.root, text="Configuration", padx=10, pady=10)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        tk.Label(top_frame, text="ROM File:", width=15, anchor="w").grid(row=0, column=0, pady=2)
        self.rom_entry = tk.Entry(top_frame, width=65)
        self.rom_entry.grid(row=0, column=1, padx=5, pady=2)
        tk.Button(top_frame, text="Browse...", command=self.browse_rom).grid(row=0, column=2, padx=5)

        tk.Label(top_frame, text="Table File:", width=15, anchor="w").grid(row=1, column=0, pady=2)
        self.tbl_entry = tk.Entry(top_frame, width=65)
        self.tbl_entry.grid(row=1, column=1, padx=5, pady=2)
        tk.Button(top_frame, text="Browse...", command=self.browse_tbl).grid(row=1, column=2, padx=5)

        tk.Label(top_frame, text="Start Offset (Hex):", width=15, anchor="w").grid(row=2, column=0, pady=2)
        self.offset_entry = tk.Entry(top_frame, width=65)
        self.offset_entry.insert(0, "50000")  # Bypasses engine code!
        self.offset_entry.grid(row=2, column=1, padx=5, pady=2)

        tk.Button(top_frame, text="Load Files & Scan ROM", command=self.process_files, bg="#e0f7fa",
                  font=("Arial", 10, "bold")).grid(row=3, column=0, columnspan=3, pady=10)

        main_frame = tk.Frame(self.root)
        main_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        left_frame = tk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        tk.Label(left_frame, text="Dialogue Bank:").pack(anchor=tk.W)

        scrollbar = tk.Scrollbar(left_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox = tk.Listbox(left_frame, yscrollcommand=scrollbar.set, font=("Courier", 10))
        self.listbox.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.listbox.bind('<<ListboxSelect>>', self.on_select)
        scrollbar.config(command=self.listbox.yview)

        tk.Button(left_frame, text="Export to TXT", command=self.export_to_txt, bg="#fff9c4", font=("Arial", 10)).pack(
            side=tk.BOTTOM, fill=tk.X, pady=5)

        right_frame = tk.Frame(main_frame, width=320)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=10, pady=10)

        tk.Label(right_frame, text="Edit Selected Text:").pack(anchor=tk.W)

        self.text_editor = tk.Text(right_frame, height=12, width=40, font=("Courier", 12))
        self.text_editor.pack(pady=5)
        self.text_editor.bind('<KeyRelease>', self.update_char_count)

        self.lbl_status = tk.Label(right_frame, text="ROM Space: 0 / 0 Bytes", font=("Arial", 10, "bold"))
        self.lbl_status.pack(pady=5)

        self.btn_save = tk.Button(right_frame, text="Inject into ROM", command=self.save_to_rom, bg="lightgreen",
                                  font=("Arial", 12, "bold"))
        self.btn_save.pack(pady=10, fill=tk.X)

        tk.Label(right_frame,
                 text="Note: Pressing ENTER creates a\nnewline, which uses 2 Bytes.\nDo not exceed ROM space limits.",
                 justify=tk.LEFT, fg="gray").pack(side=tk.BOTTOM, pady=10)


if __name__ == "__main__":
    root = tk.Tk()
    app = BuusFuryEditor(root)
    root.mainloop()