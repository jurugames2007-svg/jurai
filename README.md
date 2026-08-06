# DBZ Buu's Fury Hack — GT × Super: Rift of Wishes

Repositorio de trabajo para un hack de *Dragon Ball Z: Buu's Fury* (GBA) con
contenido inspirado en **Dragon Ball GT** y **Dragon Ball Super**, además de un
demo independiente preparado para compilarse con **devkitPRO/devkitARM +
libgba**. El diseño narrativo, la continuidad propuesta y las decisiones de
roster están documentadas en `docs/LORE_DESIGN.md` y `ROADMAP.md`.

El demo libgba arranca en **Mode 4**, usa una paleta de 256 colores, doble
buffer y espera de VBlank antes de presentar cada frame.

> Importante: este workspace privado conserva la ROM base, la ROM modificada y los assets para que el trabajo pueda continuar. El `.gitignore` solo excluye builds y caches; no excluye ROMs. Para GitHub público usa `DBZ_Buus_Fury_Hack_GitHub.zip`; para continuar con el agente usa el paquete completo y considera un repositorio privado. La ROM base nunca se sobrescribe.

## Estructura

```text
DBZ_Buus_Fury_Hack/
├── Makefile
├── README.md
├── source/main.c                 # Mode 4, input, VBlank y demo interactivo
├── include/generated_scene.h     # framebuffer/paleta generado
├── data/scene_preview.png        # vista previa del asset generado
├── ROM_BASE_REPORT.md            # identificación y offsets comprobados
├── tools/
│   ├── build_demo_assets.py      # crea la pantalla de prueba desde los assets
│   ├── png_to_mode4.py           # convierte una imagen a 240x160 + paleta GBA
│   └── create_gt_super_phase1.py # genera la primera IPS/ROM de prueba
├── new_assets/                   # imágenes adjuntas usadas como referencia/demo
├── rom_base/                     # copia limpia USA verificada por SHA-1
├── assets_extracted/             # reservado para dumps/recursos analizados
└── patch_output/                 # ROM, IPS y manifiesto de la fase 1
```

## Requisitos

1. devkitPro con `devkitARM` y la biblioteca `libgba` (`gba-dev`).
2. `make`.
3. Python 3 + Pillow **solo si se desea regenerar** `include/generated_scene.h`.
4. mGBA para probar el `.gba`; no es necesario para compilar.

En una instalación de devkitPro que use `dkp-pacman`, el grupo habitual para GBA es:

```sh
dkp-pacman -S gba-dev
```

Verifica las variables antes de compilar:

```sh
export DEVKITPRO=/opt/devkitpro
export DEVKITARM="$DEVKITPRO/devkitARM"
```

En Windows se deben definir las mismas variables desde el entorno de devkitPro; no hace falta ejecutar literalmente `export`.

## Compilar

Desde esta carpeta:

```sh
make
```

El resultado esperado es:

```text
DBZ_Buus_Fury_Hack.gba
```

Para limpiar objetos y el ROM generado:

```sh
make clean
```

Para generar la primera copia del hack usando definiciones nativas GT/Super
que ya existen dentro del juego:

```sh
python3 tools/create_gt_super_phase1.py
```

Eso crea una ROM de prueba y un parche IPS en `patch_output/`. El script
comprueba el SHA-1 antes de escribir y nunca modifica `rom_base/`.

Si aparece `DEVKITARM no esta definido`, abre una terminal de devkitPro o configura `DEVKITARM` apuntando a la carpeta `devkitARM`.

## Probar en mGBA

1. Abre mGBA.
2. Selecciona `File > Open ROM`.
3. Carga `DBZ_Buus_Fury_Hack.gba`.
4. Controles del demo:
   - `A`, `LEFT`, `RIGHT`: cambiar personaje.
   - `B`: personaje anterior; en la pantalla de información vuelve al roster.
   - `START`: alternar roster/información.

## Qué hace el código de vídeo

En `source/main.c` se encuentra el flujo pedido:

```c
irqInit();
irqEnable(IRQ_VBLANK);
SetMode(MODE_4 | BG2_ENABLE);
```

El GBA tiene dos buffers de Mode 4:

- visible: `0x06000000`;
- alternativo: `0x0600A000`.

El código dibuja en el buffer oculto, llama a `VBlankIntrWait()` y luego conmuta `BACKBUFFER`. Así no se presenta una imagen a medio copiar. El bucle principal también llama a `scanKeys()` y `keysDown()` una vez por frame.

## Regenerar la pantalla de prueba

Las imágenes adjuntas se copiaron en `new_assets/`. Para volver a crear el header y su preview:

```sh
python3 -m pip install pillow
python3 tools/build_demo_assets.py
make clean
make
```

El generador cuantiza la composición a 256 colores y escribe valores de paleta en formato BGR555 de GBA. Para convertir una imagen individual a un framebuffer Mode 4:

```sh
python3 tools/png_to_mode4.py \
  "new_assets/GOKU SSJ4.png" \
  --name goku_mode4 \
  --output include/goku_mode4.h \
  --preview data/goku_mode4.png
```

El header individual debe incluirse y dibujarse desde `main.c` si se quiere reemplazar la escena de ejemplo. La herramienta no detecta offsets, punteros ni compresión de una ROM.

## Fase 2: extracción nativa

Se incorporó `tools/DragonByteZ`, una herramienta de análisis compatible con el
checksum USA verificado. Para reconstruirla:

```sh
cmake -S tools/DragonByteZ -B tools/DragonByteZ/build \
  -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF
cmake --build tools/DragonByteZ/build -j2
```

La herramienta decodifica las estructuras reales de personajes, las tablas de
animaciones de cuatro direcciones, los registros de piezas OBJ y los
contenedores gráficos Webfoot. Los sprites nativos relevantes se conservaron en
`assets_extracted/phase2_native_sprites/` junto con su CSV de offsets.

## Fase 3: primera importación GT/Super

Ejecuta:

```sh
python3 tools/create_gt_super_phase3_roster.py
```

La salida se crea en `patch_output/`:

- `DBZ_Buus_Fury_GT_Super_phase3_roster.gba`
- `DBZ_Buus_Fury_GT_Super_phase3_roster.ips`
- `DBZ_Buus_Fury_GT_Super_phase3_roster.txt`
- `DBZ_Buus_Fury_GT_Super_phase3_roster_previews/`

Esta primera importación usa contenedores gráficos nativos de tipo 0
(descomprimidos), preserva los tiempos de animación del juego y redirige todos
los frames válidos de tres estructuras:

- `GOKU SSJ4.png` → Goku GT;
- `FUTURE TRUNKS DBS.png` → Trunks;
- `BEERUS DBS.png` → Super Buu.

El frame insertado es estático durante esta fase; el siguiente paso es separar
las hojas con múltiples poses en frames individuales para restaurar idle,
caminar, atacar, recibir daño y técnicas. Las hojas de Hit, Zamasu, Gogeta,
Vegito y otras imágenes quedan preparadas en `new_assets/` para esa fase.

## Fase 4: estados de transformación visuales

Se generó también:

```text
patch_output/DBZ_Buus_Fury_GT_Super_phase4_forms.gba
patch_output/DBZ_Buus_Fury_GT_Super_phase4_forms.ips
```

Esta versión conserva los IDs de transformación existentes y reemplaza sus
visuales:

- Goku base → forma base de `ADULT GOKU GT.png`.
- Goku SSJ → forma SSJ de `ADULT GOKU GT.png`.
- Goku SSJ3 → forma SSJ3 de `ADULT GOKU GT.png`.
- Slot Goku GT → `GOKU SSJ4.png`.
- Trunks → `FUTURE TRUNKS DBS.png`.
- Slot Super Buu → `BEERUS DBS.png`.

La fase conserva la lógica original de transformación; todavía no crea nuevos
IDs, nuevas técnicas ni una pantalla de transformación. Los frames siguen
siendo estáticos por estado, pero el motor, la paleta, los atributos OBJ, las
dimensiones y los contenedores gráficos son los del juego original.

## Fases restantes

Después de la fase 4 quedan cuatro fases principales:

5. **Texto, portraits e interfaz:** nombres, retratos, HUD y menús.
6. **Selector/roster y lógica:** selector GT/Super, slots adicionales, ataques y
   transformaciones nuevas.
7. **Mapas, objetos, NPCs e historia:** escenarios, eventos, diálogos y objetos
   nuevos.
8. **QA y distribución:** pruebas de guardado, colisiones, animaciones,
   compatibilidad mGBA y parche BPS/IPS final.

La ROM de fase 4 es una copia local de prueba; la ROM base nunca se
sobrescribe.

## Estado actual v0.1 / Phase 28

- ROM recomendada de prueba actual: `patch_output/DBZ_LOG4_phase26_bubbles_start_gateway.gba`.
- Paquete de prueba v0.1: `patch_output/LOG4_v0_1_bubbles_gateway_test_pack.zip`.
- Kit completo de assets faltantes en dimensiones nativas: `patch_output/LOG4_phase28_missing_asset_kit.zip`.
- Línea principal prevista: Buu's Fury original → post Kid Buu (`Super`, `GT`, `AF`) → dimensiones pre Kid Buu (`LOG1_DIMENSION`, `LOG2_DIMENSION`).
- Próximo hito jugable: hacer que Bubbles/Gate Guide abra un menú real de selección y conecte al menos una mini-ruta completa.

## Phase 44 title/menu asset

AI-assisted native GBA title/menu art is available at:

- `additive_content/title_screen/LOG4_title_screen_240x160.png`
- `additive_content/title_screen/LOG4_main_menu_240x160.png`
- `include/log4_title_screen.h`
- `patch_output/DBZ_LOG4_phase44_title_screen_payload.gba`

This is an append-only payload/title asset; a future runtime title hook is still required to replace the in-game title flow.

## Phase 47 title runtime hook

The first visible in-game LOG4 title screen hook is available at:

- `patch_output/DBZ_LOG4_phase47_title_screen_kind0_hook.gba`

This redirects the original splash/title graphics pointers to an appended uncompressed Webfoot container using the LOG4 title screen art. Runtime screenshots confirm the custom title appears in the title flow.

## Phase 49 boot Gateway selector

The first real boot-time route/dimension selector is available at:

- `patch_output/DBZ_LOG4_phase49_boot_gateway_menu.gba`

Controls:

- Up/Down: select route.
- A/Start on `ORIGINAL`: boot the original Buu's Fury flow.
- A/Start on `SUPER`, `GT`, `AF`, `LOG1 DIM`, `LOG2 DIM`: show the route/dimension debug screen.
- B: return from route/dimension screen to the Gateway selector.
- Start from a route/dimension screen: boot original Buu's Fury.

This is currently a debug selector with route info screens. Native map warps are the next hook.

## Phase 51–55 playable Gateway rooms and native registry

Current advanced test packages:

- v0.3 playable warp-room pack: `patch_output/LOG4_v0_3_playable_warp_rooms_pack.zip`
- v0.3.1 native-registry pack: `patch_output/LOG4_v0_3_1_native_registry_pack.zip`
- Advanced ROM: `patch_output/DBZ_LOG4_phase54_gateway_native_map_registry.gba`

What works now:

- Gateway appears immediately at boot.
- `ORIGINAL` / Start still boots the untouched Buu's Fury flow.
- `SUPER`, `GT`, `AF`, `LOG1 DIM`, and `LOG2 DIM` open playable 240×160 GBA Mode 3 debug rooms.
- D-pad moves a tester marker; A on `HOME` returns to Gateway; A on `NEXT` warps to the next room; L/R cycles rooms.
- Phase 53 traced the native AreaEntry lookup at `0x080089FC`.
- Phase 54 additively registers native route IDs `F0:01` through `F0:05` by extending the AreaEntry table from 452 to 457 entries.

Honest status: Gateway-to-native-map transition is not implemented yet. The current rooms are playable debug rooms plus native registry groundwork for the next map-constructor hook.

## Phase 56–62 v0.4 DLC asset readiness

Current asset-readiness package:

- v0.4 DLC asset-readiness pack: `patch_output/LOG4_v0_4_dlc_asset_readiness_pack.zip`
- Advanced ROM with appended asset bank: `patch_output/DBZ_LOG4_phase61_dlc_asset_bank_payload.gba`

New add-only DLC asset payloads:

- 22 playable-route 32×32 sprite sheets in `additive_content/phase57_playable_32x32_sprites/`.
- 37 enemy/boss 32×32 sprite sheets in `additive_content/phase59_enemy_32x32_sprites/`.
- 16 AI-assisted portraits, processed to 40×40 and 32×32, in `additive_content/phase58_ai_portraits/`.
- 28 item/object/warp-pad 32×32 icons in `additive_content/phase60_dlc_objects_tiles/`.
- Custom appended `LOG4A32` asset bank in `additive_content/phase61_dlc_asset_bank/` and the Phase 61 ROM.

Runtime status: the Phase 61 ROM still passes boot Gateway rooms and original fallback tests. Honest limitation: the new art is banked/payload-ready but is not yet rendered by native Buu's Fury OBJ/dialogue/item hooks.
