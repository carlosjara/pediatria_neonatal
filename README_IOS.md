# Compilar y subir a iPhone

Guía rápida para recompilar la app BeeWare/Briefcase y ejecutarla en un iPhone
conectado.

## Prerrequisitos

- Xcode instalado y abierto al menos una vez.
- iPhone conectado por cable o visible por red desde Xcode.
- El iPhone debe confiar en el Mac.
- Entorno Conda del proyecto disponible:

```bash
source /opt/anaconda3/etc/profile.d/conda.sh
conda activate pediatria-neonatal
```

## Flujo por comando

Desde la raíz del proyecto:

```bash
cd /Users/carlos.jaramillo/Developer/pediatria_neonatal
source /opt/anaconda3/etc/profile.d/conda.sh
conda activate pediatria-neonatal
```

Validar antes de compilar:

```bash
pytest
```

Actualizar el proyecto iOS generado por Briefcase:

```bash
briefcase update iOS --update-resources --no-input
```

Usa `--update-resources` cuando cambien iconos o recursos visuales de app. El
icono de iOS se toma desde `resources/app-icon-*.png`, configurado en
`pyproject.toml` con `icon = "resources/app-icon"`.

Compilar:

```bash
briefcase build iOS
```

Ejecutar/subir al iPhone:

```bash
briefcase run iOS -u
```

Con Briefcase `0.4.4`, este comando puede listar solo simuladores aunque Xcode
sí vea el iPhone físico. En ese caso, usar el flujo por Xcode o compilar con
`xcodebuild`.

Para ver los dispositivos conectados:

```bash
xcrun xctrace list devices
xcrun devicectl list devices
```

Para compilar contra un iPhone físico desde terminal, reemplazar `UDID` por el
identificador mostrado por Xcode:

```bash
xcodebuild \
  -project "build/pediatria-neonatal/ios/xcode/Pediatría Neonatal.xcodeproj" \
  -scheme "Pediatría Neonatal" \
  -configuration Debug \
  -destination "id=UDID" \
  build
```

Si aparece `Signing requires a development team`, abrir el proyecto en Xcode y
seleccionar el equipo de desarrollo en `Signing & Capabilities`.

## Flujo por Xcode

Primero actualizar el proyecto generado:

```bash
cd /Users/carlos.jaramillo/Developer/pediatria_neonatal
source /opt/anaconda3/etc/profile.d/conda.sh
conda activate pediatria-neonatal
briefcase update iOS --update-resources --no-input
```

Abrir el proyecto:

```bash
open "build/pediatria-neonatal/ios/xcode/Pediatría Neonatal.xcodeproj"
```

En Xcode:

1. Seleccionar el scheme `Pediatría Neonatal`.
2. Seleccionar el iPhone físico como destino.
3. Revisar `Signing & Capabilities` si Xcode pide equipo de desarrollo.
4. Presionar `Run`.

Este es el camino recomendado para subir al iPhone físico cuando el equipo de
firma todavía no está configurado por terminal.

## Problemas comunes

- Si no se ven cambios recientes, ejecutar `briefcase update iOS --no-input`
  antes de abrir Xcode.
- Si el iPhone no aparece, revisar que esté desbloqueado y confiando en el Mac.
- Si cambia un recurso como un icono PNG, cerrar la app en el iPhone y ejecutar
  de nuevo `briefcase run iOS -u`.
- Si Xcode muestra errores de firma, seleccionar manualmente el equipo de
  desarrollo en `Signing & Capabilities`.
