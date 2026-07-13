# Iconos Médicos

Coloca aquí los iconos PNG descargados de las fuentes recomendadas.

## Fuentes Recomendadas

1. **Healthicons** (MIT License - libre)
   - URL: https://healthicons.org
   - Ideal para: iconos médicos específicos
   
2. **Flaticon** (Gratis con atribución)
   - URL: https://www.flaticon.com/search?word=pediatric
   - Buscar: "pediatric", "baby", "medical", "growth"

3. **Lucide** (ISC License - libre)
   - URL: https://lucide.dev/icons
   - Buscar: "baby", "heart", "activity", "scale"

## Iconos Necesarios

Descarga estos iconos en formato PNG (tamaño recomendado: 64x64 o 128x128):

| Archivo | Uso | Buscar en |
|---------|-----|-----------|
| `baby.png` | Paciente neonatal | Healthicons: "baby" |
| `scale.png` | Peso | Healthicons: "weight" |
| `ruler.png` | Talla/Longitud | Healthicons: "height" |
| `head.png` | Perímetro cefálico | Healthicons: "head" |
| `chart.png` | Resultados/Gráficas | Healthicons: "chart" |
| `calculator.png` | Cálculos | Lucide: "calculator" |
| `calendar.png` | Fecha/Edad | Lucide: "calendar" |
| `alert.png` | Alertas | Lucide: "alert-triangle" |
| `check.png` | Normal/OK | Lucide: "check-circle" |
| `warning.png` | Observación | Lucide: "alert-circle" |
| `home.png` | Inicio | Lucide: "home" |
| `settings.png` | Ajustes | Lucide: "settings" |
| `history.png` | Historial | Lucide: "clock" |

## Cómo Descargar de Healthicons

1. Ve a https://healthicons.org
2. Busca el icono (ej: "baby")
3. Click en el icono
4. Selecciona "Filled" o "Outline"
5. Click en "Download PNG"
6. Renombra el archivo según la tabla anterior
7. Colócalo en esta carpeta

## Uso en la Aplicación

```python
from pathlib import Path

ICONS_DIR = Path(__file__).parent / "icons"

def get_icon(name: str) -> Path:
    return ICONS_DIR / f"{name}.png"
```
