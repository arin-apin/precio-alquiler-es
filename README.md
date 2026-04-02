# precio-alquiler-es

Evolución del precio del alquiler de vivienda en España (€/m²), visualizada como un bar chart race animado.

## 📊 Datos

- **Fuente**: [Idealista - Informes precio vivienda](https://www.idealista.com/sala-de-prensa/informes-precio-vivienda/alquiler/)
- **Período**: 2008 - Marzo 2026
- **Ciudades**: Valencia, Donosti, Madrid, Barcelona, Málaga, Sevilla
- **Actualización**: Datos actualizados a marzo 2026

## 🎬 Visualización

![Evolución del precio del alquiler](alquileres_race.gif)

## ✨ Características

- **Barras animadas con degradado** — cada ciudad tiene su color propio con efecto de profundidad y reflejo superior
- **Reordenación fluida** — las barras cambian de posición con interpolación suave (LERP) en lugar de saltos bruscos
- **Líneas históricas de fondo** — se dibuja progresivamente el histórico de precios de cada ciudad, visible a través de las barras
- **Efecto tremor** — las barras vibran ligeramente cuando el precio sube o baja con fuerza ese mes
- **Variación mensual e interanual** — cada barra muestra en tiempo real cuánto ha subido o bajado respecto al mes anterior y al año anterior
- **Etiqueta de fecha** — mes y año actuales destacados en azul en la esquina inferior derecha

## 🛠️ Uso

```bash
# Dependencias
pip install pandas numpy matplotlib

# Ejecutar
python generar_animacion.py
```

Requiere `ffmpeg` instalado en el sistema. La animación se guarda como `alquileres_race_v4.mp4`.

## 📁 Archivos

- `generar_animacion.py` — script principal
- `alquileres_race_v4.mp4` — animación completa en vídeo
- `alquileres_race.gif` — muestra animada (fragmento central)
