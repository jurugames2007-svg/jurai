#!/usr/bin/env python3
"""
Construye una ROM de GBA válida - Versión corregida
"""

import glob
import os

ROM_BASE = '/home/user/jurai/rom_base/DBZ_Buus_Fury_USA.gba'
PATCH_DIR = '/home/user/jurai/patch_output'
ROM_OUTPUT = '/home/user/jurai/output/DBZ_Buus_Fury_Final_Working.gba'
TARGET_SIZE = 16 * 1024 * 1024  # 16MB exacto

def apply_ips_patch(rom_data, patch_data):
    """Aplica un parche IPS"""
    if patch_data[:5] != b'PATCH':
        return rom_data
    
    offset = 5
    while offset < len(patch_data):
        if offset + 3 > len(patch_data):
            break
        addr = (patch_data[offset] << 16) | (patch_data[offset+1] << 8) | patch_data[offset+2]
        offset += 3
        
        if offset + 2 > len(patch_data):
            break
        size = (patch_data[offset] << 8) | patch_data[offset+1]
        offset += 2
        
        if size == 0:
            if offset + 2 > len(patch_data):
                break
            rle_size = (patch_data[offset] << 8) | patch_data[offset+1]
            offset += 2
            if offset >= len(patch_data):
                break
            byte_val = patch_data[offset]
            offset += 1
            
            for i in range(rle_size):
                if addr + i < len(rom_data):
                    rom_data[addr + i] = byte_val
                else:
                    rom_data.append(byte_val)
        else:
            if offset + size > len(patch_data):
                break
            patch_chunk = patch_data[offset:offset+size]
            offset += size
            
            for i in range(size):
                if addr + i < len(rom_data):
                    rom_data[addr + i] = patch_chunk[i]
                else:
                    rom_data.append(patch_chunk[i])
    
    return rom_data

# 1. Cargar ROM base
with open(ROM_BASE, 'rb') as f:
    rom_data = bytearray(f.read())

print(f"1. ROM base: {len(rom_data)} bytes")

# 2. Aplicar todos los parches IPS
patch_files = sorted(glob.glob(os.path.join(PATCH_DIR, '*.ips')))
for i, patch_file in enumerate(patch_files, 1):
    with open(patch_file, 'rb') as f:
        patch_data = f.read()
    rom_data = apply_ips_patch(rom_data, patch_data)

print(f"2. Después de parches: {len(rom_data)} bytes")

# 3. Expandir a 16MB exacto
if len(rom_data) < TARGET_SIZE:
    rom_data.extend(b'\x00' * (TARGET_SIZE - len(rom_data)))
print(f"3. Después de expandir: {len(rom_data)} bytes")

# 4. Corregir header GBA - USAR ASIGNACIÓN DIRECTA POR BYTE PARA EVITAR TRUNCAMIENTO
# Reset vector (0x00-0x03)
rom_data[0] = 0x2E
rom_data[1] = 0x00
rom_data[2] = 0x00
rom_data[3] = 0xEA

# Game title (0xA0-0xAC = 12 bytes)
title = b'DBZ BUU FURY'
for i, byte in enumerate(title):
    rom_data[0xA0 + i] = byte
# Rellenar el resto con ceros
for i in range(len(title), 12):
    rom_data[0xA0 + i] = 0x00

# Reservado (0xAC-0xBF = 20 bytes)
for i in range(0xAC, 0xC0):
    rom_data[i] = 0x00

# Game code (0xBC-0xBF = 4 bytes)
game_code = b'BG3E'
for i, byte in enumerate(game_code):
    rom_data[0xBC + i] = byte

# Maker code (0xC0-0xC1 = 2 bytes)
rom_data[0xC0] = 0x96
rom_data[0xC1] = 0x00

# Fixed value (0xC2)
rom_data[0xC2] = 0x96

# Main unit code (0xC3)
rom_data[0xC3] = 0x00

# Device type (0xC4)
rom_data[0xC4] = 0x00

# Reservado (0xC5-0xC6)
rom_data[0xC5] = 0x00
rom_data[0xC6] = 0x00

# Version (0xC6 ya está a 0x00)

# Header checksum (0xC7)
checksum_hdr = 0
for i in range(0xA0, 0xC7):
    checksum_hdr += rom_data[i]
checksum_hdr = (checksum_hdr + 0x19) & 0xFF
rom_data[0xC7] = checksum_hdr

print(f"4. Después de corregir header: {len(rom_data)} bytes")

# ROM checksum (últimos 2 bytes)
full_checksum = 0
for byte in rom_data[:-2]:
    full_checksum += byte
full_checksum = (full_checksum & 0xFFFF) ^ 0xFFFF
rom_data[-2] = full_checksum & 0xFF
rom_data[-1] = (full_checksum >> 8) & 0xFF

print(f"5. Después de checksum: {len(rom_data)} bytes")

# 6. Guardar
with open(ROM_OUTPUT, 'wb') as f:
    f.write(rom_data)

import os
file_size = os.path.getsize(ROM_OUTPUT)
print(f"6. Archivo guardado: {file_size} bytes")

# Verificación final
print("\n" + "=" * 80)
print("VERIFICACIÓN FINAL:")
print(f"  Tamaño: {file_size} bytes ({file_size/1024/1024:.2f} MB)")
print(f"  Potencia de 2: {file_size == TARGET_SIZE}")
print(f"  Reset vector: {rom_data[:4].hex().upper()}")
print(f"  Game title: {bytes(rom_data[0xA0:0xAC]).decode('ascii', errors='replace')}")
print(f"  Header checksum: 0x{rom_data[0xC7]:02X}")
print(f"  ROM checksum: 0x{full_checksum:04X}")

# Verificar DLC
dlc_chars = ['BROLY', 'EIS', 'NUOVA', 'COOLER', 'JANEMBA']
found = []
for char in dlc_chars:
    if char.encode() in rom_data:
        found.append(char)
print(f"  Personajes DLC: {', '.join(found)}")
print("=" * 80)
