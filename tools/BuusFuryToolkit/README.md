# BuusFuryToolkit

A Python toolkit for reverse-engineering and modding **Dragon Ball Z: Buu's Fury** (GBA).  
Explore ROM memory, decode the game's custom character encoding, and patch binary dialogue data through a GUI.

---

## Tools

### Buu's Fury Studio (`PyFiles/DialogFinder.py`)
The main GUI tool. Load a ROM and a `.tbl` character table, scan for dialogue, and edit it in-place.

**Features:**
- Scans the ROM and decodes bytes using the game's custom character table (`.tbl`)
- Filters out binary garbage using linguistic heuristics (vowel checks, known UI strings, bracket limits)
- Edit pane with byte-space constraints — prevents edits from overflowing into adjacent data
- Writes changes directly back into the ROM file
- Displays GBA memory addresses (`ROM offset + 0x08000000`)

### Text Editor (`PyFiles/TextEditor.py`)
A simpler earlier version of the same core tool with fewer UI features.

---

## Requirements

- Python 3 with `tkinter` (standard library — no pip installs needed)

```bash
python PyFiles/DialogFinder.py
```

---

## Repository Contents

| Path | Description |
|------|-------------|
| `PyFiles/` | Python GUI source code |
| `Buu's Fury.tbl` | Custom character encoding table for the game |
| `Base Stats.txt` | Documented ROM addresses for character base stats |
| `Enemies.txt` | Enemy data addresses |
| `Equipment.txt` | Equipment data addresses |
| `Findings.txt` | Research notes and ROM findings |
| `Person Types.txt` | Sprite/person type ID mappings |
| `PNG/` `Palette/` | Extracted sprite and palette data |
| `TileMolester-master/` | Java tile graphics editor (third-party, included for reference) |

---

## How It Works

GBA ROMs use custom character encodings rather than standard ASCII.  
This toolkit reads a `.tbl` file that maps hex bytes to characters (e.g. `20=space`, `0A=newline`), then scans the ROM binary for sequences that match readable text.

Edits are injected back at the exact byte offset, respecting the original byte-length of each string to avoid corrupting surrounding data.

---

## Notes

- ROM files are **not included** in this repository (copyright).
- Tested on *Dragon Ball Z: Buu's Fury* (GBA, US version).
