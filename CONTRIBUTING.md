# Contribuir al hack

## Regla principal

Nunca sobrescribas la ROM base. Cada cambio debe partir de:

```text
rom_base/DBZ_Buus_Fury_USA.gba
```

El SHA-1 esperado es:

```text
f1c4b07554d2a3b1ad2f325307051e775ce68087
```

## Antes de abrir un pull request

- Ejecuta el script de la fase correspondiente.
- Comprueba que el resultado arranca en mGBA.
- Añade o actualiza el manifiesto de offsets.
- Documenta el tamaño de cada bloque insertado.
- Indica si el cambio es visual, texto, gameplay, mapa, NPC o evento.
- No incluyas ROMs, saves ni parches generados.
- No incluyas assets de terceros sin permiso.

## Convención de commits

```text
feat: nueva mecánica o contenido
fix: corrección de un bug
assets: conversión o paleta
rom: cambio de offsets o punteros
docs: documentación/lore/roadmap
test: prueba o validación mGBA
chore: herramientas y configuración
```

## Issues recomendados

Cada issue debe indicar:

- Fase.
- Personaje/mapa/objeto afectado.
- ROM base SHA-1.
- Offset o script involucrado.
- Resultado esperado.
- Resultado observado.
- Captura de mGBA si es un problema visual.
