# Informe de análisis y modificación de la ROM base

## Identificación

- Archivo: `rom_base/DBZ_Buus_Fury_USA.gba`
- Tamaño: `0x800000` bytes (8 MiB)
- Título GBA: `DBZBUUSFURY`
- Código: `BG3E`
- SHA-1: `f1c4b07554d2a3b1ad2f325307051e775ce68087`
- SHA-256: `940ad5f01db4465b8877dfe739510cbf34f4ea3d390f3df13519808bc36f059e`

La SHA-1 coincide con el dump USA de referencia utilizado por la
descompilación pública de Buu's Fury, por lo que los offsets conocidos son
aplicables a esta copia.

## Hallazgos útiles

- Tabla de punteros de definiciones de personajes: `0x006B6BDC`.
- Entrada de Goku: `0x006B6D80`, apunta a `0x086AD1CC`.
- Entrada de Goku (GT): `0x006B6D84`, apunta a `0x086AD278`.
- Entrada de Gohan místico: `0x006B6D6C`, apunta a `0x086ACE80`.
- Entrada de Gogeta: `0x006B6D4C`, apunta a `0x086AC9B8`.
- Entrada de Vegita: `0x006B7010`, apunta a `0x086B58D4`.
- Entrada de Vegito: `0x006B7024`, apunta a `0x086B5CE0`.
- Paleta OBJ global: `0x0005652C`, 256 colores BGR555.
- Cadenas de nombres de la base: UTF-16LE alrededor de `0x00587DA`.
- Textos grandes del juego: tablas de punteros alrededor de `0x007B5B64`.

## Fase 1

`tools/create_gt_super_phase1.py` genera una primera modificación reversible:

- Goku → Goku GT nativo.
- Gohan místico → Gogeta nativo.
- Vegita → Vegito nativo.
- Header de desarrollo: `DBZGTSPHACK1`.

## Fase 2: codec y extracción

Se compiló `tools/DragonByteZ` con CMake y se usó su comando `graphics` sobre
la ROM exacta. La herramienta decodifica el formato real de Webfoot:

```text
estructura de personaje
  -> tabla de animaciones
    -> tabla de frames por dirección
      -> registros de piezas OBJ
        -> contenedores gráficos tipo 0/1/2
```

Cada registro de pieza expone posición, atributos OBJ, dimensiones y puntero al
contenedor. Los contenedores tipo 1/2 usan el bitstream propio del juego; los
tipo 0 contienen datos gráficos sin comprimir. Se conservaron los recursos
nativos relevantes en:

```text
assets_extracted/phase2_native_sprites/
```

Los IDs conservados son 028 (Broly), 092/093 (Gogeta), 105/106 (Goku/Goku GT)
y 269–275 (variantes de Vegeta/Vegito). El CSV documenta los offsets de
estructuras, animaciones y frames.

## Fase 3: importación funcional inicial

`tools/create_gt_super_phase3_roster.py` inserta tres assets adjuntos como
frames estáticos de 64×64 píxeles, 8bpp, usando la paleta OBJ nativa y
contenedores tipo 0:

- `GOKU SSJ4.png` → estructura Goku GT (`0x086AD278`).
- `FUTURE TRUNKS DBS.png` → estructura Trunks (`0x086B500C`).
- `BEERUS DBS.png` → estructura Super Buu (`0x086AA2F0`).

La salida es:

```text
patch_output/DBZ_Buus_Fury_GT_Super_phase3_roster.gba
patch_output/DBZ_Buus_Fury_GT_Super_phase3_roster.ips
patch_output/DBZ_Buus_Fury_GT_Super_phase3_roster.txt
```

La ROM de fase 3 fue abierta en mGBA y alcanza escenas de gameplay sin
cuelgue. En esta fase cada estructura conserva sus tiempos de animación, pero
todos sus frames no nulos apuntan al mismo frame importado. Esto comprueba la
ruta completa de inserción sin afirmar todavía que las animaciones estén
terminadas.

## Fase 4: estados de transformación visuales

Se generó:

```text
patch_output/DBZ_Buus_Fury_GT_Super_phase4_forms.gba
patch_output/DBZ_Buus_Fury_GT_Super_phase4_forms.ips
```

La fase 4 reusa los IDs nativos del juego y modifica visualmente:

- Goku base usando el primer recorte de `ADULT GOKU GT.png`.
- Goku SSJ usando el segundo recorte.
- Goku SSJ3 usando el tercer recorte.
- Goku GT usando `GOKU SSJ4.png`.
- Trunks usando `FUTURE TRUNKS DBS.png`.
- Super Buu usando `BEERUS DBS.png`.

Los seis estados se escriben como frames 64×64 8bpp con la paleta OBJ global,
y cada tabla de animación conserva su cantidad y timing nativos. La ROM de fase
4 fue abierta en mGBA y alcanzó escenas de gameplay sin cuelgue.

Esto es una sustitución visual de estados ya existentes, no un sistema nuevo de
transformaciones: todavía no existen nuevos IDs, técnicas, menús, mapas,
objetos, NPCs ni diálogos. Las poses de acción siguen siendo estáticas en esta
fase.

## Fases restantes

Después de la fase 4 quedan:

5. portraits, nombres, textos e interfaz;
6. selector/roster, nuevos IDs, ataques y transformaciones nuevas;
7. mapas, objetos, NPCs, eventos e historia;
8. QA de guardado, colisiones, técnicas, mGBA y parche final BPS/IPS.

La ROM base no se sobrescribe; todas las salidas se escriben en
`patch_output/`.
