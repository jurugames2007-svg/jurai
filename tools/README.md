# Herramientas del repositorio

## Scripts propios

- `build_demo_assets.py`: genera el framebuffer Mode 4 del demo libgba.
- `png_to_mode4.py`: convierte una imagen a 240×160 y 256 colores.
- `create_gt_super_phase1.py`: primera modificación con definiciones nativas.
- `create_gt_super_phase3_roster.py`: inserta frames estáticos GT/Super.
- `create_gt_super_phase4_forms.py`: reemplaza visuales de estados Goku base,
  SSJ, SSJ3, GT y otros slots compatibles.

## DragonByteZ

`DragonByteZ/` es una herramienta de análisis de código abierto utilizada en
fase 2 para decodificar el formato Webfoot. Su compilación y licencia se
conservan dentro de su propia carpeta.

```sh
cmake -S tools/DragonByteZ -B tools/DragonByteZ/build \
  -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF
cmake --build tools/DragonByteZ/build -j2
```

## Disassembly de referencia

`buusfury_disassembly/` es una referencia externa de ingeniería inversa. No es
necesaria para compilar el demo libgba ni debe ejecutarse sobre una ROM distinta
sin verificar primero el checksum.

## BuusFuryToolkit

`BuusFuryToolkit/` contiene herramientas y notas de texto para investigar
codificación, personajes y diálogos. Se usa como referencia complementaria,
pero las modificaciones reproducibles de este repo deben vivir en scripts
propios con precondiciones y manifiestos.
