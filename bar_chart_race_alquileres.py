import pandas as pd
import bar_chart_race as bcr
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from datetime import datetime
import numpy as np
import locale
import matplotlib as mpl

# Configurar locale para español
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_TIME, 'es_ES')
    except:
        pass

# SOLUCIÓN: Configurar matplotlib ANTES de importar bar_chart_race
# y usar una figura pre-configurada
plt.style.use('dark_background')  # Esto es clave

# Configuración adicional para asegurar fondo negro
mpl.rcParams.update({
    'figure.facecolor': '#000000',
    'axes.facecolor': '#000000',
    'savefig.facecolor': '#000000',
    'axes.edgecolor': '#444444',
    'text.color': 'white',
    'axes.labelcolor': 'white',
    'xtick.color': 'white',
    'ytick.color': 'white',
    'grid.color': '#333333',
    'grid.alpha': 0.3
})

# Leer el CSV
df = pd.read_csv('2025 alquileres - Todos.csv')

def clean_price(price_str):
    if pd.isna(price_str) or price_str == 'n.d.':
        return np.nan
    return float(price_str.replace('€/m2', '').replace(',', '.').strip())

for col in df.columns[1:]:
    df[col] = df[col].apply(clean_price)

def parse_month(month_str):
    months = {
        'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
        'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
        'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
    }
    parts = month_str.split()
    if len(parts) == 2:
        month = months.get(parts[0], '01')
        year = parts[1]
        return f"{year}-{month}-01"
    return None

df['Fecha'] = df['Mes'].apply(parse_month)
df['Fecha'] = pd.to_datetime(df['Fecha'])
df = df.dropna(subset=df.columns[1:-1], how='all')
df.set_index('Fecha', inplace=True)
df = df.drop('Mes', axis=1)
df = df.sort_index()
df = df.interpolate(method='linear', limit_direction='both')

# Colores específicos proporcionados para cada ciudad
color_dict = {
    'Valencia': '#D4574E',   # RGB(212, 87, 78)
    'Donosti': '#172863',    # RGB(23, 40, 99)
    'Madrid': '#0038A8',     # RGB(0, 56, 168)
    'Barcelona': '#C80000',  # RGB(200, 0, 0)
    'Málaga': '#007AB8',     # RGB(0, 122, 184)
    'Sevilla': '#FFAB60'     # RGB(255, 171, 96)
}

city_colors = [color_dict.get(ciudad, '#CCCCCC') for ciudad in df.columns]
n_cities = len(df.columns)
cmap = mcolors.LinearSegmentedColormap.from_list("custom", city_colors, N=n_cities)

# Crear figura con fondo negro ANTES de bar_chart_race
fig = plt.figure(figsize=(12, 7))
fig.patch.set_facecolor('#000000')
ax = fig.add_subplot(111)
ax.set_facecolor('#000000')
plt.close()  # Importante: cerrar para que bar_chart_race la use

# Crear la animación
bcr.bar_chart_race(
    df=df,
    filename='alquileres_race.mp4',
    orientation='h',
    sort='desc',
    n_bars=6,
    fixed_order=False,
    steps_per_period=8,
    period_length=250,
    cmap=cmap,
    title='Evolución del Precio del Alquiler (€/m²)',
    bar_label_size=14,
    tick_label_size=14,
    shared_fontdict={'color': 'white', 'weight': 'bold', 'size': 13},
    period_fmt='%B %Y',
    period_label={'x': .98, 'y': .02, 'ha': 'right', 'va': 'bottom', 
                  'size': 22, 'weight': 'bold', 'color': '#FFD700'},
    period_summary_func=lambda v, r: {'x': .98, 'y': .15, 'ha': 'right', 
                                      's': f'Media: {v.mean():.1f} €/m²', 
                                      'size': 14, 'color': '#AAAAAA'},
    figsize=(12, 7),
    dpi=100,
    bar_kwargs={'alpha': 0.9},
    filter_column_colors=False,
    interpolate_period=True,
    writer='ffmpeg',
    fig=fig  # Pasar la figura pre-configurada
)

print("\n✅ Animación creada: alquileres_race.mp4")
print("🎨 Usando plt.style.use('dark_background') + figura pre-configurada")
print("📌 Colores optimizados para fondo oscuro")