"""
Motor PDF Premium v3 — Dossier Inmobiliario
Híbrido: diseño del HTML template del usuario + gráficos del PDF anterior.
- Radar SVG puro (sin dependencias externas)
- Barras de puntuación SVG con relleno dorado
- Google Fonts (Cormorant Garamond + Inter)
- Paleta pearl/champagne/ink original
- Doble marco dorado + gradientes radiales
- Elemento decorativo orbital
"""
import base64, math, os
from datetime import datetime
from io import BytesIO

try:
    from PIL import Image as PILImage
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def _s(v, d=''):
    return str(v).strip() if v else d

def _eur(v):
    try:
        n = float(v)
        if n >= 1_000_000: return f"{n/1_000_000:.2f}M &euro;"
        return f"{int(n):,}&nbsp;&euro;".replace(",", ".")
    except: return 'N/D'

def _pct(v, d=1):
    try: return f"{float(v):.{d}f}%"
    except: return 'N/D'

def _num(v):
    try: return f"{float(v):.1f}"
    except: return str(v)

def _photo_b64(path, max_w=1400, q=82):
    try:
        if HAS_PIL:
            img = PILImage.open(path).convert('RGB')
            if img.width > max_w:
                img = img.resize((max_w, int(img.height * max_w / img.width)), PILImage.LANCZOS)
            buf = BytesIO()
            img.save(buf, 'JPEG', quality=q, optimize=True)
            return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
        with open(path, 'rb') as f:
            b = base64.b64encode(f.read()).decode()
        ext = os.path.splitext(path)[1].lower().lstrip('.')
        mime = 'jpeg' if ext in ('jpg', 'jpeg') else ext
        return f"data:image/{mime};base64,{b}"
    except:
        return ''


# ─── SVG CHARTS ───────────────────────────────────────────────────────────────

def _svg_radar(labels, values, size=160):
    """Gráfico radar/araña en SVG puro — compatible con WeasyPrint."""
    n = len(labels)
    if n < 3:
        return ''
    cx = cy = size / 2
    r = size / 2 - 28

    parts = []

    for level in [0.25, 0.5, 0.75, 1.0]:
        pts = []
        for i in range(n):
            ang = -math.pi / 2 + 2 * math.pi * i / n
            pts.append(f"{cx + r*level*math.cos(ang):.1f},{cy + r*level*math.sin(ang):.1f}")
        fill = 'rgba(215,181,109,0.07)' if level == 1.0 else 'none'
        parts.append(f'<polygon points="{" ".join(pts)}" fill="{fill}" stroke="rgba(215,181,109,0.30)" stroke-width="0.6"/>')

    for i in range(n):
        ang = -math.pi / 2 + 2 * math.pi * i / n
        x2 = cx + r * math.cos(ang)
        y2 = cy + r * math.sin(ang)
        parts.append(f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="rgba(36,52,71,0.18)" stroke-width="0.5"/>')

    data_pts = []
    for i in
