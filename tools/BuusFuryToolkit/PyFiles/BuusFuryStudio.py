"""Buu's Fury Studio — Unified GBA modding application.
Tabs: Text Editor | Dialogue | Sprites | Stats & Values
"""

import os
import re
import struct
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import gba_utils

# ---------------------------------------------------------------------------
# Character / Enemy address data (from Base Stats.txt and Enemies.txt)
# ---------------------------------------------------------------------------

CHARACTER_STAT_STRUCT = [
    ("Level",       1, "u8"),
    ("HP",          2, "u16"),
    ("EP",          2, "u16"),
    ("Strength",    1, "u8"),
    ("Power",       1, "u8"),
    ("Endurance",   1, "u8"),
    ("Speed",       1, "u8"),
    ("Person Type", 1, "u8"),
    ("Tech Count",  1, "u8"),
    ("Tech 1",      1, "u8"),
    ("Tech 2",      1, "u8"),
    ("Tech 3",      1, "u8"),
    ("Tech 4",      1, "u8"),
    ("Tech 5",      1, "u8"),
    ("Tech 6",      1, "u8"),
]

CHARACTERS = [
    ("Goku",    0x6FDA4C),
    ("Gohan",   0x6FDA5E),
    ("Goten",   0x6FDA70),
    ("Trunks",  0x6FDA82),
    ("Vegeta",  0x6FDA94),
    ("Gotenks", 0x6FDAA6),
    ("Vegito",  0x6FDAB8),
    ("Gogeta",  0x6FDACA),
    ("Hercule", 0x6FDADC),
]

# Enemy struct: [XP 3B] 00 [HP 3B] 00 [Type 2B] 00 00 [Level][Str][Pow][End][12B post-battle]
ENEMY_STAT_STRUCT = [
    ("XP (low)",    1, "u8"),
    ("XP (mid)",    1, "u8"),
    ("XP (high)",   1, "u8"),
    ("_pad1",       1, "u8"),
    ("HP (low)",    1, "u8"),
    ("HP (mid)",    1, "u8"),
    ("HP (high)",   1, "u8"),
    ("_pad2",       1, "u8"),
    ("Enemy Type",  2, "u16"),
    ("_pad3",       1, "u8"),
    ("_pad4",       1, "u8"),
    ("Level",       1, "u8"),
    ("Strength",    1, "u8"),
    ("Power",       1, "u8"),
    ("Endurance",   1, "u8"),
]

ENEMIES = [
    ("Fighter",            0x711BDC),
    ("Olibu",              0x711BC0),
    ("Pikkon",             0x711C68),
    ("Criminal",           0x711418),
    ("Mercenary",          0x711AA8),
    ("Gunman",             0x711744),
    ("Bomber",             0x711354),
    ("Thug",               0x712074),
    ("Tank",               0x712058),
    ("Goten (1)",          0x71169C),
    ("Vegeta",             0x712154),
    ("Goten (2)",          0x711680),
    ("Tournament Boy",     0x7118E8),
    ("Idasa",              0x7117D0),
    ("Hercule",            0x711760),
    ("Spopovich (1)",      0x711E60),
    ("Spopovich (2)",      0x711E7C),
    ("Spopovich (3)",      0x711E98),
    ("Yamu",               0x712288),
    ("Majin Fighter",      0x7119E4),
    ("Majin Soldier",      0x711A00),
    ("Destroyer",          0x7114A4),
    ("Laser Turret",       0x711974),
    ("PuiPui",             0x711CF4),
    ("Majin Shield Soldier", 0x711DB8),
    ("Yakon",              0x712250),
    ("Mini-Yakon",         0x71226C),
    ("Dabura",             0x71146C),
    ("Majin Vegeta",       0x711A1C),
    ("Babidi",             0x7112E4),
    ("Majin Buu (1)",      0x711568),
    ("Hooligan",           0x711798),
    ("Sniper",             0x711E44),
    ("Goon",               0x711664),
    ("Hessian",            0x71177C),
    ("Juggernaut",         0x7118CC),
    ("Mad Bomber",         0x7119C8),
    ("Skeleton",           0x711E28),
    ("Ghost",              0x7115F4),
    ("Vampire",            0x712100),
    ("Pilaf's Guardian",   0x711958),
    ("Mummy",              0x711AE0),
    ("Totenhotep",         0x712090),
    ("Ninja",              0x711AFC),
    ("Ninja in a box",     0x711B18),
    ("Samurai",            0x711D48),
    ("Ninja Boss",         0x711B34),
    ("Cyborg",             0x711450),
    ("Bio Mech",           0x711300),
    ("Mechanoid",          0x711A54),
    ("Airship Warlord",    0x711274),
    ("Phantom",            0x711C14),
    ("Elite Majin Fighter",0x7114C0),
    ("Elite Majin Soldier",0x7114DC),
    ("Shinobi in a box",   0x711DF0),
    ("Shinobi",            0x711DD4),
    ("Ghoul",              0x711610),
    ("Rapscallion",        0x711D10),
    ("Vlad",               0x71218C),
    ("Grenadier",          0x711728),
    ("Knight Destroyer",   0x71193C),
    ("Assassin",           0x7112AC),
    ("Marauder",           0x711A38),
    ("Bones",              0x711370),
    ("Bruiser",            0x7113C4),
    ("Cursed One",         0x711434),
    ("Ronin",              0x711D2C),
    ("Broly",              0x71138C),
    ("Majin Buu (2)",      0x711584),
    ("Janemba Hand",       0x7118B0),
    ("Living Dead",        0x7119AC),
    ("Poltergeist",        0x711C84),
    ("Nosferatu",          0x711B6C),
    ("Lich",               0x711990),
    ("Annihilator",        0x711290),
    ("Elite Shield Soldier",0x7114F8),
    ("Janemba",            0x711808),
    ("Mini-Janemba",       0x711894),
    ("Super Janemba",      0x711FCC),
    ("Goten (E)",          0x7116B8),
    ("Trunks (E)",         0x7120AC),
    ("Super Buu",          0x711F08),
    ("Death Machine",      0x711488),
    ("Hyper Cyborg",       0x7117B4),
    ("Super Buu (2)",      0x711F5C),
    ("Metal Hulk",         0x711AC4),
    ("Power Mechanoid",    0x711CBC),
    ("Super Buu (3)",      0x711F78),
    ("Blood Cell",         0x711338),
    ("Blister",            0x71131C),
    ("Enzyme",             0x711514),
    ("Worm Head",          0x7121FC),
    ("Worm Body & Tail",   0x712218),
    ("Gotenks (E)",        0x7116D4),
    ("Gohan (E)",          0x711648),
    ("Piccolo",            0x711C4C),
    ("Super Buu (4)",      0x711FB0),
    ("Kid Buu",            0x711904),
]

PERSON_TYPES = {
    0x00: "Goku", 0x01: "Goku (Ending)", 0x02: "Goku (Dead)",
    0x03: "Goku SSJ", 0x04: "Goku SSJ (Dead)", 0x05: "Goku SSJ3",
    0x06: "Goku SSJ3 (Dead)", 0x09: "Gohan (Black Suit)",
    0x0A: "Gohan (School)", 0x0B: "Gohan (Kai)", 0x0D: "Gohan (Orange)",
    0x0E: "Gohan (Saiyaman)", 0x0F: "Gohan (WT Suit)",
    0x10: "Gohan (School SSJ)", 0x12: "Gohan (WT SSJ)",
    0x13: "Goten", 0x14: "Goten SSJ", 0x15: "Trunks", 0x16: "Trunks SSJ",
    0x17: "Trunks (Ending)", 0x1A: "Vegeta", 0x1B: "Vegeta (Dead)",
    0x1C: "Vegeta SSJ", 0x1E: "Majin Vegeta", 0x1F: "Gotenks",
    0x20: "Gotenks (Fat)", 0x21: "Gotenks (Old)", 0x22: "Gotenks SSJ",
    0x23: "Gotenks SSJ3", 0x27: "Vegito", 0x28: "Vegito SSJ",
    0x29: "Gogeta SSJ", 0x2A: "Gogeta (Fat)", 0x2B: "Gogeta (Old)",
    0x2D: "Hercule (Glitch)", 0x2E: "Android #18", 0x2F: "Hercule",
    0x30: "Krillin", 0x31: "Piccolo", 0x32: "Pikkon",
    0x33: "Tien", 0x34: "Videl", 0x35: "Yamcha",
}

EQUIP_LIST = [
    (0x00,"None (Body)"),(0x01,"Dirty Shirt"),(0x02,"Dirty Gi"),(0x03,"Dirty Armor"),
    (0x04,"Prototype Space Armor"),(0x05,"Cotton Gi"),(0x06,"Wool Sweater"),
    (0x07,"Leather Jacket"),(0x08,"Reflective Tunic"),(0x09,"Clean Shirt"),
    (0x0A,"Wooden Armor"),(0x0B,"Fancy Wardrobe"),(0x0C,"Stone O-Yoroi"),
    (0x0D,"Bronze Keiko"),(0x0E,"Halloween Costume"),(0x0F,"Armor of Darkness"),
    (0x10,"Jade Keiko"),(0x11,"Clean Gi"),(0x12,"Iron Armor"),(0x13,"Brute Coat"),
    (0x14,"Spiked Breastplate"),(0x15,"Mystic Aegis"),(0x16,"Do-Maru of Shadows"),
    (0x17,"Silver Armor"),(0x18,"Monk's Robe"),(0x19,"Pyrite Armor"),
    (0x1A,"Gold Armor"),(0x1B,"Stylish Haori"),(0x1C,"Armor of Light"),
    (0x1D,"Rhinestone Leisure Suit"),(0x1E,"Clean Armor"),(0x1F,"Platinum Armor"),
    (0x20,"Force Suit"),(0x21,"Enhanced Space Armor"),(0x22,"Dragon Armor"),
    (0x23,"Super Armor"),(0x24,"Wet Suit"),(0x25,"Diamond Armor"),
    (0x26,'"BAD MAN" Shirt'),(0x27,"Titanium Breastplate"),(0x28,"Saiyan Armor"),
    (0x29,"Crystal O-Yoroi"),(0x2A,'"Z" Armor'),(0x2B,"Geromantium Katanigu"),
    (0x2C,"None (Hands)"),(0x2D,"Dirty Gloves"),(0x2E,"Dirty Gauntlets"),
    (0x2F,"Prototype Energy Gloves"),(0x30,"Cotton Gloves"),(0x31,"1 Ton Armbands"),
    (0x32,"Wool Mittens"),(0x33,"Reflective Gloves"),(0x34,"2 Ton Armbands"),
    (0x35,"Leather Gloves"),(0x36,"Clean Gloves"),(0x37,"Brass Knuckles"),
    (0x38,"Pilaf's Gloves"),(0x39,"10 Ton Armbands"),(0x3A,"Iron Bracer"),
    (0x3B,"Silver Gauntlets"),(0x3C,"Magician Gloves"),(0x3D,"Charge Gloves"),
    (0x3E,"20 Ton Armbands"),(0x3F,"Super Gloves"),(0x40,"Clean Gauntlets"),
    (0x41,"Platinum Gauntlets"),(0x42,"Brute Gloves"),(0x43,"100 Ton Armbands"),
    (0x44,"Diamond Gauntlets"),(0x45,"Power Gauntlets"),(0x46,"Enhanced Energy Gloves"),
    (0x47,"Scuba Gloves"),(0x48,"Kiloton Armbands"),(0x49,"Saiyan Gloves"),
    (0x4A,"Crystal Gauntlets"),(0x4B,"Geromantis Gloves"),(0x4C,"Geromantium Gloves"),
    (0x4D,"None (Feet)"),(0x4E,"Dirty Tabi"),(0x4F,"Dirty Shoes"),
    (0x50,"Prototype Hyper Boots"),(0x51,"Dirty Boots"),(0x52,"Cotton Tabi"),
    (0x53,"1 Ton Boots"),(0x54,"Woolen Shoes"),(0x55,"Leather Moccasins"),
    (0x56,"2 Ton Boots"),(0x57,"Clean Tabi"),(0x58,"Wooden Geta"),
    (0x59,"Sneakers"),(0x5A,"10 Ton Boots"),(0x5B,"Stone Geta"),
    (0x5C,"Alligator Loafers"),(0x5D,"Spirit Geta"),(0x5E,"Bronze Plated Boots"),
    (0x5F,"Iron Greaves"),(0x60,"20 Ton Boots"),(0x61,"Flippers"),
    (0x62,"Clean Shoes"),(0x63,"Silver Boots"),(0x64,"Silvery Boots"),
    (0x65,"Super Boots"),(0x66,"100 Ton Boots"),(0x67,"Gold Boots"),
    (0x68,"Shock Boots"),(0x69,"Enhanced Hyper Boots"),(0x6A,"Kiloton Boots"),
    (0x6B,"Saiyan Boots"),(0x6C,"Clean Boots"),(0x6D,"Winged Sandals"),
    (0x6E,"Soccer Cleats"),(0x6F,"Geromantium Tabi"),
    (0x70,"None (Accessories)"),(0x71,"Dirty Cape"),(0x72,"Dirty Belt"),
    (0x73,"Expensive Wristwatch"),(0x74,"White Belt"),(0x75,"Rhinestone Sunglasses"),
    (0x76,"Primordial Twisty-Straw"),(0x77,"Majestic Chopsticks"),(0x78,"Wool Cap"),
    (0x79,"Lucky Charm"),(0x7A,"Stone Men-po"),(0x7B,"Quartz Amulet"),
    (0x7C,"Yellow Belt"),(0x7D,"Topaz Amulet"),(0x7E,"Bandana"),
    (0x7F,"Red Belt"),(0x80,"Demon Mask"),(0x81,"Monocle"),
    (0x82,"Monocle (Glitch)"),(0x83,"Hare's Foot"),(0x84,"Green Belt"),
    (0x85,"Snorkel"),(0x86,"Clean Cape"),(0x87,"Garlic Necklace"),
    (0x88,"Rabbit's Foot"),(0x89,"Sapphire Amulet"),(0x8A,"Skull Ring"),
    (0x8B,"Pure Black Cape"),(0x8C,"Super Cape"),(0x8D,"Talisman of Light"),
    (0x8E,"Emerald Amulet"),(0x8F,"Doom Amulet"),(0x90,"Polka-Dot Kazoo"),
    (0x91,"Iron Kabuto"),(0x92,"Ox-King's Hat"),(0x93,"Evil Talisman"),
    (0x94,"Crystal Pendant"),(0x95,"Blue Belt"),(0x96,"Mercury's Cap"),
    (0x97,"Four-Leaf Clover"),(0x98,"Vampire Cape"),(0x99,"Crisis Ring"),
    (0x9A,"Brown Belt"),(0x9B,"Ruby Amulet"),(0x9C,"Eldritch Cameo"),
    (0x9D,"Black Belt"),(0x9E,"Diamond Amulet"),(0x9F,"Clean Belt"),
    (0xA0,"Geromantium Bandana"),(0xA1,'"Gokuu" Hat'),
]
# Per-slot filtered views (ID, display string)
_EQUIP_BODY  = [(eid, name) for eid, name in EQUIP_LIST if eid < 0x2C]
_EQUIP_HANDS = [(eid, name) for eid, name in EQUIP_LIST if 0x2C <= eid < 0x4D]
_EQUIP_FEET  = [(eid, name) for eid, name in EQUIP_LIST if 0x4D <= eid < 0x70]
_EQUIP_ACC   = [(eid, name) for eid, name in EQUIP_LIST if eid >= 0x70]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def read_bytes_at(rom_data: bytes, offset: int, count: int) -> int:
    """Read `count` bytes as little-endian unsigned int."""
    val = 0
    for k in range(count):
        val |= rom_data[offset + k] << (8 * k)
    return val


def write_bytes_at(rom_path: str, offset: int, value: int, count: int):
    with open(rom_path, 'r+b') as f:
        f.seek(offset)
        for k in range(count):
            f.write(bytes([(value >> (8 * k)) & 0xFF]))


# ---------------------------------------------------------------------------
# Tab 1 — Text Editor (ported from DialogFinder.py)
# ---------------------------------------------------------------------------

class TextEditorTab(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.text_entries = []
        self.display_mapping = {}
        self.current_entry = None
        self.max_bytes = 0
        self.editor_font_size = 12
        self._build_ui()

    def _build_ui(self):
        # Config row
        cfg = tk.LabelFrame(self, text="Scan Configuration", padx=8, pady=6)
        cfg.pack(fill=tk.X, padx=8, pady=6)
        tk.Label(cfg, text="Start Offset (Hex):").grid(row=0, column=0, sticky="w")
        self.offset_entry = tk.Entry(cfg, width=20)
        self.offset_entry.insert(0, "50000")
        self.offset_entry.grid(row=0, column=1, padx=6)
        tk.Button(cfg, text="Scan ROM", command=self.scan_rom,
                  bg="#e0f7fa", font=("Arial", 10, "bold")).grid(row=0, column=2, padx=6)
        tk.Button(cfg, text="Export TXT", command=self.export_to_txt,
                  bg="#fff9c4").grid(row=0, column=3, padx=4)

        # Paned area
        pane = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=6)
        pane.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)

        left = tk.Frame(pane)
        pane.add(left, minsize=340)

        sf = tk.Frame(left)
        sf.pack(fill=tk.X, pady=(0, 4))
        tk.Label(sf, text="Search:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *_: self.populate_list(self.search_var.get()))
        tk.Entry(sf, textvariable=self.search_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)

        sb = tk.Scrollbar(left)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox = tk.Listbox(left, yscrollcommand=sb.set, font=("Courier", 10))
        self.listbox.pack(fill=tk.BOTH, expand=True)
        self.listbox.bind("<<ListboxSelect>>", self.on_select)
        sb.config(command=self.listbox.yview)

        right = tk.Frame(pane)
        pane.add(right, minsize=280)

        hdr = tk.Frame(right)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="Edit Selected Text:").pack(side=tk.LEFT)
        tk.Button(hdr, text="A+", command=self.zoom_in, width=3).pack(side=tk.RIGHT, padx=2)
        tk.Button(hdr, text="A-", command=self.zoom_out, width=3).pack(side=tk.RIGHT)

        self.text_editor = tk.Text(right, height=12, font=("Courier", self.editor_font_size))
        self.text_editor.pack(fill=tk.BOTH, expand=True, pady=4)
        self.text_editor.bind("<KeyRelease>", self.update_char_count)

        self.lbl_status = tk.Label(right, text="ROM Space: 0 / 0 Bytes", font=("Arial", 10, "bold"))
        self.lbl_status.pack(pady=4)

        self.btn_save = tk.Button(right, text="Inject into ROM", command=self.save_to_rom,
                                  bg="lightgreen", font=("Arial", 12, "bold"))
        self.btn_save.pack(fill=tk.X, pady=6)

        tk.Label(right, text="ENTER = newline (2 bytes). Don't exceed ROM space.",
                 fg="gray", justify=tk.LEFT).pack(side=tk.BOTTOM, pady=6)

    def scan_rom(self):
        if not self.app.rom_data:
            messagebox.showerror("Error", "Load a ROM first (top bar).")
            return
        if not self.app.table:
            messagebox.showerror("Error", "Load a .tbl file first (top bar).")
            return
        try:
            start = int(self.offset_entry.get().strip(), 16)
        except ValueError:
            messagebox.showerror("Error", "Invalid hex offset.")
            return

        self.listbox.delete(0, tk.END)
        self.listbox.insert(tk.END, "Scanning... please wait")
        self.update()

        data = self.app.rom_data
        table = self.app.table
        self.text_entries.clear()

        current_str = ""
        start_addr = 0
        in_string = False
        i = start

        def flush(end_i):
            nonlocal current_str, in_string
            if in_string:
                clean = re.sub(r'(\[[0-9A-F]{2}\])+$', '', current_str).strip()
                readable = sum(1 for c in clean if c.isalnum() or c in ' .,!?\'"- ')
                brackets = clean.count('[')
                vowels = sum(1 for c in clean.lower() if c in 'aeiouy')
                is_ui = any(u in clean for u in ['HP', 'EP', 'XP', 'LVL', 'No'])
                if readable >= 2 and (vowels > 0 or is_ui) and brackets <= readable + 2:
                    bl = self._calc_bytes(clean)
                    self.text_entries.append({'address': start_addr, 'text': clean, 'max_bytes': bl})
            in_string = False
            current_str = ""

        while i < len(data) - 1:
            b1, b2 = data[i], data[i + 1]
            if b2 == 0x00:
                h = f"{b1:02X}"
                if h == "00":
                    flush(i)
                else:
                    if not in_string:
                        in_string = True
                        start_addr = i
                    current_str += table.get(h, f"[{h}]")
                i += 2
            else:
                flush(i)
                i += 1

        self.search_var.set("")
        self.populate_list()

    def _calc_bytes(self, text):
        count = 0
        i = 0
        while i < len(text):
            if text[i] == '[' and i + 3 < len(text) and text[i + 3] == ']':
                count += 2; i += 4
            else:
                count += 2; i += 1
        return count

    def populate_list(self, query=""):
        self.listbox.delete(0, tk.END)
        self.display_mapping.clear()
        idx = 0
        if not query:
            self.listbox.insert(tk.END, f"--- Found {len(self.text_entries)} strings ---")
            self.listbox.itemconfig(0, {'fg': 'green'})
            idx = 1
        q = query.lower()
        for orig_i, entry in enumerate(self.text_entries):
            ptr = f"{entry['address'] + 0x08000000:08X}"
            if q in entry['text'].lower() or q in ptr.lower():
                self.listbox.insert(tk.END, f"[{ptr}] {entry['text'].replace(chr(10), ' ↵ ')}")
                self.display_mapping[idx] = orig_i
                idx += 1

    def on_select(self, event):
        sel = self.listbox.curselection()
        if not sel or sel[0] not in self.display_mapping:
            return
        self.current_entry = self.text_entries[self.display_mapping[sel[0]]]
        self.max_bytes = self.current_entry['max_bytes']
        self.text_editor.delete(1.0, tk.END)
        self.text_editor.insert(tk.END, self.current_entry['text'])
        self.update_char_count()

    def update_char_count(self, event=None):
        raw = self.text_editor.get(1.0, tk.END).strip()
        cur = self._calc_bytes(raw)
        self.lbl_status.config(text=f"ROM Space: {cur} / {self.max_bytes} Bytes",
                               fg="red" if cur > self.max_bytes else "black")
        self.btn_save.config(state=tk.DISABLED if cur > self.max_bytes else tk.NORMAL)

    def save_to_rom(self):
        if not self.current_entry:
            return
        new_text = self.text_editor.get(1.0, tk.END).strip('\n')
        if self._calc_bytes(new_text) > self.max_bytes:
            messagebox.showerror("Error", "Text too long!")
            return
        buf = bytearray()
        i = 0
        rt = self.app.reverse_table
        while i < len(new_text):
            c = new_text[i]
            if c == '[' and i + 3 < len(new_text) and new_text[i + 3] == ']':
                try:
                    buf.append(int(new_text[i+1:i+3], 16)); buf.append(0x00); i += 4; continue
                except ValueError:
                    pass
            buf.append(int(rt.get(c, '20'), 16)); buf.append(0x00); i += 1
        while len(buf) < self.max_bytes:
            buf.append(0x00)
        try:
            with open(self.app.rom_path, 'r+b') as f:
                f.seek(self.current_entry['address'])
                f.write(buf)
            self.app.reload_rom()
            messagebox.showinfo("Success", f"Injected at {hex(self.current_entry['address'])}")
            self.current_entry['text'] = new_text
            self.populate_list(self.search_var.get())
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def export_to_txt(self):
        if not self.text_entries:
            return
        fp = filedialog.asksaveasfilename(defaultextension=".txt",
                                          filetypes=[("Text", "*.txt"), ("All", "*.*")])
        if fp:
            with open(fp, 'w', encoding='utf-8') as f:
                for e in self.text_entries:
                    f.write(f"[{e['address'] + 0x08000000:08X}] {e['text']}\n")
            messagebox.showinfo("Exported", fp)

    def zoom_in(self):
        self.editor_font_size += 2
        self.text_editor.config(font=("Courier", self.editor_font_size))

    def zoom_out(self):
        if self.editor_font_size > 8:
            self.editor_font_size -= 2
            self.text_editor.config(font=("Courier", self.editor_font_size))


# ---------------------------------------------------------------------------
# Tab 2 — Dialogue Explorer (multi-mode)
# ---------------------------------------------------------------------------

class DialogueTab(tk.Frame):
    DEFAULT_OFFSET = 0x57920

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.entries = []
        self.display_mapping = {}
        self.current_entry = None
        self.decompressed = None
        self.scan_mode = None
        self.editor_font_size = 12
        self._build_ui()

    def _build_ui(self):
        cfg = tk.LabelFrame(self, text="Dialogue Explorer", padx=8, pady=6)
        cfg.pack(fill=tk.X, padx=8, pady=6)

        # Offset + hex preview row
        row0 = tk.Frame(cfg)
        row0.pack(fill=tk.X, pady=(0, 2))
        tk.Label(row0, text="ROM Offset (hex):").pack(side=tk.LEFT)
        self.offset_entry = tk.Entry(row0, width=12)
        self.offset_entry.insert(0, f"{self.DEFAULT_OFFSET:X}")
        self.offset_entry.pack(side=tk.LEFT, padx=4)
        tk.Button(row0, text="Preview Bytes", command=self._preview_hex).pack(side=tk.LEFT, padx=4)
        tk.Button(row0, text="Export TXT", command=self.export_txt, bg="#fff9c4").pack(side=tk.RIGHT)

        self.hex_preview = tk.Label(cfg,
            text="Load ROM then click Preview Bytes to inspect the offset.",
            fg="gray", font=("Courier", 8), anchor="w", justify=tk.LEFT)
        self.hex_preview.pack(fill=tk.X, pady=(0, 4))

        # Mode selector
        mode_frame = tk.LabelFrame(cfg, text="Scan Mode", padx=6, pady=4)
        mode_frame.pack(fill=tk.X, pady=(0, 4))
        self.mode_var = tk.StringVar(value="plain2")
        modes = [
            ("Plain scan — 2-byte (char + 0x00, same as Text Editor)", "plain2"),
            ("Plain scan — 1-byte per character (null = 0x00 / 0xFF)", "plain1"),
            ("Script scan — 1-byte, terminated by 0xFE (common in GBA dialogue engines)", "script"),
            ("Decompress LZ77 (magic 0x10) then scan", "lz77"),
            ("Decompress RLE  (magic 0x30) then scan", "rle"),
        ]
        for label, val in modes:
            tk.Radiobutton(mode_frame, text=label, variable=self.mode_var,
                           value=val, anchor="w").pack(fill=tk.X)

        # Script mode terminator override
        term_row = tk.Frame(mode_frame); term_row.pack(fill=tk.X, pady=(2,0))
        tk.Label(term_row, text="Script terminator byte (hex, for Script scan):").pack(side=tk.LEFT)
        self.term_entry = tk.Entry(term_row, width=4)
        self.term_entry.insert(0, "FE")
        self.term_entry.pack(side=tk.LEFT, padx=4)

        tk.Button(cfg, text="Scan", command=self._scan,
                  bg="#e0f7fa", font=("Arial", 10, "bold")).pack(pady=4)

        # Main split pane
        pane = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=6)
        pane.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)

        left = tk.Frame(pane)
        pane.add(left, minsize=340)

        sf = tk.Frame(left)
        sf.pack(fill=tk.X, pady=(0, 4))
        tk.Label(sf, text="Search:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *_: self._populate(self.search_var.get()))
        tk.Entry(sf, textvariable=self.search_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)

        sb = tk.Scrollbar(left)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox = tk.Listbox(left, yscrollcommand=sb.set, font=("Courier", 10))
        self.listbox.pack(fill=tk.BOTH, expand=True)
        self.listbox.bind("<<ListboxSelect>>", self._on_select)
        sb.config(command=self.listbox.yview)

        right = tk.Frame(pane)
        pane.add(right, minsize=280)

        hdr = tk.Frame(right)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="Edit:").pack(side=tk.LEFT)
        tk.Button(hdr, text="A+", command=self._zoom_in, width=3).pack(side=tk.RIGHT, padx=2)
        tk.Button(hdr, text="A-", command=self._zoom_out, width=3).pack(side=tk.RIGHT)

        self.text_editor = tk.Text(right, height=12, font=("Courier", self.editor_font_size))
        self.text_editor.pack(fill=tk.BOTH, expand=True, pady=4)
        self.text_editor.bind("<KeyRelease>", self._update_count)

        self.lbl_status = tk.Label(right, text="Select a string", font=("Arial", 10, "bold"))
        self.lbl_status.pack(pady=4)

        self.btn_save = tk.Button(right, text="Inject into ROM", command=self._save,
                                  bg="lightgreen", font=("Arial", 12, "bold"))
        self.btn_save.pack(fill=tk.X, pady=6)

        tk.Label(right,
                 text="Plain modes write bytes directly.\nCompressed modes recompress on save.",
                 fg="gray", justify=tk.LEFT).pack(side=tk.BOTTOM, pady=6)

    # ---- helpers ----

    def _get_offset(self):
        try:
            return int(self.offset_entry.get().strip(), 16)
        except ValueError:
            messagebox.showerror("Error", "Invalid hex offset.")
            return None

    def _preview_hex(self):
        if not self.app.rom_data:
            messagebox.showerror("Error", "Load a ROM first.")
            return
        off = self._get_offset()
        if off is None:
            return
        chunk = self.app.rom_data[off:off + 32]
        hex_str = ' '.join(f'{b:02X}' for b in chunk)
        hint = ""
        if chunk and chunk[0] == 0x10:
            hint = "  ← LZ77 header"
        elif chunk and chunk[0] == 0x30:
            hint = "  ← RLE header"
        elif chunk and (chunk[0] & 0xF0) == 0x20:
            hint = "  ← Huffman header"
        self.hex_preview.config(
            text=f"0x{off:X}: {hex_str}{hint}", fg="black")

    def _calc_bytes(self, text):
        count = 0; i = 0
        while i < len(text):
            if text[i] == '[' and i + 3 < len(text) and text[i + 3] == ']':
                count += 2; i += 4
            else:
                count += 2; i += 1
        return count

    # ---- scanning ----

    def _scan(self):
        if not self.app.rom_data:
            messagebox.showerror("Error", "Load a ROM first.")
            return
        off = self._get_offset()
        if off is None:
            return
        mode = self.mode_var.get()
        self.scan_mode = mode
        self.decompressed = None
        self.entries.clear()

        if mode == 'plain2':
            self._scan_plain(off, two_byte=True)
        elif mode == 'plain1':
            self._scan_plain(off, two_byte=False)
        elif mode == 'script':
            try:
                term = int(self.term_entry.get().strip(), 16)
            except ValueError:
                term = 0xFE
            self._scan_script(off, term)
        elif mode == 'lz77':
            self._scan_compressed(off, gba_utils.lz77_decompress, "LZ77")
        elif mode == 'rle':
            self._scan_compressed(off, gba_utils.rle_decompress, "RLE")

        self.search_var.set("")
        self._populate()

    def _scan_plain(self, start_off, two_byte=True):
        if not self.app.table:
            messagebox.showerror("Error", "Load a .tbl file first.")
            return
        data = self.app.rom_data
        table = self.app.table
        current_str = ""
        start_addr = 0
        in_string = False
        i = start_off

        def flush():
            nonlocal current_str, in_string
            if in_string:
                clean = re.sub(r'(\[[0-9A-F]{2}\])+$', '', current_str).strip()
                readable = sum(1 for c in clean if c.isalnum() or c in ' .,!?\'"- ')
                brackets = clean.count('[')
                vowels = sum(1 for c in clean.lower() if c in 'aeiouy')
                is_ui = any(u in clean for u in ['HP', 'EP', 'XP', 'LVL', 'No'])
                if readable >= 2 and (vowels > 0 or is_ui) and brackets <= readable + 2:
                    bl = self._calc_bytes(clean) if two_byte else len(clean)
                    self.entries.append({
                        'address': start_addr, 'text': clean,
                        'max_bytes': bl, 'two_byte': two_byte,
                    })
            in_string = False
            current_str = ""

        if two_byte:
            while i < len(data) - 1:
                b1, b2 = data[i], data[i + 1]
                if b2 == 0x00:
                    h = f"{b1:02X}"
                    if h == "00":
                        flush()
                    else:
                        if not in_string:
                            in_string = True; start_addr = i
                        current_str += table.get(h, f"[{h}]")
                    i += 2
                else:
                    flush(); i += 1
        else:
            while i < len(data):
                b = data[i]
                h = f"{b:02X}"
                if b == 0x00 or b == 0xFF or h not in table:
                    flush(); i += 1
                else:
                    if not in_string:
                        in_string = True; start_addr = i
                    current_str += table[h]; i += 1

    def _scan_script(self, start_off, terminator=0xFE):
        """Scan for 1-byte strings terminated by `terminator` (e.g. 0xFE).
        Looser filter: no vowel requirement, just needs ≥3 table-mapped chars."""
        if not self.app.table:
            messagebox.showerror("Error", "Load a .tbl file first.")
            return
        data = self.app.rom_data
        table = self.app.table
        current_str = ""
        start_addr = 0
        in_string = False
        i = start_off

        def flush():
            nonlocal current_str, in_string
            if in_string:
                clean = current_str.strip()
                # Looser filter: ≥3 printable chars, >50% of chars must be letters/digits/space
                printable = sum(1 for c in clean if c.isalnum() or c in ' .,!?\'"()-:;')
                if len(clean) >= 3 and printable >= len(clean) * 0.5:
                    bl = len(clean)  # 1 byte per char
                    self.entries.append({
                        'address': start_addr, 'text': clean,
                        'max_bytes': bl, 'two_byte': False,
                    })
            in_string = False
            current_str = ""

        while i < len(data):
            b = data[i]
            h = f"{b:02X}"
            if b == terminator or b == 0x00:
                flush(); i += 1
            elif b == 0x0A:  # newline control code
                if in_string:
                    current_str += '\n'
                i += 1
            elif h in table:
                if not in_string:
                    in_string = True; start_addr = i
                current_str += table[h]; i += 1
            else:
                flush(); i += 1

    def _scan_compressed(self, off, decomp_fn, label):
        if not self.app.table:
            messagebox.showerror("Error", "Load a .tbl file first.")
            return
        try:
            self.decompressed = decomp_fn(self.app.rom_data, off)
        except Exception as e:
            messagebox.showerror(f"{label} Error",
                f"Could not decompress at 0x{off:X} using {label}:\n{e}\n\n"
                "Click 'Preview Bytes' to see what's at that offset, then try a different mode.")
            return

        data = self.decompressed
        table = self.app.table
        current_str = ""
        start_addr = 0
        in_string = False
        i = 0

        def flush():
            nonlocal current_str, in_string
            if in_string:
                clean = re.sub(r'(\[[0-9A-F]{2}\])+$', '', current_str).strip()
                readable = sum(1 for c in clean if c.isalnum() or c in ' .,!?\'"- ')
                vowels = sum(1 for c in clean.lower() if c in 'aeiouy')
                brackets = clean.count('[')
                if readable >= 2 and vowels > 0 and brackets <= readable + 2:
                    self.entries.append({
                        'address': start_addr, 'text': clean,
                        'max_bytes': self._calc_bytes(clean), 'two_byte': True,
                    })
            in_string = False
            current_str = ""

        while i < len(data) - 1:
            b1, b2 = data[i], data[i + 1]
            if b2 == 0x00:
                h = f"{b1:02X}"
                if h == "00":
                    flush()
                else:
                    if not in_string:
                        in_string = True; start_addr = i
                    current_str += table.get(h, f"[{h}]")
                i += 2
            else:
                flush(); i += 1

    # ---- list population ----

    def _populate(self, query=""):
        self.listbox.delete(0, tk.END)
        self.display_mapping.clear()
        idx = 0
        if not query:
            self.listbox.insert(tk.END, f"--- {len(self.entries)} strings found ---")
            self.listbox.itemconfig(0, {'fg': 'green'})
            idx = 1
        q = query.lower()
        for orig_i, e in enumerate(self.entries):
            addr = e.get('address', 0)
            addr_str = f"0x{addr:X}"
            preview = e['text'].replace(chr(10), ' ↵ ')
            if q in e['text'].lower() or q in addr_str.lower():
                self.listbox.insert(tk.END, f"[{addr_str}] {preview}")
                self.display_mapping[idx] = orig_i
                idx += 1

    def _on_select(self, event):
        sel = self.listbox.curselection()
        if not sel or sel[0] not in self.display_mapping:
            return
        self.current_entry = self.entries[self.display_mapping[sel[0]]]
        self.text_editor.delete(1.0, tk.END)
        self.text_editor.insert(tk.END, self.current_entry['text'])
        self._update_count()

    def _update_count(self, event=None):
        if not self.current_entry:
            return
        raw = self.text_editor.get(1.0, tk.END).strip()
        two_byte = self.current_entry.get('two_byte', True)
        cur = self._calc_bytes(raw) if two_byte else len(raw)
        max_b = self.current_entry.get('max_bytes', 0)
        self.lbl_status.config(text=f"Bytes: {cur} / {max_b}",
                               fg="red" if cur > max_b else "black")

    # ---- save ----

    def _encode_text(self, text, two_byte):
        rt = self.app.reverse_table
        buf = bytearray()
        i = 0
        while i < len(text):
            c = text[i]
            if two_byte and c == '[' and i + 3 < len(text) and text[i + 3] == ']':
                try:
                    buf.append(int(text[i + 1:i + 3], 16)); buf.append(0x00); i += 4; continue
                except ValueError:
                    pass
            buf.append(int(rt.get(c, '20'), 16))
            if two_byte:
                buf.append(0x00)
            i += 1
        return buf

    def _save(self):
        if not self.current_entry:
            return
        new_text = self.text_editor.get(1.0, tk.END).strip('\n')
        two_byte = self.current_entry.get('two_byte', True)
        max_b = self.current_entry.get('max_bytes', 0)
        buf = self._encode_text(new_text, two_byte)

        if len(buf) > max_b:
            messagebox.showerror("Error", f"Text too long ({len(buf)} > {max_b} bytes)!")
            return
        while len(buf) < max_b:
            buf.append(0x00)

        mode = self.scan_mode
        addr = self.current_entry.get('address', 0)

        if mode in ('plain1', 'plain2'):
            try:
                with open(self.app.rom_path, 'r+b') as f:
                    f.seek(addr); f.write(buf)
                self.app.reload_rom()
                messagebox.showinfo("Success", f"Injected at 0x{addr:X}")
                self.current_entry['text'] = new_text
                self._populate(self.search_var.get())
            except Exception as e:
                messagebox.showerror("Error", str(e))
        else:
            if self.decompressed is None:
                return
            dec = bytearray(self.decompressed)
            dec[addr:addr + max_b] = buf
            self.decompressed = bytes(dec)
            try:
                compressed = gba_utils.lz77_compress(self.decompressed) if mode == 'lz77' else self.decompressed
                rom_off = self._get_offset()
                with open(self.app.rom_path, 'r+b') as f:
                    f.seek(rom_off); f.write(compressed)
                self.app.reload_rom()
                messagebox.showinfo("Success", f"Written {len(compressed)} bytes at 0x{rom_off:X}")
                self.current_entry['text'] = new_text
                self._populate(self.search_var.get())
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def export_txt(self):
        if not self.entries:
            return
        fp = filedialog.asksaveasfilename(defaultextension=".txt",
                                          filetypes=[("Text", "*.txt"), ("All", "*.*")])
        if fp:
            with open(fp, 'w', encoding='utf-8') as f:
                for e in self.entries:
                    f.write(f"[0x{e.get('address', 0):X}] {e['text']}\n")
            messagebox.showinfo("Exported", fp)

    def _zoom_in(self):
        self.editor_font_size += 2
        self.text_editor.config(font=("Courier", self.editor_font_size))

    def _zoom_out(self):
        if self.editor_font_size > 8:
            self.editor_font_size -= 2
            self.text_editor.config(font=("Courier", self.editor_font_size))


# ---------------------------------------------------------------------------
# Tab 3 — Raw ROM Tile Browser
# ---------------------------------------------------------------------------

class SpriteTab(tk.Frame):
    """Frame-aware GBA sprite viewer and tile replacer."""
    TILE_SIZE = 8
    PAGE_TILES = 512

    # Confirmed sprite locations — add more as discovered via mGBA
    # Tuple: (label, ROM_offset_or_None, bpp_str, frame_w_px, frame_h_px)
    KNOWN_SPRITES = [
        ("(select preset...)",                    None,     "8", 32, 32),
        ("Special Effects / FX tiles @ 0x714300", 0x714300, "8", 32, 32),
        # Add confirmed character/overworld offsets here once found via mGBA tile viewer
    ]

    # Default OBJ palette — loaded automatically if found
    DEFAULT_PAL = r"C:\GBA Modding\Palette\Pal1.pal"

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.palette = []
        self.current_offset = 0
        self.canvas_image = None
        self._raw_override = None   # set by CompScannerTab to view decompressed bytes
        self._build_ui()
        # Auto-load the OBJ palette if it exists at the known location
        import os
        if os.path.isfile(self.DEFAULT_PAL):
            self.pal_entry.delete(0, tk.END)
            self.pal_entry.insert(0, self.DEFAULT_PAL)
            self._load_palette(self.DEFAULT_PAL)

    def _build_ui(self):
        cfg = tk.LabelFrame(self, text="Raw ROM Tile Browser  (browse ROM bytes directly as tiles, no decompression)", padx=8, pady=6)
        cfg.pack(fill=tk.X, padx=8, pady=6)

        # Palette row
        r0 = tk.Frame(cfg); r0.pack(fill=tk.X, pady=2)
        tk.Label(r0, text="Palette (.pal / raw BGR555):").pack(side=tk.LEFT)
        self.pal_entry = tk.Entry(r0, width=44)
        self.pal_entry.pack(side=tk.LEFT, padx=4)
        tk.Button(r0, text="Browse...", command=self._browse_pal).pack(side=tk.LEFT)
        self.pal_status = tk.Label(r0, text="No palette — using debug colors", fg="gray")
        self.pal_status.pack(side=tk.LEFT, padx=8)

        # BPP + zoom row
        r1 = tk.Frame(cfg); r1.pack(fill=tk.X, pady=2)
        tk.Label(r1, text="Bit depth:").pack(side=tk.LEFT)
        self.bpp_var = tk.StringVar(value="4")
        tk.Radiobutton(r1, text="4bpp (characters / maps)", variable=self.bpp_var,
                       value="4", command=self._rerender).pack(side=tk.LEFT, padx=4)
        tk.Radiobutton(r1, text="8bpp (special effects)", variable=self.bpp_var,
                       value="8", command=self._rerender).pack(side=tk.LEFT, padx=4)
        tk.Label(r1, text="   Zoom:").pack(side=tk.LEFT)
        self.zoom_var = tk.IntVar(value=2)
        for z in (1, 2, 3, 4):
            tk.Radiobutton(r1, text=f"{z}x", variable=self.zoom_var,
                           value=z, command=self._rerender).pack(side=tk.LEFT, padx=2)

        # Tiles/row row — hidden in frame mode (frame mode drives its own tiles-per-row)
        self.tpr_row = tk.Frame(cfg)
        self.tpr_row.pack(fill=tk.X, pady=2)
        tk.Label(self.tpr_row, text="Tiles/row (raw mode only):").pack(side=tk.LEFT)
        self.tpr_var = tk.IntVar(value=16)
        for tpr in (8, 16, 24, 32):
            tk.Radiobutton(self.tpr_row, text=str(tpr), variable=self.tpr_var,
                           value=tpr, command=self._rerender).pack(side=tk.LEFT, padx=2)

        # 4bpp palette sub-palette row selector (0-15, ignored in 8bpp mode)
        r1b = tk.Frame(cfg); r1b.pack(fill=tk.X, pady=2)
        self.subpal_row = r1b   # reference so _toggle_frame_mode can re-insert tpr_row before it
        tk.Label(r1b, text="4bpp sub-palette (0-15):").pack(side=tk.LEFT)
        self.subpal_var = tk.IntVar(value=0)
        tk.Spinbox(r1b, from_=0, to=15, textvariable=self.subpal_var, width=4,
                   command=self._rerender).pack(side=tk.LEFT, padx=4)
        tk.Label(r1b, text="  (selects which 16-color row of OBJ palette to apply in 4bpp mode)",
                 fg="gray").pack(side=tk.LEFT)

        # Sprite Frame Mode section
        fm_frame = tk.LabelFrame(cfg, text="Sprite Frame Mode", padx=8, pady=4)
        fm_frame.pack(fill=tk.X, pady=4)

        fm_r1 = tk.Frame(fm_frame); fm_r1.pack(fill=tk.X, pady=2)
        self.frame_mode_var = tk.BooleanVar(value=False)
        tk.Checkbutton(fm_r1, text="Enable frame mode", variable=self.frame_mode_var,
                       command=self._toggle_frame_mode).pack(side=tk.LEFT)
        tk.Label(fm_r1, text="  Frame W:").pack(side=tk.LEFT)
        self.frame_w_var = tk.IntVar(value=32)
        tk.Spinbox(fm_r1, from_=8, to=256, increment=8, textvariable=self.frame_w_var, width=5,
                   command=self._rerender).pack(side=tk.LEFT, padx=2)
        tk.Label(fm_r1, text="px  Frame H:").pack(side=tk.LEFT)
        self.frame_h_var = tk.IntVar(value=32)
        tk.Spinbox(fm_r1, from_=8, to=256, increment=8, textvariable=self.frame_h_var, width=5,
                   command=self._rerender).pack(side=tk.LEFT, padx=2)
        tk.Label(fm_r1, text="px  Frames/row:").pack(side=tk.LEFT)
        self.frames_per_row_var = tk.IntVar(value=8)
        tk.Spinbox(fm_r1, from_=1, to=32, textvariable=self.frames_per_row_var, width=4,
                   command=self._rerender).pack(side=tk.LEFT, padx=2)

        fm_r2 = tk.Frame(fm_frame); fm_r2.pack(fill=tk.X, pady=2)
        tk.Label(fm_r2, text="Known presets:").pack(side=tk.LEFT)
        preset_names = [p[0] for p in self.KNOWN_SPRITES]
        self.preset_var = tk.StringVar(value=preset_names[0])
        self.preset_combo = ttk.Combobox(fm_r2, textvariable=self.preset_var, values=preset_names,
                                          state="readonly", width=44)
        self.preset_combo.pack(side=tk.LEFT, padx=4)
        self.preset_combo.bind("<<ComboboxSelected>>", self._on_preset)

        # Navigation row
        r2 = tk.Frame(cfg); r2.pack(fill=tk.X, pady=4)
        tk.Label(r2, text="ROM Offset (hex):").pack(side=tk.LEFT)
        self.offset_entry = tk.Entry(r2, width=12)
        self.offset_entry.insert(0, "0")
        self.offset_entry.pack(side=tk.LEFT, padx=4)
        self.offset_entry.bind("<Return>", lambda e: self._go())
        tk.Button(r2, text="Go", command=self._go, bg="#e0f7fa").pack(side=tk.LEFT, padx=2)
        tk.Button(r2, text="◄◄ -Page", command=lambda: self._step(-self.PAGE_TILES)).pack(side=tk.LEFT, padx=2)
        tk.Button(r2, text="◄ -Row",  command=lambda: self._step(-self.tpr_var.get())).pack(side=tk.LEFT, padx=2)
        tk.Button(r2, text="▶ +Row",  command=lambda: self._step(self.tpr_var.get())).pack(side=tk.LEFT, padx=2)
        tk.Button(r2, text="▶▶ +Page", command=lambda: self._step(self.PAGE_TILES)).pack(side=tk.LEFT, padx=2)
        tk.Label(r2, text=f"(Page = {self.PAGE_TILES} tiles)", fg="gray").pack(side=tk.LEFT, padx=6)

        # ROM offset slider (updated when ROM loads via notify_rom_loaded)
        r3s = tk.Frame(cfg); r3s.pack(fill=tk.X, pady=(0, 2))
        tk.Label(r3s, text="ROM position:").pack(side=tk.LEFT)
        self.offset_scale = tk.Scale(r3s, orient=tk.HORIZONTAL, from_=0, to=1,
                                     showvalue=False, command=self._on_slider)
        self.offset_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)
        self._slider_updating = False   # guard against feedback loops

        # Status + export
        r3 = tk.Frame(cfg); r3.pack(fill=tk.X, pady=2)
        self.lbl_status = tk.Label(r3, text="Enter an offset and press Go.", fg="gray", anchor="w")
        self.lbl_status.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Button(r3, text="Import PNG → ROM", command=self._import_png, bg="#fce4ec").pack(side=tk.RIGHT, padx=2)
        tk.Button(r3, text="Export .bin", command=self._export_bin, bg="#fff9c4").pack(side=tk.RIGHT, padx=2)
        tk.Button(r3, text="Export .png", command=self._export_png, bg="#e8f5e9").pack(side=tk.RIGHT, padx=2)

        # Canvas with scrollbars
        cf = tk.Frame(self); cf.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        vsb = tk.Scrollbar(cf, orient=tk.VERTICAL)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb = tk.Scrollbar(cf, orient=tk.HORIZONTAL)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas = tk.Canvas(cf, bg="#1a1a1a", xscrollcommand=hsb.set, yscrollcommand=vsb.set)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        vsb.config(command=self.canvas.yview)
        hsb.config(command=self.canvas.xview)

    def _browse_pal(self):
        fp = filedialog.askopenfilename(title="Select palette",
                                        filetypes=[("Palette", "*.pal"), ("All", "*.*")])
        if fp:
            self.pal_entry.delete(0, tk.END)
            self.pal_entry.insert(0, fp)
            self._load_palette(fp)

    def _load_palette(self, path):
        self.palette = []
        try:
            raw = open(path, 'rb').read()
            text = raw.decode('ascii', errors='ignore')

            if 'JASC-PAL' in text:
                # JASC-PAL: text file, RGB 0-255 per line, 3 header lines
                for line in text.splitlines()[3:]:
                    parts = line.strip().split()
                    if len(parts) == 3:
                        self.palette.append((int(parts[0]), int(parts[1]), int(parts[2])))

            elif raw[:4] == b'RIFF' and raw[8:12] == b'PAL ':
                # Windows RIFF PAL: colors stored as (R, G, B, flags) × N at offset 24
                # Header: RIFF(4)+size(4)+PAL(4)+data(4)+chunksize(4)+version(2)+count(2) = 24 bytes
                count = raw[22] | (raw[23] << 8)
                for i in range(count):
                    base = 24 + i * 4
                    if base + 3 > len(raw):
                        break
                    self.palette.append((raw[base], raw[base + 1], raw[base + 2]))

            else:
                # Raw GBA BGR555: 2 bytes per color, little-endian
                # bits 0-4 = R, bits 5-9 = G, bits 10-14 = B
                for i in range(0, len(raw) - 1, 2):
                    v = raw[i] | (raw[i + 1] << 8)
                    r = (v & 0x1F) << 3
                    g = ((v >> 5) & 0x1F) << 3
                    b = ((v >> 10) & 0x1F) << 3
                    self.palette.append((r, g, b))

            self.pal_status.config(text=f"{len(self.palette)} colors loaded", fg="green")
            self._rerender()
        except Exception as e:
            messagebox.showerror("Palette Error", str(e))

    def _default_palette(self, size=16):
        colors16 = [
            (0,0,0),(255,0,0),(0,200,0),(0,80,255),
            (255,200,0),(180,0,255),(0,220,220),(255,120,0),
            (120,60,0),(255,180,180),(0,120,80),(80,0,120),
            (200,200,200),(255,255,0),(0,255,180),(255,255,255),
        ]
        if size == 16:
            return colors16
        pal = []
        for group in range(16):
            sc = 0.4 + group * 0.04
            for r, g, b in colors16:
                pal.append((min(255, int(r*sc)), min(255, int(g*sc)), min(255, int(b*sc))))
        return pal

    def notify_rom_loaded(self, rom_size: int):
        """Called by the app after a ROM is loaded to calibrate the slider."""
        bpp = int(self.bpp_var.get())
        step = bpp * 8   # bytes per tile
        steps = max(1, rom_size // step)
        self.offset_scale.config(from_=0, to=steps - 1)
        self.offset_scale.set(0)

    def _on_slider(self, val):
        """Slider moved — jump to the corresponding ROM offset."""
        if self._slider_updating or not self.app.rom_data:
            return
        bpp = int(self.bpp_var.get())
        step = bpp * 8
        off = int(float(val)) * step
        self.current_offset = off
        self._slider_updating = True
        self.offset_entry.delete(0, tk.END)
        self.offset_entry.insert(0, f"{off:X}")
        self._slider_updating = False
        self._rerender()

    def _go(self):
        try:
            off = int(self.offset_entry.get().strip(), 16)
        except ValueError:
            messagebox.showerror("Error", "Invalid hex offset.")
            return
        self._raw_override = None   # exit decompressed-view mode
        self.current_offset = max(0, off)
        # Sync slider without triggering _on_slider
        if self.app.rom_data:
            bpp = int(self.bpp_var.get())
            step = bpp * 8
            self._slider_updating = True
            self.offset_scale.set(self.current_offset // step)
            self._slider_updating = False
        self._rerender()

    def _step(self, tile_delta):
        if not self.app.rom_data:
            return
        self._raw_override = None   # exit decompressed-view mode
        bpp = int(self.bpp_var.get())
        step = bpp * 8
        self.current_offset = max(0, self.current_offset + tile_delta * step)
        self.offset_entry.delete(0, tk.END)
        self.offset_entry.insert(0, f"{self.current_offset:X}")
        self._slider_updating = True
        self.offset_scale.set(self.current_offset // step)
        self._slider_updating = False
        self._rerender()

    def view_raw_bytes(self, data: bytes, label: str):
        """Display arbitrary bytes (e.g. decompressed block) instead of ROM at an offset."""
        self._raw_override = data
        self.offset_entry.delete(0, tk.END)
        self.offset_entry.insert(0, "0")
        bpp = int(self.bpp_var.get())
        bytes_per_tile = bpp * 8
        raw = data[:self.PAGE_TILES * bytes_per_tile]
        if self.frame_mode_var.get():
            self._render_frames(raw, bpp)
        else:
            self._render_tiles(raw, bpp)
        self.lbl_status.config(
            text=f"[Decompressed] {label}", fg="blue")

    def _rerender(self):
        if self._raw_override is not None:
            # Viewing decompressed data — re-render from override buffer
            bpp = int(self.bpp_var.get())
            bytes_per_tile = bpp * 8
            raw = self._raw_override[:self.PAGE_TILES * bytes_per_tile]
            if self.frame_mode_var.get():
                self._render_frames(raw, bpp)
            else:
                self._render_tiles(raw, bpp)
            return
        if not self.app.rom_data:
            return
        bpp = int(self.bpp_var.get())
        bytes_per_tile = bpp * 8
        raw = self.app.rom_data[self.current_offset:self.current_offset + self.PAGE_TILES * bytes_per_tile]
        if not raw:
            self.lbl_status.config(text="Offset beyond end of ROM.", fg="red")
            return
        if self.frame_mode_var.get():
            self._render_frames(raw, bpp)
        else:
            self._render_tiles(raw, bpp)

    def _render_tiles(self, raw: bytes, bpp: int):
        bytes_per_tile = bpp * 8
        pal = self._build_pal(bpp)

        scale = self.zoom_var.get()
        tpr = self.tpr_var.get()
        tile_px = self.TILE_SIZE * scale
        num_tiles = min(len(raw) // bytes_per_tile, self.PAGE_TILES)

        if num_tiles == 0:
            self.canvas.delete("all")
            self.lbl_status.config(text="No complete tiles at this offset.", fg="orange")
            return

        rows = (num_tiles + tpr - 1) // tpr
        img_w = tpr * tile_px
        img_h = rows * tile_px
        img = tk.PhotoImage(width=img_w, height=img_h)

        for row in range(rows):
            scanlines = [[] for _ in range(self.TILE_SIZE)]
            for col in range(tpr):
                t = row * tpr + col
                if t >= num_tiles:
                    for py in range(self.TILE_SIZE):
                        scanlines[py].extend(["#111111"] * self.TILE_SIZE)
                    continue
                td = raw[t * bytes_per_tile:(t + 1) * bytes_per_tile]
                if bpp == 4:
                    for py in range(self.TILE_SIZE):
                        for pp in range(4):
                            byte = td[py * 4 + pp]
                            for ci in (byte & 0xF, (byte >> 4) & 0xF):
                                c = pal[ci] if ci < len(pal) else (0, 0, 0)
                                scanlines[py].append(f"#{c[0]:02X}{c[1]:02X}{c[2]:02X}")
                else:
                    for py in range(self.TILE_SIZE):
                        for px in range(self.TILE_SIZE):
                            ci = td[py * 8 + px] if (py * 8 + px) < len(td) else 0
                            c = pal[ci] if ci < len(pal) else (0, 0, 0)
                            scanlines[py].append(f"#{c[0]:02X}{c[1]:02X}{c[2]:02X}")

            for sy_tile, scanline in enumerate(scanlines):
                for sy in range(scale):
                    y = row * tile_px + sy_tile * scale + sy
                    scaled = []
                    for color in scanline:
                        scaled.extend([color] * scale)
                    img.put("{" + " ".join(scaled) + "}", to=(0, y))

        self.canvas.delete("all")
        self.canvas_image = img
        self.canvas.create_image(0, 0, anchor=tk.NW, image=img)
        self.canvas.config(scrollregion=(0, 0, img_w, img_h))
        end_off = self.current_offset + num_tiles * bytes_per_tile
        self.lbl_status.config(
            text=f"{num_tiles} tiles @ ROM 0x{self.current_offset:X} – 0x{end_off:X}  |  {bpp}bpp  |  zoom {scale}x",
            fg="black")

    def _toggle_frame_mode(self):
        """Show or hide the Tiles/row row depending on whether frame mode is active."""
        if self.frame_mode_var.get():
            self.tpr_row.pack_forget()
        else:
            # Restore tpr_row between the BPP/zoom row and the sub-palette row
            self.tpr_row.pack(fill=tk.X, pady=2, before=self.subpal_row)
        self._rerender()

    def _on_preset(self, event=None):
        """Load a known sprite preset — sets offset, bpp, frame size, enables frame mode."""
        name = self.preset_var.get()
        for pname, poffset, pbpp, pfw, pfh in self.KNOWN_SPRITES:
            if pname == name and poffset is not None:
                self.current_offset = poffset
                self.offset_entry.delete(0, tk.END)
                self.offset_entry.insert(0, f"{poffset:X}")
                self.bpp_var.set(pbpp)
                self.frame_w_var.set(pfw)
                self.frame_h_var.set(pfh)
                self.frame_mode_var.set(True)
                if self.app.rom_data:
                    step = int(pbpp) * 8
                    self._slider_updating = True
                    self.offset_scale.set(poffset // step)
                    self._slider_updating = False
                self._rerender()
                break

    def _build_pal(self, bpp: int):
        """Return a palette list suitable for the current bpp and sub-palette settings."""
        if bpp == 4:
            subpal = max(0, min(15, self.subpal_var.get()))
            base = subpal * 16
            if self.palette and len(self.palette) >= base + 16:
                return self.palette[base:base + 16]
            elif self.palette and len(self.palette) > base:
                return self.palette[base:] + [(0, 0, 0)] * (16 - (len(self.palette) - base))
            else:
                return self._default_palette(16)
        else:
            if self.palette and len(self.palette) >= 256:
                return self.palette[:256]
            elif self.palette:
                return self.palette + [(0, 0, 0)] * (256 - len(self.palette))
            else:
                return self._default_palette(256)

    def _render_frames(self, raw: bytes, bpp: int):
        """Frame-aware renderer: groups tiles into sprite frames with magenta borders."""
        bytes_per_tile = bpp * 8
        scale = self.zoom_var.get()
        tile_px = self.TILE_SIZE * scale

        frame_w = max(8, self.frame_w_var.get())
        frame_h = max(8, self.frame_h_var.get())
        fpr = max(1, self.frames_per_row_var.get())

        tiles_x = frame_w // self.TILE_SIZE   # tiles wide per frame
        tiles_y = frame_h // self.TILE_SIZE   # tiles tall per frame
        tiles_per_frame = tiles_x * tiles_y
        tpr = tiles_x * fpr                   # total tiles per pixel-row

        pal = self._build_pal(bpp)

        num_tiles = min(len(raw) // bytes_per_tile, self.PAGE_TILES)
        if num_tiles == 0:
            self.canvas.delete("all")
            self.lbl_status.config(text="No complete tiles at this offset.", fg="orange")
            return

        rows = (num_tiles + tpr - 1) // tpr
        img_w = tpr * tile_px
        img_h = rows * tile_px
        img = tk.PhotoImage(width=img_w, height=img_h)

        for row in range(rows):
            scanlines = [[] for _ in range(self.TILE_SIZE)]
            for col in range(tpr):
                t = row * tpr + col
                if t >= num_tiles:
                    for py in range(self.TILE_SIZE):
                        scanlines[py].extend(["#111111"] * self.TILE_SIZE)
                    continue
                td = raw[t * bytes_per_tile:(t + 1) * bytes_per_tile]
                if bpp == 4:
                    for py in range(self.TILE_SIZE):
                        for pp in range(4):
                            byte = td[py * 4 + pp]
                            for ci in (byte & 0xF, (byte >> 4) & 0xF):
                                c = pal[ci] if ci < len(pal) else (0, 0, 0)
                                scanlines[py].append(f"#{c[0]:02X}{c[1]:02X}{c[2]:02X}")
                else:
                    for py in range(self.TILE_SIZE):
                        for px in range(self.TILE_SIZE):
                            ci = td[py * 8 + px] if (py * 8 + px) < len(td) else 0
                            c = pal[ci] if ci < len(pal) else (0, 0, 0)
                            scanlines[py].append(f"#{c[0]:02X}{c[1]:02X}{c[2]:02X}")

            for sy_tile, scanline in enumerate(scanlines):
                for sy in range(scale):
                    y = row * tile_px + sy_tile * scale + sy
                    scaled = []
                    for color in scanline:
                        scaled.extend([color] * scale)
                    img.put("{" + " ".join(scaled) + "}", to=(0, y))

        self.canvas.delete("all")
        self.canvas_image = img
        self.canvas.create_image(0, 0, anchor=tk.NW, image=img)

        # Draw magenta frame borders over the image
        frame_px_w = tiles_x * tile_px
        frame_px_h = tiles_y * tile_px
        frame_rows = (rows + tiles_y - 1) // tiles_y
        for fy in range(frame_rows + 1):
            y = fy * frame_px_h
            self.canvas.create_line(0, y, img_w, y, fill="#FF00FF", width=1)
        for fx in range(fpr + 1):
            x = fx * frame_px_w
            self.canvas.create_line(x, 0, x, img_h, fill="#FF00FF", width=1)

        self.canvas.config(scrollregion=(0, 0, img_w, img_h))
        end_off = self.current_offset + num_tiles * bytes_per_tile
        num_frames = num_tiles // tiles_per_frame if tiles_per_frame > 0 else 0
        self.lbl_status.config(
            text=(f"{num_tiles} tiles ({num_frames} frames of {frame_w}×{frame_h}px)"
                  f" @ ROM 0x{self.current_offset:X}–0x{end_off:X}  |  {bpp}bpp  |  zoom {scale}x"),
            fg="black")

    def _import_png(self):
        """Import a PNG sprite sheet and encode it back into the ROM at the current offset."""
        if not self.app.rom_data:
            messagebox.showerror("Error", "Load a ROM first.")
            return
        if not self.palette:
            messagebox.showerror("Error", "Load a palette (.pal) file first — needed to match colors during import.")
            return

        fp = filedialog.askopenfilename(title="Import PNG sprite sheet",
                                        filetypes=[("PNG", "*.png"), ("All", "*.*")])
        if not fp:
            return

        try:
            from PIL import Image
            img = Image.open(fp).convert("RGB")
        except ImportError:
            messagebox.showerror("Missing library",
                                 "Pillow is required for PNG import.\nInstall it with:  pip install Pillow")
            return
        except Exception as e:
            messagebox.showerror("Error opening PNG", str(e))
            return

        bpp = int(self.bpp_var.get())
        bytes_per_tile = bpp * 8
        pal = self._build_pal(bpp)

        w, h = img.size
        tiles_x_img = w // 8
        tiles_y_img = h // 8
        if tiles_x_img == 0 or tiles_y_img == 0:
            messagebox.showerror("Error", f"Image too small ({w}×{h}px). Must be at least 8×8.")
            return

        pixels = img.load()

        # Build a fast nearest-color lookup over the palette
        def nearest_color(r, g, b):
            best_i, best_d = 0, float('inf')
            for i, (pr, pg, pb) in enumerate(pal):
                d = (r - pr) ** 2 + (g - pg) ** 2 + (b - pb) ** 2
                if d < best_d:
                    best_d = d
                    best_i = i
            return best_i

        encoded = bytearray()
        for ty in range(tiles_y_img):
            for tx in range(tiles_x_img):
                tile = bytearray(bytes_per_tile)
                for py in range(8):
                    for px in range(8):
                        r2, g2, b2 = pixels[tx * 8 + px, ty * 8 + py]
                        ci = nearest_color(r2, g2, b2)
                        if bpp == 4:
                            bi = py * 4 + px // 2
                            if px % 2 == 0:
                                tile[bi] = (tile[bi] & 0xF0) | (ci & 0xF)
                            else:
                                tile[bi] = (tile[bi] & 0x0F) | ((ci & 0xF) << 4)
                        else:
                            tile[py * 8 + px] = ci
                encoded.extend(tile)

        dest = self.current_offset
        if dest + len(encoded) > len(self.app.rom_data):
            messagebox.showerror("Error",
                f"Encoded data ({len(encoded)} bytes) would overrun ROM end at offset 0x{dest:X}.")
            return

        num_tiles = tiles_x_img * tiles_y_img
        if not messagebox.askyesno("Confirm write",
                f"Write {len(encoded)} bytes ({num_tiles} tiles from {w}×{h}px PNG)\n"
                f"to ROM offset 0x{dest:X} – 0x{dest + len(encoded):X}?\n\n"
                f"ROM file: {self.app.rom_path}\n\n"
                f"THIS CANNOT BE UNDONE."):
            return

        with open(self.app.rom_path, 'r+b') as fh:
            fh.seek(dest)
            fh.write(encoded)

        # Update in-memory ROM so the viewer reflects the change immediately
        rom = bytearray(self.app.rom_data)
        rom[dest:dest + len(encoded)] = encoded
        self.app.rom_data = bytes(rom)

        self._rerender()
        messagebox.showinfo("Import complete",
            f"Wrote {len(encoded)} bytes to ROM 0x{dest:X}.\nRe-open the ROM in-game to verify.")

    def _export_bin(self):
        if not self.app.rom_data:
            return
        bpp = int(self.bpp_var.get())
        data = self.app.rom_data[self.current_offset:self.current_offset + self.PAGE_TILES * bpp * 8]
        fp = filedialog.asksaveasfilename(
            defaultextension=".bin",
            initialfile=f"tiles_{self.current_offset:07X}_{bpp}bpp.bin",
            filetypes=[("Binary", "*.bin"), ("All", "*.*")])
        if fp:
            with open(fp, 'wb') as f: f.write(data)
            messagebox.showinfo("Exported", fp)

    def _export_png(self):
        if not self.app.rom_data:
            return
        try:
            from PIL import Image
            bpp = int(self.bpp_var.get())
            bytes_per_tile = bpp * 8
            pal_size = 16 if bpp == 4 else 256
            pal = self.palette[:pal_size] if len(self.palette) >= pal_size else self._default_palette(pal_size)
            raw = self.app.rom_data[self.current_offset:self.current_offset + self.PAGE_TILES * bytes_per_tile]
            num_tiles = len(raw) // bytes_per_tile
            tpr = self.tpr_var.get()
            rows_count = (num_tiles + tpr - 1) // tpr
            img = Image.new("RGB", (tpr * 8, rows_count * 8), (0, 0, 0))
            pixels = img.load()
            for t in range(num_tiles):
                tile = raw[t * bytes_per_tile:(t + 1) * bytes_per_tile]
                tx, ty = (t % tpr) * 8, (t // tpr) * 8
                if bpp == 4:
                    for py in range(8):
                        for pp in range(4):
                            b = tile[py * 4 + pp]
                            for pix, ci in enumerate([b & 0xF, (b >> 4) & 0xF]):
                                c = pal[ci] if ci < len(pal) else (0, 0, 0)
                                pixels[tx + pp * 2 + pix, ty + py] = c
                else:
                    for py in range(8):
                        for px in range(8):
                            ci = tile[py * 8 + px] if py * 8 + px < len(tile) else 0
                            c = pal[ci] if ci < len(pal) else (0, 0, 0)
                            pixels[tx + px, ty + py] = c
            fp = filedialog.asksaveasfilename(
                defaultextension=".png",
                initialfile=f"tiles_{self.current_offset:07X}_{bpp}bpp.png",
                filetypes=[("PNG", "*.png"), ("All", "*.*")])
            if fp:
                img.save(fp); messagebox.showinfo("Exported", fp)
        except ImportError:
            messagebox.showerror("Missing library", "Install Pillow: pip install Pillow")


# ---------------------------------------------------------------------------
# Tab 4 — Stats & Values Editor
# ---------------------------------------------------------------------------

class StatsTab(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._build_ui()

    def _build_ui(self):
        nb = ttk.Notebook(self)
        nb.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        self.char_tab = self._make_char_tab(nb)
        nb.add(self.char_tab, text="Characters")

        self.enemy_tab = self._make_enemy_tab(nb)
        nb.add(self.enemy_tab, text="Enemies")

        self.equip_tab = self._make_equip_tab(nb)
        nb.add(self.equip_tab, text="Equipment")

    # ---- Characters ----
    def _make_char_tab(self, parent):
        f = tk.Frame(parent)
        tk.Label(f, text="Select character:").pack(anchor="w", padx=10, pady=(10, 0))

        self.char_var = tk.StringVar()
        char_names = [c[0] for c in CHARACTERS]
        self.char_combo = ttk.Combobox(f, textvariable=self.char_var,
                                       values=char_names, state="readonly", width=30)
        self.char_combo.pack(anchor="w", padx=10)
        self.char_combo.bind("<<ComboboxSelected>>", self._load_char)

        form = tk.LabelFrame(f, text="Stats", padx=10, pady=8)
        form.pack(fill=tk.X, padx=10, pady=8)

        self.char_fields = {}
        # Row 0: Level | HP | EP
        # Row 1: Str | Power | Endurance | Speed
        # Row 2: Person Type (full row, label below it)
        # Row 3: person_type name label
        # Row 4: Tech Count
        stat_rows = [
            ("Level",     0, 0), ("HP",    0, 2), ("EP",  0, 4),
            ("Strength",  1, 0), ("Power", 1, 2), ("Endurance", 1, 4), ("Speed", 1, 6),
            ("Person Type", 2, 0),
            ("Tech Count", 4, 0),
        ]
        for label, row, col in stat_rows:
            tk.Label(form, text=label + ":", anchor="e", width=12).grid(row=row, column=col, sticky="e", pady=3)
            var = tk.IntVar()
            mx = 65535 if label in ("HP", "EP") else 255
            cmd = self._update_person_label if label == "Person Type" else None
            sb = tk.Spinbox(form, from_=0, to=mx, textvariable=var, width=8, command=cmd)
            sb.grid(row=row, column=col+1, sticky="w", padx=4)
            if label == "Person Type":
                sb.bind("<KeyRelease>", self._update_person_label)
            self.char_fields[label] = var

        # Person type name — own row so it never overlaps
        self.person_type_label = tk.Label(form, text="", fg="blue", anchor="w")
        self.person_type_label.grid(row=3, column=0, columnspan=8, sticky="w", padx=4)
        self.char_fields["Person Type"].trace("w", self._update_person_label)

        # Techs
        tech_frame = tk.LabelFrame(f, text="Techs (6 slots)", padx=10, pady=6)
        tech_frame.pack(fill=tk.X, padx=10, pady=4)
        self.tech_fields = []
        for i in range(6):
            tk.Label(tech_frame, text=f"Tech {i+1}:").grid(row=0, column=i*2, sticky="e")
            var = tk.IntVar()
            tk.Spinbox(tech_frame, from_=0, to=255, textvariable=var, width=5).grid(row=0, column=i*2+1, padx=4)
            self.tech_fields.append(var)

        # Starting Equipment
        equip_frame = tk.LabelFrame(f, text="Starting Equipment", padx=10, pady=6)
        equip_frame.pack(fill=tk.X, padx=10, pady=4)

        self.equip_combos = {}   # slot_name -> (Combobox, [(id, name), ...])
        equip_slots = [
            ("Body Armor", _EQUIP_BODY),
            ("Hands",      _EQUIP_HANDS),
            ("Feet",       _EQUIP_FEET),
            ("Accessory",  _EQUIP_ACC),
        ]
        for col, (slot_name, items) in enumerate(equip_slots):
            tk.Label(equip_frame, text=slot_name + ":").grid(row=0, column=col*2, sticky="e", padx=(8,2))
            cb = ttk.Combobox(equip_frame, values=[name for _, name in items],
                              state="readonly", width=22)
            cb.grid(row=0, column=col*2+1, sticky="w", padx=(0,12))
            self.equip_combos[slot_name] = (cb, items)

        self.char_addr_label = tk.Label(f, text="", fg="gray")
        self.char_addr_label.pack(anchor="w", padx=10)

        tk.Button(f, text="Save to ROM", command=self._save_char,
                  bg="lightgreen", font=("Arial", 11, "bold")).pack(pady=8)
        return f

    def _update_person_label(self, *_):
        try:
            val = self.char_fields["Person Type"].get()
            name = PERSON_TYPES.get(val, f"Unknown (0x{val:02X})")
            self.person_type_label.config(text=f"→ {name}")
        except Exception:
            pass

    def _load_char(self, event=None):
        if not self.app.rom_data:
            messagebox.showerror("Error", "Load a ROM first.")
            return
        idx = self.char_combo.current()
        name, addr = CHARACTERS[idx]
        self.char_addr_label.config(text=f"ROM address: 0x{addr:X}")
        d = self.app.rom_data

        def r(off, size): return read_bytes_at(d, addr + off, size)

        self.char_fields["Level"].set(r(0, 1))
        # offset 1 = padding byte (0x00)
        self.char_fields["HP"].set(r(2, 2))
        self.char_fields["EP"].set(r(4, 2))
        self.char_fields["Strength"].set(r(6, 1))
        self.char_fields["Power"].set(r(7, 1))
        self.char_fields["Endurance"].set(r(8, 1))
        self.char_fields["Speed"].set(r(9, 1))
        self.char_fields["Person Type"].set(r(10, 1))
        self.char_fields["Tech Count"].set(r(11, 1))
        for i in range(6):
            self.tech_fields[i].set(r(12 + i, 1))

        # Equipment slots at offsets 18–21
        equip_offsets = [("Body Armor", 18), ("Hands", 19), ("Feet", 20), ("Accessory", 21)]
        for slot_name, off in equip_offsets:
            cb, items = self.equip_combos[slot_name]
            val = r(off, 1)
            idx = next((i for i, (eid, _) in enumerate(items) if eid == val), 0)
            cb.current(idx)

    def _save_char(self):
        if not self.app.rom_path:
            messagebox.showerror("Error", "Load a ROM first.")
            return
        idx = self.char_combo.current()
        if idx < 0:
            return
        _, addr = CHARACTERS[idx]
        try:
            write_bytes_at(self.app.rom_path, addr + 0,  self.char_fields["Level"].get(), 1)
            # addr+1 = padding byte, don't write
            write_bytes_at(self.app.rom_path, addr + 2,  self.char_fields["HP"].get(), 2)
            write_bytes_at(self.app.rom_path, addr + 4,  self.char_fields["EP"].get(), 2)
            write_bytes_at(self.app.rom_path, addr + 6,  self.char_fields["Strength"].get(), 1)
            write_bytes_at(self.app.rom_path, addr + 7,  self.char_fields["Power"].get(), 1)
            write_bytes_at(self.app.rom_path, addr + 8,  self.char_fields["Endurance"].get(), 1)
            write_bytes_at(self.app.rom_path, addr + 9,  self.char_fields["Speed"].get(), 1)
            write_bytes_at(self.app.rom_path, addr + 10, self.char_fields["Person Type"].get(), 1)
            write_bytes_at(self.app.rom_path, addr + 11, self.char_fields["Tech Count"].get(), 1)
            for i in range(6):
                write_bytes_at(self.app.rom_path, addr + 12 + i, self.tech_fields[i].get(), 1)
            # Equipment slots
            equip_offsets = [("Body Armor", 18), ("Hands", 19), ("Feet", 20), ("Accessory", 21)]
            for slot_name, off in equip_offsets:
                cb, items = self.equip_combos[slot_name]
                sel = cb.current()
                if sel >= 0:
                    write_bytes_at(self.app.rom_path, addr + off, items[sel][0], 1)
            self.app.reload_rom()
            messagebox.showinfo("Saved", f"Character data written at 0x{addr:X}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ---- Enemies ----
    def _make_enemy_tab(self, parent):
        f = tk.Frame(parent)
        tk.Label(f, text="Select enemy:").pack(anchor="w", padx=10, pady=(10,0))

        self.enemy_var = tk.StringVar()
        enemy_names = [e[0] for e in ENEMIES]
        self.enemy_combo = ttk.Combobox(f, textvariable=self.enemy_var,
                                        values=enemy_names, state="readonly", width=30)
        self.enemy_combo.pack(anchor="w", padx=10)
        self.enemy_combo.bind("<<ComboboxSelected>>", self._load_enemy)

        form = tk.LabelFrame(f, text="Stats", padx=10, pady=8)
        form.pack(fill=tk.X, padx=10, pady=8)

        self.enemy_fields = {}
        # XP and HP are 3-byte; we show as single int
        fields = [
            ("XP",        0, 0, 3),
            ("HP",        0, 2, 3),
            ("Enemy Type",1, 0, 2),
            ("Level",     1, 2, 1),
            ("Strength",  2, 0, 1),
            ("Power",     2, 2, 1),
            ("Endurance", 2, 4, 1),
        ]
        # Store (offset, size) alongside
        self._enemy_field_meta = {
            "XP":         (0, 3),
            "HP":         (4, 3),
            "Enemy Type": (8, 2),
            "Level":      (12, 1),
            "Strength":   (13, 1),
            "Power":      (14, 1),
            "Endurance":  (15, 1),
        }
        for label, row, col, _ in fields:
            tk.Label(form, text=label+":", anchor="e", width=12).grid(row=row, column=col, sticky="e", pady=3)
            var = tk.IntVar()
            tk.Spinbox(form, from_=0, to=16777215, textvariable=var, width=10).grid(
                row=row, column=col+1, sticky="w", padx=4)
            self.enemy_fields[label] = var

        self.enemy_addr_label = tk.Label(f, text="", fg="gray")
        self.enemy_addr_label.pack(anchor="w", padx=10)

        tk.Button(f, text="Save to ROM", command=self._save_enemy,
                  bg="lightgreen", font=("Arial", 11, "bold")).pack(pady=8)
        return f

    def _load_enemy(self, event=None):
        if not self.app.rom_data:
            messagebox.showerror("Error", "Load a ROM first.")
            return
        idx = self.enemy_combo.current()
        name, addr = ENEMIES[idx]
        self.enemy_addr_label.config(text=f"ROM address: 0x{addr:X}")
        d = self.app.rom_data
        for label, (off, size) in self._enemy_field_meta.items():
            self.enemy_fields[label].set(read_bytes_at(d, addr + off, size))

    def _save_enemy(self):
        if not self.app.rom_path:
            messagebox.showerror("Error", "Load a ROM first.")
            return
        idx = self.enemy_combo.current()
        if idx < 0:
            return
        _, addr = ENEMIES[idx]
        try:
            for label, (off, size) in self._enemy_field_meta.items():
                write_bytes_at(self.app.rom_path, addr + off, self.enemy_fields[label].get(), size)
            self.app.reload_rom()
            messagebox.showinfo("Saved", f"Enemy data written at 0x{addr:X}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _make_equip_tab(self, parent):
        f = tk.Frame(parent)

        info = tk.Label(f,
            text="Equipment is a reference table — IDs map to items.\n"
                 "To change what equipment a character starts with, edit their Tech/stat data in Characters tab.\n"
                 "This tab shows the full item list for reference.",
            justify=tk.LEFT, fg="gray", padx=10, pady=8)
        info.pack(anchor="w")

        cols = ("ID", "Name", "Category")
        tree = ttk.Treeview(f, columns=cols, show="headings", height=25)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=150 if c == "Name" else 80)
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)

        sb = ttk.Scrollbar(f, command=tree.yview)
        tree.config(yscrollcommand=sb.set)

        for eid, ename in EQUIP_LIST:
            cat = "Body"
            if 0x2C <= eid < 0x4D: cat = "Hands"
            elif 0x4D <= eid < 0x70: cat = "Feet"
            elif 0x70 <= eid: cat = "Accessories"
            tree.insert("", tk.END, values=(f"0x{eid:02X}", ename, cat))

        return f


# ---------------------------------------------------------------------------
# Main Application
# ---------------------------------------------------------------------------
# Tab 5 — Compression Scanner (Huffman / RLE / LZ77)
# ---------------------------------------------------------------------------

class CompScannerTab(tk.Frame):
    """Scan ROM for GBA BIOS compressed blocks and preview/export decompressed data."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.results = []
        self._build_ui()

    def _build_ui(self):
        cfg = tk.LabelFrame(self, text="Compression Scanner", padx=8, pady=6)
        cfg.pack(fill=tk.X, padx=8, pady=6)

        # Type checkboxes
        r0 = tk.Frame(cfg); r0.pack(fill=tk.X, pady=2)
        tk.Label(r0, text="Scan for:").pack(side=tk.LEFT)
        self.do_huff8 = tk.BooleanVar(value=True)
        self.do_huff4 = tk.BooleanVar(value=True)
        self.do_rle   = tk.BooleanVar(value=True)
        self.do_lz77  = tk.BooleanVar(value=False)
        tk.Checkbutton(r0, text="Huffman 8-bit (0x28)", variable=self.do_huff8).pack(side=tk.LEFT, padx=6)
        tk.Checkbutton(r0, text="Huffman 4-bit (0x24)", variable=self.do_huff4).pack(side=tk.LEFT, padx=6)
        tk.Checkbutton(r0, text="RLE (0x30)",           variable=self.do_rle  ).pack(side=tk.LEFT, padx=6)
        tk.Checkbutton(r0, text="LZ77 (0x10)",          variable=self.do_lz77 ).pack(side=tk.LEFT, padx=6)

        # Size filter + scan button
        r1 = tk.Frame(cfg); r1.pack(fill=tk.X, pady=2)
        tk.Label(r1, text="Min dec. size (hex):").pack(side=tk.LEFT)
        self.min_entry = tk.Entry(r1, width=7); self.min_entry.insert(0, "100")
        self.min_entry.pack(side=tk.LEFT, padx=4)
        tk.Label(r1, text="Max:").pack(side=tk.LEFT)
        self.max_entry = tk.Entry(r1, width=8); self.max_entry.insert(0, "40000")
        self.max_entry.pack(side=tk.LEFT, padx=4)
        tk.Button(r1, text="Scan ROM", command=self._scan,
                  bg="#e0f7fa", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=12)
        self.scan_lbl = tk.Label(r1, text="", fg="gray")
        self.scan_lbl.pack(side=tk.LEFT)

        # Split: results list | hex preview
        pane = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashwidth=5)
        pane.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        # Left — results listbox
        left = tk.Frame(pane); pane.add(left, minsize=340)
        tk.Label(left, text="Found blocks (click to preview):").pack(anchor="w")
        lf = tk.Frame(left); lf.pack(fill=tk.BOTH, expand=True)
        vsb = tk.Scrollbar(lf); vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox = tk.Listbox(lf, yscrollcommand=vsb.set, font=("Courier", 9),
                                  selectmode=tk.SINGLE)
        self.listbox.pack(fill=tk.BOTH, expand=True)
        vsb.config(command=self.listbox.yview)
        self.listbox.bind("<<ListboxSelect>>", self._on_select)

        btn_row = tk.Frame(left); btn_row.pack(fill=tk.X, pady=4)
        tk.Button(btn_row, text="Export .bin", command=self._export_bin,
                  bg="#fff9c4").pack(side=tk.LEFT, padx=2)
        tk.Button(btn_row, text="View in Sprite Viewer", command=self._view_in_sprites,
                  bg="#e8f5e9").pack(side=tk.LEFT, padx=2)

        # Right — hex preview
        right = tk.Frame(pane); pane.add(right, minsize=220)
        tk.Label(right, text="Decompressed preview (first 256 bytes):").pack(anchor="w")
        self.preview = tk.Text(right, font=("Courier", 9), wrap=tk.WORD,
                               state=tk.DISABLED, bg="#1a1a1a", fg="#c8ffc8")
        self.preview.pack(fill=tk.BOTH, expand=True)

    # ---- scan ----

    def _scan(self):
        if not self.app.rom_data:
            messagebox.showerror("Error", "Load a ROM first.")
            return
        try:
            min_s = int(self.min_entry.get().strip(), 16)
            max_s = int(self.max_entry.get().strip(), 16)
        except ValueError:
            messagebox.showerror("Error", "Enter sizes as hex (e.g. 100, 40000).")
            return

        self.scan_lbl.config(text="Scanning…", fg="blue")
        self.listbox.delete(0, tk.END)
        self.listbox.insert(tk.END, "Please wait…")
        self.update()

        rom = self.app.rom_data
        self.results = []

        if self.do_huff8.get() or self.do_huff4.get():
            hits = gba_utils.scan_huffman_blocks(
                rom, min_s, max_s,
                do_4bit=self.do_huff4.get(),
                do_8bit=self.do_huff8.get())
            self.results.extend(hits)

        if self.do_rle.get():
            self.results.extend(gba_utils.scan_rle_blocks(rom, min_s, max_s))

        if self.do_lz77.get():
            for h in gba_utils.scan_lz77_blocks(rom, min_s, max_s):
                self.results.append({
                    'offset': h['offset'],
                    'type': 'LZ77',
                    'decompressed_size': h['decompressed_size'],
                })

        self.results.sort(key=lambda r: r['offset'])

        self.listbox.delete(0, tk.END)
        for r in self.results:
            self.listbox.insert(
                tk.END,
                f"0x{r['offset']:07X}  {r['type']:<12}  {r['decompressed_size']:6d} B dec")

        n = len(self.results)
        self.scan_lbl.config(text=f"{n} block{'s' if n!=1 else ''} found",
                             fg="green" if n else "orange")

    # ---- decompress on demand ----

    def _decompress_selected(self):
        sel = self.listbox.curselection()
        if not sel or sel[0] >= len(self.results):
            return None, None
        r = self.results[sel[0]]
        rom = self.app.rom_data
        try:
            if r['type'] == 'LZ77':
                data = gba_utils.lz77_decompress(rom, r['offset'])
            elif r['type'] == 'RLE':
                data = gba_utils.rle_decompress(rom, r['offset'])
            else:
                data = gba_utils.huffman_decompress(rom, r['offset'])
            return data, r
        except Exception as e:
            messagebox.showerror("Decompress error", str(e))
            return None, None

    def _on_select(self, event=None):
        data, r = self._decompress_selected()
        if data is None:
            return
        chunk = data[:256]
        lines = []
        for i in range(0, len(chunk), 16):
            row = chunk[i:i + 16]
            lines.append(f"{i:04X}: " + " ".join(f"{b:02X}" for b in row))
        self.preview.config(state=tk.NORMAL)
        self.preview.delete(1.0, tk.END)
        self.preview.insert(tk.END, "\n".join(lines))
        self.preview.config(state=tk.DISABLED)

    def _export_bin(self):
        data, r = self._decompress_selected()
        if data is None:
            if not self.results:
                messagebox.showwarning("Nothing selected", "Run a scan and select a block first.")
            return
        fp = filedialog.asksaveasfilename(
            defaultextension=".bin",
            initialfile=f"decomp_{r['type']}_{r['offset']:07X}.bin",
            filetypes=[("Binary", "*.bin"), ("All", "*.*")])
        if fp:
            with open(fp, 'wb') as f:
                f.write(data)
            messagebox.showinfo("Exported", f"Saved {len(data)} bytes → {fp}")

    def _view_in_sprites(self):
        data, r = self._decompress_selected()
        if data is None:
            if not self.results:
                messagebox.showwarning("Nothing selected", "Run a scan and select a block first.")
            return
        label = f"{r['type']} @ ROM 0x{r['offset']:X}  ({len(data)} bytes decompressed)"
        self.app.tab_sprites.view_raw_bytes(data, label)
        self.app.nb.select(self.app.tab_sprites)


# ---------------------------------------------------------------------------

class BuusFuryStudio:
    def __init__(self, root):
        self.root = root
        self.root.title("Buu's Fury Studio")
        self.root.geometry("1100x750")

        self.rom_path = ""
        self.rom_data = None
        self.table = {}
        self.reverse_table = {}

        self._build_top_bar()
        self._build_notebook()

    def _build_top_bar(self):
        bar = tk.LabelFrame(self.root, text="ROM & Table Files", padx=8, pady=6)
        bar.pack(fill=tk.X, padx=8, pady=(6, 0))

        tk.Label(bar, text="ROM:", width=6, anchor="e").grid(row=0, column=0)
        self.rom_entry = tk.Entry(bar, width=60)
        self.rom_entry.grid(row=0, column=1, padx=4)
        tk.Button(bar, text="Browse...", command=self._browse_rom).grid(row=0, column=2)

        tk.Label(bar, text=".tbl:", width=6, anchor="e").grid(row=1, column=0)
        self.tbl_entry = tk.Entry(bar, width=60)
        self.tbl_entry.grid(row=1, column=1, padx=4)
        tk.Button(bar, text="Browse...", command=self._browse_tbl).grid(row=1, column=2)

        tk.Button(bar, text="Load Files", command=self._load_files,
                  bg="#c8e6c9", font=("Arial", 10, "bold")).grid(row=0, column=3, rowspan=2, padx=10, sticky="ns")

        self.status_label = tk.Label(bar, text="No ROM loaded", fg="gray")
        self.status_label.grid(row=0, column=4, rowspan=2, padx=10)

    def _build_notebook(self):
        self.nb = ttk.Notebook(self.root)
        self.nb.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)

        self.tab_text = TextEditorTab(self.nb, self)
        self.nb.add(self.tab_text, text="Text Editor")

        self.tab_dialogue = DialogueTab(self.nb, self)
        self.nb.add(self.tab_dialogue, text="Dialogue")

        self.tab_sprites = SpriteTab(self.nb, self)
        self.nb.add(self.tab_sprites, text="Sprites")

        self.tab_stats = StatsTab(self.nb, self)
        self.nb.add(self.tab_stats, text="Stats & Values")

        self.tab_comp = CompScannerTab(self.nb, self)
        self.nb.add(self.tab_comp, text="Compression Scanner")

    def _browse_rom(self):
        fp = filedialog.askopenfilename(title="Select GBA ROM",
                                        filetypes=[("GBA ROM", "*.gba *.GBA"), ("All", "*.*")])
        if fp:
            self.rom_entry.delete(0, tk.END)
            self.rom_entry.insert(0, fp)

    def _browse_tbl(self):
        fp = filedialog.askopenfilename(title="Select Table File",
                                        filetypes=[("Table", "*.tbl"), ("All", "*.*")])
        if fp:
            self.tbl_entry.delete(0, tk.END)
            self.tbl_entry.insert(0, fp)

    def _load_files(self):
        rom = self.rom_entry.get().strip()
        tbl = self.tbl_entry.get().strip()

        if not os.path.exists(rom):
            messagebox.showerror("Error", "ROM file not found.")
            return

        self.rom_path = rom
        with open(rom, 'rb') as f:
            self.rom_data = f.read()

        if tbl and os.path.exists(tbl):
            try:
                self.table, self.reverse_table = gba_utils.load_tbl(tbl)
            except Exception as e:
                messagebox.showerror("Table Error", str(e))

        size_mb = len(self.rom_data) / (1024 * 1024)
        self.status_label.config(
            text=f"Loaded: {os.path.basename(rom)} ({size_mb:.1f} MB)",
            fg="green")
        self.tab_sprites.notify_rom_loaded(len(self.rom_data))

    def reload_rom(self):
        """Re-read ROM data from disk after a write."""
        if self.rom_path and os.path.exists(self.rom_path):
            with open(self.rom_path, 'rb') as f:
                self.rom_data = f.read()


if __name__ == "__main__":
    root = tk.Tk()
    app = BuusFuryStudio(root)
    root.mainloop()
