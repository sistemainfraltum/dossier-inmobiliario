"""
Motor de generación de contenido profesional para dossiers inmobiliarios.
Genera análisis estratégico, narrativas y puntuaciones sin necesidad de IA externa.
"""
import math
from datetime import datetime


# ─── HELPERS ──────────────────────────────────────────────────────────────────
def safe_float(val, default=0.0):
    try: return float(val) if val else default
    except: return default

def fmt_eur(val):
    try:
        n = float(val)
        if n >= 1_000_000: return f"{n/1_000_000:.2f}M €"
        return f"{int(n):,} €".replace(",", ".")
    except: return "N/D"

def fmt_pct(val, decimals=2):
    try: return f"{float(val):.{decimals}f}%"
    except: return "N/D"


# ─── CATÁLOGOS DE TEXTOS ──────────────────────────────────────────────────────
_DEMANDA_TEXT = {
    'es': {
        'muy_alta': 'una demanda de alquiler excepcional, con tasas de ocupación superiores al 95% y escasez crónica de oferta',
        'alta': 'una demanda de alquiler robusta y sostenida, que garantiza elevadas tasas de ocupación y rápida rotación de inquilinos',
        'media': 'una demanda de alquiler estable y consistente, con perspectivas de crecimiento moderado a medio plazo',
        'baja': 'un mercado de alquiler en fase de desarrollo, con oportunidades de posicionamiento anticipado y márgenes de valorización futura',
        '': 'una demanda activa en el mercado local, representativa de las tendencias del sector',
    },
    'en': {
        'muy_alta': 'exceptional rental demand, with occupancy rates above 95% and chronic supply shortage',
        'alta': 'robust and sustained rental demand, ensuring high occupancy rates and rapid tenant turnover',
        'media': 'stable and consistent rental demand, with moderate growth prospects in the medium term',
        'baja': 'a developing rental market, with early positioning opportunities and future appreciation margins',
        '': 'active demand in the local market, representative of sector trends',
    }
}

_PERFIL_TEXT = {
    'es': {
        'lujo': 'un perfil socioeconómico alto y ultra-premium, con demandantes exigentes que priorizan exclusividad, acabados de primera calidad y servicios de conserjería privada',
        'ejecutivos': 'un perfil de directivos y profesionales de alto nivel que valoran la conectividad, la proximidad a centros de negocios y los servicios premium urbanos',
        'familias': 'familias consolidadas que buscan entornos seguros, bien equipados en servicios educativos de calidad y zonas verdes accesibles',
        'jovenes': 'jóvenes profesionales y perfiles millenial que priorizan la vida urbana activa, la movilidad sostenible y la conectividad digital',
        'turistas': 'un mercado con elevado flujo turístico, que genera oportunidades excepcionales en el segmento vacacional y de alquiler de corta estancia',
        'mixto': 'una demanda diversificada que combina perfiles residenciales, inversores y usuarios corporativos, dotando al activo de una liquidez elevada',
        '': 'un perfil representativo del tejido socioeconómico de la zona, con capacidad adquisitiva acorde al posicionamiento del inmueble',
    },
    'en': {
        'lujo': 'a high and ultra-premium socioeconomic profile, with demanding buyers who prioritise exclusivity, top-quality finishes and private concierge services',
        'ejecutivos': 'a profile of senior executives and high-level professionals who value connectivity, proximity to business centres and premium urban services',
        'familias': 'established families seeking safe environments, well-equipped with quality educational services and accessible green spaces',
        'jovenes': 'young professionals and millennial profiles who prioritise active urban life, sustainable mobility and digital connectivity',
        'turistas': 'a market with high tourist flows, generating exceptional opportunities in the vacation and short-term rental segment',
        'mixto': 'diversified demand combining residential profiles, investors and corporate users, providing the asset with high liquidity',
        '': 'a profile representative of the area\'s socioeconomic fabric, with purchasing power in line with the property\'s positioning',
    }
}

_REVALORIZACION_TEXT = {
    'es': {
        'muy_alto': 'El potencial de revalorización es excepcionalmente alto. La zona se encuentra en plena fase de expansión y transformación urbana, con indicadores que apuntan a incrementos de valor anuales de entre el 8% y el 12%.',
        'alto': 'El potencial de revalorización es sólido y consistente. El mercado local presenta dinámicas de apreciación sostenida, con previsiones de incremento de valor situadas entre el 5% y el 8% anual.',
        'moderado': 'El potencial de revalorización es moderado y estable. El activo se posiciona en una zona madura con crecimiento consolidado, proyectando incrementos anuales de entre el 2% y el 5%.',
        'bajo': 'El mercado presenta una fase de consolidación con revalorizaciones contenidas, si bien el activo ofrece estabilidad patrimonial y flujos de caja predecibles como principales atractivos.',
        '': 'El mercado muestra una evolución positiva con perspectivas de revalorización alineadas a la media del sector.',
    },
    'en': {
        'muy_alto': 'The revaluation potential is exceptionally high. The area is in full expansion and urban transformation, with indicators pointing to annual value increases of between 8% and 12%.',
        'alto': 'The revaluation potential is solid and consistent. The local market presents sustained appreciation dynamics, with value increase forecasts of 5% to 8% annually.',
        'moderado': 'The revaluation potential is moderate and stable. The asset is positioned in a mature area with consolidated growth, projecting annual increases of between 2% and 5%.',
        'bajo': 'The market is in a consolidation phase with contained revaluations, although the asset offers patrimonial stability and predictable cash flows as its main attractions.',
        '': 'The market shows a positive evolution with revaluation prospects in line with the sector average.',
    }
}

_ESTADO_TEXT = {
    'es': {
        'nuevo': 'a estrenar, presentando acabados impecables y todos los sistemas constructivos en perfecto estado',
        'excelente': 'en excelente estado de conservación, listo para ocupar de inmediato sin necesidad de intervención alguna',
        'bueno': 'en buen estado general, con un mantenimiento correcto a lo largo de los años',
        'reformar': 'con necesidad de reforma, lo que abre una oportunidad de creación de valor significativa mediante una inversión estratégica en mejoras',
        'ruina': 'en estado de ruina, ofreciendo una oportunidad de desarrollo desde cero con plena libertad proyectual',
        '': 'con condiciones generales acordes a su antigüedad y tipología',
    },
    'en': {
        'nuevo': 'brand new, with impeccable finishes and all construction systems in perfect condition',
        'excelente': 'in excellent conservation state, ready for immediate occupation without any intervention needed',
        'bueno': 'in good general condition, with proper maintenance over the years',
        'reformar': 'in need of renovation, opening a significant value creation opportunity through strategic investment in improvements',
        'ruina': 'in a state of ruin, offering a development opportunity from scratch with full design freedom',
        '': 'with general conditions in line with its age and typology',
    }
}

_TIPO_TEXT = {
    'es': {
        'apartamento': 'apartamento', 'atico': 'ático penthouse', 'casa': 'casa unifamiliar',
        'villa': 'villa de lujo', 'local': 'local comercial', 'oficina': 'oficina corporativa',
        'solar': 'solar edificable', 'edificio': 'edificio completo', 'nave': 'nave industrial', '': 'inmueble',
    },
    'en': {
        'apartamento': 'apartment', 'atico': 'penthouse', 'casa': 'detached house',
        'villa': 'luxury villa', 'local': 'commercial premises', 'oficina': 'corporate office',
        'solar': 'building plot', 'edificio': 'full building', 'nave': 'industrial unit', '': 'property',
    }
}

_RIESGOS_INV = {
    'es': [
        ('Volatilidad del mercado inmobiliario', 'medio', 'Diversificación geográfica y de activos. Horizonte de inversión a largo plazo (≥5 años). Monitorización trimestral de indicadores de mercado.'),
        ('Vacancia prolongada del activo', 'bajo', 'Precio de alquiler competitivo (≤95% de la media de zona). Reserva de liquidez equivalente a 3 meses de renta. Plan de marketing activo en portales premium.'),
        ('Variación en tipos de interés', 'medio', 'Financiación preferiblemente a tipo fijo o con cobertura de tasa (IRS). Evaluación del impacto en la TIR bajo escenarios de subida de 100-200 bps.'),
        ('Cambios normativos y regulatorios', 'bajo', 'Monitorización continua del marco legal de arrendamientos. Asesoramiento jurídico especializado para adaptación proactiva a nuevas normativas.'),
        ('Deterioro del activo', 'bajo', 'Plan de mantenimiento preventivo con revisión anual. Dotación de reserva para capex equivalente al 1-2% del valor del activo por año.'),
        ('Impago de inquilinos', 'bajo', 'Selección rigurosa de inquilinos con análisis de solvencia. Seguro de impago de alquiler. Avales o garantías adicionales para perfiles de riesgo medio.'),
    ],
    'en': [
        ('Real estate market volatility', 'medium', 'Geographic and asset diversification. Long-term investment horizon (≥5 years). Quarterly monitoring of market indicators.'),
        ('Extended asset vacancy', 'low', 'Competitive rental price (≤95% of area average). Liquidity reserve equivalent to 3 months rent. Active marketing plan on premium portals.'),
        ('Interest rate fluctuation', 'medium', 'Preferably fixed-rate or hedged financing (IRS). Impact assessment on IRR under scenarios of 100-200 bps increase.'),
        ('Regulatory and legal changes', 'low', 'Continuous monitoring of tenancy legal framework. Specialised legal advice for proactive adaptation to new regulations.'),
        ('Asset deterioration', 'low', 'Preventive maintenance plan with annual review. Capex reserve equivalent to 1-2% of asset value per year.'),
        ('Tenant default', 'low', 'Rigorous tenant selection with solvency analysis. Rental default insurance. Additional guarantees for medium-risk profiles.'),
    ]
}

_RIESGOS_PART = {
    'es': [
        ('Evolución del precio del mercado', 'bajo', 'El análisis de zona confirma una tendencia de precios positiva. La ubicación estratégica del inmueble actúa como amortiguador ante correcciones de mercado.'),
        ('Costes de mantenimiento futuros', 'bajo', 'El estado del inmueble minimiza necesidades de reforma inmediata. Plan de mantenimiento preventivo recomendado con dotación anual del 0.5-1% del valor.'),
        ('Cambios en el entorno urbano', 'muy bajo', 'La consolidación del barrio y sus servicios reduce significativamente el riesgo de degradación del entorno residencial.'),
    ],
    'en': [
        ('Market price evolution', 'low', 'The area analysis confirms a positive price trend. The strategic location of the property acts as a buffer against market corrections.'),
        ('Future maintenance costs', 'low', 'The condition of the property minimises immediate renovation needs. Recommended preventive maintenance plan with annual allocation of 0.5-1% of value.'),
        ('Changes in the urban environment', 'very low', 'The consolidation of the neighbourhood and its services significantly reduces the risk of residential environment degradation.'),
    ]
}


# ─── CÁLCULOS FINANCIEROS ────────────────────────────────────────────────────
def calculate_financials(data):
    precio     = safe_float(data.get('precio_venta'))
    renta_mes  = safe_float(data.get('renta_mensual'))
    ocupacion  = safe_float(data.get('ocupacion'), 90) / 100
    gas_com    = safe_float(data.get('gastos_comunidad')) * 12
    ibi        = safe_float(data.get('ibi'))
    otros      = safe_float(data.get('otros_gastos'))
    reforma    = safe_float(data.get('coste_reforma'))
    m2         = safe_float(data.get('metros_construidos'))
    m2_zona    = safe_float(data.get('precio_m2_zona'))

    ingresos_brutos = renta_mes * 12 * ocupacion
    gestion         = ingresos_brutos * 0.10            # 10% gestión estimada
    gastos_totales  = gas_com + ibi + otros + gestion
    ingresos_netos  = ingresos_brutos - gastos_totales
    inversion_total = precio + reforma

    yield_bruto = (ingresos_brutos / precio * 100)       if precio else 0
    yield_neto  = (ingresos_netos  / inversion_total * 100) if inversion_total else 0
    payback     = (inversion_total / ingresos_netos)     if ingresos_netos > 0 else 0
    precio_m2   = precio / m2                            if m2 else 0

    _rev_rate = {'muy_alto': 0.09, 'alto': 0.06, 'moderado': 0.04, 'bajo': 0.02, '': 0.05}
    rev_rate  = _rev_rate.get(data.get('revalorizacion',''), 0.05)
    val_5y    = precio * (1 + rev_rate) ** 5
    ganancia  = val_5y - precio
    roi_5y    = ((ingresos_netos * 5 + ganancia) / inversion_total * 100) if inversion_total else 0

    # Differential vs zone price
    diferencial_m2 = ((precio_m2 - m2_zona) / m2_zona * 100) if m2_zona and precio_m2 else 0

    return {
        'precio': precio, 'inversion_total': inversion_total,
        'ingresos_brutos': ingresos_brutos, 'gestion': gestion,
        'gastos_totales': gastos_totales, 'ingresos_netos': ingresos_netos,
        'yield_bruto': yield_bruto, 'yield_neto': yield_neto,
        'payback': payback, 'roi_5y': roi_5y,
        'precio_m2': precio_m2, 'diferencial_m2': diferencial_m2,
        'rev_rate': rev_rate * 100,
        'gas_com_anual': gas_com, 'ibi': ibi, 'otros': otros, 'gestion': gestion, 'reforma': reforma,
    }


# ─── PUNTUACIONES RADAR ──────────────────────────────────────────────────────
def _score_location(data):
    ciudad = (data.get('ciudad') or '').lower()
    barrio = (data.get('barrio') or '').lower()
    servicios = (data.get('servicios_cercanos') or '').lower()
    dem = data.get('demanda_alquiler', '')
    rev = data.get('revalorizacion', '')

    # Base scores from city tier
    city_tier = 9 if any(c in ciudad for c in ['madrid','barcelona']) else \
                8 if any(c in ciudad for c in ['valencia','sevilla','bilbao','málaga','malaga']) else 7

    dem_score = {'muy_alta': 9.5, 'alta': 8.5, 'media': 7.0, 'baja': 5.5}.get(dem, 7.5)
    rev_score = {'muy_alto': 9.5, 'alto': 8.0, 'moderado': 6.5, 'bajo': 5.0}.get(rev, 7.0)

    # Service scores based on keywords
    def kw_score(text, keywords, base=6.0, bonus=0.5):
        return min(10.0, base + sum(bonus for k in keywords if k in text))

    transp = kw_score(servicios, ['metro','bus','tren','renfe','cercanias','tranvía','tranvia'], 6.5, 0.7)
    serv   = kw_score(servicios, ['hospital','clínica','clinica','salud','farmacia','colegio','escuela','universidad'], 6.5, 0.6)
    comercio = kw_score(servicios, ['comercio','supermercado','restaurante','bar','centro comercial','tienda'], 6.5, 0.6)

    return {
        'conectividad':  round(min(10, city_tier * 0.95), 1),
        'transporte':    round(min(10, transp), 1),
        'servicios':     round(min(10, serv), 1),
        'comercios':     round(min(10, comercio), 1),
        'perfil_socioeconomico': {'lujo':9.5,'ejecutivos':8.5,'familias':7.5,'jovenes':7.0,'turistas':8.0,'mixto':7.5}.get(data.get('perfil_compradores',''),7.0),
        'crecimiento':   round(rev_score, 1),
        'atractivo_residencial': round((city_tier + dem_score) / 2, 1),
        'atractivo_inversor':    round((dem_score + rev_score) / 2, 1),
    }

def _score_investment(data, fin):
    yb   = fin.get('yield_bruto', 0)
    yn   = fin.get('yield_neto',  0)
    dem  = data.get('demanda_alquiler', '')
    rev  = data.get('revalorizacion', '')

    rent_score  = min(10, max(2, yb * 1.4)) if yb else 6.0
    risk_score  = {'muy_alta':8.5,'alta':7.5,'media':6.0,'baja':5.0}.get(dem, 6.5)  # higher demand = lower risk
    liq_score   = {'lujo':7.5,'ejecutivos':8.0,'familias':7.5,'jovenes':7.0,'turistas':8.5,'mixto':7.5}.get(data.get('perfil_compradores',''),7.0)
    escal_score = {'muy_alto':9.0,'alto':7.5,'moderado':6.0,'bajo':4.5}.get(rev, 6.5)
    pos_score   = {'muy_alta':9.0,'alta':8.0,'media':6.5,'baja':5.0}.get(dem, 7.0)
    dem_score   = {'muy_alta':9.5,'alta':8.5,'media':6.5,'baja':5.0}.get(dem, 7.0)
    dif_score   = min(10, 7.0 + abs(fin.get('diferencial_m2', 0)) * 0.05)

    return {
        'rentabilidad':    round(rent_score, 1),
        'seguridad':       round(risk_score, 1),
        'liquidez':        round(liq_score, 1),
        'escalabilidad':   round(escal_score, 1),
        'posicionamiento': round(pos_score, 1),
        'demanda':         round(dem_score, 1),
        'diferenciacion':  round(dif_score, 1),
    }

def _score_premium(data):
    tipo = data.get('tipo_propiedad', '')
    estado = data.get('estado', '')
    feats = data.get('caracteristicas', [])
    if isinstance(feats, str):
        import json
        try: feats = json.loads(feats)
        except: feats = []

    base = {'villa':9.5,'atico':9.0,'casa':7.5,'apartamento':7.0,'local':6.5,'oficina':6.5,'solar':5.5,'edificio':7.0,'nave':5.0}.get(tipo,7.0)
    estado_bonus = {'nuevo':1.5,'excelente':1.0,'bueno':0.3,'reformar':-0.5,'ruina':-1.5}.get(estado,0)
    feat_bonus = min(2.0, len(feats) * 0.15)
    premium_feats = {'domotica','vistas_mar','spa','portero','seguridad','gimnasio'}
    premium_bonus = sum(0.3 for f in feats if f in premium_feats)
    return round(min(10, base + estado_bonus + feat_bonus + premium_bonus), 1)


# ─── ANÁLISIS DE UBICACIÓN ───────────────────────────────────────────────────
def gen_location_analysis(data, scores, lang='es'):
    L = lang
    barrio  = data.get('barrio', '') or data.get('ciudad', 'la zona')
    ciudad  = data.get('ciudad', 'la ciudad')
    dem     = data.get('demanda_alquiler', '')
    perfil  = data.get('perfil_compradores', '')
    servicios = data.get('servicios_cercanos', '')
    tendencia = data.get('tendencia_mercado', '')
    rev     = data.get('revalorizacion', '')

    dem_t  = _DEMANDA_TEXT[L].get(dem,  _DEMANDA_TEXT[L][''])
    perf_t = _PERFIL_TEXT[L].get(perfil, _PERFIL_TEXT[L][''])
    rev_t  = _REVALORIZACION_TEXT[L].get(rev, _REVALORIZACION_TEXT[L][''])

    if L == 'es':
        p1 = f"El inmueble se ubica en {barrio}, {ciudad}, un enclave estratégico caracterizado por {dem_t}. El tejido socioeconómico de la zona corresponde a {perf_t}."
        p2 = f"Desde una perspectiva de conectividad y equipamiento urbano, la ubicación presenta una puntuación de {scores['conectividad']}/10 en conectividad general y {scores['transporte']}/10 en accesibilidad por transporte público."
        p3 = f"El score de servicios de la zona alcanza {scores['servicios']}/10, reflejo de su dotación en equipamientos sanitarios, educativos y asistenciales, mientras que el dinamismo comercial y de restauración puntúa {scores['comercios']}/10."
        p4 = rev_t
        p5 = f"El índice de atractivo inversor de la zona se sitúa en {scores['atractivo_inversor']}/10, sustentado por una demanda robusta y perspectivas de apreciación favorables a medio y largo plazo."
        if servicios:
            p_serv = f"\n\nEn cuanto al equipamiento urbano próximo, el inmueble cuenta con acceso directo a: {servicios}. Esta dotación refuerza de forma notable el posicionamiento del activo."
        else:
            p_serv = ""
        if tendencia:
            p_tend = f"\n\nSituación actual del mercado: {tendencia}"
        else:
            p_tend = f"\n\nEl mercado inmobiliario en {ciudad} mantiene una dinámica positiva con tendencia al alza en activos bien ubicados."
        return p1 + "\n\n" + p2 + " " + p3 + "\n\n" + p4 + p_serv + p_tend
    else:
        p1 = f"The property is located in {barrio}, {ciudad}, a strategic enclave characterised by {dem_t}. The socioeconomic fabric of the area corresponds to {perf_t}."
        p2 = f"From a connectivity and urban infrastructure perspective, the location scores {scores['conectividad']}/10 in general connectivity and {scores['transporte']}/10 in public transport accessibility."
        p3 = f"The area's services score reaches {scores['servicios']}/10, reflecting its healthcare, educational and welfare facilities, while commercial and dining dynamism scores {scores['comercios']}/10."
        p4 = rev_t
        p5 = f"The area's investor attractiveness index stands at {scores['atractivo_inversor']}/10, underpinned by robust demand and favourable appreciation prospects in the medium and long term."
        if servicios:
            p_serv = f"\n\nRegarding nearby urban facilities, the property has direct access to: {servicios}. This provision notably reinforces the asset's positioning."
        else:
            p_serv = ""
        if tendencia:
            p_tend = f"\n\nCurrent market situation: {tendencia}"
        else:
            p_tend = f"\n\nThe real estate market in {ciudad} maintains positive dynamics with an upward trend in well-located assets."
        return p1 + "\n\n" + p2 + " " + p3 + "\n\n" + p4 + p_serv + p_tend


# ─── ANÁLISIS FINANCIERO ─────────────────────────────────────────────────────
def gen_financial_analysis(data, fin, lang='es'):
    if fin['ingresos_brutos'] <= 0:
        if lang == 'es':
            return "No se han facilitado datos de renta para el cálculo de rentabilidad. El análisis financiero se puede completar una vez se establezca el precio de mercado del alquiler para la zona."
        else:
            return "No rental data has been provided for profitability calculation. The financial analysis can be completed once the market rental price for the area has been established."
    L = lang
    yb  = fin['yield_bruto']
    yn  = fin['yield_neto']
    pb  = fin['payback']
    r5y = fin['roi_5y']

    # Reference yields by type
    tipo = data.get('tipo_propiedad', '')
    ref_yields = {'apartamento':5.5,'atico':4.8,'casa':4.5,'villa':3.8,'local':6.5,'oficina':6.0,'edificio':5.8}
    ref = ref_yields.get(tipo, 5.0)
    vs_market = yb - ref

    if L == 'es':
        p1 = f"El análisis de rentabilidad del activo arroja una yield bruta del {fmt_pct(yb)}, situándose {'por encima' if vs_market > 0 else 'en línea'} de la media del mercado para activos de esta tipología en la zona ({fmt_pct(ref)} de referencia)."
        p2 = f"Una vez descontados los costes operativos estimados (gestión, comunidad, IBI y otros), la rentabilidad neta del activo se establece en el {fmt_pct(yn)}, con un cash flow anual neto de {fmt_eur(fin['ingresos_netos'])}."
        if pb > 0:
            p3 = f"El período de recuperación de la inversión (payback) se estima en {pb:.1f} años bajo un escenario de referencia con ocupación del {data.get('ocupacion','90')}%."
        else:
            p3 = ""
        p4 = f"Considerando una tasa de revalorización anual estimada del {fmt_pct(fin['rev_rate'],1)}, el ROI proyectado a 5 años alcanza el {fmt_pct(r5y)}, incluyendo tanto los ingresos recurrentes por alquiler como la ganancia patrimonial por apreciación del activo."
        return p1 + "\n\n" + p2 + " " + p3 + "\n\n" + p4
    else:
        p1 = f"The asset's profitability analysis yields a gross yield of {fmt_pct(yb)}, positioning it {'above' if vs_market > 0 else 'in line with'} the market average for assets of this typology in the area ({fmt_pct(ref)} reference)."
        p2 = f"Once estimated operating costs are deducted (management, community fees, property tax and others), the net yield of the asset stands at {fmt_pct(yn)}, with an annual net cash flow of {fmt_eur(fin['ingresos_netos'])}."
        if pb > 0:
            p3 = f"The investment payback period is estimated at {pb:.1f} years under a reference scenario with {data.get('ocupacion','90')}% occupancy."
        else:
            p3 = ""
        p4 = f"Considering an estimated annual appreciation rate of {fmt_pct(fin['rev_rate'],1)}, the projected 5-year ROI reaches {fmt_pct(r5y)}, including both recurring rental income and capital gains from asset appreciation."
        return p1 + "\n\n" + p2 + " " + p3 + "\n\n" + p4


# ─── NARRATIVA COMERCIAL ─────────────────────────────────────────────────────
def gen_commercial_narrative(data, fin, premium_score, lang='es'):
    tipo  = _TIPO_TEXT[lang].get(data.get('tipo_propiedad',''), _TIPO_TEXT[lang][''])
    barrio = data.get('barrio','') or data.get('ciudad', '')
    ciudad = data.get('ciudad','')
    estado_t = _ESTADO_TEXT[lang].get(data.get('estado',''), _ESTADO_TEXT[lang][''])
    precio = fmt_eur(data.get('precio_venta'))
    m2     = data.get('metros_construidos','')
    descripcion = data.get('descripcion','')

    feats = data.get('caracteristicas', [])
    if isinstance(feats, str):
        import json
        try: feats = json.loads(feats)
        except: feats = []

    feat_names_es = {'ascensor':'ascensor','aire_acondicionado':'climatización','calefaccion':'calefacción central','amueblado':'mobiliario de diseño','seguridad':'sistema de seguridad','piscina':'piscina','parking':'parking privado','terraza':'terraza','jardin':'jardín','trastero':'trastero','domotica':'domótica integrada','vistas_mar':'vistas al mar','vistas_ciudad':'vistas panorámicas','portero':'portería física','gimnasio':'gimnasio','spa':'zona spa'}
    feat_names_en = {'ascensor':'elevator','aire_acondicionado':'air conditioning','calefaccion':'central heating','amueblado':'designer furniture','seguridad':'security system','piscina':'swimming pool','parking':'private parking','terraza':'terrace','jardin':'garden','trastero':'storage room','domotica':'integrated home automation','vistas_mar':'sea views','vistas_ciudad':'panoramic city views','portero':'concierge service','gimnasio':'gymnasium','spa':'spa & wellness area'}
    feat_names = feat_names_es if lang == 'es' else feat_names_en
    feat_list = [feat_names.get(f, f) for f in feats[:6]]

    if lang == 'es':
        p1 = f"Presentamos una singular oportunidad de adquisición de este exclusivo {tipo} situado en {barrio}, {ciudad} — un activo que combina una posición de mercado privilegiada con un posicionamiento premium de {premium_score}/10 puntos sobre la escala de excelencia inmobiliaria."
        p2 = f"El inmueble se encuentra {estado_t}, con una superficie de {m2} m² distribuida de forma eficiente y funcional. A un precio de {precio}, el activo presenta una ecuación valor-precio altamente competitiva respecto al mercado de referencia de la zona."
        if descripcion:
            desc_clean = descripcion.strip().rstrip('.')
            p3 = (f"En cuanto a sus características interiores, {desc_clean[0].lower()}{desc_clean[1:]}. "
                  f"Un conjunto que refleja el cuidado puesto en cada detalle y el nivel de confort que define a los activos de este segmento.")
        else:
            p3 = f"Las calidades constructivas y los acabados del inmueble responden al más alto estándar del segmento, con especial atención al detalle y al confort de sus ocupantes."
        if feat_list:
            feats_str = ', '.join(feat_list[:-1]) + (' y ' + feat_list[-1] if len(feat_list) > 1 else (feat_list[0] if feat_list else ''))
            p4 = f"Entre sus prestaciones más destacadas, el inmueble cuenta con {feats_str}, dotando al activo de un valor añadido diferencial en el mercado."
        else:
            p4 = "El inmueble presenta una configuración completa y funcional, pensada para maximizar el confort y la experiencia de sus ocupantes."
        return p1 + "\n\n" + p2 + "\n\n" + p3 + "\n\n" + p4
    else:
        p1 = f"We present a unique acquisition opportunity for this exclusive {tipo} located in {barrio}, {ciudad} — an asset that combines a privileged market position with a premium rating of {premium_score}/10 on the real estate excellence scale."
        p2 = f"The property is {estado_t}, with a {m2} m² surface area distributed in an efficient and functional manner. At a price of {precio}, the asset presents a highly competitive value-price equation relative to the area's reference market."
        if descripcion:
            desc_clean = descripcion.strip().rstrip('.')
            p3 = (f"As for its interior characteristics, {desc_clean[0].lower()}{desc_clean[1:]}. "
                  f"A combination that reflects the care put into every detail and the level of comfort that defines assets in this segment.")
        else:
            p3 = "The construction qualities and finishes of the property meet the highest standard in the segment, with special attention to detail and occupant comfort."
        if feat_list:
            feats_str = ', '.join(feat_list[:-1]) + (' and ' + feat_list[-1] if len(feat_list) > 1 else (feat_list[0] if feat_list else ''))
            p4 = f"Among its most notable features, the property includes {feats_str}, providing the asset with a differential added value in the market."
        else:
            p4 = "The property presents a complete and functional configuration, designed to maximise comfort and the experience of its occupants."
        return p1 + "\n\n" + p2 + "\n\n" + p3 + "\n\n" + p4


# ─── RESUMEN EJECUTIVO ────────────────────────────────────────────────────────
def gen_executive_summary(data, fin, loc_scores, inv_scores, premium_score, tipo_dossier, lang='es'):
    tipo  = _TIPO_TEXT[lang].get(data.get('tipo_propiedad',''), _TIPO_TEXT[lang][''])
    barrio = data.get('barrio','') or data.get('ciudad','')
    ciudad = data.get('ciudad','')
    precio = fmt_eur(data.get('precio_venta'))
    m2     = data.get('metros_construidos','')
    avg_loc = round(sum(loc_scores.values()) / len(loc_scores), 1)
    avg_inv = round(sum(inv_scores.values()) / len(inv_scores), 1) if inv_scores else 0

    if lang == 'es':
        if tipo_dossier == 'inversores':
            lines = [
                f"El presente dossier analiza en profundidad la oportunidad de inversión que representa este {tipo} ubicado en {barrio}, {ciudad}.",
                f"Con un precio de salida de {precio} ({m2} m²), el activo ofrece un perfil de rentabilidad-riesgo altamente atractivo para inversores institucionales y particulares con visión patrimonial.",
                f"El análisis de ubicación sitúa al inmueble en una zona con índice de atractivo global de {avg_loc}/10, mientras que el análisis de inversión arroja una puntuación media de {avg_inv}/10 en los factores clave de evaluación.",
                f"Se recomienda su consideración como activo de cartera de alta convicción, con sólidos fundamentos de mercado y perspectivas de rentabilidad total superior a la media del sector.",
            ]
        else:
            lines = [
                f"El presente dossier presenta de manera estratégica y persuasiva este exclusivo {tipo} ubicado en {barrio}, {ciudad}, concebido para el comprador que busca calidad de vida excepcional.",
                f"Con una puntuación de excelencia inmobiliaria de {premium_score}/10 y un índice de calidad de zona de {avg_loc}/10, este inmueble representa una oportunidad singular en el mercado actual.",
                f"El activo se posiciona en el segmento premium del mercado local, con características diferenciadas y un entorno urbano de primer nivel.",
            ]
        return "\n\n".join(lines)
    else:
        if tipo_dossier == 'inversores':
            lines = [
                f"This dossier provides an in-depth analysis of the investment opportunity represented by this {tipo} located in {barrio}, {ciudad}.",
                f"With an asking price of {precio} ({m2} m²), the asset offers a highly attractive risk-return profile for institutional and private investors with a wealth management perspective.",
                f"The location analysis places the property in an area with a global attractiveness index of {avg_loc}/10, while the investment analysis yields an average score of {avg_inv}/10 across key evaluation factors.",
                f"We recommend its consideration as a high-conviction portfolio asset, with solid market fundamentals and total return prospects above the sector average.",
            ]
        else:
            lines = [
                f"This dossier strategically and persuasively presents this exclusive {tipo} located in {barrio}, {ciudad}, conceived for the buyer seeking exceptional quality of life.",
                f"With a real estate excellence score of {premium_score}/10 and a zone quality index of {avg_loc}/10, this property represents a unique opportunity in today's market.",
                f"The asset is positioned in the premium segment of the local market, with differentiated features and a first-class urban environment.",
            ]
        return "\n\n".join(lines)


# ─── ANÁLISIS COMERCIAL ───────────────────────────────────────────────────────
def gen_commercial_analysis(data, fin, premium_score, lang='es'):
    tipo  = _TIPO_TEXT[lang].get(data.get('tipo_propiedad',''), _TIPO_TEXT[lang][''])
    barrio = data.get('barrio','') or data.get('ciudad','')
    perfil = data.get('perfil_compradores','')
    dem    = data.get('demanda_alquiler','')
    tipo_dossier = data.get('tipo_dossier','inversores')

    _perfil_buyer_es = {
        'lujo': 'Familia o particular de alto poder adquisitivo, UHNWI, Family Office o fondo de inversión buscando activos trophy. Valora exclusividad, privacidad y activos sin comparación directa en mercado.',
        'ejecutivos': 'Directivo o alto profesional (35-55 años), inversor sofisticado o empresa buscando activo corporativo. Prioriza ubicación, conectividad y calidad de acabados.',
        'familias': 'Familia con hijos (30-50 años), buscando estabilidad, zona segura, servicios educativos y espacio de vida. Decisión emocional y racional combinada.',
        'jovenes': 'Profesional joven (25-38 años), alta movilidad urbana, sensible al precio por m², valoriza diseño contemporáneo y proximidad a centros de ocio y transporte.',
        'turistas': 'Inversor turístico o fondo de short-term rentals. Prioriza rentabilidad por m² en periodo de alta demanda vacacional y existencia o posibilidad de licencia.',
        'mixto': 'Perfil amplio y diversificado: tanto inversor puro como usuario final o perfil mixto. El activo admite múltiples estrategias de monetización.',
        '': 'Comprador potencial con perfil alineado al posicionamiento premium del activo y la zona.',
    }
    _perfil_buyer_en = {
        'lujo': 'High net worth individual, UHNWI, Family Office or investment fund seeking trophy assets. Values exclusivity, privacy and assets without direct market comparison.',
        'ejecutivos': 'Executive or senior professional (35-55 years), sophisticated investor or company seeking a corporate asset. Prioritises location, connectivity and finish quality.',
        'familias': 'Family with children (30-50 years), seeking stability, safe area, educational services and living space. Combined emotional and rational decision.',
        'jovenes': 'Young professional (25-38 years), high urban mobility, price-per-m² sensitive, values contemporary design and proximity to leisure and transport hubs.',
        'turistas': 'Tourism investor or short-term rental fund. Prioritises yield per m² in high vacation demand periods and existence or possibility of tourist licence.',
        'mixto': 'Broad and diversified profile: both pure investor and end user or mixed profile. The asset supports multiple monetisation strategies.',
        '': 'Potential buyer with a profile aligned to the premium positioning of the asset and the area.',
    }
    buyer = (_perfil_buyer_es if lang == 'es' else _perfil_buyer_en).get(perfil, '')
    if not buyer:
        buyer = (_perfil_buyer_es if lang == 'es' else _perfil_buyer_en)['']

    if lang == 'es':
        prop_valor = f"Activo {tipo} de alto posicionamiento en {barrio}, con una puntuación de excelencia de {premium_score}/10, dotado de características diferenciales y ubicación estratégica en una zona de alta demanda."
        args = [
            f"Ubicación de primer nivel con índice de conectividad y servicios en el cuartil superior del mercado local",
            f"Posicionamiento premium con puntuación de excelencia de {premium_score}/10 sobre escala de referencia del sector",
            f"Demanda {'muy alta' if dem in ['muy_alta','alta'] else 'activa'} en la zona que garantiza alta ocupabilidad y mínimo riesgo de vacancia",
            f"Perspectivas de revalorización favorables alineadas con la tendencia del mercado en {data.get('ciudad','la ciudad')}",
        ]
        if fin.get('yield_bruto', 0) > 0:
            args.append(f"Yield bruta del {fmt_pct(fin['yield_bruto'])} que supera la media del mercado para activos comparables")
        oportunidades = [
            f"Reposicionamiento de precio tras reforma de calidad: potencial de incremento de valor del 15-25%",
            f"Adaptación al segmento turístico-vacacional si obtención de licencia: multiplicador de rentabilidad ×1.8-×2.5",
            f"Mercado con escasez estructural de oferta premium: margen de negociación reducido a favor del vendedor",
        ]
        return {
            'propuesta_valor': prop_valor,
            'argumentos': args,
            'oportunidades': oportunidades,
            'perfil_comprador': buyer,
        }
    else:
        prop_valor = f"High-positioning {tipo} asset in {barrio}, with an excellence score of {premium_score}/10, endowed with differential features and strategic location in a high-demand area."
        args = [
            f"First-class location with connectivity and services index in the upper quartile of the local market",
            f"Premium positioning with excellence score of {premium_score}/10 on sector reference scale",
            f"{'Very high' if dem in ['muy_alta','alta'] else 'Active'} demand in the area guaranteeing high occupancy and minimal vacancy risk",
            f"Favourable revaluation prospects aligned with market trend in {data.get('ciudad','the city')}",
        ]
        if fin.get('yield_bruto', 0) > 0:
            args.append(f"Gross yield of {fmt_pct(fin['yield_bruto'])} exceeding market average for comparable assets")
        oportunidades = [
            f"Price repositioning after quality renovation: potential value increase of 15-25%",
            f"Adaptation to tourist-vacation segment upon licence obtainment: yield multiplier ×1.8-×2.5",
            f"Market with structural shortage of premium supply: reduced negotiation margin in favour of seller",
        ]
        return {
            'propuesta_valor': prop_valor,
            'argumentos': args,
            'oportunidades': oportunidades,
            'perfil_comprador': buyer,
        }


# ─── CONCLUSIONES ─────────────────────────────────────────────────────────────
def gen_conclusions(data, fin, loc_scores, inv_scores, premium_score, lang='es'):
    tipo  = _TIPO_TEXT[lang].get(data.get('tipo_propiedad',''), _TIPO_TEXT[lang][''])
    barrio = data.get('barrio','') or data.get('ciudad','')
    tipo_dossier = data.get('tipo_dossier','inversores')
    avg_loc = round(sum(loc_scores.values()) / len(loc_scores), 1)
    overall = round((avg_loc + premium_score) / 2, 1)

    if lang == 'es':
        if tipo_dossier == 'inversores':
            texto = f"Este {tipo} en {barrio} reúne los atributos fundamentales de un activo de inversión de alta convicción: ubicación estratégica con índice de calidad {avg_loc}/10, perfil de rentabilidad competitivo y perspectivas de apreciación favorables a medio-largo plazo. La puntuación global del activo sobre el índice de excelencia inmobiliaria se establece en {overall}/10."
            recs = [
                "Realizar due diligence documental completa (cargas, nota registral, ITE, cédula de habitabilidad)",
                f"Valorar la contratación de un seguro de impago de alquiler para optimizar el perfil de riesgo",
                "Estudiar la optimización fiscal de la renta mediante amortización y deducción de gastos permitidos",
                "Evaluar el potencial de incremento de renta vía reforma cosmética con inversión controlada",
            ]
        else:
            texto = f"Este {tipo} en {barrio} representa una oportunidad única de adquisición en el mercado actual, combinando calidad de vida excepcional con un posicionamiento premium. La puntuación global del activo en el índice de excelencia inmobiliaria es de {overall}/10."
            recs = [
                "Verificar documentación completa del inmueble antes de la firma de arras",
                "Solicitar informes técnicos de estado general del edificio (ITE) si aplica",
                "Consultar con arquitecto para valorar posibles mejoras y reforma personalizada",
                "Negociar condiciones de financiación con múltiples entidades bancarias",
            ]
    else:
        if tipo_dossier == 'inversores':
            texto = f"This {tipo} in {barrio} brings together the fundamental attributes of a high-conviction investment asset: strategic location with quality index {avg_loc}/10, competitive return profile and favourable medium-to-long term appreciation prospects. The asset's overall score on the real estate excellence index is established at {overall}/10."
            recs = [
                "Conduct complete documentary due diligence (encumbrances, land registry note, technical inspections)",
                f"Consider rental default insurance to optimise the risk profile",
                "Study fiscal optimisation of rental income through depreciation and permitted expense deductions",
                "Evaluate rent increase potential via cosmetic renovation with controlled investment",
            ]
        else:
            texto = f"This {tipo} in {barrio} represents a unique acquisition opportunity in today's market, combining exceptional quality of life with premium positioning. The asset's overall score on the real estate excellence index is {overall}/10."
            recs = [
                "Verify complete property documentation before signing the preliminary contract",
                "Request technical inspection reports for the building's general condition (ITE) if applicable",
                "Consult with an architect to assess possible improvements and personalised renovation",
                "Negotiate financing conditions with multiple banking institutions",
            ]

    return {'texto': texto, 'recomendaciones': recs, 'overall': overall}


# ─── ANÁLISIS DE ZONA PARA PARTICULARES ──────────────────────────────────────
def gen_lifestyle_analysis(data, scores, lang='es'):
    barrio  = data.get('barrio','') or data.get('ciudad','')
    ciudad  = data.get('ciudad','')
    servicios = data.get('servicios_cercanos','')

    if lang == 'es':
        p1 = f"Vivir en {barrio}, {ciudad} es mucho más que elegir una dirección: es adoptar un estilo de vida. La zona ofrece un equilibrio único entre la vibración urbana y la calidad residencial, con acceso privilegiado a servicios de primer nivel."
        p2 = f"El entorno inmediato puntúa {scores['servicios']}/10 en equipamientos y servicios, reflejo de una dotación completa que cubre todas las necesidades cotidianas. La conectividad general alcanza {scores['conectividad']}/10, facilitando el acceso a cualquier punto de la ciudad en tiempos reducidos."
        if servicios:
            p3 = f"Entre los principales servicios y puntos de interés accesibles desde el inmueble se encuentran: {servicios}."
        else:
            p3 = f"La zona cuenta con todos los servicios urbanos necesarios para una vida cómoda y de calidad."
        p4 = f"El perfil socioeconómico del barrio, con una puntuación de {scores['perfil_socioeconomico']}/10, garantiza un entorno residencial tranquilo, seguro y de alto nivel, donde el bienestar de sus residentes es una prioridad compartida."
        return p1 + "\n\n" + p2 + "\n\n" + p3 + "\n\n" + p4
    else:
        p1 = f"Living in {barrio}, {ciudad} is much more than choosing an address: it's adopting a lifestyle. The area offers a unique balance between urban vibrancy and residential quality, with privileged access to first-class services."
        p2 = f"The immediate surroundings score {scores['servicios']}/10 in facilities and services, reflecting a comprehensive provision covering all daily needs. General connectivity reaches {scores['conectividad']}/10, facilitating access to any point in the city in reduced times."
        if servicios:
            p3 = f"Among the main services and points of interest accessible from the property are: {servicios}."
        else:
            p3 = f"The area has all the urban services necessary for a comfortable, quality life."
        p4 = f"The neighbourhood's socioeconomic profile, scoring {scores['perfil_socioeconomico']}/10, guarantees a peaceful, safe and high-standard residential environment where residents' wellbeing is a shared priority."
        return p1 + "\n\n" + p2 + "\n\n" + p3 + "\n\n" + p4


# ─── FUNCIÓN PRINCIPAL ────────────────────────────────────────────────────────
def generate_all_content(data):
    """
    Genera todo el contenido del dossier a partir de los datos del formulario.
    Retorna un diccionario estructurado con todos los textos, scores y análisis.
    """
    lang = data.get('idioma', 'es')
    tipo_dossier = data.get('tipo_dossier', 'inversores')

    # Calcular financieros
    fin = calculate_financials(data)

    # Scores
    loc_scores = _score_location(data)
    inv_scores = _score_investment(data, fin) if tipo_dossier == 'inversores' else {}
    premium    = _score_premium(data)

    # Textos
    exec_summary = gen_executive_summary(data, fin, loc_scores, inv_scores, premium, tipo_dossier, lang)

    if tipo_dossier == 'inversores':
        zona_text = gen_location_analysis(data, loc_scores, lang)
    else:
        zona_text = gen_lifestyle_analysis(data, loc_scores, lang)

    financial_text = gen_financial_analysis(data, fin, lang) if tipo_dossier == 'inversores' else ''
    narrative      = gen_commercial_narrative(data, fin, premium, lang)
    commercial     = gen_commercial_analysis(data, fin, premium, lang)
    conclusions    = gen_conclusions(data, fin, loc_scores, inv_scores, premium, lang)

    riesgos = (_RIESGOS_INV if tipo_dossier == 'inversores' else _RIESGOS_PART)[lang]

    # Image recommendations
    tipo_txt = _TIPO_TEXT[lang].get(data.get('tipo_propiedad',''), _TIPO_TEXT[lang][''])
    barrio = data.get('barrio','') or data.get('ciudad','')
    if lang == 'es':
        img_recs = {
            'portada': f"Fotografía exterior frontal del inmueble a última hora de la tarde (golden hour), resaltando la fachada y el entorno",
            'galeria': f"Secuencia de interiores: salón principal, cocina, dormitorio principal y baño — luz natural, gran angular",
            'lifestyle': f"Imágenes de estilo de vida en la zona: terrazas, restaurantes y espacios verdes de {barrio}",
            'zona': f"Vista aérea o panorámica del barrio {barrio} y sus accesos principales",
            'cierre': f"Detalle arquitectónico premium del inmueble o vista de las vistas más destacadas",
        }
    else:
        img_recs = {
            'portada': f"Front exterior photograph of the property at golden hour, highlighting the facade and surroundings",
            'galeria': f"Interior sequence: main living room, kitchen, master bedroom and bathroom — natural light, wide angle",
            'lifestyle': f"Lifestyle images in the area: terraces, restaurants and green spaces of {barrio}",
            'zona': f"Aerial or panoramic view of {barrio} neighbourhood and its main access routes",
            'cierre': f"Premium architectural detail of the property or view of the most outstanding views",
        }

    return {
        'financials':      fin,
        'loc_scores':      loc_scores,
        'inv_scores':      inv_scores,
        'premium_score':   premium,
        'exec_summary':    exec_summary,
        'zona_text':       zona_text,
        'financial_text':  financial_text,
        'narrative':       narrative,
        'commercial':      commercial,
        'conclusions':     conclusions,
        'riesgos':         riesgos,
        'img_recs':        img_recs,
    }
