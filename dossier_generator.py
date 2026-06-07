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

    # Niveles de la cuadrícula
    for level in [0.25, 0.5, 0.75, 1.0]:
        pts = []
        for i in range(n):
            ang = -math.pi / 2 + 2 * math.pi * i / n
            pts.append(f"{cx + r*level*math.cos(ang):.1f},{cy + r*level*math.sin(ang):.1f}")
        fill = 'rgba(215,181,109,0.07)' if level == 1.0 else 'none'
        parts.append(f'<polygon points="{" ".join(pts)}" fill="{fill}" stroke="rgba(215,181,109,0.30)" stroke-width="0.6"/>')

    # Ejes radiales
    for i in range(n):
        ang = -math.pi / 2 + 2 * math.pi * i / n
        x2 = cx + r * math.cos(ang)
        y2 = cy + r * math.sin(ang)
        parts.append(f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="rgba(36,52,71,0.18)" stroke-width="0.5"/>')

    # Polígono de datos
    data_pts = []
    for i in range(n):
        ang = -math.pi / 2 + 2 * math.pi * i / n
        v = min(max(float(values[i]) / 10.0, 0), 1)
        data_pts.append(f"{cx + r*v*math.cos(ang):.1f},{cy + r*v*math.sin(ang):.1f}")
    parts.append(f'<polygon points="{" ".join(data_pts)}" fill="rgba(215,181,109,0.25)" stroke="#d7b56d" stroke-width="1.8" stroke-linejoin="round"/>')

    # Puntos de datos
    for i in range(n):
        ang = -math.pi / 2 + 2 * math.pi * i / n
        v = min(max(float(values[i]) / 10.0, 0), 1)
        px = cx + r * v * math.cos(ang)
        py = cy + r * v * math.sin(ang)
        parts.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3.5" fill="#d7b56d" stroke="white" stroke-width="1.2"/>')

    # Etiquetas
    for i, label in enumerate(labels):
        ang = -math.pi / 2 + 2 * math.pi * i / n
        lx = cx + (r + 16) * math.cos(ang)
        ly = cy + (r + 16) * math.sin(ang)
        anchor = 'middle'
        if lx < cx - 8:
            anchor = 'end'
        elif lx > cx + 8:
            anchor = 'start'
        parts.append(
            f'<text x="{lx:.1f}" y="{ly + 3:.1f}" '
            f'text-anchor="{anchor}" '
            f'font-family="Inter,Arial,sans-serif" font-size="6.5" '
            f'fill="#9b7638" font-weight="700" letter-spacing="0.8">'
            f'{label.upper()}</text>'
        )

    return (
        f'<svg viewBox="0 0 {size} {size}" width="{size}" height="{size}" '
        f'xmlns="http://www.w3.org/2000/svg">{"".join(parts)}</svg>'
    )


def _svg_bar(label, value, max_val=10, width=165, color='#d7b56d'):
    """Barra horizontal SVG con relleno dorado — estilo del PDF anterior."""
    h = 22
    lbl_w = 52
    val_w = 22
    bar_w = width - lbl_w - val_w - 4
    fill_w = bar_w * min(float(value) / max_val, 1)
    pct_int = int(fill_w)
    return (
        f'<svg viewBox="0 0 {width} {h}" width="{width}" height="{h}" '
        f'xmlns="http://www.w3.org/2000/svg">'
        f'<text x="0" y="14" font-family="Inter,Arial,sans-serif" font-size="6.5" '
        f'fill="#9b7638" font-weight="800" letter-spacing="0.8">{label.upper()}</text>'
        f'<rect x="{lbl_w}" y="7" width="{bar_w}" height="7" rx="3.5" fill="rgba(36,52,71,0.10)"/>'
        f'<rect x="{lbl_w}" y="7" width="{fill_w:.1f}" height="7" rx="3.5" fill="{color}"/>'
        f'<text x="{width}" y="14" font-family="Inter,Arial,sans-serif" font-size="7.5" '
        f'fill="#223246" font-weight="700" text-anchor="end">{_num(value)}</text>'
        f'</svg>'
    )


def _svg_donut(pct, label, size=80, color='#d7b56d'):
    """Mini donut chart SVG para métricas de inversión."""
    cx = cy = size / 2
    r = size / 2 - 10
    circ = 2 * math.pi * r
    dash = circ * min(float(pct) / 100.0, 1)
    gap = circ - dash
    return (
        f'<svg viewBox="0 0 {size} {size}" width="{size}" height="{size}" '
        f'xmlns="http://www.w3.org/2000/svg">'
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="rgba(36,52,71,0.12)" stroke-width="6"/>'
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" stroke-width="6" '
        f'stroke-dasharray="{dash:.2f} {gap:.2f}" '
        f'stroke-dashoffset="{circ/4:.2f}" stroke-linecap="round"/>'
        f'<text x="{cx}" y="{cy+3}" text-anchor="middle" dominant-baseline="middle" '
        f'font-family="Inter,Arial,sans-serif" font-size="11" font-weight="700" fill="#223246">'
        f'{label}</text>'
        f'</svg>'
    )


# ─── UNSPLASH ─────────────────────────────────────────────────────────────────

_U = 'https://images.unsplash.com/photo-'
IMGS = {
    'city':       _U+'1477959858617-67f85cf4f1df?fm=jpg&q=80&w=700',
    'building':   _U+'1486406146926-c627a92ad1ab?fm=jpg&q=80&w=700',
    'skyline':    _U+'1518005020951-eccb494ad742?fm=jpg&q=80&w=700',
    'park':       _U+'1441974231531-c6227db76b6e?fm=jpg&q=80&w=700',
    'metro':      _U+'1474487548417-781cb71495f3?fm=jpg&q=80&w=700',
    'restaurant': _U+'1414235077428-338989a2e8c0?fm=jpg&q=80&w=700',
    'shopping':   _U+'1555529669-e69e7aa0ba9a?fm=jpg&q=80&w=700',
    'school':     _U+'1580582932707-520aed937b7b?fm=jpg&q=80&w=700',
    'hospital':   _U+'1586773860418-d37222d8fce3?fm=jpg&q=80&w=700',
    'gym':        _U+'1534438327276-14e5300c3a48?fm=jpg&q=80&w=700',
    'beach':      _U+'1507525428034-b723cf961d3e?fm=jpg&q=80&w=700',
    'street':     _U+'1480714378408-67cf0d13bc1b?fm=jpg&q=80&w=700',
    'plaza':      _U+'1558618666-fcd25c85cd64?fm=jpg&q=80&w=700',
    'garden':     _U+'1416879595882-3373a0480b5b?fm=jpg&q=80&w=700',
    'interior1':  _U+'1615529182904-14819c35db37?fm=jpg&q=80&w=700',
    'interior2':  _U+'1586023492125-27b2c045efd7?fm=jpg&q=80&w=700',
    'pool':       _U+'1519046904884-53d885cc3e68?fm=jpg&q=80&w=700',
    'cover1':     _U+'1449824913935-59a10b8d2000?fm=jpg&q=80&w=1200',
    'cover2':     _U+'1486406146926-c627a92ad1ab?fm=jpg&q=80&w=1200',
    'terrace':    _U+'1555041469-68ad9154f720?fm=jpg&q=80&w=700',
    'market':     _U+'1481437156560-3205f6a55735?fm=jpg&q=80&w=700',
    'dining':     _U+'1517248135467-4c7edcad34c4?fm=jpg&q=80&w=700',
}

def _zone_imgs(data, lang):
    srv = (data.get('servicios_cercanos') or '').lower()
    es = lang == 'es'
    pool = []
    checks = [
        (['metro','bus','tren','cercanias','tranvia','transporte'], 'metro', 'Transporte Publico', 'Public Transport'),
        (['parque','jardin','verde','nature'], 'park', 'Parques y Jardines', 'Parks & Gardens'),
        (['restaurante','bar','gastro','cafeteria'], 'restaurant', 'Gastronomia', 'Gastronomy'),
        (['colegio','escuela','universidad','educacion'], 'school', 'Centros Educativos', 'Schools'),
        (['hospital','clinica','medico','salud','farmacia'], 'hospital', 'Servicios Sanitarios', 'Healthcare'),
        (['comercio','supermercado','tienda','shopping'], 'shopping', 'Zona Comercial', 'Shopping'),
        (['playa','mar','costa'], 'beach', 'Playa', 'Beach'),
        (['gimnasio','gym','deporte'], 'gym', 'Deportes', 'Sports'),
    ]
    for keywords, key, lbl_es, lbl_en in checks:
        if any(k in srv for k in keywords):
            pool.append((IMGS[key], lbl_es if es else lbl_en))
    defaults = [
        ('city', 'Entorno Urbano', 'Urban Environment'),
        ('plaza', 'Plaza Principal', 'Main Square'),
        ('street', 'Vias Principales', 'Main Streets'),
        ('garden', 'Zonas Verdes', 'Green Spaces'),
        ('market', 'Vida Comercial', 'Commercial Life'),
        ('skyline', 'Panoramica', 'Skyline'),
    ]
    for key, lbl_es, lbl_en in defaults:
        if len(pool) >= 6:
            break
        entry = (IMGS[key], lbl_es if es else lbl_en)
        if entry not in pool:
            pool.append(entry)
    return pool[:6]

def _service_imgs(lang):
    es = lang == 'es'
    return [
        (IMGS['metro'],      'Metro y Transporte' if es else 'Metro & Transport'),
        (IMGS['school'],     'Colegios'           if es else 'Schools'),
        (IMGS['hospital'],   'Salud'              if es else 'Healthcare'),
        (IMGS['restaurant'], 'Restauracion'       if es else 'Dining'),
        (IMGS['shopping'],   'Comercios'          if es else 'Shopping'),
        (IMGS['park'],       'Parques'            if es else 'Parks'),
    ]


# ─── CSS ──────────────────────────────────────────────────────────────────────

def _css():
    return """
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700;800&family=Inter:wght@300;400;500;600;700;800;900&display=swap');
@page { size: A4; margin: 0; }
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
    --ink:       #223246;
    --ink-soft:  #405166;
    --slate:     #52657a;
    --pearl:     #fbf7ef;
    --ivory:     #fffaf2;
    --mist:      #edf5f8;
    --sky:       #dceef6;
    --champagne: #d7b56d;
    --champ-soft:#f1dfad;
    --bronze:    #9b7638;
    --line:      rgba(36,52,71,0.14);
    --line-gold: rgba(215,181,109,0.46);
}

body {
    font-family: 'Inter', Arial, sans-serif;
    background: var(--pearl);
    color: var(--ink);
    width: 210mm;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
}

/* ── PAGE SHELL ── */
.page {
    position: relative;
    width: 210mm;
    min-height: 297mm;
    overflow: hidden;
    page-break-after: always;
    background:
        radial-gradient(circle at 88% 6%, rgba(215,181,109,0.18), transparent 28%),
        radial-gradient(circle at 6% 90%, rgba(183,217,232,0.28), transparent 32%),
        linear-gradient(135deg, var(--ivory) 0%, var(--pearl) 44%, var(--mist) 100%);
    isolation: isolate;
}
.page:last-child { page-break-after: auto; }

/* double gold border — taken from user's template */
.page::before {
    content: '';
    position: absolute;
    inset: 9mm;
    border: 1px solid rgba(215,181,109,0.34);
    pointer-events: none;
    z-index: 8;
}
.page::after {
    content: '';
    position: absolute;
    inset: 12mm;
    border: 1px solid rgba(36,52,71,0.07);
    pointer-events: none;
    z-index: 8;
}
.no-frame::before, .no-frame::after { display: none; }

/* ── GRID OVERLAY ── */
.decor-grid {
    position: absolute;
    inset: 0;
    z-index: 1;
    pointer-events: none;
    opacity: 0.15;
    background:
        linear-gradient(90deg, rgba(36,52,71,0.10) 1px, transparent 1px),
        linear-gradient(180deg, rgba(36,52,71,0.08) 1px, transparent 1px);
    background-size: 18mm 18mm;
}

/* ── ORBITAL DECORATION — from user's template ── */
.decor-orbit {
    position: absolute;
    z-index: 2;
    right: -22mm;
    top: 20mm;
    width: 112mm;
    height: 112mm;
    border-radius: 50%;
    border: 1px solid rgba(215,181,109,0.22);
    pointer-events: none;
}
.decor-orbit::after {
    content: '';
    position: absolute;
    inset: 18mm;
    border-radius: 50%;
    border: 1px solid rgba(36,52,71,0.08);
}

/* ── INNER ── */
.inner {
    position: relative;
    z-index: 3;
    padding: 17mm 18mm 18mm;
    min-height: 297mm;
}

/* ── TYPOGRAPHY — hybrid: Cormorant for headings, Inter for body ── */
h1 {
    font-family: 'Cormorant Garamond', Georgia, serif;
    font-size: 38pt;
    line-height: 0.92;
    letter-spacing: -0.04em;
    font-weight: 700;
    color: var(--ink);
}
h2 {
    font-family: 'Cormorant Garamond', Georgia, serif;
    font-size: 24pt;
    line-height: 1.06;
    letter-spacing: -0.035em;
    font-weight: 700;
    color: var(--ink);
    max-width: 150mm;
}
h3 {
    font-family: 'Cormorant Garamond', Georgia, serif;
    font-size: 15pt;
    line-height: 1.15;
    letter-spacing: -0.02em;
    font-weight: 700;
    color: inherit;
}
h4 {
    font-family: 'Inter', Arial, sans-serif;
    font-size: 6.5pt;
    letter-spacing: 0.20em;
    text-transform: uppercase;
    font-weight: 800;
    color: var(--bronze);
    margin-bottom: 2mm;
}
.lead {
    font-family: 'Inter', Arial, sans-serif;
    font-size: 10pt;
    line-height: 1.65;
    letter-spacing: -0.01em;
    color: var(--ink-soft);
    margin-bottom: 6mm;
    max-width: 165mm;
    font-weight: 400;
}
.text {
    font-family: 'Inter', Arial, sans-serif;
    font-size: 8pt;
    line-height: 1.58;
    color: var(--slate);
    margin-top: 2mm;
    font-weight: 400;
}
.eyebrow {
    font-family: 'Inter', Arial, sans-serif;
    font-size: 7pt;
    letter-spacing: 0.26em;
    text-transform: uppercase;
    font-weight: 900;
    color: var(--bronze);
    margin-bottom: 3mm;
}
.micro {
    font-family: 'Inter', Arial, sans-serif;
    font-size: 5.5pt;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    font-weight: 700;
    color: rgba(36,52,71,0.45);
}

/* ── DECORATIVES ── */
.gold-line {
    width: 22mm;
    height: 1.2mm;
    border-radius: 99px;
    background: linear-gradient(90deg, var(--champagne), var(--champ-soft), var(--bronze));
    margin-bottom: 4.5mm;
}
.divider {
    width: 100%;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(215,181,109,0.55), rgba(36,52,71,0.09), transparent);
    margin: 5.5mm 0;
}

/* ── SECTION HEAD ── */
.section-head {
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 10mm;
    align-items: start;
    padding-top: 4.5mm;
    border-top: 1px solid var(--line-gold);
    margin-bottom: 8mm;
}
.section-num {
    font-family: 'Inter', Arial, sans-serif;
    font-size: 6.5pt;
    letter-spacing: 0.20em;
    text-transform: uppercase;
    font-weight: 900;
    color: rgba(36,52,71,0.35);
    padding: 2.5mm 3mm;
    border: 1px solid rgba(215,181,109,0.38);
    background: rgba(255,255,255,0.60);
    white-space: nowrap;
    text-align: right;
}

/* ── FOOTER ── */
.footer {
    position: absolute;
    left: 18mm;
    right: 18mm;
    bottom: 6mm;
    display: flex;
    justify-content: space-between;
    font-family: 'Inter', Arial, sans-serif;
    font-size: 5.5pt;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    font-weight: 700;
    color: rgba(36,52,71,0.40);
    padding-top: 2.5mm;
    border-top: 1px solid rgba(215,181,109,0.26);
}

/* ── GRIDS ── */
.g2 { display: grid; grid-template-columns: 1fr 1fr; gap: 5mm; }
.g3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 4mm; }
.g4 { display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 3.5mm; }

/* ── CARDS ── */
.card {
    padding: 5mm;
    border: 1px solid rgba(36,52,71,0.11);
    background: linear-gradient(135deg, rgba(255,255,255,0.90), rgba(251,247,239,0.72));
    border-left: 1.2mm solid var(--champagne);
}
.card.stone {
    background: linear-gradient(135deg, rgba(239,231,218,0.96), rgba(255,250,242,0.80));
    border-color: rgba(155,118,56,0.18);
}
.card.sky {
    background: linear-gradient(135deg, rgba(237,245,248,0.96), rgba(220,238,246,0.82));
    border-color: rgba(85,132,156,0.18);
}
.card.dark {
    background: linear-gradient(135deg, #2c3e52, #384d65);
    border: none;
    border-left: 1.2mm solid var(--champ-soft);
    color: #fff;
}
.card.dark .text { color: rgba(255,255,255,0.78); }
.card.dark h4    { color: var(--champ-soft); }
.card.dark h3    { color: #fff; }
.card.gold {
    background: linear-gradient(135deg, #c9a44a, #a87e32);
    border: none;
    border-left: 1.2mm solid rgba(255,255,255,0.45);
    color: #fff;
}
.card.gold .text { color: rgba(255,255,255,0.84); }
.card.gold h4    { color: #fff3cc; }

/* ── KPIs ── */
.kpi-row { display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 4mm; margin: 5mm 0; }
.kpi {
    padding: 5mm 4mm;
    background: rgba(255,255,255,0.90);
    border: 1px solid rgba(36,52,71,0.11);
}
.kpi.dark {
    background: linear-gradient(135deg, #2c3e52, #384d65);
    border: none;
}
.kpi .num {
    font-family: 'Cormorant Garamond', Georgia, serif;
    font-size: 20pt;
    line-height: 1;
    letter-spacing: -0.04em;
    font-weight: 700;
    color: var(--ink);
}
.kpi.dark .num { color: var(--champ-soft); }
.kpi .lbl {
    margin-top: 3mm;
    font-family: 'Inter', Arial, sans-serif;
    font-size: 5.8pt;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    font-weight: 700;
    color: rgba(36,52,71,0.60);
}
.kpi.dark .lbl { color: rgba(255,255,255,0.75); }

/* ── NOTE / CALLOUT ── */
.note {
    padding: 4.5mm 5mm;
    background: linear-gradient(135deg, rgba(255,255,255,0.90), rgba(241,223,173,0.16));
    border-left: 1.6mm solid var(--champagne);
    font-family: 'Inter', Arial, sans-serif;
    font-size: 8.5pt;
    line-height: 1.56;
    color: var(--ink);
    margin: 5mm 0;
}

/* ── TABLE ── */
.dtable {
    width: 100%;
    border-collapse: collapse;
    background: rgba(255,255,255,0.86);
    border: 1px solid rgba(36,52,71,0.11);
}
.dtable th {
    text-align: left;
    padding: 3mm 4mm;
    font-family: 'Inter', Arial, sans-serif;
    font-size: 5.8pt;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    font-weight: 800;
    color: var(--bronze);
    background: linear-gradient(90deg, rgba(241,223,173,0.38), rgba(237,245,248,0.62));
    border-bottom: 1px solid rgba(36,52,71,0.10);
}
.dtable td {
    padding: 2.8mm 4mm;
    font-family: 'Inter', Arial, sans-serif;
    font-size: 8pt;
    line-height: 1.45;
    color: var(--ink-soft);
    border-top: 1px solid rgba(36,52,71,0.06);
    vertical-align: top;
}
.dtable td:first-child {
    width: 36%;
    font-weight: 700;
    color: var(--ink);
}

/* ── IMAGES ── */
.img-box {
    overflow: hidden;
    border: 1px solid rgba(36,52,71,0.10);
}
.img-box img { display: block; width: 100%; object-fit: cover; }
.img-cap {
    padding: 2mm 3mm;
    background: rgba(255,255,255,0.93);
    font-family: 'Inter', Arial, sans-serif;
    font-size: 5.5pt;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    font-weight: 700;
    color: var(--ink);
    border-top: 1px solid rgba(215,181,109,0.26);
}

/* ── VISUAL GALLERY ── */
.vgallery { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 3.5mm; margin: 5mm 0; }
.vitem { border: 1px solid rgba(36,52,71,0.11); overflow: hidden; }
.vitem img { display: block; width: 100%; height: 32mm; object-fit: cover; }
.vcap {
    padding: 2mm 3mm;
    background: rgba(255,255,255,0.93);
    font-family: 'Inter', Arial, sans-serif;
    font-size: 5.5pt;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    font-weight: 700;
    color: var(--ink);
}

/* ── SCORE BAR WRAPPER ── */
.bars-block { display: flex; flex-direction: column; gap: 2.5mm; }
.bar-row { display: flex; align-items: center; gap: 3mm; }

/* ── ADVANTAGE ── */
.adv {
    display: grid;
    grid-template-columns: 9mm 1fr;
    gap: 3.5mm;
    padding: 4mm;
    background: rgba(255,255,255,0.88);
    border: 1px solid rgba(36,52,71,0.11);
    align-items: start;
}
.adv-n {
    width: 8mm;
    height: 8mm;
    border-radius: 50%;
    background: linear-gradient(135deg, var(--champagne), var(--bronze));
    color: #fff;
    font-family: 'Inter', Arial, sans-serif;
    font-size: 6pt;
    font-weight: 900;
    text-align: center;
    line-height: 8mm;
    flex-shrink: 0;
}

/* ── TIMELINE ── */
.timeline { display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 4mm; margin: 5mm 0; }
.step {
    padding: 4mm;
    background: rgba(255,255,255,0.88);
    border: 1px solid rgba(36,52,71,0.11);
}
.step-n {
    font-family: 'Cormorant Garamond', Georgia, serif;
    font-size: 18pt;
    line-height: 1;
    color: rgba(215,181,109,0.65);
    font-weight: 700;
    margin-bottom: 3mm;
}

/* ── PHOTO STRIP ── */
.photo-strip { display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 4mm; margin: 5mm 0; }
.photo-stack { display: grid; gap: 4mm; grid-template-rows: 1fr 1fr; }

/* ── COVER ── */
.cover {
    background: #0a1624;
    color: #fff;
}
.cover-photo {
    position: absolute;
    inset: 0;
    z-index: 1;
}
.cover-photo img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    opacity: 0.40;
}
.cover-overlay {
    position: absolute;
    inset: 0;
    z-index: 2;
    background:
        linear-gradient(100deg, rgba(6,13,24,0.90) 0%, rgba(12,24,40,0.55) 55%, rgba(12,24,40,0.16) 100%),
        linear-gradient(180deg, rgba(6,13,24,0.08) 0%, rgba(6,13,24,0.65) 100%);
}
.cover-inner {
    position: relative;
    z-index: 5;
    padding: 18mm 20mm 16mm;
    min-height: 297mm;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}
.topbar {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    font-family: 'Inter', Arial, sans-serif;
    font-size: 5.8pt;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: rgba(255,255,255,0.68);
    font-weight: 700;
}
.brand { display: flex; align-items: center; gap: 3mm; }
.brand-mark {
    width: 10mm;
    height: 10mm;
    border: 1px solid rgba(215,181,109,0.70);
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--champ-soft);
    background: rgba(255,255,255,0.07);
    font-family: 'Cormorant Garamond', Georgia, serif;
    font-size: 9pt;
    font-weight: 700;
}
.cover-box {
    width: 148mm;
    padding: 7mm 8mm;
    border: 1px solid rgba(215,181,109,0.36);
    background: rgba(8,18,30,0.52);
}
.cover-kicker {
    display: inline-block;
    padding: 2mm 4mm;
    border: 1px solid rgba(215,181,109,0.52);
    background: rgba(255,255,255,0.07);
    font-family: 'Inter', Arial, sans-serif;
    font-size: 5.8pt;
    letter-spacing: 0.24em;
    text-transform: uppercase;
    font-weight: 800;
    color: var(--champ-soft);
    margin-bottom: 6mm;
}
.cover h1 {
    color: #fff;
    font-size: 40pt;
    line-height: 0.92;
}
.cover-loc {
    display: block;
    color: var(--champ-soft);
    font-style: italic;
}
.cover-copy {
    margin-top: 7mm;
    font-family: 'Inter', Arial, sans-serif;
    font-size: 10.5pt;
    line-height: 1.52;
    color: rgba(255,255,255,0.84);
    max-width: 118mm;
    font-weight: 400;
}
.cover-bottom {
    display: grid;
    grid-template-columns: 76mm 1fr;
    gap: 7mm;
    align-items: end;
}
.price-panel {
    padding: 5.5mm 6mm;
    border: 1px solid rgba(215,181,109,0.60);
    background: rgba(255,255,255,0.93);
}
.price-lbl {
    font-family: 'Inter', Arial, sans-serif;
    font-size: 5.8pt;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: var(--bronze);
    font-weight: 800;
    margin-bottom: 2mm;
}
.price-val {
    font-family: 'Cormorant Garamond', Georgia, serif;
    font-size: 22pt;
    line-height: 1;
    font-weight: 700;
    color: var(--ink);
}
.tags { display: flex; flex-wrap: wrap; gap: 2mm; justify-content: flex-end; }
.tag {
    padding: 2mm 3mm;
    border: 1px solid rgba(215,181,109,0.46);
    background: rgba(255,255,255,0.11);
    font-family: 'Inter', Arial, sans-serif;
    font-size: 5.5pt;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    font-weight: 700;
    color: rgba(255,255,255,0.88);
    white-space: nowrap;
}

/* ── FINAL PAGE ── */
.final {
    background: #0a1624;
    color: #fff;
    position: relative;
}
.final-photo { position: absolute; inset: 0; z-index: 1; }
.final-photo img { width: 100%; height: 100%; object-fit: cover; opacity: 0.30; }
.final-overlay {
    position: absolute;
    inset: 0;
    z-index: 2;
    background: linear-gradient(100deg, rgba(6,13,24,0.90) 0%, rgba(12,24,40,0.62) 55%, rgba(12,24,40,0.20) 100%);
}
.final-inner {
    position: relative;
    z-index: 5;
    padding: 18mm 20mm 16mm;
    min-height: 297mm;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}
.final-title {
    font-family: 'Cormorant Garamond', Georgia, serif;
    font-size: 30pt;
    line-height: 1.05;
    font-weight: 700;
    color: #fff;
    max-width: 148mm;
    margin-bottom: 6mm;
}
.contact-panel {
    padding: 5.5mm 6mm;
    border: 1px solid rgba(215,181,109,0.44);
    background: rgba(255,255,255,0.93);
}
.contact-grid {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 5mm;
    margin-top: 5mm;
}
.contact-item { border-left: 1px solid rgba(215,181,109,0.70); padding-left: 3mm; }
.contact-item span {
    display: block;
    font-family: 'Inter', Arial, sans-serif;
    font-size: 5.5pt;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: rgba(36,52,71,0.52);
    font-weight: 700;
    margin-bottom: 1.5mm;
}
.contact-item strong {
    display: block;
    font-family: 'Inter', Arial, sans-serif;
    font-size: 9pt;
    color: var(--ink);
    font-weight: 700;
}
"""


# ─── PAGE BUILDERS ────────────────────────────────────────────────────────────

def _page(content, cls='', orbit=True):
    orbit_html = '<div class="decor-orbit"></div>' if orbit else ''
    return (
        f'<section class="page {cls}">'
        f'<div class="decor-grid"></div>'
        f'{orbit_html}'
        f'{content}'
        f'</section>'
    )

def _sh(eyebrow, title, num):
    return (
        f'<div class="section-head">'
        f'<div><div class="gold-line"></div>'
        f'<div class="eyebrow">{eyebrow}</div>'
        f'<h2>{title}</h2></div>'
        f'<div class="section-num">{num:02d}</div>'
        f'</div>'
    )

def _foot(l, r):
    return f'<div class="footer"><span>{l}</span><span>{r}</span></div>'

def _card(lbl, ttl, txt, variant=''):
    ttl_html = f'<h3>{ttl}</h3>' if ttl else ''
    return (
        f'<div class="card {variant}">'
        f'<h4>{lbl}</h4>'
        f'{ttl_html}'
        f'<p class="text">{txt}</p>'
        f'</div>'
    )

def _kpi(val, lbl, dark=False):
    cls = 'kpi dark' if dark else 'kpi'
    return (
        f'<div class="{cls}">'
        f'<div class="num">{val}</div>'
        f'<div class="lbl">{lbl}</div>'
        f'</div>'
    )


# ── COVER ──────────────────────────────────────────────────────────────────────
def _build_cover(data, content, lang):
    es = lang == 'es'
    fin = content['financials']
    precio = _eur(data.get('precio_venta'))
    ciudad = _s(data.get('ciudad'), 'Espana')
    barrio = _s(data.get('barrio')) or ciudad
    tipo_p = data.get('tipo_propiedad', '')
    tipo_dossier = data.get('tipo_dossier', 'inversores')
    m2 = _s(data.get('metros_construidos'))
    dorms = _s(data.get('dormitorios'))
    anyo = datetime.now().year

    t_es = {'apartamento':'Apartamento','atico':'Atico Premium','casa':'Casa Unifamiliar','villa':'Villa','local':'Local Comercial','oficina':'Oficina','solar':'Solar','edificio':'Edificio','nave':'Nave'}
    t_en = {'apartamento':'Apartment','atico':'Penthouse','casa':'House','villa':'Villa','local':'Commercial','oficina':'Office','solar':'Plot','edificio':'Building','nave':'Industrial'}
    tipo_lbl = (t_es if es else t_en).get(tipo_p, tipo_p.capitalize() if tipo_p else ('Inmueble' if es else 'Property'))

    fotos = data.get('foto_paths', [])
    photo_src = (_photo_b64(fotos[0]) or IMGS['cover1']) if fotos else IMGS['cover1']

    if es:
        kicker = f"{tipo_lbl} · Oportunidad Seleccionada"
        copy = (f"Inmueble premium en {barrio} — seleccionado por su posicionamiento excepcional, "
                f"calidad diferencial y potencial de rentabilidad.")
        if tipo_dossier != 'inversores':
            copy = f"Tu nuevo hogar en {barrio} — una oportunidad unica de vivir en un entorno excepcional con calidad de vida superior."
        dossier_lbl = 'Dossier Privado de Inversion' if tipo_dossier == 'inversores' else 'Dossier Premium Residencial'
        precio_lbl = 'Precio de salida'
        acceso = 'Acceso Reservado'
    else:
        kicker = f"{tipo_lbl} · Selected Opportunity"
        copy = (f"Premium property in {barrio} — selected for exceptional positioning, "
                f"differential quality and return potential.")
        if tipo_dossier != 'inversores':
            copy = f"Your new home in {barrio} — a unique opportunity to live in an exceptional environment."
        dossier_lbl = 'Private Investment Dossier' if tipo_dossier == 'inversores' else 'Premium Residential Dossier'
        precio_lbl = 'Asking price'
        acceso = 'Restricted Access'

    tags_list = [tipo_lbl]
    if m2: tags_list.append(f"{m2} m2")
    if dorms and dorms != '0': tags_list.append(f"{dorms} {'dorm.' if es else 'bed.'}")
    tags_list.append(ciudad)
    tags_html = ''.join(f'<div class="tag">{t}</div>' for t in tags_list[:5])
    subtexto = f"{m2} m2 &middot; {tipo_lbl} &middot; {barrio}" if m2 else f"{tipo_lbl} &middot; {barrio}"
    agente = _s(data.get('nombre_destinatario')) or _s(data.get('nombre_agente'), 'Dossier Premium')

    return (
        f'<section class="page cover no-frame">'
        f'<div class="decor-grid"></div>'
        f'<div class="cover-photo"><img src="{photo_src}" alt=""/></div>'
        f'<div class="cover-overlay"></div>'
        f'<div class="cover-inner">'
        f'  <div class="topbar">'
        f'    <div class="brand"><div class="brand-mark">RE</div><div>{dossier_lbl}</div></div>'
        f'    <div>{acceso} &middot; {anyo}</div>'
        f'  </div>'
        f'  <div class="cover-box">'
        f'    <div class="cover-kicker">{kicker}</div>'
        f'    <h1>{ciudad}<span class="cover-loc">{barrio}</span></h1>'
        f'    <p class="cover-copy">{copy}</p>'
        f'  </div>'
        f'  <div class="cover-bottom">'
        f'    <div class="price-panel">'
        f'      <div class="price-lbl">{precio_lbl}</div>'
        f'      <div class="price-val">{precio}</div>'
        f'      <p class="text" style="margin-top:2mm; color:#52657a;">{subtexto}</p>'
        f'    </div>'
        f'    <div>'
        f'      <div class="tags">{tags_html}</div>'
        f'      <p class="micro" style="text-align:right; margin-top:4mm; color:rgba(255,255,255,0.52);">{agente} &middot; {ciudad} &middot; {anyo}</p>'
        f'    </div>'
        f'  </div>'
        f'</div>'
        f'</section>'
    )


# ── EXECUTIVE SUMMARY ──────────────────────────────────────────────────────────
def _build_summary(data, content, lang, n):
    es = lang == 'es'
    fin = content['financials']
    ps = content['premium_score']
    ls = content['loc_scores']
    tipo_dossier = data.get('tipo_dossier', 'inversores')
    ciudad = _s(data.get('ciudad'), '')

    paras = [p.strip() for p in content['exec_summary'].split('\n\n') if p.strip()]
    lead = paras[0] if paras else ''

    if tipo_dossier == 'inversores':
        kpis = [
            (_pct(fin.get('yield_bruto', 0)), 'Yield Bruta' if es else 'Gross Yield', True),
            (_pct(fin.get('roi_5y', 0)), 'ROI 5 Anos' if es else '5Y ROI', False),
            (f"{ps}/10", 'Score Premium', False),
            (f"{ls.get('atractivo_inversor', 7)}/10", 'Inversor' if es else 'Investor', True),
        ]
    else:
        kpis = [
            (f"{ps}/10", 'Score Premium', True),
            (f"{ls.get('servicios', 7)}/10", 'Servicios' if es else 'Services', False),
            (f"{ls.get('conectividad', 7)}/10", 'Conectividad' if es else 'Connectivity', False),
            (f"{ls.get('atractivo_residencial', 7)}/10", 'Zona', True),
        ]
    kpis_html = ''.join(_kpi(v, l, d) for v, l, d in kpis)

    comm = content['commercial']
    prop_val = comm.get('propuesta_valor', '')
    perf_c = comm.get('perfil_comprador', '')
    tesis = content['conclusions']['texto']

    if es:
        sh_ey = 'Resumen Ejecutivo'
        sh_tt = 'Una oportunidad inmobiliaria presentada con criterio institucional.'
        c1_lbl = 'Propuesta de Valor'; c2_lbl = 'Perfil Inversor' if tipo_dossier == 'inversores' else 'Comprador Ideal'
        t_lbl = 'Tesis'
    else:
        sh_ey = 'Executive Summary'
        sh_tt = 'A real estate opportunity with institutional-grade analysis.'
        c1_lbl = 'Value Proposition'; c2_lbl = 'Investor Profile' if tipo_dossier == 'inversores' else 'Ideal Buyer'
        t_lbl = 'Investment thesis'

    return _page(
        f'<div class="inner">'
        f'{_sh(sh_ey, sh_tt, n)}'
        f'<p class="lead">{lead}</p>'
        f'<div class="kpi-row">{kpis_html}</div>'
        f'<div class="divider"></div>'
        f'<div class="g2">'
        f'{_card(c1_lbl, "", prop_val, "stone")}'
        f'{_card(c2_lbl, "", perf_c, "dark")}'
        f'</div>'
        f'<div class="note"><strong>{t_lbl}:</strong> {tesis}</div>'
        f'{_foot(sh_ey, ciudad)}'
        f'</div>'
    )


# ── TECHNICAL SHEET ────────────────────────────────────────────────────────────
def _build_ficha(data, content, lang, n):
    es = lang == 'es'
    fin = content['financials']
    ciudad = _s(data.get('ciudad'), '')
    barrio = _s(data.get('barrio')) or ciudad

    t_es = {'apartamento':'Apartamento','atico':'Atico / Penthouse','casa':'Casa Unifamiliar','villa':'Villa','local':'Local Comercial','oficina':'Oficina','solar':'Solar','edificio':'Edificio','nave':'Nave Industrial'}
    t_en = {'apartamento':'Apartment','atico':'Penthouse','casa':'House','villa':'Villa','local':'Commercial','oficina':'Office','solar':'Plot','edificio':'Building','nave':'Industrial'}
    tipo_lbl = (t_es if es else t_en).get(data.get('tipo_propiedad', ''), _s(data.get('tipo_propiedad', '')))

    e_es = {'nuevo':'Nuevo / A estrenar','excelente':'Excelente estado','bueno':'Buen estado','reformar':'A reformar','ruina':'Ruina'}
    e_en = {'nuevo':'Brand new','excelente':'Excellent','bueno':'Good condition','reformar':'Needs renovation','ruina':'Ruin'}
    estado_lbl = (e_es if es else e_en).get(data.get('estado', ''), _s(data.get('estado', '')))

    feats = data.get('caracteristicas', [])
    if isinstance(feats, str):
        import json as _j
        try: feats = _j.loads(feats)
        except: feats = []
    fn_es = {'ascensor':'Ascensor','aire_acondicionado':'Aire Acondicionado','calefaccion':'Calefaccion','amueblado':'Amueblado','seguridad':'Seguridad','piscina':'Piscina','parking':'Parking','terraza':'Terraza','jardin':'Jardin','trastero':'Trastero','domotica':'Domotica','vistas_mar':'Vistas Mar','vistas_ciudad':'Vistas Ciudad','portero':'Portero','gimnasio':'Gimnasio','spa':'Spa'}
    fn_en = {'ascensor':'Elevator','aire_acondicionado':'A/C','calefaccion':'Heating','amueblado':'Furnished','seguridad':'Security','piscina':'Pool','parking':'Parking','terraza':'Terrace','jardin':'Garden','trastero':'Storage','domotica':'Home auto.','vistas_mar':'Sea views','vistas_ciudad':'City views','portero':'Concierge','gimnasio':'Gym','spa':'Spa'}
    fn = fn_es if es else fn_en
    feats_str = ', '.join(fn.get(f, f) for f in feats) if feats else '—'

    a_es = {'vender':'Venta','alquilar':'Alquiler','vender_alquilar':'Venta o Alquiler'}
    a_en = {'vender':'For Sale','alquilar':'For Rent','vender_alquilar':'Sale or Rent'}
    accion = (a_es if es else a_en).get(data.get('accion', ''), _s(data.get('accion', '')))

    fotos = data.get('foto_paths', [])
    hero_src = (_photo_b64(fotos[1]) or _photo_b64(fotos[0])) if len(fotos) > 1 else (_photo_b64(fotos[0]) if fotos else IMGS['interior1'])
    if not hero_src: hero_src = IMGS['interior1']

    rows = []
    def row(k, v):
        if v and v not in ('N/D', '—'):
            rows.append(f'<tr><td>{k}</td><td>{v}</td></tr>')

    if es:
        sh_ey = 'Ficha Tecnica'; sh_tt = 'Datos esenciales del inmueble.'
        row('Direccion', _s(data.get('direccion')))
        row('Ciudad / Barrio', f"{ciudad} / {barrio}" if barrio != ciudad else ciudad)
        row('Codigo Postal', _s(data.get('cp')))
        row('Tipo de activo', tipo_lbl)
        row('Precio', _eur(data.get('precio_venta')))
        row('Sup. construida', f"{_s(data.get('metros_construidos'))} m2")
        if data.get('metros_utiles'): row('Sup. util', f"{_s(data.get('metros_utiles'))} m2")
        if data.get('dormitorios'): row('Dormitorios / Banos', f"{_s(data.get('dormitorios'))} / {_s(data.get('banos'))}")
        row('Ano construccion', _s(data.get('anyo_construccion')))
        row('Estado', estado_lbl)
        row('Cert. Energetico', _s(data.get('certificado_energetico')))
        row('Modalidad', accion)
        row('Extras', feats_str)
    else:
        sh_ey = 'Technical Sheet'; sh_tt = 'Essential property data.'
        row('Address', _s(data.get('direccion')))
        row('City / Area', f"{ciudad} / {barrio}" if barrio != ciudad else ciudad)
        row('Postcode', _s(data.get('cp')))
        row('Asset type', tipo_lbl)
        row('Price', _eur(data.get('precio_venta')))
        row('Built area', f"{_s(data.get('metros_construidos'))} m2")
        if data.get('metros_utiles'): row('Usable area', f"{_s(data.get('metros_utiles'))} m2")
        if data.get('dormitorios'): row('Beds / Baths', f"{_s(data.get('dormitorios'))} / {_s(data.get('banos'))}")
        row('Year built', _s(data.get('anyo_construccion')))
        row('Condition', estado_lbl)
        row('Energy cert.', _s(data.get('certificado_energetico')))
        row('Listing type', accion)
        row('Features', feats_str)

    pm2 = fin.get('precio_m2', 0)
    pm2z = float(data.get('precio_m2_zona') or 0)
    pm2_str = f"{pm2:,.0f} EUR/m2".replace(',', '.') if pm2 else '—'
    pm2z_str = f"{pm2z:,.0f} EUR/m2".replace(',', '.') if pm2z else '—'
    ps = content['premium_score']

    return _page(
        f'<div class="inner">'
        f'{_sh(sh_ey, sh_tt, n)}'
        f'<div class="img-box" style="margin-bottom:4.5mm;">'
        f'<img src="{hero_src}" style="height:55mm; width:100%; object-fit:cover;" alt=""/>'
        f'<div class="img-cap">{_s(data.get("direccion"), barrio + ", " + ciudad)}</div>'
        f'</div>'
        f'<table class="dtable"><tbody>{"".join(rows)}</tbody></table>'
        f'<div class="divider"></div>'
        f'<div class="g3">'
        f'{_card("Precio/m2" if es else "Price/m2", pm2_str, "Precio por metro cuadrado construido" if es else "Price per built sq metre", "dark")}'
        f'{_card("Zona / Precio" if es else "Area / Price", pm2z_str, "Media de la zona de referencia" if es else "Area reference average", "sky")}'
        f'{_card("Score Premium", f"{ps}/10", "Calidad y posicionamiento del activo" if es else "Asset quality and positioning", "stone")}'
        f'</div>'
        f'{_foot(sh_ey, ciudad)}'
        f'</div>'
    )


# ── COMMERCIAL DESCRIPTION ─────────────────────────────────────────────────────
def _build_commercial(data, content, lang, n):
    es = lang == 'es'
    fotos = data.get('foto_paths', [])
    ciudad = _s(data.get('ciudad'), '')
    paras = [p.strip() for p in content['narrative'].split('\n\n') if p.strip()]
    lead = paras[0] if paras else ''
    body = ''.join(f'<p class="text" style="margin-bottom:3mm;">{p}</p>' for p in paras[1:3])

    fallbacks = [IMGS['interior1'], IMGS['interior2'], IMGS['terrace']]

    def img_tag(idx, height, cap=''):
        src = (_photo_b64(fotos[idx]) if idx < len(fotos) else '') or fallbacks[idx % len(fallbacks)]
        cap_html = f'<div class="img-cap">{cap}</div>' if cap else ''
        return f'<div class="img-box"><img src="{src}" style="height:{height}; width:100%; object-fit:cover;" alt=""/>{cap_html}</div>'

    if es:
        sh_ey = 'Descripcion Comercial'; sh_tt = 'El inmueble presentado en toda su dimension.'
        cap1 = 'Vista principal'; cap2 = 'Detalle'; cap3 = 'Espacio'
    else:
        sh_ey = 'Commercial Description'; sh_tt = 'The property in its full dimension.'
        cap1 = 'Main view'; cap2 = 'Detail'; cap3 = 'Space'

    return _page(
        f'<div class="inner">'
        f'{_sh(sh_ey, sh_tt, n)}'
        f'<p class="lead">{lead}</p>'
        f'{body}'
        f'<div class="divider"></div>'
        f'<div class="g2" style="margin-top:4mm;">'
        f'<div>{img_tag(0, "58mm", cap1)}</div>'
        f'<div style="display:grid; gap:4mm;">'
        f'{img_tag(1, "27mm", cap2)}'
        f'{img_tag(2, "27mm", cap3)}'
        f'</div>'
        f'</div>'
        f'{_foot(sh_ey, ciudad)}'
        f'</div>'
    )


# ── LOCATION ANALYSIS — con radar SVG ─────────────────────────────────────────
def _build_location(data, content, lang, n):
    es = lang == 'es'
    ciudad = _s(data.get('ciudad'), '')
    barrio = _s(data.get('barrio')) or ciudad
    ls = content['loc_scores']
    paras = [p.strip() for p in content['zona_text'].split('\n\n') if p.strip()]
    lead = paras[0] if paras else ''
    body = ''.join(f'<p class="text" style="margin-bottom:2.5mm;">{p}</p>' for p in paras[1:2])

    # Radar chart — estilo del PDF anterior adaptado a SVG
    if es:
        radar_labels = ['Conectividad', 'Transporte', 'Servicios', 'Comercios', 'Calidad Zona', 'Seguridad']
    else:
        radar_labels = ['Connectivity', 'Transport', 'Services', 'Commerce', 'Zone Quality', 'Safety']

    radar_values = [
        float(ls.get('conectividad', 7.5)),
        float(ls.get('transporte', 7.5)),
        float(ls.get('servicios', 7.5)),
        float(ls.get('comercios', 7.0)),
        float(ls.get('atractivo_residencial', 7.0)),
        float(ls.get('seguridad', 8.0)),
    ]
    radar_svg = _svg_radar(radar_labels, radar_values, size=162)

    # Barras horizontales — estilo del PDF anterior
    bar_items = list(zip(radar_labels, radar_values))
    bars_html = ''.join(_svg_bar(lbl, val, 10, 158) for lbl, val in bar_items)

    # Zone images
    zone_imgs = _zone_imgs(data, lang)
    zone_html = ''.join(
        f'<div class="vitem"><img src="{u}" alt="{l}"/><div class="vcap">{l}</div></div>'
        for u, l in zone_imgs[:6]
    )

    if es:
        sh_ey = 'Analisis de Ubicacion'
        sh_tt = f'{ciudad} — multiplicador de valor y calidad de vida.'
        radar_lbl = 'Indice de Ubicacion'
        bars_lbl = 'Puntuaciones por factor'
    else:
        sh_ey = 'Location Analysis'
        sh_tt = f'{ciudad} — value and quality-of-life multiplier.'
        radar_lbl = 'Location Index'
        bars_lbl = 'Factor scores'

    return _page(
        f'<div class="inner">'
        f'{_sh(sh_ey, sh_tt, n)}'
        f'<p class="lead">{lead}</p>'
        f'{body}'
        f'<div class="divider"></div>'
        f'<div class="g2" style="align-items:start;">'
        f'  <div>'
        f'    <h4>{radar_lbl}</h4>'
        f'    <div style="margin-top:3mm; display:flex; justify-content:center;">{radar_svg}</div>'
        f'  </div>'
        f'  <div>'
        f'    <h4>{bars_lbl}</h4>'
        f'    <div class="bars-block" style="margin-top:4mm;">{bars_html}</div>'
        f'  </div>'
        f'</div>'
        f'<div class="divider"></div>'
        f'<div class="vgallery">{zone_html}</div>'
        f'{_foot(sh_ey, ciudad)}'
        f'</div>'
    )


# ── SERVICES ───────────────────────────────────────────────────────────────────
def _build_services(data, content, lang, n):
    es = lang == 'es'
    ciudad = _s(data.get('ciudad'), '')
    servicios_texto = _s(data.get('servicios_cercanos', ''))
    tendencia = _s(data.get('tendencia_mercado', ''))

    if es:
        sh_ey = 'Servicios e Infraestructura'; sh_tt = 'Todo lo que potencia el valor y el bienestar.'
        intro = f"El entorno inmediato ofrece acceso directo a una red de servicios de primer nivel en {ciudad}."
        if servicios_texto: intro += f" {servicios_texto}"
        conclusion = tendencia or f"El acceso integral a estos servicios posiciona el inmueble en el cuartil superior del mercado en {ciudad}."
    else:
        sh_ey = 'Services & Infrastructure'; sh_tt = 'Everything that enhances value and wellbeing.'
        intro = f"The immediate surroundings offer direct access to a first-class urban services network in {ciudad}."
        if servicios_texto: intro += f" {servicios_texto}"
        conclusion = tendencia or f"This comprehensive service access positions the property in the top quartile of the {ciudad} market."

    svc_imgs = _service_imgs(lang)
    svcs_html = ''.join(
        f'<div class="vitem"><img src="{u}" alt="{l}"/><div class="vcap">{l}</div></div>'
        for u, l in svc_imgs
    )

    return _page(
        f'<div class="inner">'
        f'{_sh(sh_ey, sh_tt, n)}'
        f'<p class="lead">{intro}</p>'
        f'<div class="vgallery">{svcs_html}</div>'
        f'<div class="note">{conclusion}</div>'
        f'{_foot(sh_ey, ciudad)}'
        f'</div>'
    )


# ── INVESTMENT ANALYSIS — con donuts SVG ──────────────────────────────────────
def _build_investment(data, content, lang, n):
    es = lang == 'es'
    fin = content['financials']
    ciudad = _s(data.get('ciudad'), '')
    paras = [p.strip() for p in content['financial_text'].split('\n\n') if p.strip()]
    lead = paras[0] if paras else ''

    yb  = fin.get('yield_bruto', 0)
    yn  = fin.get('yield_neto', 0)
    roi = fin.get('roi_5y', 0)
    rev = float(fin.get('rev_rate', 5))
    ing   = fin.get('ingresos_brutos', 0)
    ing_n = fin.get('ingresos_netos', 0)
    precio    = fin.get('precio', 0)
    reforma   = fin.get('reforma', 0)
    inv_total = fin.get('inversion_total', precio)
    pb = fin.get('payback', 0)
    gastos_total = (fin.get('gas_com_anual', 0) + fin.get('ibi', 0) +
                    fin.get('gestion', 0) + fin.get('otros', 0))

    # Donut SVGs
    yb_float = float(yb) if yb else 0
    yn_float = float(yn) if yn else 0
    roi_float = float(roi) if roi else 0
    donut1 = _svg_donut(min(yb_float * 10, 100), f"{yb_float:.1f}%", 76)
    donut2 = _svg_donut(min(yn_float * 10, 100), f"{yn_float:.1f}%", 76, '#9b7638')
    donut3 = _svg_donut(min(roi_float * 3, 100), f"{roi_float:.1f}%", 76, '#2c3e52')

    if es:
        sh_ey = 'Escenario de Inversion'; sh_tt = 'Potencial financiero y logica de retorno.'
        rows = [
            ('Precio de adquisicion', _eur(precio)),
            ('Reforma estimada', _eur(reforma) if reforma else 'No necesaria'),
            ('Inversion total', _eur(inv_total)),
            ('Ingresos brutos anuales', _eur(ing) if ing else 'Pendiente'),
            ('Gastos operativos', _eur(gastos_total) if gastos_total else '—'),
            ('Ingresos netos anuales', _eur(ing_n) if ing_n else '—'),
            ('Payback', f"{pb:.1f} anos" if pb else '—'),
        ]
        d1l = 'Yield Bruta'; d2l = 'Yield Neta'; d3l = 'ROI 5 Anos'
        nota = f"Escenario calculado con {_s(data.get('ocupacion','90'))}% ocupacion y revalorizacion estimada del {_pct(rev)}/ano. Datos orientativos."
    else:
        sh_ey = 'Investment Scenario'; sh_tt = 'Financial potential and return rationale.'
        rows = [
            ('Acquisition price', _eur(precio)),
            ('Estimated renovation', _eur(reforma) if reforma else 'Not needed'),
            ('Total investment', _eur(inv_total)),
            ('Annual gross income', _eur(ing) if ing else 'TBD'),
            ('Operating costs', _eur(gastos_total) if gastos_total else '—'),
            ('Annual net income', _eur(ing_n) if ing_n else '—'),
            ('Payback', f"{pb:.1f} years" if pb else '—'),
        ]
        d1l = 'Gross Yield'; d2l = 'Net Yield'; d3l = '5Y ROI'
        nota = f"Scenario at {_s(data.get('ocupacion','90'))}% occupancy and estimated {_pct(rev)}/yr appreciation. Indicative data."

    rows_html = ''.join(f'<tr><td>{k}</td><td>{v}</td></tr>' for k, v in rows if v not in ('—',''))

    donuts_html = (
        f'<div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:3mm; margin-top:5mm;">'
        f'  <div style="text-align:center; padding:4mm; background:rgba(255,255,255,0.88); border:1px solid rgba(36,52,71,0.11);">'
        f'    {donut1}<div class="micro" style="margin-top:2mm;">{d1l}</div></div>'
        f'  <div style="text-align:center; padding:4mm; background:rgba(255,255,255,0.88); border:1px solid rgba(36,52,71,0.11);">'
        f'    {donut2}<div class="micro" style="margin-top:2mm;">{d2l}</div></div>'
        f'  <div style="text-align:center; padding:4mm; background:rgba(255,255,255,0.88); border:1px solid rgba(36,52,71,0.11);">'
        f'    {donut3}<div class="micro" style="margin-top:2mm;">{d3l}</div></div>'
        f'</div>'
    )

    return _page(
        f'<div class="inner">'
        f'{_sh(sh_ey, sh_tt, n)}'
        f'<p class="lead">{lead}</p>'
        f'<div class="divider"></div>'
        f'<table class="dtable" style="margin-bottom:0;"><tbody>{rows_html}</tbody></table>'
        f'{donuts_html}'
        f'<div class="note">{nota}</div>'
        f'{_foot(sh_ey, "Estimaciones orientativas" if es else "Indicative estimates")}'
        f'</div>'
    )


# ── COMPETITIVE ADVANTAGES ─────────────────────────────────────────────────────
def _build_advantages(data, content, lang, n):
    es = lang == 'es'
    ciudad = _s(data.get('ciudad'), '')
    tipo_dossier = data.get('tipo_dossier', 'inversores')
    args = list(content['commercial'].get('argumentos', []))

    if es:
        sh_ey = 'Ventajas Competitivas'; sh_tt = 'Razones para priorizar este activo.'
        titles = (['Ubicacion Estrategica','Posicionamiento Premium','Demanda Sostenida','Potencial de Revalorizacion','Rentabilidad Diferencial','Liquidez del Activo']
                  if tipo_dossier == 'inversores' else
                  ['Ubicacion Privilegiada','Calidad de Construccion','Entorno Residencial','Servicios de Primer Nivel','Espacios y Distribucion','Inversion Segura'])
    else:
        sh_ey = 'Competitive Advantages'; sh_tt = 'Reasons to prioritise this asset.'
        titles = (['Strategic Location','Premium Positioning','Sustained Demand','Appreciation Potential','Differential Return','Asset Liquidity']
                  if tipo_dossier == 'inversores' else
                  ['Prime Location','Construction Quality','Residential Environment','First-Class Services','Layout & Space','Safe Investment'])

    while len(args) < 6:
        args.append(titles[len(args)] if len(args) < len(titles) else '')

    advs_html = ''.join(
        f'<div class="adv">'
        f'<div class="adv-n">{i+1:02d}</div>'
        f'<div><h3>{titles[i] if i < len(titles) else ""}</h3>'
        f'<p class="text">{txt}</p></div>'
        f'</div>'
        for i, txt in enumerate(args[:6])
    )
    concl = content['conclusions'].get('texto', '')

    return _page(
        f'<div class="inner">'
        f'{_sh(sh_ey, sh_tt, n)}'
        f'<div class="g2">{advs_html}</div>'
        f'<div class="note">{concl}</div>'
        f'{_foot(sh_ey, ciudad)}'
        f'</div>'
    )


# ── VALUE CREATION PLAN ────────────────────────────────────────────────────────
def _build_value_plan(data, content, lang, n):
    es = lang == 'es'
    ciudad = _s(data.get('ciudad'), '')
    info_inv = _s(data.get('info_adicional_inversores', ''))

    if es:
        sh_ey = 'Plan de Creacion de Valor'; sh_tt = 'Como convertir este activo en rentabilidad sostenida.'
        fases = [
            ('Fase 1','Adquisicion','Due diligence, negociacion y cierre en condiciones optimas.'),
            ('Fase 2','Optimizacion','Reforma estrategica o puesta a punto. Posicionamiento de mercado.'),
            ('Fase 3','Monetizacion','Comercializacion con pricing competitivo. Seleccion de inquilino/comprador.'),
            ('Fase 4','Consolidacion','Gestion activa. Revision anual y analisis de estrategia de salida.'),
        ]
        extras = [
            ('Fiscal', 'Amortizacion, deduccion de gastos y estructura juridica optima para el perfil inversor.', 'stone'),
            ('Gestion', 'Delegacion a empresa especializada. Comision tipica: 8-12% sobre renta bruta.', 'sky'),
            ('Salida', 'Venta a 5 anos en mercado abierto o a inquilino con tanteo. Plusvalia estimada por revalorizacion.', 'dark'),
        ]
    else:
        sh_ey = 'Value Creation Plan'; sh_tt = 'How to turn this asset into sustained returns.'
        fases = [
            ('Phase 1','Acquisition','Full due diligence, negotiation and closing under optimal conditions.'),
            ('Phase 2','Optimisation','Strategic renovation or asset preparation. Market positioning.'),
            ('Phase 3','Monetisation','Competitive pricing. Rigorous tenant or buyer selection.'),
            ('Phase 4','Consolidation','Active management. Annual review and exit strategy analysis.'),
        ]
        extras = [
            ('Tax', 'Depreciation, expense deductions and optimal legal structure for the investor profile.', 'stone'),
            ('Management', 'Delegation to specialist firm. Typical fee: 8-12% on gross rent.', 'sky'),
            ('Exit', 'Sale at 5 years on open market or to tenant with pre-emption right.', 'dark'),
        ]

    timeline_html = ''.join(
        f'<div class="step"><div class="step-n">{lbl}</div><h3>{ttl}</h3><p class="text">{txt}</p></div>'
        for lbl, ttl, txt in fases
    )
    extras_html = ''.join(_card(lbl, '', txt, var) for lbl, txt, var in extras)
    info_block = f'<div class="note">{info_inv}</div>' if info_inv else ''

    return _page(
        f'<div class="inner">'
        f'{_sh(sh_ey, sh_tt, n)}'
        f'<div class="timeline">{timeline_html}</div>'
        f'<div class="divider"></div>'
        f'<div class="g3">{extras_html}</div>'
        f'{info_block}'
        f'{_foot(sh_ey, ciudad)}'
        f'</div>'
    )


# ── STRATEGIC ANALYSIS ─────────────────────────────────────────────────────────
def _build_strategic(data, content, lang, n):
    es = lang == 'es'
    ciudad = _s(data.get('ciudad'), '')
    riesgos = content['riesgos']
    comm = content['commercial']

    if es:
        sh_ey = 'Analisis Estrategico y Riesgos'; sh_tt = 'Lectura avanzada del activo y estrategia de salida.'
    else:
        sh_ey = 'Strategic Analysis & Risks'; sh_tt = 'Advanced asset reading and exit strategy.'

    variants = ['stone', 'sky', 'gold']
    risks_html = ''.join(
        _card(item[0], item[1].upper(), item[2], variants[i % len(variants)])
        for i, item in enumerate(riesgos[:3])
    )

    opps = comm.get('oportunidades', [])
    opps_html = ''.join(
        f'<div class="adv"><div class="adv-n">+</div><div><p class="text">{o}</p></div></div>'
        for o in opps[:3]
    )
    recs = content['conclusions'].get('recomendaciones', [])
    recs_li = ''.join(
        f'<li style="margin-bottom:2mm; font-family:Inter,Arial,sans-serif; font-size:7.5pt; line-height:1.48; color:rgba(255,255,255,0.86);">{r}</li>'
        for r in recs[:4]
    )
    opp_lbl = 'Oportunidades' if es else 'Opportunities'
    rec_lbl = 'Recomendaciones' if es else 'Recommendations'

    return _page(
        f'<div class="inner">'
        f'{_sh(sh_ey, sh_tt, n)}'
        f'<div class="g3">{risks_html}</div>'
        f'<div class="divider"></div>'
        f'<div class="g2">'
        f'<div><h4>{opp_lbl}</h4><div style="margin-top:3mm;">{opps_html}</div></div>'
        f'<div class="card dark"><h4>{rec_lbl}</h4><ul style="margin-top:3mm; padding-left:4mm;">{recs_li}</ul></div>'
        f'</div>'
        f'{_foot(sh_ey, ciudad)}'
        f'</div>'
    )


# ── LIFESTYLE (Particulares) ───────────────────────────────────────────────────
def _build_lifestyle(data, content, lang, n):
    es = lang == 'es'
    ciudad = _s(data.get('ciudad'), '')
    barrio = _s(data.get('barrio')) or ciudad
    ls = content['loc_scores']
    paras = [p.strip() for p in content['zona_text'].split('\n\n') if p.strip()]
    lead = paras[0] if paras else ''
    body = ''.join(f'<p class="text" style="margin-bottom:2.5mm;">{p}</p>' for p in paras[1:3])

    # Score bars (like old PDF) for lifestyle version
    if es:
        sh_ey = 'Calidad de Vida y Entorno'; sh_tt = f'Vivir en {barrio} es mucho mas que una direccion.'
        bar_items = [
            ('Servicios', ls.get('servicios', 7.5)),
            ('Colegios', ls.get('educacion', 7.0)),
            ('Conectividad', ls.get('conectividad', 7.5)),
            ('Verde', ls.get('zonas_verdes', 7.0)),
            ('Seguridad', ls.get('seguridad', 8.0)),
        ]
    else:
        sh_ey = 'Quality of Life & Environment'; sh_tt = f'Living in {barrio} is much more than an address.'
        bar_items = [
            ('Services', ls.get('servicios', 7.5)),
            ('Schools', ls.get('educacion', 7.0)),
            ('Connectivity', ls.get('conectividad', 7.5)),
            ('Green', ls.get('zonas_verdes', 7.0)),
            ('Safety', ls.get('seguridad', 8.0)),
        ]

    bars_html = ''.join(_svg_bar(lbl, val, 10, 158) for lbl, val in bar_items)
    zone_imgs = _zone_imgs(data, lang)
    imgs_html = ''.join(
        f'<div class="vitem"><img src="{u}" alt="{l}"/><div class="vcap">{l}</div></div>'
        for u, l in zone_imgs[:6]
    )

    return _page(
        f'<div class="inner">'
        f'{_sh(sh_ey, sh_tt, n)}'
        f'<div class="g2" style="margin-bottom:5mm;">'
        f'  <div><p class="lead" style="margin-bottom:3mm;">{lead}</p>{body}</div>'
        f'  <div><h4>{"Puntuaciones de zona" if es else "Zone scores"}</h4><div class="bars-block" style="margin-top:4mm;">{bars_html}</div></div>'
        f'</div>'
        f'<div class="vgallery">{imgs_html}</div>'
        f'{_foot(sh_ey, ciudad)}'
        f'</div>'
    )


# ── PHOTO GALLERY ──────────────────────────────────────────────────────────────
def _build_gallery(data, content, lang, n):
    es = lang == 'es'
    ciudad = _s(data.get('ciudad'), '')
    fotos = data.get('foto_paths', [])
    fallbacks = [IMGS['interior1'], IMGS['interior2'], IMGS['terrace'], IMGS['pool'], IMGS['garden'], IMGS['city']]

    def get_src(idx):
        if idx < len(fotos):
            s = _photo_b64(fotos[idx])
            if s: return s
        return fallbacks[(idx - len(fotos)) % len(fallbacks)]

    if es:
        sh_ey = 'Galeria del Inmueble'; sh_tt = 'Presentacion visual del activo.'
        note_txt = 'Imagenes seleccionadas para ofrecer una vision completa del inmueble y su entorno. Se recomienda solicitar una visita privada para una experiencia completa.'
    else:
        sh_ey = 'Property Gallery'; sh_tt = 'Visual presentation of the asset.'
        note_txt = 'Images selected to offer a complete view of the property and its surroundings. A private visit is recommended for the full experience.'

    extra_html = '<div class="g3" style="margin-top:4mm;">'
    for i in range(3, 6):
        extra_html += f'<div class="img-box"><img src="{get_src(i)}" style="height:36mm; width:100%; object-fit:cover;" alt=""/></div>'
    extra_html += '</div>'

    return _page(
        f'<div class="inner">'
        f'{_sh(sh_ey, sh_tt, n)}'
        f'<div class="photo-strip">'
        f'<div class="img-box" style="height:98mm;"><img src="{get_src(0)}" style="height:98mm; width:100%; object-fit:cover;" alt=""/></div>'
        f'<div class="photo-stack">'
        f'<div class="img-box" style="height:47mm;"><img src="{get_src(1)}" style="height:47mm; width:100%; object-fit:cover;" alt=""/></div>'
        f'<div class="img-box" style="height:47mm;"><img src="{get_src(2)}" style="height:47mm; width:100%; object-fit:cover;" alt=""/></div>'
        f'</div></div>'
        f'{extra_html}'
        f'<div class="note" style="margin-top:4mm;">{note_txt}</div>'
        f'{_foot(sh_ey, ciudad)}'
        f'</div>'
    )


# ── FINAL CTA ──────────────────────────────────────────────────────────────────
def _build_final(data, content, lang):
    es = lang == 'es'
    ciudad = _s(data.get('ciudad'), '')
    barrio = _s(data.get('barrio')) or ciudad
    nombre = _s(data.get('nombre_destinatario')) or _s(data.get('nombre_agente'), 'Contacto')
    email  = _s(data.get('email_destinatario'), _s(data.get('email_agente', '')))
    tel    = _s(data.get('telefono_destinatario')) or _s(data.get('telefono_agente', ''))
    web    = _s(data.get('web_agente', ''))
    tipo_dossier = data.get('tipo_dossier', 'inversores')
    anyo = datetime.now().year
    ps = content['premium_score']

    fotos = data.get('foto_paths', [])
    final_src = (_photo_b64(fotos[-1]) or IMGS['cover2']) if fotos else IMGS['cover2']
    if not final_src: final_src = IMGS['cover2']

    if es:
        if tipo_dossier == 'inversores':
            title = f"Una oportunidad limitada para tomar posicion en {ciudad}."
            copy = f"Este activo representa una ventana de inversion con fundamentos solidos en {barrio}. Las oportunidades de este calibre son escasas y de alta rotacion."
            cta = "Solicite visita privada y documentacion tecnica completa."
        else:
            title = f"Tu hogar en {barrio} te esta esperando."
            copy = f"Cada detalle de este inmueble ha sido seleccionado para ofrecerte una calidad de vida superior en el corazon de {ciudad}."
            cta = "Solicite visita privada para conocer el inmueble en persona."
        dossier_tag = 'Dossier Premium Inmobiliario'
        cta_lbl = 'Agente / Contacto'
        prox = 'Proximo Paso'
        tel_lbl = 'Telefono'
        score_lbl = 'Score Premium'
    else:
        if tipo_dossier == 'inversores':
            title = f"A limited opportunity to take position in {ciudad}."
            copy = f"This asset represents an investment window with solid fundamentals in {barrio}. Opportunities of this calibre are scarce and high-turnover."
            cta = "Request a private visit and complete technical documentation."
        else:
            title = f"Your home in {barrio} is waiting for you."
            copy = f"Every detail of this property has been carefully selected to offer you superior quality of life in the heart of {ciudad}."
            cta = "Request a private visit to see the property in person."
        dossier_tag = 'Premium Real Estate Dossier'
        cta_lbl = 'Agent / Contact'
        prox = 'Next Step'
        tel_lbl = 'Phone'
        score_lbl = 'Premium Score'

    tags_html = ''.join(f'<div class="tag">{t}</div>' for t in [dossier_tag, ciudad, str(anyo)])
    third = (f'<div class="contact-item"><span>Web</span><strong>{web}</strong></div>'
             if web else
             f'<div class="contact-item"><span>{score_lbl}</span><strong>{ps}/10</strong></div>')

    return (
        f'<section class="page final no-frame">'
        f'<div class="decor-grid"></div>'
        f'<div class="final-photo"><img src="{final_src}" alt=""/></div>'
        f'<div class="final-overlay"></div>'
        f'<div class="final-inner">'
        f'  <div class="topbar">'
        f'    <div class="brand"><div class="brand-mark">RE</div><div>{dossier_tag}</div></div>'
        f'    <div>{ciudad} &middot; {anyo}</div>'
        f'  </div>'
        f'  <div>'
        f'    <div class="cover-kicker">{prox}</div>'
        f'    <div class="final-title">{title}</div>'
        f'    <p class="cover-copy" style="max-width:132mm;">{copy}</p>'
        f'    <div class="note" style="max-width:132mm; margin-top:6mm; background:rgba(255,255,255,0.93); color:#223246;">'
        f'      <strong>{cta}</strong></div>'
        f'  </div>'
        f'  <div>'
        f'    <div class="contact-panel">'
        f'      <h3 style="font-family:\'Cormorant Garamond\',Georgia,serif; font-size:16pt; color:#223246;">{nombre}</h3>'
        f'      <p class="text" style="color:#52657a; margin-top:1mm;">{cta_lbl}</p>'
        f'      <div class="contact-grid">'
        f'        <div class="contact-item"><span>Email</span><strong>{email}</strong></div>'
        f'        <div class="contact-item"><span>{tel_lbl}</span><strong>{tel or "—"}</strong></div>'
        f'        {third}'
        f'      </div>'
        f'    </div>'
        f'    <div class="tags" style="margin-top:5mm; justify-content:flex-start;">{tags_html}</div>'
        f'  </div>'
        f'</div>'
        f'</section>'
    )


# ─── MAIN BUILDER ─────────────────────────────────────────────────────────────

def _build_html(data, content, lang):
    tipo_dossier = data.get('tipo_dossier', 'inversores')
    pages = [_build_cover(data, content, lang)]
    n = 1

    pages.append(_build_summary(data, content, lang, n)); n += 1
    pages.append(_build_ficha(data, content, lang, n)); n += 1
    pages.append(_build_commercial(data, content, lang, n)); n += 1
    pages.append(_build_location(data, content, lang, n)); n += 1
    pages.append(_build_services(data, content, lang, n)); n += 1

    if tipo_dossier == 'inversores':
        pages.append(_build_investment(data, content, lang, n)); n += 1
        pages.append(_build_advantages(data, content, lang, n)); n += 1
        pages.append(_build_value_plan(data, content, lang, n)); n += 1
        pages.append(_build_strategic(data, content, lang, n)); n += 1
    else:
        pages.append(_build_lifestyle(data, content, lang, n)); n += 1
        pages.append(_build_advantages(data, content, lang, n)); n += 1

    pages.append(_build_gallery(data, content, lang, n)); n += 1
    pages.append(_build_final(data, content, lang))

    return (
        f'<!DOCTYPE html><html lang="{lang}"><head>'
        f'<meta charset="UTF-8"/>'
        f'<title>Dossier Premium</title>'
        f'<style>{_css()}</style>'
        f'</head><body>{"".join(pages)}</body></html>'
    )


# ─── ENTRY POINT ──────────────────────────────────────────────────────────────

def generate_dossier(data, content, lang='es'):
    html = _build_html(data, content, lang)
    from weasyprint import HTML
    return HTML(string=html, base_url='https://images.unsplash.com').write_pdf()
