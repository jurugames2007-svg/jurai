#!/usr/bin/env python3
"""
Corrige el vector de reset de la ROM
"""

ROM_INPUT = '/home/user/jurai/output/DBZ_Buus_Fury_10_10_Final_16MB.gba'
ROM_OUTPUT = '/home/user/jurai/output/DBZ_Buus_Fury_10_10_Final_Working.gba'

# Vector de reset correcto para GBA
CORRECT_RESET = bytes([0x2E, 0x00, 0x00, 0xEA])

with open(ROM_INPUT, 'rb') as f:
    rom_data = bytearray(f.read())

print(f"Vector de reset actual: {rom_data[:4].hex().upper()}")

# Corregir vector de reset
rom_data[:4] = CORRECT_RESET
print(f"Vector de reset corregido: {rom_data[:4].hex().upper()}")

# Recalcular checksum
checksum = 0
for byte in rom_data[:-2]:
    checksum += byte
checksum = (checksum & 0xFFFF) ^ 0xFFFF
rom_data[-2:] = checksum.to_bytes(2, 'little')

with open(ROM_OUTPUT, 'wb') as f:
    f.write(rom_data)

print(f"\nROM final: {len(rom_data)} bytes ({len(rom_data)/1024/1024:.2f} MB)")
print(f"Checksum: 0x{checksum:04X}")
print(f"Guardada en: {ROM_OUTPUT}")

# Verificar
with open(ROM_OUTPUT, 'rb') as f:
    data = f.read()

name = data[0xA0:0xAC].decode('ascii', errors='replace')
print(f"Nombre: {name}")

# Verificar DLC
dlc_chars = ['BROLY', 'EIS', 'NUOVA']
found = []
for char in dlc_chars:
    if char.encode() in data:
        found.append(char)
print(f"Personajes DLC: {', '.join(found)}")
