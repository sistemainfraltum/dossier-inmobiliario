"""
Motor PDF Premium v4 — Dossier Inmobiliario
Rediseño completo: letras grandes, fondos arquitectónicos, cards visibles,
habitaciones en descripción, servicios ampliados, gráficos grandes.
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

def _svg_radar(labels, values, size=200):
    n = len(labels)
    if n < 3:
        return ''
    cx = cy = size / 2
    r = size / 2 - 34
    parts = []
    for level in [0.25, 0.5, 0.75, 1.0]:
        pts = []
        for i in range(n):
            ang = -math.pi / 2 + 2 * math.pi * i / n
            pts.append(f"{cx + r*level*math.cos(ang):.1f},{cy + r*level*math.sin(ang):.1f}")
        fill = 'rgba(215,181,109,0.08)' if level == 1.0 else 'none'
        parts.append(f'<polygon points="{" ".join(pts)}" fill="{fill}" stroke="rgba(215,181,109,0.35)" stroke-width="0.7"/>')
    for i in range(n):
        ang = -math.pi / 2 + 2 * math.pi * i / n
        x2 = cx + r * math.cos(ang)
        y2 = cy + r * math.sin(ang)
        parts.append(f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="rgba(36,52,71,0.20)" stroke-width="0.6"/>')
    data_pts = []
    for i in range(n):
        ang = -math.pi / 2 + 2 * math.pi * i / n
        v = min(max(float(values[i]) / 10.0, 0), 1)
        data_pts.append(f"{cx + r*v*math.cos(ang):.1f},{cy + r*v*math.sin(ang):.1f}")
    parts.append(f'<polygon points="{" ".join(data_pts)}" fill="rgba(215,181,109,0.28)" stroke="#d7b56d" stroke-width="2.2" stroke-linejoin="round"/>')
    for i in range(n):
        ang = -math.pi / 2 + 2 * math.pi * i / n
        v = min(max(float(values[i]) / 10.0, 0), 1)
        px = cx + r * v * math.cos(ang)
        py = cy + r * v * math.sin(ang)
        parts.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4.2" fill="#d7b56d" stroke="white" stroke-width="1.5"/>')
    for i, label in enumerate(labels):
        ang = -math.pi / 2 + 2 * math.pi * i / n
        lx = cx + (r + 20) * math.cos(ang)
        ly = cy + (r + 20) * math.sin(ang)
        anchor = 'middle'
        if lx < cx - 8: anchor = 'end'
        elif lx > cx + 8: anchor = 'start'
        val_str = f"{values[i]:.1f}" if isinstance(values[i], float) else str(values[i])
        parts.append(
            f'<text x="{lx:.1f}" y="{ly+3:.1f}" text-anchor="{anchor}" '
            f'font-family="Inter,Arial,sans-serif" font-size="8" '
            f'fill="#7a5c2a" font-weight="800" letter-spacing="0.6">{label.upper()}</text>'
        )
        parts.append(
            f'<text x="{lx:.1f}" y="{ly+13:.1f}" text-anchor="{anchor}" '
            f'font-family="Inter,Arial,sans-serif" font-size="9" '
            f'fill="#223246" font-weight="700">{val_str}</text>'
        )
    return (
        f'<svg viewBox="0 0 {size} {size}" width="{size}" height="{size}" '
        f'xmlns="http://www.w3.org/2000/svg">{"".join(parts)}</svg>'
    )


def _svg_bar(label, value, max_val=10, width=200, color='#d7b56d'):
    h = 28
    lbl_w = 68
    val_w = 28
    bar_w = width - lbl_w - val_w - 4
    fill_w = bar_w * min(float(value) / max_val, 1)
    score_color = '#2c7a2c' if float(value) >= 8 else ('#d7b56d' if float(value) >= 6 else '#c05050')
    return (
        f'<svg viewBox="0 0 {width} {h}" width="{width}" height="{h}" xmlns="http://www.w3.org/2000/svg">'
        f'<text x="0" y="17" font-family="Inter,Arial,sans-serif" font-size="8" '
        f'fill="#7a5c2a" font-weight="800" letter-spacing="0.8">{label.upper()}</text>'
        f'<rect x="{lbl_w}" y="8" width="{bar_w}" height="9" rx="4.5" fill="rgba(36,52,71,0.12)"/>'
        f'<rect x="{lbl_w}" y="8" width="{fill_w:.1f}" height="9" rx="4.5" fill="{color}"/>'
        f'<text x="{width}" y="17" font-family="Inter,Arial,sans-serif" font-size="10" '
        f'fill="#223246" font-weight="800" text-anchor="end">{_num(value)}</text>'
        f'</svg>'
    )


def _svg_donut(pct, label, size=96, color='#d7b56d'):
    cx = cy = size / 2
    r = size / 2 - 12
    circ = 2 * math.pi * r
    dash = circ * min(float(pct) / 100.0, 1)
    gap = circ - dash
    return (
        f'<svg viewBox="0 0 {size} {size}" width="{size}" height="{size}" xmlns="http://www.w3.org/2000/svg">'
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="rgba(36,52,71,0.10)" stroke-width="8"/>'
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" stroke-width="8" '
        f'stroke-dasharray="{dash:.2f} {gap:.2f}" stroke-dashoffset="{circ/4:.2f}" stroke-linecap="round"/>'
        f'<text x="{cx}" y="{cy+3}" text-anchor="middle" dominant-baseline="middle" '
        f'font-family="Inter,Arial,sans-serif" font-size="14" font-weight="800" fill="#223246">{label}</text>'
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
    'arch1':      _U+'1493809842364-78817add7ffb?fm=jpg&q=60&w=900',
    'arch2':      _U+'1524230659092-07914300325d?fm=jpg&q=60&w=900',
    'arch3':      _U+'1416331108676-a22ccb276e35?fm=jpg&q=60&w=900',
    'arch4':      _U+'1512917774080-9991f1c4c750?fm=jpg&q=60&w=900',
    'arch5':      _U+'1560448204-e02f11c3d0e2?fm=jpg&q=60&w=900',
    'arch6':      _U+'1502005097973-6a7082348e28?fm=jpg&q=60&w=900',
    'living':     _U+'1555041469-68ad9154f720?fm=jpg&q=80&w=700',
    'kitchen':    _U+'1556909114-f6e7ad7d3136?fm=jpg&q=80&w=700',
    'bedroom':    _U+'1540518614846-7eded433c457?fm=jpg&q=80&w=700',
    'bathroom':   _U+'1552321554-5fefe8c9ef14?fm=jpg&q=80&w=700',
}

# Page background images — architectural, low opacity
PAGE_BG = {
    'summary':    IMGS['arch1'],
    'ficha':      IMGS['arch2'],
    'commercial': IMGS['arch3'],
    'location':   IMGS['arch4'],
    'services':   IMGS['arch5'],
    'investment': IMGS['arch6'],
    'advantages': IMGS['arch1'],
    'value':      IMGS['arch2'],
    'strategic':  IMGS['arch3'],
    'lifestyle':  IMGS['arch4'],
    'gallery':    IMGS['arch5'],
}

def _zone_imgs(data, lang):
    srv = (data.get('servicios_cerca&ntilde;os') or '').lower()
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
        if len(pool) >= 6: break
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
    --ink:       #1e2f40;
    --ink-soft:  #374f66;
    --slate:     #4d6275;
    --pearl:     #fbf8f2;
    --ivory:     #fffcf5;
    --mist:      #eef5f8;
    --sky:       #dceef6;
    --champagne: #c9a84c;
    --champ-soft:#e8cc80;
    --bronze:    #8a6828;
    --cream:     #f5ecd7;
    --warm:      #fdf4e3;
    --line:      rgba(30,47,64,0.14);
    --line-gold: rgba(201,168,76,0.50);
}

body {
    font-family: 'Inter', Arial, sans-serif;
    background: var(--pearl);
    color: var(--ink);
    width: 210mm;
    font-size: 10pt;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
}

.page {
    position: relative;
    width: 210mm;
    min-height: 297mm;
    overflow: hidden;
    page-break-after: always;
    background:
        radial-gradient(circle at 88% 6%, rgba(201,168,76,0.15), transparent 30%),
        radial-gradient(circle at 6% 92%, rgba(183,217,232,0.22), transparent 34%),
        linear-gradient(135deg, var(--ivory) 0%, var(--pearl) 46%, var(--mist) 100%);
    isolation: isolate;
}
.page:last-child { page-break-after: auto; }

/* City overlay — igual que el HTML original */
.city-overlay {
    position: absolute;
    inset: 0;
    pointer-events: none;
    z-index: 1;
}
.city-overlay::before {
    content: "";
    position: absolute;
    inset: 0;
    opacity: 0.22;
    mix-blend-mode: multiply;
    filter: grayscale(70%) contrast(130%) brightness(0.85);
    -webkit-mask-image: linear-gradient(90deg, transparent 0%, rgba(0,0,0,0.7) 22%, rgba(0,0,0,1) 100%);
    mask-image: linear-gradient(90deg, transparent 0%, rgba(0,0,0,0.7) 22%, rgba(0,0,0,1) 100%);
    background-size: cover;
    background-position: center;
}
.city-overlay.bg-one::before {
    background-image:
        linear-gradient(180deg, rgba(7,12,22,0.25), rgba(7,12,22,0.07)),
        url('https://images.unsplash.com/photo-1518005020951-eccb494ad742?fm=jpg&q=80&w=1600');
}
.city-overlay.bg-two::before {
    background-image:
        linear-gradient(180deg, rgba(7,12,22,0.25), rgba(7,12,22,0.10)),
        url('https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?fm=jpg&q=80&w=1600');
}

/* Double gold border frames */
.page::before {
    content: '';
    position: absolute;
    inset: 9mm;
    border: 1px solid rgba(201,168,76,0.40);
    pointer-events: none;
    z-index: 9;
}
.page::after {
    content: '';
    position: absolute;
    inset: 12.5mm;
    border: 1px solid rgba(30,47,64,0.08);
    pointer-events: none;
    z-index: 9;
}
.no-frame::before, .no-frame::after { display: none; }

.decor-grid {
    position: absolute;
    inset: 0;
    z-index: 1;
    pointer-events: none;
    opacity: 0.10;
    background:
        linear-gradient(90deg, rgba(30,47,64,0.08) 1px, transparent 1px),
        linear-gradient(180deg, rgba(30,47,64,0.06) 1px, transparent 1px);
    background-size: 20mm 20mm;
}

.decor-orbit {
    position: absolute;
    z-index: 2;
    right: -20mm;
    top: 18mm;
    width: 108mm;
    height: 108mm;
    border-radius: 50%;
    border: 1px solid rgba(201,168,76,0.20);
    pointer-events: none;
}
.decor-orbit::after {
    content: '';
    position: absolute;
    inset: 16mm;
    border-radius: 50%;
    border: 1px solid rgba(30,47,64,0.07);
}

.inner {
    position: relative;
    z-index: 4;
    padding: 13mm 15mm 13mm;
    min-height: 297mm;
}

/* ── TYPOGRAPHY ── */
h1 {
    font-family: 'Cormorant Garamond', Georgia, serif;
    font-size: 40pt;
    line-height: 0.92;
    letter-spacing: -0.04em;
    font-weight: 700;
    color: var(--ink);
}
h2 {
    font-family: 'Cormorant Garamond', Georgia, serif;
    font-size: 25pt;
    line-height: 1.06;
    letter-spacing: -0.03em;
    font-weight: 700;
    color: var(--ink);
    max-width: 155mm;
}
h3 {
    font-family: 'Cormorant Garamond', Georgia, serif;
    font-size: 16pt;
    line-height: 1.15;
    letter-spacing: -0.02em;
    font-weight: 700;
    color: inherit;
}
h4 {
    font-family: 'Inter', Arial, sans-serif;
    font-size: 7.5pt;
    letter-spacing: 0.20em;
    text-transform: uppercase;
    font-weight: 800;
    color: var(--bronze);
    margin-bottom: 2mm;
}
.lead {
    font-family: 'Inter', Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.62;
    letter-spacing: -0.01em;
    color: var(--ink-soft);
    margin-bottom: 5mm;
    font-weight: 400;
}
.text {
    font-family: 'Inter', Arial, sans-serif;
    font-size: 9.5pt;
    line-height: 1.62;
    color: var(--slate);
    margin-top: 2mm;
    font-weight: 600;
}
.eyebrow {
    font-family: 'Inter', Arial, sans-serif;
    font-size: 8pt;
    letter-spacing: 0.24em;
    text-transform: uppercase;
    font-weight: 900;
    color: var(--bronze);
    margin-bottom: 3mm;
}
.micro {
    font-family: 'Inter', Arial, sans-serif;
    font-size: 7pt;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    font-weight: 700;
    color: rgba(30,47,64,0.48);
}

.gold-line {
    width: 24mm;
    height: 1.4mm;
    border-radius: 99px;
    background: linear-gradient(90deg, var(--champagne), var(--champ-soft), var(--bronze));
    margin-bottom: 4mm;
}
.divider {
    width: 100%;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(201,168,76,0.60), rgba(30,47,64,0.10), transparent);
    margin: 5mm 0;
}

.section-head {
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 8mm;
    align-items: start;
    padding-top: 4mm;
    border-top: 1.5px solid var(--line-gold);
    margin-bottom: 7mm;
}
.section-num {
    font-family: 'Inter', Arial, sans-serif;
    font-size: 7pt;
    letter-spacing: 0.20em;
    text-transform: uppercase;
    font-weight: 900;
    color: rgba(30,47,64,0.38);
    padding: 2.5mm 3mm;
    border: 1px solid rgba(201,168,76,0.42);
    background: rgba(255,255,255,0.70);
    white-space: nowrap;
}

.footer {
    position: absolute;
    left: 17mm;
    right: 17mm;
    bottom: 5.5mm;
    display: flex;
    justify-content: space-between;
    font-family: 'Inter', Arial, sans-serif;
    font-size: 7pt;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    font-weight: 700;
    color: rgba(30,47,64,0.42);
    padding-top: 2mm;
    border-top: 1px solid rgba(201,168,76,0.28);
}

.g2 { display: grid; grid-template-columns: 1fr 1fr; gap: 4mm; }
.g3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 3.5mm; }
.g4 { display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 3mm; }

/* ── CARDS — colores exactos del HTML original ── */
.card {
    position: relative;
    padding: 5mm;
    border: 1px solid rgba(36,52,71,0.15);
    background: linear-gradient(135deg, rgba(255,255,255,0.96), rgba(251,247,239,0.92));
    overflow: hidden;
}
.card::before {
    content: '';
    position: absolute;
    left: 0; top: 0;
    width: 1.1mm; height: 100%;
    background: linear-gradient(180deg, var(--champagne), rgba(215,181,109,0.10));
}
.card h3 { color: var(--ink); }
.card h4 { color: var(--bronze); }
.card .text { color: var(--navy); font-size: 9pt; font-weight: 600; }

.card.stone {
    background: linear-gradient(135deg, rgba(239,231,218,0.98), rgba(255,250,242,0.96));
    border-color: rgba(155,118,56,0.22);
}
.card.sky {
    background: linear-gradient(135deg, rgba(237,245,248,0.98), rgba(220,238,246,0.96));
    border-color: rgba(85,132,156,0.22);
}
.card.sky h4 { color: #2d5468; }
.card.sky .text { color: #1e3d52; font-weight: 600; }

.card.dark {
    background: linear-gradient(135deg, #31465d 0%, #405a72 58%, #b99755 160%);
    border: none;
    color: #fff;
}
.card.dark::before { background: linear-gradient(180deg, var(--champ-soft), var(--champagne)); }
.card.dark .text { color: rgba(255,255,255,0.82); }
.card.dark h4    { color: var(--champ-soft); }
.card.dark h3    { color: #fff; }

.card.gold {
    background: linear-gradient(135deg, #d9bb74 0%, #b98f45 52%, #f2dfaa 130%);
    border: none;
    color: #fff;
}
.card.gold::before { background: rgba(255,255,255,0.45); }
.card.gold .text { color: rgba(255,255,255,0.88); }
.card.gold h4    { color: #fff7df; }

/* KPI boxes */
.kpi-row { display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 3.5mm; margin: 4mm 0; }
.kpi {
    min-height: 28mm;
    padding: 4mm;
    background: linear-gradient(135deg, rgba(255,255,255,0.97), rgba(230,242,248,0.95));
    border: 1.5px solid rgba(36,52,71,0.22);
    box-shadow: 0 1px 4px rgba(30,47,64,0.08);
}
.kpi.dark {
    background: linear-gradient(135deg, rgba(49,70,93,0.96), rgba(64,90,114,0.90));
    border: none;
    color: #fff;
}
.kpi .num {
    font-family: 'Cormorant Garamond', Georgia, serif;
    font-size: 24pt;
    line-height: 1;
    letter-spacing: -0.04em;
    font-weight: 700;
    color: var(--navy);
}
.kpi.dark .num { color: var(--champ-soft); }
.kpi .lbl {
    margin-top: 3mm;
    font-family: 'Inter', Arial, sans-serif;
    font-size: 7.5pt;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    font-weight: 800;
    color: rgba(30,47,64,0.75);
}
.kpi.dark .lbl { color: rgba(255,255,255,0.90); }

.note {
    padding: 5mm 6mm;
    background: linear-gradient(135deg, var(--warm), rgba(241,229,186,0.28));
    border-left: 2.5mm solid var(--champagne);
    font-family: 'Inter', Arial, sans-serif;
    font-size: 9.5pt;
    line-height: 1.58;
    color: var(--ink);
    margin: 5mm 0;
}
.note strong { color: var(--ink); }

.dtable {
    width: 100%;
    border-collapse: collapse;
    background: rgba(255,252,245,0.95);
    border: 1px solid rgba(201,168,76,0.25);
}
.dtable th {
    text-align: left;
    padding: 3.5mm 4mm;
    font-family: 'Inter', Arial, sans-serif;
    font-size: 7pt;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    font-weight: 800;
    color: var(--bronze);
    background: linear-gradient(90deg, rgba(240,232,214,0.60), rgba(237,245,248,0.60));
    border-bottom: 1px solid rgba(201,168,76,0.25);
}
.dtable td {
    padding: 3mm 4mm;
    font-family: 'Inter', Arial, sans-serif;
    font-size: 9.5pt;
    line-height: 1.46;
    color: var(--ink-soft);
    border-top: 1px solid rgba(201,168,76,0.14);
    vertical-align: top;
}
.dtable td:first-child {
    width: 38%;
    font-weight: 700;
    color: var(--ink);
}

.img-box {
    overflow: hidden;
    border: 1px solid rgba(30,47,64,0.12);
}
.img-box img { display: block; width: 100%; object-fit: cover; }
.img-cap {
    padding: 2.5mm 3.5mm;
    background: rgba(255,252,245,0.96);
    font-family: 'Inter', Arial, sans-serif;
    font-size: 7pt;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    font-weight: 700;
    color: var(--ink);
    border-top: 1px solid rgba(201,168,76,0.28);
}

/* Room grid */
.room-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 3mm; margin: 3mm 0; }
.room-item { border: 1px solid rgba(201,168,76,0.25); overflow: hidden; background: var(--warm); }
.room-item img { display: block; width: 100%; height: 30mm; object-fit: cover; }
.room-cap {
    padding: 2mm 3mm 1.5mm;
    background: linear-gradient(135deg, var(--warm), var(--ivory));
    font-family: 'Inter', Arial, sans-serif;
    font-size: 7pt;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    font-weight: 800;
    color: var(--bronze);
    border-top: 1px solid rgba(201,168,76,0.25);
}
.room-desc {
    padding: 2.5mm 3mm 3mm;
    font-family: 'Inter', Arial, sans-serif;
    font-size: 8.5pt;
    line-height: 1.50;
    color: var(--navy);
    font-weight: 500;
    margin: 0;
    background: rgba(255,255,255,0.82);
}

.vgallery { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 3.5mm; margin: 4mm 0; }
.vitem { border: 1px solid rgba(201,168,76,0.22); overflow: hidden; background: var(--warm); }
.vitem img { display: block; width: 100%; height: 34mm; object-fit: cover; }
.vcap {
    padding: 2mm 3mm;
    background: linear-gradient(135deg, var(--warm), var(--ivory));
    font-family: 'Inter', Arial, sans-serif;
    font-size: 7pt;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    font-weight: 700;
    color: var(--ink);
}

.bars-block { display: flex; flex-direction: column; gap: 3mm; }

.adv {
    display: grid;
    grid-template-columns: 10mm 1fr;
    gap: 3.5mm;
    padding: 4.5mm;
    background: linear-gradient(135deg, var(--warm), var(--pearl));
    border: 1px solid rgba(201,168,76,0.28);
    border-left: 2px solid var(--champagne);
    align-items: start;
}
.adv-n {
    width: 9mm; height: 9mm; border-radius: 50%;
    background: linear-gradient(135deg, var(--champagne), var(--bronze));
    color: #fff;
    font-family: 'Inter', Arial, sans-serif;
    font-size: 7pt; font-weight: 900;
    text-align: center; line-height: 9mm; flex-shrink: 0;
}
.adv h3 { color: var(--ink); font-size: 14pt; }
.adv .text { color: var(--slate); }

.timeline { display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 4mm; margin: 5mm 0; }
.step {
    padding: 4.5mm;
    background: linear-gradient(135deg, var(--warm), var(--pearl));
    border: 1px solid rgba(201,168,76,0.28);
}
.step-n {
    font-family: 'Cormorant Garamond', Georgia, serif;
    font-size: 20pt; line-height: 1;
    color: rgba(201,168,76,0.70); font-weight: 700; margin-bottom: 3mm;
}
.step h3 { font-size: 13pt; color: var(--ink); }
.step .text { color: var(--slate); }

.photo-strip { display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 4mm; margin: 4mm 0; }
.photo-stack { display: grid; gap: 4mm; grid-template-rows: 1fr 1fr; }

/* Service analysis cards */
.svc-card {
    padding: 4mm 5mm;
    background: linear-gradient(135deg, var(--warm), var(--ivory));
    border: 1px solid rgba(201,168,76,0.25);
    border-top: 2.5px solid var(--champagne);
}
.svc-card h4 { color: var(--bronze); margin-bottom: 1.5mm; }
.svc-card .text { color: var(--slate); font-size: 8.5pt; }
.svc-score {
    display: inline-block;
    padding: 1.5mm 3mm;
    background: var(--champagne);
    color: #fff;
    font-family: 'Inter', Arial, sans-serif;
    font-size: 8pt; font-weight: 800;
    border-radius: 2mm;
    margin-top: 2.5mm;
}

/* Cover */
.cover { background: #08121f; color: #fff; }
.cover-photo { position: absolute; inset: 0; z-index: 1; }
.cover-photo img { width: 100%; height: 100%; object-fit: cover; opacity: 0.42; }
.cover-overlay {
    position: absolute; inset: 0; z-index: 2;
    background:
        linear-gradient(100deg, rgba(4,10,20,0.92) 0%, rgba(10,20,36,0.55) 55%, rgba(10,20,36,0.18) 100%),
        linear-gradient(180deg, rgba(4,10,20,0.08) 0%, rgba(4,10,20,0.68) 100%);
}
.cover-inner {
    position: relative; z-index: 5;
    padding: 17mm 19mm 15mm;
    min-height: 297mm;
    display: flex; flex-direction: column; justify-content: space-between;
}
.topbar {
    display: flex; justify-content: space-between; align-items: flex-start;
    font-family: 'Inter', Arial, sans-serif;
    font-size: 7pt; letter-spacing: 0.22em; text-transform: uppercase;
    color: rgba(255,255,255,0.65); font-weight: 700;
}
.brand { display: flex; align-items: center; gap: 3mm; }
.brand-mark {
    width: 11mm; height: 11mm;
    border: 1px solid rgba(201,168,76,0.70);
    display: flex; align-items: center; justify-content: center;
    color: var(--champ-soft); background: rgba(255,255,255,0.07);
    font-family: 'Cormorant Garamond', Georgia, serif;
    font-size: 10pt; font-weight: 700;
}
.cover-box {
    width: 152mm;
    padding: 7mm 9mm;
    border: 1px solid rgba(201,168,76,0.36);
    background: rgba(6,14,26,0.55);
}
.cover-kicker {
    display: inline-block;
    padding: 2mm 4mm;
    border: 1px solid rgba(201,168,76,0.54);
    background: rgba(255,255,255,0.07);
    font-family: 'Inter', Arial, sans-serif;
    font-size: 7pt; letter-spacing: 0.24em; text-transform: uppercase;
    font-weight: 800; color: var(--champ-soft); margin-bottom: 5mm;
}
.cover h1 { color: #fff; font-size: 42pt; line-height: 0.92; }
.cover-loc { display: block; color: var(--champ-soft); font-style: italic; }
.cover-copy {
    margin-top: 6mm;
    font-family: 'Inter', Arial, sans-serif;
    font-size: 11pt; line-height: 1.55;
    color: rgba(255,255,255,0.86); max-width: 122mm; font-weight: 400;
}
.cover-bottom { display: grid; grid-template-columns: 80mm 1fr; gap: 7mm; align-items: end; }
.price-panel {
    padding: 5.5mm 6mm;
    border: 1px solid rgba(201,168,76,0.64);
    background: rgba(255,255,255,0.95);
}
.price-lbl {
    font-family: 'Inter', Arial, sans-serif;
    font-size: 7pt; letter-spacing: 0.22em; text-transform: uppercase;
    color: var(--bronze); font-weight: 800; margin-bottom: 2mm;
}
.price-val {
    font-family: 'Cormorant Garamond', Georgia, serif;
    font-size: 24pt; line-height: 1; font-weight: 700; color: var(--ink);
}
.tags { display: flex; flex-wrap: wrap; gap: 2mm; justify-content: flex-end; }
.tag {
    padding: 2.5mm 3.5mm;
    border: 1px solid rgba(201,168,76,0.48);
    background: rgba(255,255,255,0.11);
    font-family: 'Inter', Arial, sans-serif;
    font-size: 7pt; letter-spacing: 0.14em; text-transform: uppercase;
    font-weight: 700; color: rgba(255,255,255,0.90); white-space: nowrap;
}

/* Final CTA */
.final { background: #08121f; color: #fff; position: relative; }
.final-photo { position: absolute; inset: 0; z-index: 1; }
.final-photo img { width: 100%; height: 100%; object-fit: cover; opacity: 0.32; }
.final-overlay {
    position: absolute; inset: 0; z-index: 2;
    background: linear-gradient(100deg, rgba(4,10,20,0.92) 0%, rgba(10,20,36,0.65) 55%, rgba(10,20,36,0.22) 100%);
}
.final-inner {
    position: relative; z-index: 5;
    padding: 17mm 19mm 15mm;
    min-height: 297mm;
    display: flex; flex-direction: column; justify-content: space-between;
}
.final-title {
    font-family: 'Cormorant Garamond', Georgia, serif;
    font-size: 32pt; line-height: 1.05; font-weight: 700;
    color: #fff; max-width: 150mm; margin-bottom: 5mm;
}
.contact-panel {
    padding: 5.5mm 6mm;
    border: 1px solid rgba(201,168,76,0.46);
    background: rgba(255,252,245,0.96);
}
.contact-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 5mm; margin-top: 5mm; }
.contact-item { border-left: 1.5px solid rgba(201,168,76,0.70); padding-left: 3mm; }
.contact-item span {
    display: block;
    font-family: 'Inter', Arial, sans-serif;
    font-size: 7pt; letter-spacing: 0.18em; text-transform: uppercase;
    color: rgba(30,47,64,0.54); font-weight: 700; margin-bottom: 1.5mm;
}
.contact-item strong {
    display: block;
    font-family: 'Inter', Arial, sans-serif;
    font-size: 10pt; color: var(--ink); font-weight: 700;
}
"""


# ─── PAGE / SECTION HELPERS ───────────────────────────────────────────────────

_BG_CYCLE = ['bg-one', 'bg-two', 'bg-one', 'bg-two', 'bg-one', 'bg-two',
             'bg-one', 'bg-two', 'bg-one', 'bg-two', 'bg-one', 'bg-two']
_bg_counter = [0]

def _page(content, cls='', orbit=True, bg_key=None):
    orbit_html = '<div class="decor-orbit"></div>' if orbit else ''
    bg_variant = _BG_CYCLE[_bg_counter[0] % len(_BG_CYCLE)]
    _bg_counter[0] += 1
    return (
        f'<section class="page {cls}">'
        f'<div class="decor-grid"></div>'
        f'<div class="city-overlay {bg_variant}"></div>'
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


# ─── COVER ────────────────────────────────────────────────────────────────────

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
        copy = (f"Inmueble premium en {barrio} seleccionado por su posicionamiento excepcional, "
                f"calidad diferencial y potencial de rentabilidad destacado.") if tipo_dossier == 'inversores' else \
               f"Tu nuevo hogar en {barrio} — una oportunidad unica de vivir con calidad de vida superior en {ciudad}."
        dossier_lbl = 'Dossier Privado de Inversion' if tipo_dossier == 'inversores' else 'Dossier Premium Residencial'
        precio_lbl = 'Precio de salida'; acceso = 'Acceso Reservado'
    else:
        kicker = f"{tipo_lbl} · Selected Opportunity"
        copy = (f"Premium property in {barrio} selected for exceptional positioning, "
                f"differential quality and outstanding return potential.") if tipo_dossier == 'inversores' else \
               f"Your new home in {barrio} — a unique opportunity to live with superior quality of life in {ciudad}."
        dossier_lbl = 'Private Investment Dossier' if tipo_dossier == 'inversores' else 'Premium Residential Dossier'
        precio_lbl = 'Asking price'; acceso = 'Restricted Access'

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
        f'      <p class="text" style="margin-top:2mm; color:#52657a; font-size:9pt;">{subtexto}</p>'
        f'    </div>'
        f'    <div>'
        f'      <div class="tags">{tags_html}</div>'
        f'      <p class="micro" style="text-align:right; margin-top:4mm; color:rgba(255,255,255,0.54);">{agente} &middot; {ciudad} &middot; {anyo}</p>'
        f'    </div>'
        f'  </div>'
        f'</div>'
        f'</section>'
    )


# ─── EXECUTIVE SUMMARY ────────────────────────────────────────────────────────

def _build_summary(data, content, lang, n):
    es = lang == 'es'
    fin = content['financials']
    ps = content['premium_score']
    ls = content['loc_scores']
    tipo_dossier = data.get('tipo_dossier', 'inversores')
    ciudad = _s(data.get('ciudad'), '')

    paras = [p.strip() for p in content['exec_summary'].split('\n\n') if p.strip()]
    lead = paras[0] if paras else ''
    body2 = paras[1] if len(paras) > 1 else ''

    if tipo_dossier == 'inversores':
        kpis = [
            (_pct(fin.get('yield_bruto', 0)), 'Yield Bruta' if es else 'Gross Yield', True),
            (_pct(fin.get('roi_5y', 0)), 'ROI 5 Anos' if es else '5Y ROI', False),
            (f"{ps}/10", 'Score Premium', False),
            (f"{ls.get('atractivo_inversor', 7)}/10", 'Atractivo' if es else 'Attractiveness', True),
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

    # Enrich investor profile with extra data-driven characteristics
    dem = _s(data.get('demanda_alquiler', ''))
    rev = _s(data.get('revalorizacion', ''))
    yb = fin.get('yield_bruto', 0)
    if es:
        sh_ey = 'Resumen Ejecutivo'; sh_tt = 'Una oportunidad inmobiliaria con analisis de criterio institucional.'
        c1_lbl = 'Propuesta de Valor'; c2_lbl = 'Perfil Inversor' if tipo_dossier == 'inversores' else 'Comprador Ideal'
        t_lbl = 'Tesis de inversion'
        dem_txt = {'muy_alta':'demanda de alquiler muy alta — minima vacancia esperada','alta':'demanda de alquiler alta y sostenida','media':'demanda moderada y estable en la zona','baja':'mercado con selectividad — activo de nicho'}.get(dem,'demanda activa en la zona')
        rev_txt = {'muy_alto':'potencial de revalorizacion muy alto a largo plazo','alto':'revalorizacion estimada superior a la media de mercado','moderado':'apreciacion moderada y estable del activo','bajo':'activo de renta con menor componente especulativo'}.get(rev,'buenas perspectivas de revalorizacion')
        yb_txt = f'Yield bruta objetivo del {yb:.1f}%. ' if yb else ''
        inv_extra = f' {yb_txt}Zona con {dem_txt}. Perspectiva: {rev_txt}.'
    else:
        sh_ey = 'Executive Summary'; sh_tt = 'A real estate opportunity with institutional-grade analysis.'
        c1_lbl = 'Value Proposition'; c2_lbl = 'Investor Profile' if tipo_dossier == 'inversores' else 'Ideal Buyer'
        t_lbl = 'Investment thesis'
        dem_txt = {'muy_alta':'very high rental demand — minimal expected vacancy','alta':'high and sustained rental demand','media':'moderate and stable demand in the area','baja':'selective market — niche asset'}.get(dem,'active demand in the area')
        rev_txt = {'muy_alto':'very high long-term appreciation potential','alto':'estimated appreciation above market average','moderado':'moderate and stable asset appreciation','bajo':'income asset with lower speculative component'}.get(rev,'good appreciation prospects')
        yb_txt = f'Target gross yield of {yb:.1f}%. ' if yb else ''
        inv_extra = f' {yb_txt}Area with {dem_txt}. Outlook: {rev_txt}.'

    perf_c_full = perf_c + inv_extra if perf_c else inv_extra

    body2_html = f'<p class="text" style="margin-bottom:3mm;">{body2}</p>' if body2 else ''

    return _page(
        f'<div class="inner">'
        f'{_sh(sh_ey, sh_tt, n)}'
        f'<p class="lead">{lead}</p>'
        f'{body2_html}'
        f'<div class="kpi-row">{kpis_html}</div>'
        f'<div class="divider"></div>'
        f'<div class="g2">'
        f'{_card(c1_lbl, "", prop_val, "stone")}'
        f'{_card(c2_lbl, "", perf_c_full, "dark")}'
        f'</div>'
        f'<div class="note"><strong>{t_lbl}:</strong> {tesis}</div>'
        f'{_foot(sh_ey, ciudad)}'
        f'</div>',
        bg_key='summary'
    )


# ─── TECHNICAL SHEET ──────────────────────────────────────────────────────────

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
    hero_src = (_photo_b64(fotos[1]) or _photo_b64(fotos[0])) if len(fotos) > 1 else (_photo_b64(fotos[0]) if fotos else '')
    if not hero_src: hero_src = IMGS['interior1']

    rows = []
    def row(k, v):
        if v and v not in ('N/D', '—'):
            rows.append(f'<tr><td>{k}</td><td>{v}</td></tr>')

    if es:
        sh_ey = 'Ficha Tecnica'; sh_tt = 'Datos esenciales del activo inmobiliario.'
        row('Direccion', _s(data.get('direccion')))
        row('Ciudad / Barrio', f"{ciudad} / {barrio}" if barrio != ciudad else ciudad)
        row('Codigo Postal', _s(data.get('cp')))
        row('Tipo de activo', tipo_lbl)
        row('Precio', _eur(data.get('precio_venta')))
        row('Sup. construida', f"{_s(data.get('metros_construidos'))} m2")
        if data.get('metros_utiles'): row('Sup. util', f"{_s(data.get('metros_utiles'))} m2")
        if data.get('dormitorios'): row('Dormitorios / Ba&ntilde;os', f"{_s(data.get('dormitorios'))} / {_s(data.get('banos'))}")
        row('Ano construccion', _s(data.get('anyo_construccion')))
        row('Estado', estado_lbl)
        row('Cert. Energetico', _s(data.get('certificado_energetico')))
        row('Modalidad', accion)
        row('Equipamiento', feats_str)
    else:
        sh_ey = 'Technical Sheet'; sh_tt = 'Essential data for the real estate asset.'
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
        f'<div class="img-box" style="margin-bottom:4mm;">'
        f'<img src="{hero_src}" style="height:52mm; width:100%; object-fit:cover;" alt=""/>'
        f'<div class="img-cap">{_s(data.get("direccion"), barrio + " &middot; " + ciudad)}</div>'
        f'</div>'
        f'<table class="dtable"><tbody>{"".join(rows)}</tbody></table>'
        f'<div class="divider"></div>'
        f'<div class="g3">'
        f'{_card("Precio/m2" if es else "Price/m2", pm2_str, "Precio por metro cuadrado construido" if es else "Price per built m2", "stone")}'
        f'{_card("Media de zona" if es else "Area average", pm2z_str, "Precio medio de referencia en la zona" if es else "Reference area average price", "sky")}'
        f'{_card("Score Premium", f"{ps}/10", "Calidad y posicionamiento global" if es else "Overall quality and positioning", "dark")}'
        f'</div>'
        f'{_foot(sh_ey, ciudad)}'
        f'</div>',
        bg_key='ficha'
    )


# ─── COMMERCIAL DESCRIPTION (con habitaciones) ────────────────────────────────

def _build_commercial(data, content, lang, n):
    es = lang == 'es'
    fotos = data.get('foto_paths', [])
    ciudad = _s(data.get('ciudad'), '')
    barrio = _s(data.get('barrio')) or ciudad
    tipo_p = data.get('tipo_propiedad', '')
    m2 = _s(data.get('metros_construidos'))
    dorms = _s(data.get('dormitorios'))
    banos = _s(data.get('banos'))
    estado = data.get('estado', '')

    paras = [p.strip() for p in content['narrative'].split('\n\n') if p.strip()]
    lead = paras[0] if paras else ''
    body = ''.join(f'<p class="text" style="margin-bottom:2.5mm;">{p}</p>' for p in paras[1:2])

    # Room labels, descriptions and fallback images
    if es:
        sh_ey = 'Descripcion del Inmueble'; sh_tt = 'Cada espacio, presentado con criterio y detalle.'
        room_data = [
            ('Salon Principal',   'Amplio salon de estar con luz natural, distribucion diafana y acabados de calidad. Espacio ideal para la vida familiar y la representacion social.'),
            ('Cocina',            'Cocina funcional y bien equipada, con disposicion eficiente y materiales de calidad. Perfectamente integrada con el resto de la vivienda.'),
            ('Dormitorio Princ.', 'Dormitorio principal de generosas dimensiones, buena orientacion y armarios integrados. Ambiente tranquilo y confortable para el descanso.'),
            ('Ba&ntilde;o',       'Ba&ntilde;o completo con acabados cuidados, sanitarios de primera calidad y buena ventilacion. Estetica contemporanea y funcionalidad integral.'),
            ('Zona Exterior',     'Espacio exterior propio que amplia la superficie util y ofrece contacto directo con el exterior, la luz natural y el entorno.'),
            ('Zona Adicional',    'Espacio versatil susceptible de multiples usos: despacho, sala de estudio, sala de juegos o habitacion de invitados.'),
        ]
        estado_desc = {
            'nuevo': 'Inmueble a estrenar con acabados de primera calidad en todos sus espacios.',
            'excelente': 'Excelente estado de conservacion, listo para entrar a vivir sin actuacion alguna.',
            'bueno': 'Buen estado general con mantenimiento cuidado a lo largo de los a&ntilde;os.',
            'reformar': 'Con potencial de reforma — gran oportunidad de personalizacion y creacion de valor.',
            '': 'Calidades y acabados acordes al posicionamiento del activo en el mercado.'
        }.get(estado, '')
    else:
        sh_ey = 'Property Description'; sh_tt = 'Every space, presented with criterion and detail.'
        room_data = [
            ('Living Room',      'Spacious living room with natural light, open layout and quality finishes. Ideal for family life and social entertaining.'),
            ('Kitchen',          'Functional and well-equipped kitchen with efficient layout and quality materials. Perfectly integrated with the rest of the home.'),
            ('Master Bedroom',   'Generously sized master bedroom with good orientation and built-in wardrobes. Peaceful and comfortable environment for rest.'),
            ('Bathroom',         'Full bathroom with careful finishes, first-class sanitary ware and good ventilation. Contemporary aesthetics and comprehensive functionality.'),
            ('Exterior Area',    'Private exterior space that extends the usable area and offers direct contact with the outdoors, natural light and the surrounding environment.'),
            ('Additional Space', 'Versatile space suitable for multiple uses: office, study room, games room or guest bedroom according to the occupant\'s needs.'),
        ]
        estado_desc = {
            'nuevo': 'Brand new property with first-class finishes throughout all spaces.',
            'excelente': 'Excellent condition, ready for immediate occupation with no works needed.',
            'bueno': 'Good general condition with careful maintenance over the years.',
            'reformar': 'Renovation potential — great opportunity for personalisation and value creation.',
            '': 'Qualities and finishes in line with the asset\'s market positioning.'
        }.get(estado, '')

    room_fallbacks = [IMGS['living'], IMGS['kitchen'], IMGS['bedroom'], IMGS['bathroom'], IMGS['terrace'], IMGS['interior2']]

    def get_room_src(idx):
        if idx < len(fotos):
            s = _photo_b64(fotos[idx])
            if s: return s
        return room_fallbacks[idx % len(room_fallbacks)]

    # Build room grid — max 6 rooms (2 rows of 3) with descriptions below each image
    num_rooms = max(3, min(6, len(fotos) if fotos else 6))
    rooms_html = ''.join(
        f'<div class="room-item">'
        f'<img src="{get_room_src(i)}" alt="{room_data[i][0]}"/>'
        f'<div class="room-cap">{room_data[i][0]}</div>'
        f'<p class="room-desc">{room_data[i][1]}</p>'
        f'</div>'
        for i in range(num_rooms)
    )

    # Data chips
    chips = []
    if m2: chips.append(f"{m2} m2")
    if dorms and dorms != '0': chips.append(f"{dorms} {'dorm.' if es else 'bed.'}")
    if banos and banos != '0': chips.append(f"{banos} {'ban.' if es else 'bath.'}")
    chips_html = ' &nbsp;&middot;&nbsp; '.join(f'<strong>{c}</strong>' for c in chips)

    return _page(
        f'<div class="inner">'
        f'{_sh(sh_ey, sh_tt, n)}'
        f'<p class="lead">{lead}</p>'
        f'{body}'
        f'<div class="note" style="margin-bottom:4mm;">'
        f'{chips_html}'
        f'{"&nbsp;&nbsp;&middot;&nbsp;&nbsp;" + estado_desc if estado_desc and chips else estado_desc}'
        f'</div>'
        f'<div class="room-grid">{rooms_html}</div>'
        f'{_foot(sh_ey, ciudad)}'
        f'</div>',
        bg_key='commercial'
    )


# ─── LOCATION ANALYSIS ────────────────────────────────────────────────────────

def _build_location(data, content, lang, n):
    es = lang == 'es'
    ciudad = _s(data.get('ciudad'), '')
    barrio = _s(data.get('barrio')) or ciudad
    ls = content['loc_scores']
    paras = [p.strip() for p in content['zona_text'].split('\n\n') if p.strip()]
    lead = paras[0] if paras else ''
    body_paras = paras[1:3]
    body = ''.join(f'<p class="text" style="margin-bottom:2.5mm;">{p}</p>' for p in body_paras)

    if es:
        radar_labels = ['Conectividad', 'Transporte', 'Servicios', 'Comercios', 'Calidad', 'Potencial']
        sh_ey = 'Analisis de Ubicacion'; sh_tt = f'{ciudad} — multiplicador de valor y calidad de vida.'
        radar_lbl = 'Indice de Ubicacion'; bars_lbl = 'Puntuaciones por factor'
    else:
        radar_labels = ['Connectivity', 'Transport', 'Services', 'Commerce', 'Quality', 'Potential']
        sh_ey = 'Location Analysis'; sh_tt = f'{ciudad} — value and quality-of-life multiplier.'
        radar_lbl = 'Location Index'; bars_lbl = 'Factor scores'

    radar_values = [
        float(ls.get('conectividad', 7.5)),
        float(ls.get('transporte', 7.5)),
        float(ls.get('servicios', 7.5)),
        float(ls.get('comercios', 7.0)),
        float(ls.get('atractivo_residencial', 7.0)),
        float(ls.get('crecimiento', 7.5)),
    ]
    radar_svg = _svg_radar(radar_labels, radar_values, size=210)

    bar_items = list(zip(radar_labels, radar_values))
    bars_html = ''.join(_svg_bar(lbl, val, 10, 210) for lbl, val in bar_items)

    zone_imgs = _zone_imgs(data, lang)
    zone_html = ''.join(
        f'<div class="vitem"><img src="{u}" alt="{l}"/><div class="vcap">{l}</div></div>'
        for u, l in zone_imgs[:3]
    )

    return _page(
        f'<div class="inner">'
        f'{_sh(sh_ey, sh_tt, n)}'
        f'<div class="card stone" style="padding:4mm 5mm; margin-bottom:4mm;">'
        f'<p class="text" style="margin:0; font-weight:500; line-height:1.6;">{lead}</p>'
        f'{body}'
        f'</div>'
        f'<div class="g2" style="align-items:start; margin-bottom:4mm;">'
        f'  <div class="card sky" style="padding:4mm;">'
        f'    <h4>{radar_lbl}</h4>'
        f'    <div style="margin-top:3mm; display:flex; justify-content:center;">{radar_svg}</div>'
        f'  </div>'
        f'  <div class="card" style="padding:4mm;">'
        f'    <h4>{bars_lbl}</h4>'
        f'    <div class="bars-block" style="margin-top:3mm;">{bars_html}</div>'
        f'  </div>'
        f'</div>'
        f'<div class="vgallery" style="grid-template-columns:1fr 1fr 1fr; margin-top:3mm;">{zone_html}</div>'
        f'{_foot(sh_ey, ciudad)}'
        f'</div>',
        bg_key='location'
    )


# ─── SERVICES — análisis ampliado ─────────────────────────────────────────────

def _build_services(data, content, lang, n):
    es = lang == 'es'
    ciudad = _s(data.get('ciudad'), '')
    barrio = _s(data.get('barrio')) or ciudad
    srv_raw = (data.get('servicios_cerca&ntilde;os') or '').lower()
    ls = content['loc_scores']

    if es:
        sh_ey = 'Servicios e Infraestructura'; sh_tt = f'Todo lo que define la calidad de vida en {barrio}.'
        intro = (f"El entorno de {barrio} ofrece un ecosistema completo de servicios urbanos que potencia "
                 f"significativamente el valor del activo y la calidad de vida de sus ocupantes. "
                 f"A continuacion se analiza en detalle cada categoria de equipamiento.")

        # Build service analysis based on keywords
        svc_blocks = []

        # Transport
        transp_score = ls.get('transporte', 7.0)
        transp_detail = "Red de transporte publico con acceso directo a metro, bus y cercanias." if any(k in srv_raw for k in ['metro','bus','tren','renfe']) else "Buena conectividad viaria y acceso a transporte urbano."
        svc_blocks.append(('Transporte y Movilidad', transp_detail, f"{transp_score}/10"))

        # Education
        edu_detail = "Oferta educativa completa: colegios concertados y privados, con opciones de educacion infantil hasta universitaria en el entorno inmediato." if any(k in srv_raw for k in ['colegio','escuela','universidad']) else "Centros educativos accesibles en el area metropolitana."
        svc_blocks.append(('Educacion', edu_detail, f"{ls.get('servicios', 7.0)}/10"))

        # Healthcare
        health_detail = "Cobertura sanitaria de primer nivel con hospitales, clinicas privadas y farmacias en el radio cercano al inmueble." if any(k in srv_raw for k in ['hospital','clinica','salud','farmacia']) else "Servicios de salud publicos y privados accesibles en la zona."
        svc_blocks.append(('Servicios Sanitarios', health_detail, f"{min(10, float(ls.get('servicios', 7.0)) + 0.5):.1f}/10"))

        # Commerce
        com_detail = "Tejido comercial activo con supermercados, restaurantes y zonas de ocio en el entorno directo." if any(k in srv_raw for k in ['supermercado','comercio','restaurante','bar']) else "Zona con oferta comercial y hostelera variada en su radio de influencia."
        svc_blocks.append(('Comercio y Restauracion', com_detail, f"{ls.get('comercios', 7.0)}/10"))

        # Green spaces
        verde_detail = "Parques, jardines y zonas verdes accesibles a pie, que contribuyen a la calidad ambiental del entorno residencial." if any(k in srv_raw for k in ['parque','jardin','verde']) else "Espacios verdes urbanos en el area, contribuyendo al bienestar ambiental."
        svc_blocks.append(('Zonas Verdes', verde_detail, f"{ls.get('conectividad', 7.5):.1f}/10"))

        # Security / Urban quality
        svc_blocks.append(('Seguridad y Entorno', f"Barrio consolidado de {barrio} con perfil residencial estable, baja conflictividad y entorno urbano cuidado.", f"{ls.get('atractivo_residencial', 7.5):.1f}/10"))

        conclusion = (f"La dotacion global de servicios en {barrio} alcanza una puntuacion de {ls.get('servicios', 7.5)}/10, "
                      f"situando al inmueble en una zona de alta dotacion urbana que respalda tanto la calidad de vida "
                      f"de sus ocupantes como la solidez de la inversion a largo plazo.")
    else:
        sh_ey = 'Services & Infrastructure'; sh_tt = f'Everything that defines quality of life in {barrio}.'
        intro = (f"The surroundings of {barrio} offer a complete urban services ecosystem that significantly "
                 f"enhances the asset value and quality of life for its occupants. "
                 f"Below is a detailed analysis of each services category.")

        svc_blocks = []
        transp_score = ls.get('transporte', 7.0)
        transp_detail = "Public transport network with direct access to metro, bus and commuter rail." if any(k in srv_raw for k in ['metro','bus','train']) else "Good road connectivity and access to urban transport."
        svc_blocks.append(('Transport & Mobility', transp_detail, f"{transp_score}/10"))
        edu_detail = "Full educational offer: state and private schools, with options from nursery to university nearby." if any(k in srv_raw for k in ['school','college','university']) else "Educational centres accessible in the metropolitan area."
        svc_blocks.append(('Education', edu_detail, f"{ls.get('servicios', 7.0)}/10"))
        health_detail = "First-class healthcare with hospitals, private clinics and pharmacies in the property's close radius." if any(k in srv_raw for k in ['hospital','clinic','health','pharmacy']) else "Public and private health services accessible in the area."
        svc_blocks.append(('Healthcare', health_detail, f"{min(10, float(ls.get('servicios', 7.0)) + 0.5):.1f}/10"))
        com_detail = "Active commercial fabric with supermarkets, restaurants and leisure areas in the immediate vicinity." if any(k in srv_raw for k in ['supermarket','commerce','restaurant']) else "Area with varied commercial and hospitality offer in its radius of influence."
        svc_blocks.append(('Commerce & Dining', com_detail, f"{ls.get('comercios', 7.0)}/10"))
        verde_detail = "Parks, gardens and green areas walkable from the property, contributing to environmental quality." if any(k in srv_raw for k in ['park','garden','green']) else "Urban green spaces in the area, contributing to environmental wellbeing."
        svc_blocks.append(('Green Spaces', verde_detail, f"{ls.get('conectividad', 7.5):.1f}/10"))
        svc_blocks.append(('Safety & Urban Quality', f"Consolidated neighbourhood of {barrio} with stable residential profile, low conflict and well-maintained urban environment.", f"{ls.get('atractivo_residencial', 7.5):.1f}/10"))

        conclusion = (f"The global services provision in {barrio} reaches a score of {ls.get('servicios', 7.5)}/10, "
                      f"placing the property in a high urban provision area that supports both the occupants' quality of life "
                      f"and the long-term investment solidity.")

    svc_cards_html = ''.join(
        f'<div class="svc-card">'
        f'<h4>{lbl}</h4>'
        f'<p class="text">{desc}</p>'
        f'<div class="svc-score">{score}</div>'
        f'</div>'
        for lbl, desc, score in svc_blocks
    )

    svc_imgs = _service_imgs(lang)
    imgs_html = ''.join(
        f'<div class="vitem"><img src="{u}" alt="{l}"/><div class="vcap">{l}</div></div>'
        for u, l in svc_imgs
    )

    return _page(
        f'<div class="inner">'
        f'{_sh(sh_ey, sh_tt, n)}'
        f'<p class="lead">{intro}</p>'
        f'<div class="g3" style="margin-bottom:4mm;">{svc_cards_html}</div>'
        f'<div class="vgallery" style="margin-bottom:4mm;">{imgs_html}</div>'
        f'<div class="note">{conclusion}</div>'
        f'{_foot(sh_ey, ciudad)}'
        f'</div>',
        bg_key='services'
    )


# ─── INVESTMENT ANALYSIS ──────────────────────────────────────────────────────

def _build_investment(data, content, lang, n):
    es = lang == 'es'
    fin = content['financials']
    ciudad = _s(data.get('ciudad'), '')
    paras = [p.strip() for p in content['financial_text'].split('\n\n') if p.strip()]
    lead = paras[0] if paras else ''
    body = ''.join(f'<p class="text" style="margin-bottom:2mm;">{p}</p>' for p in paras[1:2])

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

    yb_float = float(yb) if yb else 0
    yn_float = float(yn) if yn else 0
    roi_float = float(roi) if roi else 0
    donut1 = _svg_donut(min(yb_float * 10, 100), f"{yb_float:.1f}%", 96)
    donut2 = _svg_donut(min(yn_float * 10, 100), f"{yn_float:.1f}%", 96, '#8a6828')
    donut3 = _svg_donut(min(roi_float * 3, 100),  f"{roi_float:.1f}%", 96, '#1e3248')

    if es:
        sh_ey = 'Escenario de Inversion'; sh_tt = 'Potencial financiero y logica de retorno del activo.'
        rows = [
            ('Precio de adquisicion', _eur(precio)),
            ('Reforma estimada', _eur(reforma) if reforma else 'No necesaria'),
            ('Inversion total', _eur(inv_total)),
            ('Ingresos brutos anuales', _eur(ing) if ing else 'Pendiente'),
            ('Gastos operativos', _eur(gastos_total) if gastos_total else '—'),
            ('Ingresos netos anuales', _eur(ing_n) if ing_n else '—'),
            ('Rentabilidad neta anual', _pct(yn) if yn else '—'),
        ]
        d1l = 'Yield Bruta'; d2l = 'Yield Neta'; d3l = 'ROI 5 Anos'
        nota = (f"Escenario calculado con {_s(data.get('ocupacion','90'))}% de ocupacion y revalorizacion "
                f"estimada del {_pct(rev)}/ano. Datos de caracter orientativo — revisar con asesor financiero.")
    else:
        sh_ey = 'Investment Scenario'; sh_tt = 'Financial potential and asset return rationale.'
        rows = [
            ('Acquisition price', _eur(precio)),
            ('Estimated renovation', _eur(reforma) if reforma else 'Not needed'),
            ('Total investment', _eur(inv_total)),
            ('Annual gross income', _eur(ing) if ing else 'TBD'),
            ('Operating costs', _eur(gastos_total) if gastos_total else '—'),
            ('Annual net income', _eur(ing_n) if ing_n else '—'),
            ('Annual net return', _pct(yn) if yn else '—'),
        ]
        d1l = 'Gross Yield'; d2l = 'Net Yield'; d3l = '5Y ROI'
        nota = (f"Scenario at {_s(data.get('ocupacion','90'))}% occupancy and estimated {_pct(rev)}/yr appreciation. "
                f"Indicative data — review with a financial advisor.")

    rows_html = ''.join(f'<tr><td>{k}</td><td>{v}</td></tr>' for k, v in rows if v not in ('—',''))

    donuts_html = (
        f'<div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:4mm; margin:5mm 0;">'
        f'  <div style="text-align:center; padding:5mm; background:linear-gradient(135deg,var(--warm),var(--pearl)); border:1px solid rgba(201,168,76,0.28);">'
        f'    {donut1}<div class="micro" style="margin-top:2.5mm;">{d1l}</div></div>'
        f'  <div style="text-align:center; padding:5mm; background:linear-gradient(135deg,var(--warm),var(--pearl)); border:1px solid rgba(201,168,76,0.28);">'
        f'    {donut2}<div class="micro" style="margin-top:2.5mm;">{d2l}</div></div>'
        f'  <div style="text-align:center; padding:5mm; background:linear-gradient(135deg,var(--warm),var(--pearl)); border:1px solid rgba(201,168,76,0.28);">'
        f'    {donut3}<div class="micro" style="margin-top:2.5mm;">{d3l}</div></div>'
        f'</div>'
    )

    return _page(
        f'<div class="inner">'
        f'{_sh(sh_ey, sh_tt, n)}'
        f'<p class="lead">{lead}</p>'
        f'{body}'
        f'<div class="divider"></div>'
        f'<table class="dtable"><tbody>{rows_html}</tbody></table>'
        f'{donuts_html}'
        f'<div class="note">{nota}</div>'
        f'{_foot(sh_ey, "Estimaciones orientativas" if es else "Indicative estimates")}'
        f'</div>',
        bg_key='investment'
    )


# ─── COMPETITIVE ADVANTAGES ───────────────────────────────────────────────────

def _build_advantages(data, content, lang, n):
    es = lang == 'es'
    ciudad = _s(data.get('ciudad'), '')
    tipo_dossier = data.get('tipo_dossier', 'inversores')
    args = list(content['commercial'].get('argumentos', []))

    if es:
        sh_ey = 'Ventajas Competitivas'; sh_tt = 'Razones de peso para priorizar este activo.'
        titles = (['Ubicacion Estrategica','Posicionamiento Premium','Demanda Sostenida','Potencial de Revalorizacion','Rentabilidad Diferencial','Liquidez del Activo']
                  if tipo_dossier == 'inversores' else
                  ['Ubicacion Privilegiada','Calidad de Construccion','Entorno Residencial','Servicios de Primer Nivel','Espacios y Distribucion','Inversion Segura'])
    else:
        sh_ey = 'Competitive Advantages'; sh_tt = 'Compelling reasons to prioritise this asset.'
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
        f'</div>',
        bg_key='advantages'
    )


# ─── VALUE CREATION PLAN ──────────────────────────────────────────────────────

def _build_value_plan(data, content, lang, n):
    es = lang == 'es'
    ciudad = _s(data.get('ciudad'), '')
    info_inv = _s(data.get('info_adicional_inversores', ''))

    if es:
        sh_ey = 'Plan de Creacion de Valor'; sh_tt = 'Como convertir este activo en rentabilidad sostenida.'
        fases = [
            ('Fase 1','Adquisicion','Due diligence completa, negociacion y cierre en condiciones optimas de mercado.'),
            ('Fase 2','Optimizacion','Reforma estrategica o puesta a punto del activo. Posicionamiento diferencial de mercado.'),
            ('Fase 3','Monetizacion','Comercializacion con pricing competitivo. Seleccion rigurosa de inquilino o comprador.'),
            ('Fase 4','Consolidacion','Gestion activa del activo. Revision anual y analisis continuo de la estrategia de salida.'),
        ]
        extras = [
            ('Optimizacion Fiscal', 'Amortizacion del activo, deduccion de gastos operativos y estructura juridica optima para el perfil inversor. Ahorro fiscal estimado 20-30%.', 'stone'),
            ('Gestion Profesional', 'Delegacion a empresa especializada en gestion de activos. Comision tipica del 8-12% sobre renta bruta. Cero gestion directa del inversor.', 'sky'),
            ('Estrategia de Salida', 'Venta a 5-7 a&ntilde;os en mercado abierto, a inquilino con derecho de tanteo, o incorporacion a fondo patrimonial. Plusvalia estimada por revalorizacion incluida en el ROI.', 'dark'),
        ]
    else:
        sh_ey = 'Value Creation Plan'; sh_tt = 'How to turn this asset into sustained returns.'
        fases = [
            ('Phase 1','Acquisition','Full due diligence, negotiation and closing under optimal market conditions.'),
            ('Phase 2','Optimisation','Strategic renovation or asset preparation. Differential market positioning.'),
            ('Phase 3','Monetisation','Competitive pricing. Rigorous tenant or buyer selection.'),
            ('Phase 4','Consolidation','Active asset management. Annual review and continuous exit strategy analysis.'),
        ]
        extras = [
            ('Tax Optimisation', 'Asset depreciation, operating expense deductions and optimal legal structure. Estimated tax saving 20-30%.', 'stone'),
            ('Professional Management', 'Delegation to specialist asset management firm. Typical fee: 8-12% on gross rent. Zero direct management for the investor.', 'sky'),
            ('Exit Strategy', 'Sale at 5-7 years on open market, to tenant with pre-emption right, or incorporation into a wealth fund. Estimated capital gain included in ROI.', 'dark'),
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
        f'</div>',
        bg_key='value'
    )


# ─── STRATEGIC ANALYSIS ───────────────────────────────────────────────────────

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
        f'<li style="margin-bottom:2.5mm; font-family:Inter,Arial,sans-serif; font-size:9pt; line-height:1.50; color:rgba(255,255,255,0.90);">{r}</li>'
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
        f'<div class="card dark"><h4>{rec_lbl}</h4><ul style="margin-top:3mm; padding-left:5mm; list-style:disc;">{recs_li}</ul></div>'
        f'</div>'
        f'{_foot(sh_ey, ciudad)}'
        f'</div>',
        bg_key='strategic'
    )


# ─── LIFESTYLE (Particulares) ─────────────────────────────────────────────────

def _build_lifestyle(data, content, lang, n):
    es = lang == 'es'
    ciudad = _s(data.get('ciudad'), '')
    barrio = _s(data.get('barrio')) or ciudad
    ls = content['loc_scores']
    paras = [p.strip() for p in content['zona_text'].split('\n\n') if p.strip()]
    lead = paras[0] if paras else ''
    body = ''.join(f'<p class="text" style="margin-bottom:2.5mm;">{p}</p>' for p in paras[1:3])

    if es:
        sh_ey = 'Calidad de Vida y Entorno'
        sh_tt = f'Vivir en {barrio} es mucho mas que una direccion.'
        bar_items = [
            ('Servicios', ls.get('servicios', 7.5)),
            ('Educacion', ls.get('perfil_socioeconomico', 7.0)),
            ('Conectividad', ls.get('conectividad', 7.5)),
            ('Zona Verde', ls.get('comercios', 7.0)),
            ('Seguridad', ls.get('atractivo_residencial', 8.0)),
            ('Potencial', ls.get('crecimiento', 7.5)),
        ]
    else:
        sh_ey = 'Quality of Life & Environment'
        sh_tt = f'Living in {barrio} is much more than an address.'
        bar_items = [
            ('Services', ls.get('servicios', 7.5)),
            ('Education', ls.get('perfil_socioeconomico', 7.0)),
            ('Connectivity', ls.get('conectividad', 7.5)),
            ('Green Areas', ls.get('comercios', 7.0)),
            ('Safety', ls.get('atractivo_residencial', 8.0)),
            ('Potential', ls.get('crecimiento', 7.5)),
        ]

    bars_html = ''.join(_svg_bar(lbl, val, 10, 210) for lbl, val in bar_items)
    zone_imgs = _zone_imgs(data, lang)
    imgs_html = ''.join(
        f'<div class="vitem"><img src="{u}" alt="{l}"/><div class="vcap">{l}</div></div>'
        for u, l in zone_imgs[:6]
    )

    return _page(
        f'<div class="inner">'
        f'{_sh(sh_ey, sh_tt, n)}'
        f'<div class="g2" style="margin-bottom:5mm; align-items:start;">'
        f'  <div><p class="lead" style="margin-bottom:3mm;">{lead}</p>{body}</div>'
        f'  <div><h4>{"Puntuaciones de zona" if es else "Zone scores"}</h4>'
        f'  <div class="bars-block" style="margin-top:4mm;">{bars_html}</div></div>'
        f'</div>'
        f'<div class="vgallery">{imgs_html}</div>'
        f'{_foot(sh_ey, ciudad)}'
        f'</div>',
        bg_key='lifestyle'
    )


def _build_gallery(data, content, lang, n):
    es = lang == 'es'
    ciudad = _s(data.get('ciudad'), '')
    fotos = data.get('foto_paths', [])
    fallbacks = [IMGS['interior1'], IMGS['interior2'], IMGS['terrace'], IMGS['pool'],
                 IMGS['garden'], IMGS['city'], IMGS['living'], IMGS['kitchen']]

    def get_src(idx):
        if idx < len(fotos):
            s = _photo_b64(fotos[idx])
            if s: return s
        return fallbacks[idx % len(fallbacks)]

    if es:
        sh_ey = 'Galeria del Inmueble'
        sh_tt = 'Presentacion visual completa del activo.'
        note_txt = 'Imagenes seleccionadas para una vision completa del inmueble y su entorno. Se recomienda solicitar una visita privada para una experiencia integral.'
    else:
        sh_ey = 'Property Gallery'
        sh_tt = 'Complete visual presentation of the asset.'
        note_txt = 'Images selected for a comprehensive view of the property and surroundings. A private visit is recommended for the full experience.'

    extra_count = min(5, max(3, len(fotos)) - 3 if len(fotos) > 3 else 3)
    extra_html = '<div class="g3" style="margin-top:3.5mm;">'
    for i in range(3, 3 + extra_count):
        extra_html += f'<div class="img-box"><img src="{get_src(i)}" style="height:38mm; width:100%; object-fit:cover;" alt=""/></div>'
    extra_html += '</div>'

    return _page(
        f'<div class="inner">'
        f'{_sh(sh_ey, sh_tt, n)}'
        f'<div class="photo-strip">'
        f'<div class="img-box"><img src="{get_src(0)}" style="height:90mm; width:100%; object-fit:cover;" alt=""/></div>'
        f'<div class="photo-stack">'
        f'<div class="img-box"><img src="{get_src(1)}" style="height:43mm; width:100%; object-fit:cover;" alt=""/></div>'
        f'<div class="img-box"><img src="{get_src(2)}" style="height:43mm; width:100%; object-fit:cover;" alt=""/></div>'
        f'</div></div>'
        f'{extra_html}'
        f'<div class="note" style="margin-top:3.5mm;">{note_txt}</div>'
        f'{_foot(sh_ey, ciudad)}'
        f'</div>',
        bg_key='gallery'
    )


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
    if not final_src:
        final_src = IMGS['cover2']

    if es:
        if tipo_dossier == 'inversores':
            title = f"Una oportunidad limitada para tomar posicion en {ciudad}."
            copy  = f"Este activo representa una ventana de inversion con fundamentos solidos en {barrio}. Las oportunidades de este calibre son escasas y de alta rotacion en el mercado actual."
            cta   = "Solicite su visita privada y documentacion tecnica completa."
        else:
            title = f"Tu hogar en {barrio} te esta esperando."
            copy  = f"Cada espacio de este inmueble ha sido seleccionado para ofrecerte calidad de vida superior en {ciudad}. Da el primer paso hoy."
            cta   = "Solicite una visita privada para conocer el inmueble en persona."
        dossier_tag = 'Dossier Premium Inmobiliario'
        cta_lbl = 'Agente / Contacto'
        prox = 'Proximo Paso'
        tel_lbl = 'Telefono'
        score_lbl = 'Score Premium'
    else:
        if tipo_dossier == 'inversores':
            title = f"A limited opportunity to take position in {ciudad}."
            copy  = f"This asset represents an investment window with solid fundamentals in {barrio}. Opportunities of this calibre are scarce and high-turnover in today's market."
            cta   = "Request your private visit and complete technical documentation."
        else:
            title = f"Your home in {barrio} is waiting for you."
            copy  = f"Every space in this property has been selected to offer you superior quality of life in {ciudad}. Take the first step today."
            cta   = "Request a private visit to see the property in person."
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
        f'    <p class="cover-copy" style="max-width:135mm;">{copy}</p>'
        f'    <div class="note" style="max-width:135mm; margin-top:6mm; background:rgba(255,252,245,0.96); color:#1e2f40;">'
        f'      <strong>{cta}</strong></div>'
        f'  </div>'
        f'  <div>'
        f'    <div class="contact-panel">'
        f'      <h3 style="font-family:\'Cormorant Garamond\',Georgia,serif; font-size:18pt; color:#1e2f40;">{nombre}</h3>'
        f'      <p class="text" style="color:#4d6275; margin-top:1mm; font-size:9pt;">{cta_lbl}</p>'
        f'      <div class="contact-grid">'
        f'        <div class="contact-item"><span>Email</span><strong>{email}</strong></div>'
        f'        <div class="contact-item"><span>{tel_lbl}</span><strong>{tel or chr(8212)}</strong></div>'
        f'        {third}'
        f'      </div>'
        f'    </div>'
        f'    <div class="tags" style="margin-top:5mm; justify-content:flex-start;">{tags_html}</div>'
        f'  </div>'
        f'</div>'
        f'</section>'
    )


def _build_html(data, content, lang):
    tipo_dossier = data.get('tipo_dossier', 'inversores')
    pages = [_build_cover(data, content, lang)]
    n = 1

    pages.append(_build_summary(data, content, lang, n));    n += 1
    pages.append(_build_ficha(data, content, lang, n));      n += 1
    pages.append(_build_commercial(data, content, lang, n)); n += 1
    pages.append(_build_location(data, content, lang, n));   n += 1
    pages.append(_build_services(data, content, lang, n));   n += 1

    if tipo_dossier == 'inversores':
        pages.append(_build_investment(data, content, lang, n));  n += 1
        pages.append(_build_advantages(data, content, lang, n));  n += 1
        pages.append(_build_value_plan(data, content, lang, n));  n += 1
        pages.append(_build_strategic(data, content, lang, n));   n += 1
    else:
        pages.append(_build_lifestyle(data, content, lang, n));   n += 1
        pages.append(_build_advantages(data, content, lang, n));  n += 1

    pages.append(_build_gallery(data, content, lang, n));    n += 1
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
    global _bg_counter
    _bg_counter = [0]
    html = _build_html(data, content, lang)
    from weasyprint import HTML
    return HTML(string=html, base_url='https://images.unsplash.com').write_pdf()
