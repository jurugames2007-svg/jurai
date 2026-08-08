#!/usr/bin/env python3
"""
Corrige el header de la ROM para que tenga un nombre mejor
"""

ROM_INPUT = '/home/user/jurai/output/DBZ_Buus_Fury_Fully_Patched_Cascade.gba'
ROM_OUTPUT = '/home/user/jurai/output/DBZ_Buus_Fury_10_10_Complete.gba'

# Nombre del juego (12 bytes, offset 0xA0)
NEW_TITLE = b'DBZ BUU FURY 10'
# Rellenar con espacios si es necesario
NEW_TITLE = NEW_TITLE.ljust(12, b' ')

# Código del juego (4 bytes, offset 0xBC)
NEW_CODE = b'BG3E'

# Maker code (2 bytes, offset 0xBE) - usualmente 96 para juegos de Bandai
NEW_MAKER = b'\x96\x00'

with open(ROM_INPUT, 'rb') as f:
    rom_data = bytearray(f.read())

# Aplicar nuevos valores
rom_data[0xA0:0xA0+12] = NEW_TITLE
rom_data[0xBC:0xBC+4] = NEW_CODE
rom_data[0xBE:0xBE+2] = NEW_MAKER

# Recalcular checksum
checksum = 0
for byte in rom_data[:-2]:
    checksum += byte
checksum = (checksum & 0xFFFF) ^ 0xFFFF
rom_data[-2:] = checksum.to_bytes(2, 'little')

with open(ROM_OUTPUT, 'wb') as f:
    f.write(rom_data)

print(f"ROM final: {len(rom_data)} bytes ({len(rom_data)/1024/1024:.2f} MB)")
print(f"Nuevo título: {NEW_TITLE.decode('ascii')}")
print(f"Checksum: 0x{checksum:04X}")
print(f"Guardada en: {ROM_OUTPUT}")
