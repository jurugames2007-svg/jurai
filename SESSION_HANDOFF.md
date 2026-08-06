# Session handoff — DBZ Buu's Fury GT × Super

Use this file to restore the working context in a new authorized GitHub session.
Do not share tokens or credentials in chat.

## Suggested first prompt in the new session

```text
Continúa el proyecto DBZ Buu's Fury GT × Super desde SESSION_HANDOFF.md.

Repositorio: https://github.com/TU_USUARIO/DBZ_Buus_Fury_Hack
Rama: main
Lee primero README.md, ROADMAP.md, ROM_BASE_REPORT.md,
docs/LORE_DESIGN.md y docs/GITHUB_SETUP.md.

Base SHA-1: f1c4b07554d2a3b1ad2f325307051e775ce68087
Fase actual: 4 completada; empezar fase 5.
Objetivo inicial: portraits, nombres, textos y preparación de selector GT/Super.
No sobrescribas rom_base/.
Crea una rama nueva y un Pull Request para cada bloque de trabajo.
```

## Identidad de la ROM base

```text
Archivo: rom_base/DBZ_Buus_Fury_USA.gba
Tamaño: 8 MiB (8388608 bytes)
Game code: BG3E
SHA-1: f1c4b07554d2a3b1ad2f325307051e775ce68087
SHA-256: 940ad5f01db4465b8877dfe739510cbf34f4ea3d390f3df13519808bc36f059e
```

Si el SHA-1 cambia, no aplicar offsets automáticamente.

## Estado técnico

### Fase 1 — completada

- devkitPRO/devkitARM/libgba.
- Demo Mode 4 con doble buffer y VBlank.
- Makefile en la raíz.

### Fase 2 — completada

- DragonByteZ compilado y usado para analizar el codec Webfoot.
- Estructura confirmada:

```text
character structure
  -> animation table
    -> four-direction frame pointers
      -> OBJ piece records
        -> Webfoot graphics containers
```

- Paleta OBJ global: `0x0005652C`.
- Tabla de personajes: `0x006B6BDC`.
- Sprites nativos relevantes/documentación: `assets_extracted/phase2_native_sprites/`.

### Fase 3 — completada

`create_gt_super_phase3_roster.py` probó la inserción de frames estáticos tipo 0.

### Fase 4 — completada como prototipo

Archivo principal:

```text
patch_output/DBZ_Buus_Fury_GT_Super_phase4_forms.gba
patch_output/DBZ_Buus_Fury_GT_Super_phase4_forms.ips
```

SHA-1 de la ROM fase 4:

```text
4c1045609add45e92010f3363d74ae5f5ca7257f
```

Cambios visuales:

- Goku base: recorte de `ADULT GOKU GT.png`.
- Goku SSJ: recorte de `ADULT GOKU GT.png`.
- Goku SSJ3: recorte de `ADULT GOKU GT.png`.
- Goku GT: `GOKU SSJ4.png`.
- Trunks: `FUTURE TRUNKS DBS.png`.
- Super Buu slot: `BEERUS DBS.png`.
- Mystic Gohan slot: Gogeta nativo.
- Vegita slot: Vegito nativo.

La fase 4 conserva los IDs y la lógica de transformación del juego original,
pero todavía usa un frame estático por estado. No hay mapas, objetos, historia,
NPCs nuevos, selector nuevo ni nuevas técnicas todavía.

## Fases siguientes

### Fase 5 — siguiente

- Separar hojas de Hit, Zamasu, Broly, Gogeta y Vegito.
- Crear animaciones idle, caminar, correr, atacar y recibir daño.
- Insertar portraits.
- Cambiar nombres y textos con comprobación de tamaño.
- Preparar HUD y menú GT/Super.

### Fase 6

- Selector GT/Super.
- Nuevos slots o IDs documentados.
- Nuevas técnicas y costes de energía.
- Lógica de transformaciones nuevas: SSJ4, Blue, Rosé, Ultra Instinct.

### Fase 7

- Black Star Dragon Balls.
- Arco Baby/Tuffle.
- Beerus/Universe 6.
- Future Trunks/Goku Black/Zamasu.
- Torneo de Poder o Shadow Dragons.
- Mapas, NPCs, objetos, flags, eventos y diálogos.

### Fase 8

- QA de mGBA.
- Guardado/carga.
- Colisiones, técnicas y transformaciones.
- IPS/BPS final.

## Diseño narrativo

El proyecto usa una fractura temporal para unir GT y Super sin afirmar que ambas
continuidades son una sola línea oficial. La documentación de lore se encuentra
en `docs/LORE_DESIGN.md`, con enlaces a fuentes oficiales.

## Reglas de seguridad del proyecto

- Nunca escribir sobre `rom_base/`.
- Cada script debe comprobar el SHA-1.
- Cada modificación debe producir un manifiesto.
- Mantener ROM base y ROM modificada separadas.
- No compartir credenciales GitHub.
- Usar repositorio privado si se conservan ROMs y assets.

## Flujo GitHub con integración autorizada

Si la nueva sesión dispone de integración GitHub:

1. Leer este archivo.
2. Leer `docs/GITHUB_SETUP.md`.
3. Crear rama, por ejemplo `agent/phase5-text-portraits`.
4. Trabajar únicamente en esa rama.
5. Ejecutar pruebas y escribir manifiesto.
6. Crear Pull Request hacia `main`.
7. No modificar ni borrar `rom_base/`.
