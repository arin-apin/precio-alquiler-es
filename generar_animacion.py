"""
Bar Chart Race v4 - Precio del Alquiler en España
==================================================
Igual que v3 + barra de progreso a ancho completo en el borde inferior.

Uso:
    conda run -n foo python bar_chart_race_v4.py

Output:
    alquileres_race_v4.mp4
    precio-alquiler-es/alquileres_race_v4.mp4
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
from matplotlib.animation import FuncAnimation, FFMpegWriter
import os, shutil

# ── Fuente del sistema ────────────────────────────────────────────────────────
_available = {f.name for f in fm.fontManager.ttflist}
FONT      = next((f for f in ['Ubuntu', 'Noto Sans', 'DejaVu Sans'] if f in _available),
                 'sans-serif')
FONT_MONO = next((f for f in ['DejaVu Sans Mono', 'Courier New'] if f in _available),
                 'monospace')
plt.rcParams.update({
    'font.family':      'sans-serif',
    'font.sans-serif':  [FONT],
    'text.antialiased': True,
    'patch.antialiased': True,
})

# ── Colores ───────────────────────────────────────────────────────────────────
BG = '#FFFFFF'

CITY_COLORS = {
    'Valencia':  '#D4574E',
    'Donosti':   '#172863',
    'Madrid':    '#0038A8',
    'Barcelona': '#C80000',
    'Málaga':    '#007AB8',
    'Sevilla':   '#FFAB60',
}

MONTHS_ES = {
    1:'Enero', 2:'Febrero', 3:'Marzo', 4:'Abril',
    5:'Mayo', 6:'Junio', 7:'Julio', 8:'Agosto',
    9:'Septiembre', 10:'Octubre', 11:'Noviembre', 12:'Diciembre'
}

# ── Parámetros ────────────────────────────────────────────────────────────────
FPS             = 24
STEPS_PER_MONTH = 10
LERP_SPEED      = 0.18
BAR_H           = 0.62
DPI             = 150
ROUNDING        = 0.18

TREMOR_THRESHOLD = 0.25
TREMOR_MAX_AMP   = 0.07
TREMOR_FREQ      = 0.9

HIST_LINE_ALPHA  = 0.22
HIST_LINE_WIDTH  = 1.8

# ── Rutas ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH  = os.path.join(SCRIPT_DIR, '2025 alquileres - Todos.csv')
OUT_PATH   = os.path.join(SCRIPT_DIR, 'alquileres_race_v4.mp4')
REPO_PATH  = os.path.join(SCRIPT_DIR, 'precio-alquiler-es', 'alquileres_race_v4.mp4')


# ── Degradados precalculados ──────────────────────────────────────────────────
GRADIENT_W = 256

def _make_gradient_img(color: str) -> np.ndarray:
    rgb  = np.array(mcolors.to_rgb(color))
    dark = rgb * 0.15
    img  = np.zeros((1, GRADIENT_W, 4))
    for i in range(GRADIENT_W):
        t_raw = i / (GRADIENT_W - 1)
        t     = t_raw ** 0.55
        c     = dark * (1 - t) + rgb * t
        if 0.65 < t_raw < 0.88:
            boost = 1.0 + 0.18 * np.sin(np.pi * (t_raw - 0.65) / 0.23)
            c = np.clip(c * boost, 0, 1)
        img[0, i] = [c[0], c[1], c[2], 1.0]
    return img

def _make_shine_img(color: str) -> np.ndarray:
    rgb   = np.array(mcolors.to_rgb(color))
    light = np.clip(rgb + (1 - rgb) * 0.55, 0, 1)
    img   = np.zeros((32, 1, 4))
    for i in range(32):
        t = i / 31
        c = light * (1 - t) + rgb * t
        img[i, 0] = [c[0], c[1], c[2], 0.50 * (1 - t)]
    return img

GRAD_IMGS  = {city: _make_gradient_img(color) for city, color in CITY_COLORS.items()}
SHINE_IMGS = {city: _make_shine_img(color)    for city, color in CITY_COLORS.items()}
GRAD_IMGS['__default__']  = _make_gradient_img('#CCCCCC')
SHINE_IMGS['__default__'] = _make_shine_img('#CCCCCC')


# ── Helpers ───────────────────────────────────────────────────────────────────
def _update_fancy_box(patch, x0, y0, w, h):
    patch.set_bounds(x0, y0, w, h)


# ── Datos ─────────────────────────────────────────────────────────────────────
def load_data():
    df = pd.read_csv(DATA_PATH)

    def clean(x):
        s = str(x).strip()
        return np.nan if s in ('nan', 'n.d.', '') \
               else float(s.replace('€/m2', '').replace(',', '.').strip())

    for col in df.columns[1:]:
        df[col] = df[col].apply(clean)

    m = dict(enero='01', febrero='02', marzo='03', abril='04', mayo='05', junio='06',
             julio='07', agosto='08', septiembre='09', octubre='10',
             noviembre='11', diciembre='12')
    df['Fecha'] = pd.to_datetime(
        df['Mes'].apply(lambda s: f"{s.lower().split()[1]}-{m[s.lower().split()[0]]}-01"))
    df.set_index('Fecha', inplace=True)
    df.drop('Mes', axis=1, inplace=True)
    df.sort_index(inplace=True)
    df = df[df.notna().sum(axis=1) >= 2]
    df = df.interpolate(method='linear', limit_direction='both').ffill().bfill()
    return df


def compute_yoy(df):
    yoy = {}
    for date in df.index:
        prev = date - pd.DateOffset(years=1)
        yoy[date] = {}
        for city in df.columns:
            if prev in df.index:
                pv, cv = df.loc[prev, city], df.loc[date, city]
                yoy[date][city] = (cv - pv) / pv * 100 if pd.notna(pv) and pv > 0 else None
            else:
                yoy[date][city] = None
    return yoy


def compute_mom(df):
    mom  = {}
    dates = df.index.tolist()
    for i, date in enumerate(dates):
        mom[date] = {}
        for city in df.columns:
            mom[date][city] = float(df.iloc[i][city] - df.iloc[i-1][city]) if i > 0 else 0.0
    return mom


def build_frames(df):
    cities = list(df.columns)
    dates  = df.index.tolist()
    frames = []
    for i in range(len(dates) - 1):
        for step in range(STEPS_PER_MONTH):
            t    = step / STEPS_PER_MONTH
            vals = {c: float(df.iloc[i][c] + (df.iloc[i+1][c] - df.iloc[i][c]) * t)
                    for c in cities}
            frames.append((vals, dates[i] if t < 0.5 else dates[i+1]))
    frames.append(({c: float(df.iloc[-1][c]) for c in cities}, dates[-1]))
    return frames, cities


# ── Animación ─────────────────────────────────────────────────────────────────
def make_animation(frames, cities, df, hist_max, yoy_data, mom_data):
    n_cities    = len(cities)
    max_v       = max(v for vals, _ in frames for v in vals.values()) * 1.10
    dates_all   = df.index.tolist()
    n_months    = len(dates_all)
    date_to_idx = {date: i for i, date in enumerate(dates_all)}

    fig = plt.figure(figsize=(16, 9), facecolor=BG)

    # ── Axes trasero: líneas históricas ───────────────────────────────────────
    ax_bg = fig.add_axes([0.18, 0.12, 0.66, 0.78])
    ax_bg.set_facecolor('none')
    ax_bg.set_xlim(0, n_months - 1)
    ax_bg.set_ylim(0, max_v)
    ax_bg.set_xticks([])
    ax_bg.set_yticks([])
    for sp in ax_bg.spines.values():
        sp.set_visible(False)

    hist_lines = {}
    for city in cities:
        color = CITY_COLORS.get(city, '#888888')
        line, = ax_bg.plot([], [], color=color,
                           alpha=HIST_LINE_ALPHA, linewidth=HIST_LINE_WIDTH,
                           solid_capstyle='round', zorder=2)
        hist_lines[city] = line

    # ── Axes frontal: barras ──────────────────────────────────────────────────
    ax = fig.add_axes([0.18, 0.12, 0.66, 0.78])
    ax.set_zorder(ax_bg.get_zorder() + 1)
    ax.patch.set_visible(False)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.set_yticks([])
    ax.set_xticks([])
    ax.set_xlim(0, max_v)
    ax.set_ylim(-0.8, n_cities - 0.2)

    # ── Textos estáticos ───────────────────────────────────────────────────────
    fig.text(0.18, 0.965, 'Precio del Alquiler en España',
             color='#111111', fontsize=22, fontweight='bold', va='top', ha='left')
    fig.text(0.18, 0.930, '€/m²  ·  Fuente: Idealista',
             color='#888888', fontsize=12, va='top', ha='left')

    # ── Fecha ──────────────────────────────────────────────────────────────────
    vals0, date0 = frames[0]
    date_label = ax.text(
        0.985, 0.04,
        f"{MONTHS_ES[date0.month].upper()} {date0.year}",
        color='#0038A8', fontsize=36, fontweight='bold',
        ha='right', va='bottom', transform=ax.transAxes, zorder=10)

    # ── Estado inicial ─────────────────────────────────────────────────────────
    ranked0 = sorted(cities, key=lambda c: vals0[c])
    lerp_y  = {c: float(ranked0.index(c)) for c in cities}

    # ── Artistas de barras ─────────────────────────────────────────────────────
    bar_patches   = {}
    grad_imgs     = {}
    shine_imgs    = {}
    pulse_patches = {}
    name_txts     = {}
    val_txts      = {}
    mom_txts      = {}

    for city in ranked0:
        color = CITY_COLORS.get(city, '#CCCCCC')
        v     = vals0[city]
        y     = float(ranked0.index(city))
        hmax  = hist_max.get(city, v * 1.1)
        vmin  = max(v, 0.1)

        bp = mpatches.FancyBboxPatch(
            (0, y - BAR_H/2), vmin, BAR_H,
            boxstyle=f"round,pad=0,rounding_size={ROUNDING}",
            facecolor=color, edgecolor='none', zorder=3)
        ax.add_patch(bp)
        bar_patches[city] = bp

        gi = ax.imshow(
            GRAD_IMGS.get(city, GRAD_IMGS['__default__']),
            aspect='auto',
            extent=[0, vmin, y - BAR_H/2, y + BAR_H/2],
            zorder=4, interpolation='bilinear',
            clip_path=bp, clip_on=True)
        grad_imgs[city] = gi

        si = ax.imshow(
            SHINE_IMGS.get(city, SHINE_IMGS['__default__']),
            aspect='auto',
            extent=[0, vmin, y, y + BAR_H/2],
            zorder=5, interpolation='bilinear',
            clip_path=bp, clip_on=True)
        shine_imgs[city] = si

        pp = mpatches.FancyBboxPatch(
            (0, y - BAR_H/2), vmin, BAR_H,
            boxstyle=f"round,pad=0,rounding_size={ROUNDING}",
            facecolor='white', edgecolor='none', alpha=0.0, zorder=6)
        ax.add_patch(pp)
        pulse_patches[city] = pp

        name_txts[city] = ax.text(
            -max_v * 0.018, y, city,
            ha='right', va='center',
            color=color, fontsize=13, fontweight='bold', zorder=5)

        label_x = vmin + max_v * 0.013
        val_txts[city] = ax.text(
            label_x, y + 0.13, f'{v:.1f} €',
            ha='left', va='center',
            color='#222222', fontsize=12, fontweight='bold', zorder=5)

        mom_txts[city] = ax.text(
            label_x, y - 0.13, '',
            ha='left', va='center',
            color='#22aa44', fontsize=9, fontfamily=FONT_MONO, zorder=5)

    # ── Update ────────────────────────────────────────────────────────────────
    total = len(frames)

    def update(idx):
        if idx % 100 == 0:
            print(f"  frame {idx}/{total}  ({idx/total*100:.0f}%)", flush=True)

        vals, date = frames[idx]
        ranked     = sorted(cities, key=lambda c: vals[c])
        mom_frame  = mom_data.get(date, {})
        yoy_frame  = yoy_data.get(date, {})

        # Líneas históricas
        date_idx = date_to_idx.get(date, 0)
        xs = np.arange(date_idx + 1)
        for city in cities:
            hist_lines[city].set_data(xs, df[city].values[:date_idx + 1])

        for city in cities:
            target_rank = float(ranked.index(city))
            lerp_y[city] += (target_rank - lerp_y[city]) * LERP_SPEED

            mom_val = mom_frame.get(city, 0.0)
            if abs(mom_val) > TREMOR_THRESHOLD:
                amp    = min(abs(mom_val) / 3.0 * TREMOR_MAX_AMP, TREMOR_MAX_AMP)
                tremor = amp * np.sin(idx * TREMOR_FREQ)
            else:
                tremor = 0.0

            y    = lerp_y[city] + tremor
            v    = vals[city]
            vmin = max(v, 0.1)
            hmax = hist_max.get(city, vmin * 1.1)

            _update_fancy_box(bar_patches[city],   0, y - BAR_H/2, vmin, BAR_H)
            grad_imgs[city].set_extent([0, vmin, y - BAR_H/2, y + BAR_H/2])
            shine_imgs[city].set_extent([0, vmin, y, y + BAR_H/2])

            _update_fancy_box(pulse_patches[city], 0, y - BAR_H/2, vmin, BAR_H)
            if abs(mom_val) > TREMOR_THRESHOLD:
                pulse_amp = min(abs(mom_val) / 4.0, 1.0) * 0.30
                pulse_patches[city].set_alpha(pulse_amp * abs(np.sin(idx * 0.5)))
            else:
                pulse_patches[city].set_alpha(0.0)

            name_txts[city].set_y(y)

            label_x = vmin + max_v * 0.013
            val_txts[city].set_x(label_x)
            val_txts[city].set_y(y + 0.13)
            val_txts[city].set_text(f'{v:.1f} €')

            if mom_val != 0.0:
                sign = '▲' if mom_val >= 0 else '▼'
                mcol = '#22aa44' if mom_val >= 0 else '#cc3333'
                yoy_pct = yoy_frame.get(city)
                if yoy_pct is not None:
                    ysign = '+' if yoy_pct >= 0 else ''
                    mom_txts[city].set_text(
                        f'{sign} {abs(mom_val):.1f} €/mes · {ysign}{yoy_pct:.1f}% interanual')
                else:
                    mom_txts[city].set_text(f'{sign} {abs(mom_val):.1f} €/mes')
                mom_txts[city].set_color(mcol)
            else:
                mom_txts[city].set_text('')
            mom_txts[city].set_x(label_x)
            mom_txts[city].set_y(y - 0.13)

        date_label.set_text(f"{MONTHS_ES[date.month].upper()} {date.year}")

        return (list(hist_lines.values()) +
                list(bar_patches.values()) +
                list(grad_imgs.values()) +
                list(shine_imgs.values()) +
                list(pulse_patches.values()) +
                list(name_txts.values()) +
                list(val_txts.values()) +
                list(mom_txts.values()) +
                [date_label])

    anim = FuncAnimation(fig, update, frames=total,
                         interval=1000 / FPS, blit=True)
    return fig, anim


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print(f"Fuente: {FONT}  /  Mono: {FONT_MONO}")

    print("Cargando datos...")
    df = load_data()
    print(f"  {len(df)} meses  ({df.index[0].strftime('%m/%Y')} → {df.index[-1].strftime('%m/%Y')})")

    hist_max = {city: float(df[city].max()) for city in df.columns}

    print("Calculando métricas...")
    yoy = compute_yoy(df)
    mom = compute_mom(df)

    print("Construyendo frames...")
    frames, cities = build_frames(df)
    print(f"  {len(frames)} frames · {len(frames)/FPS:.0f}s a {FPS}fps")

    print("Preparando figura...")
    fig, anim = make_animation(frames, cities, df, hist_max, yoy, mom)

    print(f"Renderizando → {OUT_PATH}")
    writer = FFMpegWriter(
        fps=FPS,
        extra_args=['-vcodec', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p']
    )
    anim.save(OUT_PATH, writer=writer, dpi=DPI,
              savefig_kwargs={'facecolor': BG})
    plt.close(fig)

    os.makedirs(os.path.dirname(REPO_PATH), exist_ok=True)
    shutil.copy2(OUT_PATH, REPO_PATH)
    print(f"\n✅ Listo!")
    print(f"   {OUT_PATH}")
    print(f"   {REPO_PATH}")
