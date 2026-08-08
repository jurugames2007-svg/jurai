#!/usr/bin/env python3
"""
Expande la ROM a 16MB (potencia de 2) con padding de ceros
"""

ROM_INPUT = '/home/user/jurai/output/DBZ_Buus_Fury_10_10_Complete.gba'
ROM_OUTPUT = '/home/user/jurai/output/DBZ_Buus_Fury_10_10_Final_16MB.gba'
TARGET_SIZE = 16 * 1024 * 1024  # 16MB

with open(ROM_INPUT, 'rb') as f:
    rom_data = bytearray(f.read())

print(f"Tamaño actual: {len(rom_data)} bytes ({len(rom_data)/1024/1024:.2f} MB)")

# Expandir a 16MB con ceros
if len(rom_data) < TARGET_SIZE:
    rom_data.extend(b'\x00' * (TARGET_SIZE - len(rom_data)))
    print(f"Expandido a: {len(rom_data)} bytes ({len(rom_data)/1024/1024:.2f} MB)")
else:
    print(f"Ya es de 16MB o más")

# Recalcular checksum
checksum = 0
for byte in rom_data[:-2]:
    checksum += byte
checksum = (checksum & 0xFFFF) ^ 0xFFFF
rom_data[-2:] = checksum.to_bytes(2, 'little')

with open(ROM_OUTPUT, 'wb') as f:
    f.write(rom_data)

print(f"ROM final guardada: {ROM_OUTPUT}")
print(f"Checksum: 0x{checksum:04X}")
print(f"Tamaño: {len(rom_data)} bytes ({len(rom_data)/1024/1024:.2f} MB)")
