#!/usr/bin/env python3
import json
import sys
from pathlib import Path

def extract_files(rom_path):
    with open(rom_path, 'rb') as f:
        rom_data = f.read()
    
    # Read file table from ROM
    file_table_end = rom_data.find(b'\x00\x00', 256)
    if file_table_end == -1:
        file_table_end = file_table_offset + 4096  # Max size for file table
    
    file_table_json = rom_data[file_table_offset:file_table_end].decode('utf-8', errors='ignore')
    
    try:
        file_table = json.loads(file_table_json)
    except:
        print("ERROR: Could not parse file table")
        return
    
    # Create output directory
    output_dir = Path("extracted_files")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Extract each file
    for file_info in file_table.get('files', []):
        offset = file_info['offset']
        size = file_info['size']
        name = file_info['name']
        
        file_data = rom_data[offset:offset+size]
        output_path = output_dir / name
        
        with open(output_path, 'wb') as f:
            f.write(file_data)
        
        print(f"Extracted: {name} ({size} bytes) to {output_path}")
    
    print(f"\nAll files extracted to: {output_dir.absolute()}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("USAGE: python extract_files.py [rom_path]")
        sys.exit(1)
    
    extract_files(sys.argv[1])
