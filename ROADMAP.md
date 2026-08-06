# Roadmap redefinido — GT × Super: Rift of Wishes

## Principios

- Trabajar siempre sobre el dump USA con SHA-1
  `f1c4b07554d2a3b1ad2f325307051e775ce68087`.
- No sobrescribir `rom_base/`.
- Todo cambio debe tener script reproducible, manifiesto de offsets y prueba en
  mGBA.
- No distribuir ROMs ni assets de terceros sin permisos; en GitHub se suben
  scripts, documentación y parches, no la ROM.
- Mantener el formato visual de Buu's Fury: pixel art, paletas GBA, piezas OBJ,
  frames de cuatro direcciones y mapas por tiles.

## Fases

### Fase 1 — Entorno y base verificada — COMPLETADA

- devkitPRO/devkitARM/libgba.
- mGBA para pruebas.
- Makefile y demo Mode 4.
- ROM base verificada por SHA-1.

### Fase 2 — Ingeniería inversa y extracción — COMPLETADA

- Tabla de personajes y punteros.
- Codec Webfoot mediante DragonByteZ.
- Exportación de estructuras, animaciones, frames y piezas OBJ.
- Paleta OBJ global documentada.

### Fase 3 — Primer roster GT/Super — COMPLETADA

- Goku GT, Trunks y Beerus sobre slots compatibles.
- Contenedores tipo 0 para probar inserción segura.
- Primer IPS y ROM de prueba.

### Fase 4 — Formas y estados visuales — COMPLETADA / PROTOTIPO

- Goku base, SSJ, SSJ3 y GT/SSJ4.
- Frames de 64×64 y paleta nativa.
- Conserva la lógica de estados existentes.
- Falta separar poses de acción.

### Fase 5 — Animaciones, portraits y texto — SIGUIENTE

Objetivos:

1. Separar `GOKU.png`, `HIT.png`, `ZAMASU.png`, `BROLY DBS.png` y las demás
   hojas en celdas y poses.
2. Crear un manifiesto por personaje:

   ```json
   {
     "character": "GOKU_GT",
     "idle": ["idle_00.png", "idle_01.png"],
     "walk": ["walk_00.png", "walk_01.png"],
     "attack": ["attack_00.png", "attack_01.png"],
     "hurt": ["hurt_00.png"]
   }
   ```

3. Asociar las poses a los índices de animación nativos.
4. Añadir nombres y portraits con límites de bytes comprobados.
5. Mantener cuatro direcciones y origen de pies consistente.

### Fase 6 — Selector y lógica de personajes

Objetivos:

- Crear un roster GT/Super seleccionable sin destruir el sistema de guardado.
- Ampliar o reutilizar slots con IDs documentados.
- Añadir técnicas compatibles con el sistema de energía de Buu's Fury.
- Implementar transformaciones nuevas:
  - SSJ4.
  - Super Saiyan God.
  - Super Saiyan Blue.
  - Rosé.
  - Ultra Instinct como estado experimental.
- Crear condiciones de transformación, coste de energía y reversión.
- Mantener una ruta segura de fallback si un frame falta.

### Fase 7 — Historia, mapas, NPCs y objetos

Orden recomendado:

1. Flags y diálogos de la fractura temporal.
2. Black Star Dragon Balls como coleccionables.
3. Arco Baby/Tuffle.
4. Arco Beerus/Universe 6.
5. Future Trunks/Goku Black/Zamasu.
6. Torneo de Poder o Shadow Dragons.

Cada mapa nuevo debe incluir:

- Tileset.
- Paleta.
- Mapa/collision layer.
- Entradas y salidas.
- NPCs.
- Scripts de eventos.
- Flags de progreso.
- Prueba de transición y guardado.

### Fase 8 — QA y distribución

- Probar arranque, guardado, carga y reinicio.
- Probar todas las transformaciones.
- Probar cada técnica y animación.
- Revisar colisiones y mapas.
- Verificar que no existan punteros fuera de la ROM.
- Comparar checksums.
- Generar IPS/BPS final.
- Publicar en GitHub solo código, documentación y parches permitidos.

## Hitos jugables

### Hito A — Sprite preview

Fase 4 actual: personajes modificados, sin historia nueva.

### Hito B — Roster visual

Fase 5: animaciones, portraits y nombres de GT/Super.

### Hito C — Demo narrativa

Fase 6/7: prólogo de la fractura temporal, un mapa pequeño y un jefe Baby o
Beerus.

### Hito D — Vertical slice

Una cadena completa: mapa → NPC → diálogo → batalla → transformación →
guardado.

### Hito E — Campaña

Arcos GT y Super con rutas y final seleccionable.
