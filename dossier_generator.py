"""
Motor PDF Premium — Dossier Inmobiliario
Genera dossieres visuales de alto nivel con gráficos radar, barras, scoring y galería.
"""
import math
import os
from io import BytesIO
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether, Image as RLImage
)
from reportlab.graphics.shapes import (
    Drawing, Polygon, Line, String, Circle, Rect, Group
)
from reportlab.graphics import renderPDF
from reportlab.pdfgen import canvas as pdfcanvas

try:
    from PIL import Image as PILImage
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# ─── PALETA ───────────────────────────────────────────────────────────────────
DARK       = colors.HexColor('#07101D')
DARK2      = colors.HexColor('#0D1A2B')
DARK3      = colors.HexColor('#111F30')
GOLD       = colors.HexColor('#C9A84C')
GOLD_L     = colors.HexColor('#E8CC80')
GOLD_DIM   = colors.Color(0.788, 0.659, 0.298, 0.25)
WHITE      = colors.white
GRAY       = colors.HexColor('#F4F6F9')
BORDER     = colors.HexColor('#1A2E44')
TEXT       = colors.HexColor('#E8EFF8')
MUTED      = colors.HexColor('#6B82A0')
MUTED2     = colors.HexColor('#8BA5C5')
SUCCESS    = colors.HexColor('#22C55E')
DANGER     = colors.HexColor('#EF4444')
WARNING    = colors.HexColor('#F59E0B')

W, H = A4   # 595 x 842 pts

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def safe_float(v, d=0.0):
    try: return float(v) if v else d
    except: return d

def fmt_eur(v):
    try:
        n = float(v)
        if n >= 1e6: return f"{n/1e6:.2f}M €"
        return f"{int(n):,} €".replace(",", ".")
    except: return "N/D"

def fmt_pct(v, d=2):
    try: return f"{float(v):.{d}f}%"
    except: return "N/D"


# ─── ESTILOS ──────────────────────────────────────────────────────────────────
def S(name, **kw):
    defaults = dict(fontName='Helvetica', fontSize=10, leading=14, textColor=TEXT)
    defaults.update(kw)
    return ParagraphStyle(name, **defaults)

STYLES = {
    'h_section': S('hs', fontName='Helvetica-Bold', fontSize=10, textColor=WHITE,
                   leading=14, spaceAfter=0),
    'body':      S('bo', fontSize=10, leading=15, alignment=TA_JUSTIFY,
                   textColor=colors.HexColor('#C8D8E8'), spaceAfter=6),
    'body_sm':   S('bs', fontSize=9,  leading=13, textColor=MUTED2, spaceAfter=4),
    'label':     S('lb', fontName='Helvetica-Bold', fontSize=8, textColor=MUTED,
                   leading=11, spaceAfter=2),
    'value':     S('va', fontSize=10, textColor=TEXT, leading=14, spaceAfter=4),
    'kpi_val':   S('kv', fontName='Helvetica-Bold', fontSize=22, textColor=GOLD,
                   leading=28, alignment=TA_CENTER),
    'kpi_lbl':   S('kl', fontSize=8, textColor=MUTED2, leading=11, alignment=TA_CENTER),
    'bullet':    S('bu', fontSize=10, textColor=colors.HexColor('#C8D8E8'), leading=15,
                   leftIndent=12, spaceAfter=4),
    'note':      S('no', fontName='Helvetica-Oblique', fontSize=8, textColor=MUTED,
                   leading=11, spaceAfter=4),
    'cover_t':   S('ct', fontName='Helvetica-Bold', fontSize=30, textColor=WHITE,
                   leading=38, alignment=TA_CENTER),
    'cover_s':   S('cs', fontSize=13, textColor=GOLD_L, leading=19, alignment=TA_CENTER),
    'cover_p':   S('cp', fontName='Helvetica-Bold', fontSize=38, textColor=GOLD,
                   leading=46, alignment=TA_CENTER),
    'cover_m':   S('cm', fontSize=10, textColor=MUTED2, leading=16, alignment=TA_CENTER),
    'risk_hi':   S('rh', fontName='Helvetica-Bold', fontSize=9, textColor=DANGER,  leading=12),
    'risk_med':  S('rm', fontName='Helvetica-Bold', fontSize=9, textColor=WARNING, leading=12),
    'risk_low':  S('rl', fontName='Helvetica-Bold', fontSize=9, textColor=SUCCESS, leading=12),
    'risk_body': S('rb', fontSize=9, textColor=MUTED2, leading=13),
    'toc_item':  S('ti', fontSize=11, textColor=TEXT, leading=18),
    'toc_page':  S('tp', fontName='Helvetica-Bold', fontSize=11, textColor=GOLD,
                   leading=18, alignment=TA_RIGHT),
}

LABELS = {
    'es': {
        'dossier': 'DOSSIER PREMIUM', 'confidencial': '● DOCUMENTO CONFIDENCIAL ●',
        'exec': '01  ·  RESUMEN EJECUTIVO', 'zona': '02  ·  ANÁLISIS DE UBICACIÓN',
        'financiero': '03  ·  ANÁLISIS FINANCIERO', 'inversion': '04  ·  ANÁLISIS DE INVERSIÓN',
        'comercial': '05  ·  ANÁLISIS COMERCIAL', 'narrativa': '06  ·  NARRATIVA COMERCIAL',
        'riesgos': '07  ·  RIESGOS Y MITIGACIONES', 'galeria': '08  ·  GALERÍA DEL INMUEBLE',
        'conclusiones': '09  ·  CONCLUSIONES Y RECOMENDACIONES', 'contacto': '✦  CONTACTO',
        'lifestyle': '02  ·  CALIDAD DE VIDA Y ZONA',
        'desc_premium': '03  ·  DESCRIPCIÓN PREMIUM',
        'precio': 'Precio de Venta', 'superficie': 'Superficie', 'precio_m2': 'Precio / m²',
        'yield_bruto': 'Yield Bruto', 'yield_neto': 'Yield Neto', 'payback': 'Payback',
        'cash_flow': 'Cash Flow Anual', 'roi_5y': 'ROI 5 años',
        'ingresos': 'Ingresos Anuales', 'gastos': 'Gastos Anuales', 'neto': 'Beneficio Neto',
        'comunidad': 'Comunidad', 'ibi': 'IBI', 'otros': 'Otros', 'gestion': 'Gestión (est.)',
        'reforma': 'Reforma', 'inv_total': 'Inversión Total',
        'prop_valor': 'Propuesta de Valor', 'args': 'Argumentos de Venta',
        'oportunidades': 'Oportunidades Comerciales', 'perfil': 'Perfil del Comprador Ideal',
        'riesgo_alto': 'ALTO', 'riesgo_medio': 'MEDIO', 'riesgo_bajo': 'BAJO',
        'riesgo_muy_bajo': 'MUY BAJO',
        'mitigacion': 'Mitigación', 'riesgo_col': 'Riesgo', 'nivel': 'Nivel',
        'recomendaciones': 'Recomendaciones', 'overall': 'Puntuación Global',
        'img_recomendadas': '📸 IMÁGENES RECOMENDADAS PARA ESTE DOSSIER',
        'img_portada': 'Portada', 'img_galeria': 'Galería', 'img_lifestyle': 'Lifestyle',
        'img_zona': 'Zona', 'img_cierre': 'Cierre',
        'presented_by': 'Presentado por', 'presented_to': 'Presentado a',
        'fecha': 'Fecha', 'ref': 'Referencia',
        'anos': 'años',
        'nota': '* Las proyecciones financieras son estimaciones basadas en datos de mercado. Se recomienda due diligence independiente antes de tomar decisiones de inversión.',
    },
    'en': {
        'dossier': 'PREMIUM DOSSIER', 'confidencial': '● CONFIDENTIAL DOCUMENT ●',
        'exec': '01  ·  EXECUTIVE SUMMARY', 'zona': '02  ·  LOCATION ANALYSIS',
        'financiero': '03  ·  FINANCIAL ANALYSIS', 'inversion': '04  ·  INVESTMENT ANALYSIS',
        'comercial': '05  ·  COMMERCIAL ANALYSIS', 'narrativa': '06  ·  COMMERCIAL NARRATIVE',
        'riesgos': '07  ·  RISKS & MITIGATIONS', 'galeria': '08  ·  PROPERTY GALLERY',
        'conclusiones': '09  ·  CONCLUSIONS & RECOMMENDATIONS', 'contacto': '✦  CONTACT',
        'lifestyle': '02  ·  QUALITY OF LIFE & LOCATION',
        'desc_premium': '03  ·  PREMIUM DESCRIPTION',
        'precio': 'Sale Price', 'superficie': 'Surface Area', 'precio_m2': 'Price / m²',
        'yield_bruto': 'Gross Yield', 'yield_neto': 'Net Yield', 'payback': 'Payback',
        'cash_flow': 'Annual Cash Flow', 'roi_5y': '5-Year ROI',
        'ingresos': 'Annual Income', 'gastos': 'Annual Expenses', 'neto': 'Net Profit',
        'comunidad': 'Community', 'ibi': 'Property Tax', 'otros': 'Other', 'gestion': 'Management (est.)',
        'reforma': 'Renovation', 'inv_total': 'Total Investment',
        'prop_valor': 'Value Proposition', 'args': 'Sales Arguments',
        'oportunidades': 'Commercial Opportunities', 'perfil': 'Ideal Buyer Profile',
        'riesgo_alto': 'HIGH', 'riesgo_medio': 'MEDIUM', 'riesgo_bajo': 'LOW',
        'riesgo_muy_bajo': 'VERY LOW',
        'mitigacion': 'Mitigation', 'riesgo_col': 'Risk', 'nivel': 'Level',
        'recomendaciones': 'Recommendations', 'overall': 'Overall Score',
        'img_recomendadas': '📸 RECOMMENDED IMAGES FOR THIS DOSSIER',
        'img_portada': 'Cover', 'img_galeria': 'Gallery', 'img_lifestyle': 'Lifestyle',
        'img_zona': 'Area', 'img_cierre': 'Closing',
        'presented_by': 'Presented by', 'presented_to': 'Presented to',
        'fecha': 'Date', 'ref': 'Reference',
        'anos': 'years',
        'nota': '* Financial projections are market-based estimates. Independent due diligence is recommended before making investment decisions.',
    }
}


# ─── CANVAS PERSONALIZADO ─────────────────────────────────────────────────────
class PremiumCanvas(pdfcanvas.Canvas):
    def __init__(self, *args, **kwargs):
        self.data    = kwargs.pop('data', {}) or {}
        self.content = kwargs.pop('content', {}) or {}
        self.lang    = kwargs.pop('lang', 'es')
        self._pages  = []
        super().__init__(*args, **kwargs)

    def showPage(self):
        self._pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        n = len(self._pages)
        for i, state in enumerate(self._pages):
            self.__dict__.update(state)
            self._draw_chrome(i + 1, n)
            super().showPage()
        super().save()

    def _draw_chrome(self, page_num, total):
        L = LABELS[self.lang]
        # Skip chrome on cover (page 1)
        if page_num == 1:
            return
        # Header bar
        self.setFillColor(DARK2)
        self.rect(0, H - 14*mm, W, 14*mm, fill=1, stroke=0)
        self.setFillColor(GOLD)
        self.rect(0, H - 14.8*mm, W, 0.8*mm, fill=1, stroke=0)
        # Header text
        agente = self.data.get('nombre_agente', '')
        if agente:
            self.setFillColor(WHITE)
            self.setFont('Helvetica-Bold', 7.5)
            self.drawString(18*mm, H - 9*mm, agente.upper())
        self.setFillColor(GOLD)
        self.setFont('Helvetica-Bold', 7)
        self.drawRightString(W - 18*mm, H - 9*mm, L['dossier'])
        # Footer bar
        self.setFillColor(DARK2)
        self.rect(0, 0, W, 11*mm, fill=1, stroke=0)
        self.setFillColor(GOLD)
        self.rect(0, 10.5*mm, W, 0.5*mm, fill=1, stroke=0)
        # Page number
        self.setFillColor(MUTED)
        self.setFont('Helvetica', 7)
        self.drawRightString(W - 18*mm, 3.5*mm, f"{page_num} / {total}")
        # Address
        addr = self.data.get('direccion', '')
        if addr:
            self.setFillColor(MUTED)
            self.setFont('Helvetica', 7)
            self.drawString(18*mm, 3.5*mm, f"📍 {addr[:75]}")
        # Confidential watermark
        if self.data.get('confidencial') in ('1', True, 1):
            self.saveState()
            self.translate(W/2, H/2)
            self.rotate(45)
            self.setFont('Helvetica-Bold', 55)
            self.setFillColor(colors.Color(1, 0, 0, 0.04))
            self.drawCentredString(0, 0, 'CONFIDENCIAL' if self.lang == 'es' else 'CONFIDENTIAL')
            self.restoreState()


# ─── COMPONENTES VISUALES ─────────────────────────────────────────────────────
def section_header(title, styles):
    t = Table([[Paragraph(title, styles['h_section'])]], colWidths=[17*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), DARK2),
        ('LEFTPADDING',  (0,0), (-1,-1), 14),
        ('RIGHTPADDING', (0,0), (-1,-1), 14),
        ('TOPPADDING',   (0,0), (-1,-1), 10),
        ('BOTTOMPADDING',(0,0), (-1,-1), 10),
        ('LINEBELOW', (0,0), (-1,-1), 2.5, GOLD),
    ]))
    return t


def kpi_row(kpis, styles):
    n = len(kpis)
    cw = 17*cm / n
    row_vals = [Paragraph(k[0], styles['kpi_val']) for k in kpis]
    row_lbls = [Paragraph(k[1], styles['kpi_lbl']) for k in kpis]
    t = Table([row_vals, row_lbls], colWidths=[cw]*n)
    ts = [
        ('BACKGROUND', (0,0), (-1,-1), DARK3),
        ('TOPPADDING',    (0,0), (-1,0), 18), ('BOTTOMPADDING', (0,0), (-1,0), 4),
        ('TOPPADDING',    (0,1), (-1,1), 2),  ('BOTTOMPADDING', (0,1), (-1,1), 16),
        ('LEFTPADDING',   (0,0), (-1,-1), 6),
        ('RIGHTPADDING',  (0,0), (-1,-1), 6),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER),
        ('LINEAFTER', (0,0), (-2,-1), 0.5, BORDER),
    ]
    for i in range(n):
        ts.append(('LINEABOVE', (i,0), (i,0), 3, GOLD))
    t.setStyle(TableStyle(ts))
    return t


def info_table(rows, styles, col_w=(5.5*cm, 11.5*cm)):
    data = [[Paragraph(r[0], styles['label']), Paragraph(str(r[1]) if r[1] else 'N/D', styles['value'])] for r in rows]
    t = Table(data, colWidths=list(col_w))
    t.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING',    (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ('LEFTPADDING',  (0,0), (0,-1), 2),
        ('LEFTPADDING',  (1,0), (1,-1), 10),
        ('LINEBELOW', (0,0), (-1,-2), 0.3, BORDER),
        ('BACKGROUND', (0,0), (-1,-1), DARK2),
    ]))
    return t


def score_bar(label, value, max_val=10, width=16*cm, styles=None):
    """Horizontal score bar with gold fill"""
    bar_w = width - 4*cm
    fill_w = bar_w * min(value / max_val, 1)

    d = Drawing(width, 22)
    # Label
    d.add(String(0, 7, label, fontName='Helvetica', fontSize=8, textColor=MUTED2))
    # Background track
    d.add(Rect(4.5*cm, 6, bar_w, 10, fillColor=DARK3, strokeColor=BORDER, strokeWidth=0.5))
    # Fill
    if fill_w > 0:
        d.add(Rect(4.5*cm, 6, fill_w, 10, fillColor=GOLD, strokeColor=None, strokeWidth=0))
    # Value
    d.add(String(width - 1, 7, f"{value:.1f}", fontName='Helvetica-Bold', fontSize=8,
                 textAnchor='end', textColor=GOLD))
    return d


def radar_chart(labels, values, size=210):
    """Radar/spider chart as ReportLab Drawing"""
    d = Drawing(size, size)
    n = len(labels)
    if n < 3: return d
    cx, cy = size/2, size/2
    r = size/2 - 32

    # Grid polygons
    for level in [0.25, 0.5, 0.75, 1.0]:
        pts = []
        for i in range(n):
            ang = -math.pi/2 + 2*math.pi*i/n
            pts += [cx + r*level*math.cos(ang), cy + r*level*math.sin(ang)]
        pts += [pts[0], pts[1]]
        d.add(Polygon(pts, fillColor=colors.Color(0.07,0.1,0.17, 0.6 if level==1 else 0.0),
                      strokeColor=BORDER, strokeWidth=0.6))

    # Spokes
    for i in range(n):
        ang = -math.pi/2 + 2*math.pi*i/n
        d.add(Line(cx, cy, cx+r*math.cos(ang), cy+r*math.sin(ang),
                   strokeColor=BORDER, strokeWidth=0.6))

    # Data polygon
    pts = []
    for i, v in enumerate(values):
        ang = -math.pi/2 + 2*math.pi*i/n
        frac = min(max(v/10.0, 0), 1)
        pts += [cx + r*frac*math.cos(ang), cy + r*frac*math.sin(ang)]
    pts += [pts[0], pts[1]]
    d.add(Polygon(pts, fillColor=colors.Color(0.788,0.659,0.298,0.28),
                  strokeColor=GOLD, strokeWidth=2))

    # Dots + value labels
    for i, v in enumerate(values):
        ang = -math.pi/2 + 2*math.pi*i/n
        frac = min(max(v/10.0, 0), 1)
        x = cx + r*frac*math.cos(ang)
        y = cy + r*frac*math.sin(ang)
        d.add(Circle(x, y, 4.5, fillColor=GOLD, strokeColor=WHITE, strokeWidth=1))
        # small value
        vx = cx + (r*frac+12)*math.cos(ang)
        vy = cy + (r*frac+12)*math.sin(ang) - 3
        d.add(String(vx, vy, f"{v:.0f}", fontName='Helvetica-Bold', fontSize=7,
                     textAnchor='middle', fillColor=GOLD))

    # Labels
    for i, lbl in enumerate(labels):
        ang = -math.pi/2 + 2*math.pi*i/n
        lx = cx + (r+22)*math.cos(ang)
        ly = cy + (r+22)*math.sin(ang) - 4
        d.add(String(lx, ly, lbl, fontName='Helvetica-Bold', fontSize=7.5,
                     textAnchor='middle', fillColor=MUTED2))
    return d


def bar_chart_h(items, max_val=None, width=16*cm, height=None):
    """Horizontal bar chart: items = [(label, value, color?), ...]"""
    bar_h = 22
    gap   = 8
    n     = len(items)
    h     = height or (n * (bar_h + gap) + 10)
    if not max_val:
        max_val = max((v for _,v,*_ in items), default=1)
    bar_w = width - 5.5*cm

    d = Drawing(width, h)
    for i, item in enumerate(items):
        lbl, val = item[0], item[1]
        col = item[2] if len(item) > 2 else GOLD
        y = h - (i+1)*(bar_h+gap)
        # Label
        d.add(String(0, y+6, lbl, fontName='Helvetica', fontSize=8.5, textColor=MUTED2))
        # Track
        d.add(Rect(5.5*cm, y, bar_w, bar_h,
                   fillColor=DARK3, strokeColor=BORDER, strokeWidth=0.5))
        # Fill
        fw = bar_w * min(val/max_val, 1)
        if fw > 0:
            d.add(Rect(5.5*cm, y, fw, bar_h, fillColor=col, strokeColor=None, strokeWidth=0))
        # Value label
        d.add(String(5.5*cm + fw + 6, y+7,
                     fmt_eur(val) if val > 100 else f"{val:.1f}",
                     fontName='Helvetica-Bold', fontSize=8, textColor=col))
    return d


def premium_score_gauge(score, max_val=10, width=120, height=70, label=''):
    """Semi-circular gauge for premium score"""
    d = Drawing(width, height + 10)
    cx = width / 2
    cy = 10

    # Arc background (grey)
    steps = 60
    pts_bg = []
    r = width/2 - 8
    for s in range(steps+1):
        ang = math.pi + math.pi * s/steps
        pts_bg += [cx + r*math.cos(ang), cy + r*math.sin(ang)]
    # Draw as polygon (approximate arc)
    for s in range(steps):
        ang1 = math.pi + math.pi*s/steps
        ang2 = math.pi + math.pi*(s+1)/steps
        x1 = cx + r*math.cos(ang1); y1 = cy + r*math.sin(ang1)
        x2 = cx + r*math.cos(ang2); y2 = cy + r*math.sin(ang2)
        x3 = cx + (r-12)*math.cos(ang2); y3 = cy + (r-12)*math.sin(ang2)
        x4 = cx + (r-12)*math.cos(ang1); y4 = cy + (r-12)*math.sin(ang1)
        frac = s/steps
        base_col = GOLD if frac <= score/max_val else DARK3
        d.add(Polygon([x1,y1,x2,y2,x3,y3,x4,y4,x1,y1],
                      fillColor=base_col, strokeColor=DARK2, strokeWidth=0.5))

    # Center value
    d.add(String(cx, cy + r/2 - 2, f"{score:.1f}", fontName='Helvetica-Bold', fontSize=18,
                 textAnchor='middle', fillColor=GOLD))
    d.add(String(cx, cy + r/2 - 18, f"/ {max_val}", fontName='Helvetica', fontSize=9,
                 textAnchor='middle', fillColor=MUTED))
    if label:
        d.add(String(cx, cy - 8, label, fontName='Helvetica-Bold', fontSize=7.5,
                     textAnchor='middle', fillColor=MUTED2))
    return d


def image_placeholder(width, height, label, sub=''):
    """Placeholder rectangle for recommended images"""
    d = Drawing(width, height)
    d.add(Rect(0, 0, width, height, fillColor=DARK3, strokeColor=BORDER, strokeWidth=1))
    # Camera icon area
    cx, cy = width/2, height/2
    d.add(String(cx, cy+8, '📷', fontName='Helvetica', fontSize=18, textAnchor='middle', fillColor=MUTED))
    if label:
        d.add(String(cx, cy-12, label, fontName='Helvetica-Bold', fontSize=8,
                     textAnchor='middle', fillColor=MUTED2))
    if sub:
        d.add(String(cx, cy-24, sub[:50], fontName='Helvetica', fontSize=7,
                     textAnchor='middle', fillColor=MUTED))
    return d


# ─── SECCIONES DEL DOSSIER ────────────────────────────────────────────────────
def build_cover(data, content, styles, lang):
    L = LABELS[lang]
    story = []
    story.append(Spacer(1, 2.2*cm))
    # Badge
    tipos_str = ('INVERSORES' if data.get('tipo_dossier') == 'inversores' else 'PARTICULARES')
    badge_sty = ParagraphStyle('bg', fontName='Helvetica-Bold', fontSize=9,
                                textColor=DARK, alignment=TA_CENTER, leading=12)
    badge_t = Table([[Paragraph(tipos_str, badge_sty)]], colWidths=[5*cm])
    badge_t.setStyle(TableStyle([
        ('BACKGROUND', (0,0),(-1,-1), GOLD),
        ('TOPPADDING', (0,0),(-1,-1), 5), ('BOTTOMPADDING',(0,0),(-1,-1), 5),
        ('ROUNDEDCORNERS', [12,12,12,12]),
    ]))
    story.append(badge_t)
    story.append(Spacer(1, 0.7*cm))
    # Type
    tipo_map = {
        'es': {'apartamento':'Apartamento','atico':'Ático Penthouse','casa':'Casa Unifamiliar',
               'villa':'Villa de Lujo','local':'Local Comercial','oficina':'Oficina Corporativa',
               'solar':'Solar Edificable','edificio':'Edificio Completo','nave':'Nave Industrial','':'Propiedad'},
        'en': {'apartamento':'Apartment','atico':'Penthouse','casa':'Detached House',
               'villa':'Luxury Villa','local':'Commercial Premises','oficina':'Corporate Office',
               'solar':'Building Plot','edificio':'Full Building','nave':'Industrial Unit','':'Property'},
    }
    tipo_txt = tipo_map[lang].get(data.get('tipo_propiedad',''), tipo_map[lang][''])
    story.append(Paragraph(tipo_txt.upper(), styles['cover_s']))
    story.append(Spacer(1, 0.3*cm))
    # Address
    story.append(Paragraph(data.get('direccion', 'Propiedad Premium'), styles['cover_t']))
    story.append(Spacer(1, 0.3*cm))
    zona_str = ', '.join(filter(None, [data.get('barrio',''), data.get('ciudad','')]))
    if zona_str:
        story.append(Paragraph(f"📍 {zona_str}", styles['cover_m']))
    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width='55%', thickness=2, color=GOLD, hAlign='CENTER'))
    story.append(Spacer(1, 0.8*cm))
    # Price
    story.append(Paragraph(fmt_eur(data.get('precio_venta')), styles['cover_p']))
    story.append(Spacer(1, 0.3*cm))
    # Quick stats
    parts = []
    if data.get('metros_construidos'): parts.append(f"📐 {data['metros_construidos']} m²")
    if data.get('dormitorios'): parts.append(f"🛏 {data['dormitorios']}")
    if data.get('banos'): parts.append(f"🚿 {data['banos']}")
    if parts:
        story.append(Paragraph('   ·   '.join(parts), styles['cover_m']))
    story.append(Spacer(1, 1.2*cm))
    story.append(HRFlowable(width='35%', thickness=1,
                             color=colors.Color(1,1,1,0.15), hAlign='CENTER'))
    story.append(Spacer(1, 0.8*cm))
    # Meta
    fecha = datetime.now().strftime('%d / %m / %Y')
    ref   = f"DOS-{datetime.now().strftime('%Y%m%d%H%M')}"
    for line in filter(None, [
        f"<b>{L['presented_by']}:</b>   {data.get('nombre_agente','')}",
        f"<b>{L['presented_to']}:</b>   {data.get('nombre_destinatario','')}",
        f"<b>{L['fecha']}:</b>   {fecha}",
        f"<b>{L['ref']}:</b>   {ref}",
    ]):
        story.append(Paragraph(line, styles['cover_m']))
        story.append(Spacer(1, 0.18*cm))
    story.append(PageBreak())
    return story


def build_exec_summary(data, content, styles, lang):
    L = LABELS[lang]
    fin = content['financials']
    story = [Spacer(1, 0.5*cm), section_header(L['exec'], styles), Spacer(1, 0.4*cm)]
    # Executive summary text
    story.append(Paragraph(content['exec_summary'], styles['body']))
    story.append(Spacer(1, 0.5*cm))
    # KPI row
    kpis = [(fmt_eur(data.get('precio_venta')), L['precio'])]
    m2 = safe_float(data.get('metros_construidos'))
    precio = safe_float(data.get('precio_venta'))
    if m2 and precio:
        kpis.append((fmt_eur(precio/m2), L['precio_m2']))
    if data.get('tipo_dossier') == 'inversores' and fin.get('yield_bruto',0) > 0:
        kpis.append((fmt_pct(fin['yield_bruto']), L['yield_bruto']))
        if fin.get('payback',0) > 0:
            kpis.append((f"{fin['payback']:.1f} {L['anos']}", L['payback']))
    if len(kpis) >= 2:
        story.append(kpi_row(kpis[:4], styles))
    story.append(Spacer(1, 0.5*cm))

    # Premium score gauges
    ps = content['premium_score']
    ls = content['loc_scores']
    avg_loc = round(sum(ls.values())/len(ls), 1)
    overall = round((ps + avg_loc)/2, 1)
    gauge_data = [
        (overall, 'Score Global' if lang=='es' else 'Overall Score'),
        (ps, 'Premium' if lang=='es' else 'Premium'),
        (avg_loc, 'Ubicación' if lang=='es' else 'Location'),
    ]
    if data.get('tipo_dossier') == 'inversores' and content.get('inv_scores'):
        inv_s = content['inv_scores']
        avg_inv = round(sum(inv_s.values())/len(inv_s), 1)
        gauge_data.append((avg_inv, 'Inversión' if lang=='es' else 'Investment'))

    gauges = [premium_score_gauge(g[0], label=g[1]) for g in gauge_data[:4]]
    cw = 17*cm / len(gauges)
    gt = Table([gauges], colWidths=[cw]*len(gauges))
    gt.setStyle(TableStyle([
        ('BACKGROUND', (0,0),(-1,-1), DARK2),
        ('ALIGN', (0,0),(-1,-1), 'CENTER'),
        ('VALIGN', (0,0),(-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0),(-1,-1), 14),
        ('BOTTOMPADDING', (0,0),(-1,-1), 14),
        ('BOX', (0,0),(-1,-1), 0.5, BORDER),
        ('LINEAFTER', (0,0),(-2,-1), 0.5, BORDER),
    ]))
    story.append(gt)
    story.append(PageBreak())
    return story


def build_location(data, content, styles, lang):
    L = LABELS[lang]
    sec_key = 'lifestyle' if data.get('tipo_dossier') != 'inversores' else 'zona'
    story = [Spacer(1, 0.5*cm), section_header(L[sec_key], styles), Spacer(1, 0.4*cm)]

    # Main text
    story.append(Paragraph(content['zona_text'].replace('\n\n', '<br/><br/>'), styles['body']))
    story.append(Spacer(1, 0.4*cm))

    # Score bars
    ls = content['loc_scores']
    labels_es = ['Conectividad', 'Transporte', 'Servicios', 'Comercios',
                 'Perfil Socioecon.', 'Crecimiento', 'Atractivo Resid.', 'Atractivo Inv.']
    labels_en = ['Connectivity', 'Transport', 'Services', 'Commerce',
                 'Socioeconomic', 'Growth', 'Residential', 'Investor']
    bar_labels = labels_es if lang == 'es' else labels_en
    bar_vals   = list(ls.values())

    # Two-column: bars left (as table), radar right
    bar_rows = [[score_bar(lbl, val, width=8.5*cm, styles=styles)]
                for lbl, val in zip(bar_labels, bar_vals)]
    bars_drawing = Table(bar_rows, colWidths=[9*cm])
    bars_drawing.setStyle(TableStyle([
        ('TOPPADDING',    (0,0),(-1,-1), 2),
        ('BOTTOMPADDING', (0,0),(-1,-1), 2),
        ('LEFTPADDING',   (0,0),(-1,-1), 0),
        ('RIGHTPADDING',  (0,0),(-1,-1), 0),
    ]))

    radar_labels_es = ['Conect.','Transport.','Servicios','Comercios','Socioecon.','Crecim.','Resid.','Inversor']
    radar_labels_en = ['Connec.','Transport','Services','Commerce','Socioecon.','Growth','Resid.','Investor']
    rl = radar_labels_es if lang == 'es' else radar_labels_en
    radar = radar_chart(rl, bar_vals, size=190)

    loc_table = Table([[bars_drawing, radar]], colWidths=[9.5*cm, 7.5*cm])
    loc_table.setStyle(TableStyle([
        ('VALIGN', (0,0),(-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0),(-1,-1), 0),
        ('RIGHTPADDING', (0,0),(-1,-1), 0),
        ('TOPPADDING', (0,0),(-1,-1), 0),
        ('BOTTOMPADDING', (0,0),(-1,-1), 0),
    ]))
    story.append(loc_table)
    story.append(Spacer(1, 0.4*cm))

    # Zone image placeholder
    img_lbl = content.get('img_recs', {}).get('zona', 'Vista de la zona')
    story.append(image_placeholder(17*cm, 3.5*cm, '📸 ' + ('IMAGEN RECOMENDADA: VISTA DE LA ZONA' if lang=='es' else 'RECOMMENDED IMAGE: AREA VIEW'), img_lbl[:60]))
    story.append(PageBreak())
    return story


def build_financial(data, content, styles, lang):
    L = LABELS[lang]
    fin = content['financials']
    story = [Spacer(1, 0.5*cm), section_header(L['financiero'], styles), Spacer(1, 0.4*cm)]

    # Main text
    story.append(Paragraph(content['financial_text'].replace('\n\n', '<br/><br/>'), styles['body']))
    story.append(Spacer(1, 0.5*cm))

    # KPI row
    kpis_fin = []
    if fin.get('yield_bruto',0):  kpis_fin.append((fmt_pct(fin['yield_bruto']), L['yield_bruto']))
    if fin.get('yield_neto',0):   kpis_fin.append((fmt_pct(fin['yield_neto']),  L['yield_neto']))
    if fin.get('payback',0):      kpis_fin.append((f"{fin['payback']:.1f} {L['anos']}", L['payback']))
    if fin.get('roi_5y',0):       kpis_fin.append((fmt_pct(fin['roi_5y']), L['roi_5y']))
    if kpis_fin:
        story.append(kpi_row(kpis_fin[:4], styles))
        story.append(Spacer(1, 0.5*cm))

    # Financial detail table
    detail = []
    if fin.get('ingresos_brutos',0):
        p_green = ParagraphStyle('g', fontName='Helvetica-Bold', fontSize=10, textColor=SUCCESS, leading=13)
        p_red   = ParagraphStyle('r', fontName='Helvetica', fontSize=10, textColor=DANGER, leading=13)
        p_redb  = ParagraphStyle('rb', fontName='Helvetica-Bold', fontSize=10, textColor=DANGER, leading=13)
        p_gold  = ParagraphStyle('gb', fontName='Helvetica-Bold', fontSize=11, textColor=GOLD, leading=14)
        p_sub   = ParagraphStyle('su', fontName='Helvetica', fontSize=9, textColor=MUTED, leading=12)
        detail.append([Paragraph(L['ingresos'], STYLES['label']),
                       Paragraph(fmt_eur(fin['ingresos_brutos']), p_green)])
        for k, v in [(L['comunidad'],fin.get('gas_com_anual',0)), (L['ibi'],fin.get('ibi',0)),
                     (L['otros'],fin.get('otros',0)), (L['gestion'],fin.get('gestion',0))]:
            if v > 0:
                detail.append([Paragraph(f"  · {k}", p_sub), Paragraph(f"- {fmt_eur(v)}", p_red)])
        detail.append([Paragraph(L['gastos'], STYLES['label']),
                       Paragraph(f"- {fmt_eur(fin['gastos_totales'])}", p_redb)])
        if fin.get('reforma',0):
            detail.append([Paragraph(L['reforma'], STYLES['label']),
                           Paragraph(f"- {fmt_eur(fin['reforma'])}", p_red)])
            detail.append([Paragraph(L['inv_total'], STYLES['label']),
                           Paragraph(fmt_eur(fin['inversion_total']),
                                     ParagraphStyle('it',fontName='Helvetica-Bold',fontSize=10,textColor=TEXT,leading=13))])
        detail.append([Paragraph(L['neto'], ParagraphStyle('nl',fontName='Helvetica-Bold',fontSize=10,textColor=TEXT,leading=13)),
                       Paragraph(fmt_eur(fin['ingresos_netos']), p_gold)])

        dt = Table(detail, colWidths=[10*cm, 7*cm])
        dt.setStyle(TableStyle([
            ('TOPPADDING',    (0,0),(-1,-1), 7), ('BOTTOMPADDING',(0,0),(-1,-1), 7),
            ('LEFTPADDING',   (0,0),(-1,-1), 12),
            ('LINEBELOW',     (0,0),(-1,-2), 0.3, BORDER),
            ('BACKGROUND',    (0,0),(-1,-1), DARK2),
            ('BACKGROUND',    (0,-1),(-1,-1), DARK3),
            ('LINEABOVE',     (0,-1),(-1,-1), 1.5, GOLD),
        ]))
        story.append(dt)

    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(L['nota'], STYLES['note']))
    story.append(PageBreak())
    return story


def build_investment(data, content, styles, lang):
    L = LABELS[lang]
    inv = content.get('inv_scores', {})
    if not inv: return []

    story = [Spacer(1, 0.5*cm), section_header(L['inversion'], styles), Spacer(1, 0.4*cm)]

    lbl_es = ['Rentabilidad','Seguridad','Liquidez','Escalabilidad','Posicion.','Demanda','Diferenc.']
    lbl_en = ['Yield','Safety','Liquidity','Scalability','Positioning','Demand','Differentiation']
    rlabels = lbl_es if lang == 'es' else lbl_en
    rvals   = list(inv.values())

    # Radar + bar side by side
    radar   = radar_chart(rlabels, rvals[:len(rlabels)], size=200)
    inv_bar_data = list(zip(rlabels, rvals[:len(rlabels)]))
    bars = bar_chart_h(inv_bar_data, max_val=10, width=8.5*cm)

    tbl = Table([[radar, bars]], colWidths=[10*cm, 7*cm])
    tbl.setStyle(TableStyle([
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),0), ('RIGHTPADDING',(0,0),(-1,-1),0),
        ('TOPPADDING',(0,0),(-1,-1),0), ('BOTTOMPADDING',(0,0),(-1,-1),0),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 0.4*cm))

    # Score summary table
    avg = round(sum(rvals)/len(rvals), 1)
    sum_rows = []
    for lbl, val in zip(rlabels, rvals):
        bar_d = bar_chart_h([(lbl, val)], max_val=10, width=7*cm, height=30)
        sum_rows.append([Paragraph(lbl, STYLES['label']),
                         bar_d,
                         Paragraph(f"{val:.1f}/10", ParagraphStyle('sv',fontName='Helvetica-Bold',fontSize=10,textColor=GOLD,leading=13,alignment=TA_RIGHT))])
    sum_t = Table(sum_rows, colWidths=[4*cm, 9.5*cm, 3.5*cm])
    sum_t.setStyle(TableStyle([
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('TOPPADDING',(0,0),(-1,-1),4), ('BOTTOMPADDING',(0,0),(-1,-1),4),
        ('LEFTPADDING',(0,0),(-1,-1),8), ('RIGHTPADDING',(0,0),(-1,-1),8),
        ('LINEBELOW',(0,0),(-1,-2),0.3,BORDER),
        ('BACKGROUND',(0,0),(-1,-1),DARK2),
    ]))
    story.append(sum_t)
    story.append(Spacer(1, 0.3*cm))
    avg_text = (f"Puntuación media del activo en los factores clave de inversión: <b>{avg}/10</b>" if lang=='es' else
                f"Asset average score across key investment factors: <b>{avg}/10</b>")
    story.append(Paragraph(avg_text, STYLES['body']))
    story.append(PageBreak())
    return story


def build_commercial(data, content, styles, lang):
    L = LABELS[lang]
    com = content['commercial']
    story = [Spacer(1, 0.5*cm), section_header(L['comercial'], styles), Spacer(1, 0.4*cm)]

    # Value proposition box
    vp_sty = ParagraphStyle('vp', fontName='Helvetica-Bold', fontSize=11, textColor=GOLD, leading=16, spaceAfter=8)
    vp_box = Table([[Paragraph(com['propuesta_valor'], vp_sty)]], colWidths=[17*cm])
    vp_box.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1), DARK3),
        ('TOPPADDING',(0,0),(-1,-1),14), ('BOTTOMPADDING',(0,0),(-1,-1),14),
        ('LEFTPADDING',(0,0),(-1,-1),18), ('RIGHTPADDING',(0,0),(-1,-1),18),
        ('LINEBELOW',(0,0),(-1,-1),2,GOLD),
        ('LINELEFT',(0,0),(0,-1),4,GOLD),
    ]))
    story.append(vp_box)
    story.append(Spacer(1, 0.5*cm))

    # Two-column: args + buyer profile
    args_text = ''.join(f"<br/>✦  {a}" for a in com['argumentos'])
    opp_text  = ''.join(f"<br/>▸  {o}" for o in com['oportunidades'])

    left_col = [
        Paragraph(f"<b>{L['args']}</b>", STYLES['label']), Spacer(1,0.15*cm),
        Paragraph(args_text.lstrip('<br/>'), STYLES['bullet']), Spacer(1,0.3*cm),
        Paragraph(f"<b>{L['oportunidades']}</b>", STYLES['label']), Spacer(1,0.15*cm),
        Paragraph(opp_text.lstrip('<br/>'), STYLES['bullet']),
    ]
    right_col = [
        Paragraph(f"<b>{L['perfil']}</b>", STYLES['label']), Spacer(1,0.15*cm),
        Paragraph(com['perfil_comprador'], STYLES['body']),
    ]
    lt = Table([[left_col, right_col]], colWidths=[9.5*cm, 7.5*cm])
    lt.setStyle(TableStyle([
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),0), ('RIGHTPADDING',(0,0),(-1,-1),0),
        ('LEFTPADDING',(1,0),(1,-1),20),
    ]))
    story.append(lt)
    story.append(PageBreak())
    return story


def build_narrative(data, content, styles, lang):
    L = LABELS[lang]
    story = [Spacer(1, 0.5*cm), section_header(L['narrativa'], styles), Spacer(1, 0.4*cm)]
    story.append(Paragraph(content['narrative'].replace('\n\n', '<br/><br/>'), styles['body']))
    story.append(Spacer(1, 0.5*cm))
    # Lifestyle image placeholder
    img_lbl = content.get('img_recs', {}).get('lifestyle', '')
    story.append(image_placeholder(17*cm, 4*cm,
        '📸 ' + ('IMAGEN RECOMENDADA: LIFESTYLE' if lang=='es' else 'RECOMMENDED IMAGE: LIFESTYLE'),
        img_lbl[:65]))
    story.append(PageBreak())
    return story


def build_risks(data, content, styles, lang):
    L = LABELS[lang]
    story = [Spacer(1, 0.5*cm), section_header(L['riesgos'], styles), Spacer(1, 0.4*cm)]

    nivel_map = {
        'es': {'alto': ('ALTO', DANGER), 'muy alto': ('MUY ALTO', DANGER),
               'medio': ('MEDIO', WARNING), 'bajo': ('BAJO', SUCCESS), 'muy bajo': ('MUY BAJO', SUCCESS)},
        'en': {'alto': ('HIGH', DANGER), 'muy alto': ('VERY HIGH', DANGER),
               'medio': ('MEDIUM', WARNING), 'bajo': ('LOW', SUCCESS), 'muy bajo': ('VERY LOW', SUCCESS)},
    }

    hdr_sty = ParagraphStyle('rh', fontName='Helvetica-Bold', fontSize=9, textColor=WHITE, leading=12)
    rows_data = [[
        Paragraph(L['riesgo_col'], hdr_sty),
        Paragraph(L['nivel'],      hdr_sty),
        Paragraph(L['mitigacion'], hdr_sty),
    ]]
    for risk_item in content['riesgos']:
        r_text, r_nivel, r_mit = risk_item
        nivel_info = nivel_map[lang].get(r_nivel.lower(), ('N/D', MUTED))
        nivel_label, nivel_col = nivel_info
        nivel_sty = ParagraphStyle('ns', fontName='Helvetica-Bold', fontSize=8,
                                   textColor=nivel_col, leading=12, alignment=TA_CENTER)
        rows_data.append([
            Paragraph(r_text, STYLES['body_sm']),
            Paragraph(nivel_label, nivel_sty),
            Paragraph(r_mit, STYLES['body_sm']),
        ])

    rt = Table(rows_data, colWidths=[5.5*cm, 2*cm, 9.5*cm])
    ts = [
        ('BACKGROUND',(0,0),(-1,0), DARK3),
        ('BACKGROUND',(0,1),(-1,-1), DARK2),
        ('TOPPADDING',   (0,0),(-1,-1), 8), ('BOTTOMPADDING',(0,0),(-1,-1), 8),
        ('LEFTPADDING',  (0,0),(-1,-1), 10), ('RIGHTPADDING', (0,0),(-1,-1), 10),
        ('LINEBELOW',    (0,0),(-1,-2), 0.4, BORDER),
        ('LINEBELOW',    (0,0),(-1,0),  1.5, GOLD),
        ('VALIGN',       (0,0),(-1,-1), 'TOP'),
    ]
    for i in range(1, len(rows_data), 2):
        ts.append(('BACKGROUND', (0,i),(-1,i), colors.Color(0.08,0.13,0.2,1)))
    rt.setStyle(TableStyle(ts))
    story.append(rt)
    story.append(PageBreak())
    return story


def build_gallery(foto_paths, content, styles, lang, max_photos=6):
    if not foto_paths:
        return []
    L = LABELS[lang]
    story = [Spacer(1, 0.5*cm), section_header(L['galeria'], styles), Spacer(1, 0.4*cm)]

    # Load and lay out photos in a 2-col grid
    photos = []
    for path in foto_paths[:max_photos]:
        try:
            if HAS_PIL:
                img = PILImage.open(path)
                iw, ih = img.size
                target_w = 8*cm
                target_h = target_w * ih / iw
                if target_h > 6*cm: target_h = 6*cm; target_w = target_h * iw / ih
            else:
                target_w, target_h = 8*cm, 6*cm
            rl_img = RLImage(path, width=target_w, height=target_h)
            photos.append(rl_img)
        except Exception:
            photos.append(image_placeholder(8*cm, 6*cm, 'Foto'))

    # Pair into rows of 2
    for i in range(0, len(photos), 2):
        row = photos[i:i+2]
        if len(row) < 2: row.append(Spacer(1,1))
        pt = Table([row], colWidths=[8.5*cm, 8.5*cm])
        pt.setStyle(TableStyle([
            ('VALIGN',(0,0),(-1,-1),'TOP'),
            ('ALIGN', (0,0),(-1,-1),'CENTER'),
            ('TOPPADDING',(0,0),(-1,-1),4), ('BOTTOMPADDING',(0,0),(-1,-1),4),
            ('LEFTPADDING',(0,0),(-1,-1),4), ('RIGHTPADDING',(0,0),(-1,-1),4),
        ]))
        story.append(pt)
        story.append(Spacer(1, 0.2*cm))

    # Image recommendations
    img_recs = content.get('img_recs', {})
    if img_recs:
        story.append(Spacer(1, 0.4*cm))
        story.append(Paragraph(L['img_recomendadas'], STYLES['label']))
        story.append(Spacer(1, 0.2*cm))
        rec_rows = []
        keys_es = ['portada','galeria','lifestyle','zona','cierre']
        keys_en = ['portada','galeria','lifestyle','zona','cierre']
        lbls_es = [L['img_portada'], L['img_galeria'], L['img_lifestyle'], L['img_zona'], L['img_cierre']]
        for k, lbl in zip(keys_es, lbls_es):
            if k in img_recs:
                rec_rows.append([Paragraph(f"<b>{lbl}:</b>", STYLES['label']),
                                  Paragraph(img_recs[k], STYLES['body_sm'])])
        if rec_rows:
            rec_t = Table(rec_rows, colWidths=[3.5*cm, 13.5*cm])
            rec_t.setStyle(TableStyle([
                ('VALIGN',(0,0),(-1,-1),'TOP'),
                ('TOPPADDING',(0,0),(-1,-1),5), ('BOTTOMPADDING',(0,0),(-1,-1),5),
                ('LINEBELOW',(0,0),(-1,-2),0.3,BORDER),
                ('BACKGROUND',(0,0),(-1,-1),DARK2),
                ('LEFTPADDING',(0,0),(-1,-1),8),
            ]))
            story.append(rec_t)
    story.append(PageBreak())
    return story


def build_conclusions(data, content, styles, lang):
    L = LABELS[lang]
    conc = content['conclusions']
    story = [Spacer(1, 0.5*cm), section_header(L['conclusiones'], styles), Spacer(1, 0.4*cm)]

    # Overall score prominent
    overall = conc.get('overall', 0)
    gauge = premium_score_gauge(overall, label='Score Final' if lang=='es' else 'Final Score', width=140, height=80)
    g_t = Table([[gauge, Paragraph(conc['texto'].replace('\n\n','<br/><br/>'), styles['body'])]],
                colWidths=[4.5*cm, 12.5*cm])
    g_t.setStyle(TableStyle([
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),0), ('RIGHTPADDING',(0,0),(-1,-1),0),
        ('LEFTPADDING',(1,0),(1,-1),16),
    ]))
    story.append(g_t)
    story.append(Spacer(1, 0.5*cm))
    # Recommendations
    story.append(Paragraph(f"<b>{L['recomendaciones']}</b>", STYLES['label']))
    story.append(Spacer(1, 0.15*cm))
    for rec in conc.get('recomendaciones', []):
        story.append(Paragraph(f"▸  {rec}", STYLES['bullet']))
    story.append(Spacer(1, 0.4*cm))
    # Image recommendation: cierre
    img_cierre = content.get('img_recs',{}).get('cierre','')
    story.append(image_placeholder(17*cm, 3*cm,
        '📸 ' + ('IMAGEN RECOMENDADA: CIERRE DEL DOSSIER' if lang=='es' else 'RECOMMENDED IMAGE: DOSSIER CLOSING'),
        img_cierre[:65]))
    story.append(PageBreak())
    return story


def build_contact(data, content, styles, lang):
    L = LABELS[lang]
    story = [Spacer(1, 0.5*cm), section_header(L['contacto'], styles), Spacer(1, 0.6*cm)]

    c_bold = ParagraphStyle('cb', fontName='Helvetica-Bold', fontSize=14, textColor=WHITE, leading=20)
    c_text = ParagraphStyle('ct', fontSize=12, textColor=TEXT, leading=20)

    if data.get('nombre_agente'):
        story.append(Paragraph(data['nombre_agente'], c_bold))
    for icon, field in [('📞', 'telefono_agente'), ('✉️', 'email_agente'), ('🌐', 'web_agente')]:
        if data.get(field):
            story.append(Paragraph(f"{icon}  {data[field]}", c_text))
    story.append(Spacer(1, 0.6*cm))
    story.append(HRFlowable(width='100%', thickness=1, color=BORDER))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(L['nota'], STYLES['note']))
    return story


# ─── FUNCIÓN PRINCIPAL ────────────────────────────────────────────────────────
def generate_dossier(data: dict, content: dict, lang: str = 'es') -> bytes:
    buf = BytesIO()

    def canvas_maker(filename, **kwargs):
        kwargs.pop('lang', None)
        kwargs.pop('data', None)
        kwargs.pop('content', None)
        return PremiumCanvas(filename, data=data, content=content, lang=lang, **kwargs)

    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2.2*cm, bottomMargin=1.8*cm,
        title=f"Dossier Premium — {data.get('direccion','')}",
        author=data.get('nombre_agente',''),
        subject='Dossier Inmobiliario Premium',
    )

    tipo_dossier = data.get('tipo_dossier', 'inversores')
    story = []

    # 1. PORTADA (dark background drawn via canvas — use white text on color)
    story += build_cover(data, content, STYLES, lang)

    # 2. RESUMEN EJECUTIVO
    story += build_exec_summary(data, content, STYLES, lang)

    # 3. ANÁLISIS DE ZONA / CALIDAD DE VIDA
    story += build_location(data, content, STYLES, lang)

    # 4. ANÁLISIS FINANCIERO (sólo inversores)
    if tipo_dossier == 'inversores' and content['financials'].get('ingresos_brutos', 0) > 0:
        story += build_financial(data, content, STYLES, lang)

    # 5. ANÁLISIS DE INVERSIÓN (sólo inversores)
    if tipo_dossier == 'inversores':
        story += build_investment(data, content, STYLES, lang)

    # 6. ANÁLISIS COMERCIAL
    story += build_commercial(data, content, STYLES, lang)

    # 7. NARRATIVA COMERCIAL
    story += build_narrative(data, content, STYLES, lang)

    # 8. RIESGOS
    story += build_risks(data, content, STYLES, lang)

    # 9. GALERÍA
    foto_paths = data.get('foto_paths', [])
    story += build_gallery(foto_paths, content, STYLES, lang)

    # 10. CONCLUSIONES
    story += build_conclusions(data, content, STYLES, lang)

    # 11. CONTACTO
    story += build_contact(data, content, STYLES, lang)

    # Build with dark page background via canvas
    doc.build(story, canvasmaker=canvas_maker,
              onFirstPage=_dark_page, onLaterPages=_dark_page)
    return buf.getvalue()


def _dark_page(c, doc):
    """Draw dark background on every page"""
    c.saveState()
    c.setFillColor(DARK)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    # Cover gold gradient strip at bottom
    if doc.page == 1:
        c.setFillColor(DARK2)
        c.rect(0, 0, W, H * 0.35, fill=1, stroke=0)
        c.setFillColor(GOLD)
        c.rect(0, H * 0.35 + 1, W, 2, fill=1, stroke=0)
    c.restoreState()
