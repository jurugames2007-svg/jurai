# Subir este repositorio completo a GitHub

Este repo está configurado como **workspace privado completo**. A petición del
usuario, `.gitignore` ya no excluye:

- ROM base `.gba`.
- ROMs modificadas `.gba`.
- Parches `.ips`/`.bps`.
- Imágenes de `new_assets/`.
- Saves locales de prueba.

## Advertencia importante

Una ROM comercial y algunos sprites/imágenes pueden estar protegidos por
copyright y por las reglas de GitHub. Para un repositorio público, la opción
recomendada sigue siendo el paquete sanitizado que no contiene ROM ni assets.
Para continuar el trabajo con el agente, usa el paquete completo en un
repositorio **privado** o conserva el ZIP completo fuera de GitHub.

La decisión de no ignorar las ROMs se tomó para que otra sesión pueda leer todos
los archivos inmediatamente, pero no convierte automáticamente esos archivos
en redistribuibles.

## Contenido completo

El ZIP completo contiene:

- ROM base USA verificada.
- ROM de fase 4.
- Parches y manifiestos.
- Assets adjuntos.
- Scripts de fase 1–4.
- Herramientas DragonByteZ, BuusFuryToolkit y disassembly de referencia.
- Lore, roadmap e instructivos.

## Subir el workspace completo

Después de descomprimir:

```sh
cd DBZ_Buus_Fury_Hack

git init
git branch -M main
git add .
git status
git commit -m "chore: complete GT Super ROM hacking workspace"
```

Comprueba que el estado incluye los archivos que deseas antes de hacer push:

```sh
git status
find rom_base patch_output new_assets -maxdepth 2 -type f -print
```

Conecta tu repositorio privado:

```sh
git remote add origin https://github.com/TU_USUARIO/DBZ_Buus_Fury_Hack.git
git push -u origin main
```

## Después de clonar en otra sesión

```sh
git clone https://github.com/TU_USUARIO/DBZ_Buus_Fury_Hack.git
cd DBZ_Buus_Fury_Hack
```

La ROM debe estar en:

```text
rom_base/DBZ_Buus_Fury_USA.gba
```

Checksum esperado:

```text
f1c4b07554d2a3b1ad2f325307051e775ce68087
```

## Cómo pedir continuar el trabajo

En una nueva sesión proporciona:

```text
Repositorio: https://github.com/TU_USUARIO/DBZ_Buus_Fury_Hack
Rama: main
Base SHA-1: f1c4b07554d2a3b1ad2f325307051e775ce68087
Fase actual: 4
Objetivo: continuar fase 5 con portraits y textos GT/Super
```

Si el repositorio es privado, la sesión necesitará que adjuntes el ZIP o que
uses un entorno con acceso al repositorio. No compartas credenciales ni tokens
en el chat.

## Compilar y reproducir

### Demo libgba

```sh
source /etc/profile.d/devkit-env.sh
export DEVKITPRO=/opt/devkitpro
export DEVKITARM=$DEVKITPRO/devkitARM
make
```

### DragonByteZ

```sh
cmake -S tools/DragonByteZ -B tools/DragonByteZ/build \
  -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF
cmake --build tools/DragonByteZ/build -j2
```

### Fases

```sh
python3 tools/create_gt_super_phase1.py
python3 tools/create_gt_super_phase3_roster.py
python3 tools/create_gt_super_phase4_forms.py
```

Cada script comprueba el SHA-1 de la ROM base antes de modificar una copia.
