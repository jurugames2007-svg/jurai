#!/usr/bin/env python3
"""
Aplica parches IPS en cascada (uno tras otro)
"""

import os
import glob

ROM_BASE = '/home/user/jurai/rom_base/DBZ_Buus_Fury_USA.gba'
PATCH_DIR = '/home/user/jurai/patch_output'
OUTPUT_ROM = '/home/user/jurai/output/DBZ_Buus_Fury_Fully_Patched_Cascade.gba'


def apply_ips_patch(rom_data, patch_data):
    """Aplica un parche IPS a los datos de la ROM"""
    if patch_data[:5] != b'PATCH':
        raise ValueError("Archivo no es un parche IPS válido")
    
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


def main():
    # Cargar ROM base
    with open(ROM_BASE, 'rb') as f:
        rom_data = bytearray(f.read())
    
    print(f"ROM base: {len(rom_data)} bytes")
    
    # Obtener parches ordenados
    patch_files = sorted(glob.glob(os.path.join(PATCH_DIR, '*.ips')))
    print(f"Parches a aplicar: {len(patch_files)}")
    
    # Aplicar en cascada
    for i, patch_file in enumerate(patch_files, 1):
        patch_name = os.path.basename(patch_file)
        with open(patch_file, 'rb') as f:
            patch_data = f.read()
        
        old_size = len(rom_data)
        rom_data = apply_ips_patch(rom_data, patch_data)
        new_size = len(rom_data)
        
        size_diff = new_size - old_size
        print(f"[{i}/{len(patch_files)}] {patch_name}: {old_size/1024/1024:.2f}MB -> {new_size/1024/1024:.2f}MB ({size_diff:+d} bytes)")
    
    # Calcular checksum
    checksum = 0
    for byte in rom_data[:-2]:
        checksum += byte
    checksum = (checksum & 0xFFFF) ^ 0xFFFF
    rom_data[-2:] = checksum.to_bytes(2, 'little')
    
    # Guardar
    with open(OUTPUT_ROM, 'wb') as f:
        f.write(rom_data)
    
    print(f"\nROM final: {len(rom_data)} bytes ({len(rom_data)/1024/1024:.2f} MB)")
    print(f"Checksum: 0x{checksum:04X}")
    print(f"Guardada en: {OUTPUT_ROM}")
    
    # Verificar cambios
    with open(ROM_BASE, 'rb') as f:
        original = f.read()
    
    min_len = min(len(original), len(rom_data))
    diffs = sum(1 for a, b in zip(original[:min_len], rom_data[:min_len]) if a != b)
    print(f"Bytes diferentes en área común: {diffs}")
    
    if len(rom_data) > len(original):
        print(f"Bytes adicionales: {len(rom_data) - len(original)}")


if __name__ == '__main__':
    main()
