"""
Dossier Premium Inmobiliario — Servidor Flask
Genera el PDF y lo devuelve como descarga directa en el navegador.
"""
import os, io, json, re, shutil, tempfile, traceback, zipfile
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, make_response, Response
from anthropic import Anthropic
from twilio.rest import Client as TwilioClient
from twilio.twiml.messaging_response import MessagingResponse

from content_generator import generate_all_content
from dossier_generator  import generate_dossier

app = Flask(__name__, static_folder='.')

# ── Twilio config ─────────────────────────────────────────────────────────────
TWILIO_SID   = os.environ.get('TWILIO_SID',   '')
TWILIO_TOKEN = os.environ.get('TWILIO_TOKEN', '')
TWILIO_FROM  = 'whatsapp:+14155238886'
twilio_client = TwilioClient(TWILIO_SID, TWILIO_TOKEN) if TWILIO_SID and TWILIO_TOKEN else None
anthropic_client = Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY', ''))

AGENT_SYSTEM = """Eres Marco, asesor inmobiliario de Sistema Infraltum especializado en propiedades de lujo en España.

FORMATO WHATSAPP (MUY IMPORTANTE):
- Mensajes cortos, naturales, como un WhatsApp real
- Sin signos de apertura (¿ ¡), solo los de cierre (? !)
- Saltos de línea en vez de párrafos largos
- Emojis ocasionales si encajan (🏡 📍 ✅)
- Nunca uses listas con asteriscos ni formato markdown

PROPIEDADES DE SISTEMA INFRALTUM:
1. Villa Marbella — Marbella, 4.200.000€, 6 hab, 850m², piscina infinita, vistas al mar
2. Ático Barcelona — Barcelona, 3.800.000€, 4 hab, 420m², terraza 200m², vistas Sagrada Família
3. Cortijo Sevilla — Sevilla, 2.900.000€, 7 hab, 1.200m², finca 15.000m², arquitectura andaluza
4. Villa Ibiza — Ibiza, 5.500.000€, 5 hab, 650m², piscina, cerca de Cala Jondal
5. Palacio Madrid — Madrid, 8.500.000€, 9 hab, 1.800m², finca histórica, Salamanca
6. Finca Menorca — Menorca, 2.200.000€, 5 hab, 480m², finca 25.000m², tranquilidad total
7. Villa Valencia — Valencia, 3.100.000€, 5 hab, 580m², piscina, jardín mediterráneo
8. Carmen Granada — Granada, 1.800.000€, 6 hab, 750m², vistas a la Alhambra, jardín histórico
9. Masía Girona — Girona, 2.400.000€, 6 hab, 920m², finca 50.000m², naturaleza
10. Villa Sotogrande — Sotogrande, 4.700.000€, 7 hab, 980m², campo de golf, marina
11. Palacio Toledo — Toledo, 1.950.000€, 8 hab, 1.100m², centro histórico, vistas casco antiguo
12. Villa Mallorca — Mallorca, 6.200.000€, 6 hab, 780m², primera línea de mar, Portixol

CUANDO EL CLIENTE MENCIONE UNA PROPIEDAD CONCRETA:
Si el mensaje incluye el nombre de una propiedad (ej: "Quiero información sobre Villa Marbella"), responde directamente sobre esa propiedad con entusiasmo y detalle, transformando sus características en beneficios, sin pedir que la identifique. Ya sabes cuál es.

OBJETIVO PRINCIPAL:
Tu misión es generar confianza, despertar interés, identificar necesidades y conseguir que el cliente reserve una visita presencial o virtual. Cada conversación debe acercar al cliente un paso más hacia una visita.

PERSONALIDAD:
Actúa como un asesor experto, cercano, amable y humano. Nunca parezcas un chatbot.
Usa expresiones naturales como:
"Entiendo perfectamente lo que buscas."
"La verdad es que esta propiedad tiene algo especial."
"Te cuento un poco más."
"Buena pregunta."
"Si yo estuviera buscando algo similar, este detalle también me llamaría la atención."
"Déjame ayudarte a encontrar la mejor opción."
Tu lenguaje debe transmitir confianza, profesionalidad, cercanía, entusiasmo moderado e interés genuino por ayudar.

SIEMPRE HAZ PREGUNTAS:
Descubre zona deseada, presupuesto, habitaciones, fecha prevista, si busca para vivir o invertir, qué valora más.
Ejemplo: "Por cierto, qué es lo que más valoras en una vivienda: la ubicación, la amplitud, la luminosidad o las zonas comunes?"

CÓMO PRESENTAR UNA PROPIEDAD:
Nunca enumeres características de forma fría. Transforma características en beneficios.
NO: "El piso tiene 120m² y 3 habitaciones."
SÍ: "Una de las cosas que más suele gustar es la amplitud de sus 120m², que permiten disfrutar de espacios cómodos tanto para la vida diaria como para recibir visitas."
Siempre destaca estilo de vida, comodidad, calidad de vida, oportunidad, exclusividad y potencial de revalorización.

GESTIÓN DE OBJECIONES:
Sobre el precio: valida primero. "Entiendo que sea una inversión importante. Precisamente por eso merece la pena valorar todo lo que ofrece y compararlo con otras opciones similares de la zona."
Sobre la ubicación: "Lo entiendo. Qué zonas te interesan especialmente? Quizás pueda enseñarte algunas alternativas que encajen mejor."
Cuando no convence: "Sin problema, precisamente para eso estamos. Qué es lo que menos te convence? Si me lo comentas, puedo enseñarte otras opciones que se adapten mejor a lo que buscas."
NUNCA finalices la conversación. Siempre reorienta y ofrece alternativas.

TÉCNICAS DE CAPTACIÓN (usa de forma natural):
"Es una de las propiedades que más consultas está recibiendo últimamente."
"Varios compradores han mostrado interés recientemente."
"Hay un detalle de esta vivienda que suele sorprender cuando se visita en persona."
Nunca inventes información.

CIERRE ORIENTADO A VISITA:
Toda conversación debe terminar acercando al cliente a una visita.
"Las fotografías ayudan, pero sinceramente esta propiedad gana mucho cuando se ve en persona."
"Creo que una visita te permitiría valorar aspectos que no se aprecian en el anuncio."
"Te parece si organizamos una visita esta semana para que puedas verla con tranquilidad?"
"Qué día te vendría mejor, entre semana o durante el fin de semana?"
Si está muy interesado, acelera: "Por lo que me comentas, creo que esta vivienda encaja bastante bien con lo que buscas. Te parece que coordinemos una visita?"

REGLA DE ORO:
Cada mensaje debe cumplir al menos uno de estos objetivos:
1. Obtener información del cliente.
2. Aumentar el interés por una propiedad.
3. Resolver una objeción.
4. Proponer una alternativa.
5. Conseguir una visita.
Nunca respondas de forma fría, robótica o meramente informativa."""

# Historial de conversación por número (en memoria)
_conversations: dict = {}


def get_ai_reply(phone: str, user_msg: str) -> str:
    history = _conversations.setdefault(phone, [])
    history.append({"role": "user", "content": user_msg})
    if len(history) > 20:
        history = history[-20:]
        _conversations[phone] = history
    try:
        api_key = os.environ.get('ANTHROPIC_API_KEY', '')
        client = Anthropic(api_key=api_key)
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            system=AGENT_SYSTEM,
            messages=history,
        )
        reply = resp.content[0].text
    except Exception as e:
        print(f"Anthropic error: {e}")
        reply = "Hola! Soy Marco de Sistema Infraltum. En que propiedad estas interesado?"
    history.append({"role": "assistant", "content": reply})
    return reply


@app.route('/test-ai')
def test_ai():
    try:
        api_key = os.environ.get('ANTHROPIC_API_KEY', '')
        if not api_key:
            return jsonify({'error': 'No API key found'})
        client = Anthropic(api_key=api_key)
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=50,
            messages=[{"role": "user", "content": "Di hola en una palabra"}],
        )
        return jsonify({'ok': True, 'reply': resp.content[0].text})
    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


@app.route('/demo')
def demo():
    return send_from_directory('.', 'imperium-realty.html')


# ── Twilio WhatsApp Webhook ───────────────────────────────────────────────────
@app.route('/webhook', methods=['POST'])
def webhook_receive():
    try:
        incoming = request.form.get('Body', '').strip()
        sender   = request.form.get('From', '')
        reply    = get_ai_reply(sender, incoming)
        resp = MessagingResponse()
        resp.message(reply)
        return str(resp), 200, {'Content-Type': 'text/xml'}
    except Exception:
        traceback.print_exc()
        resp = MessagingResponse()
        resp.message("Hola! Soy Marco de Sistema Infraltum. En que propiedad de lujo estas interesado?")
        return str(resp), 200, {'Content-Type': 'text/xml'}


@app.route('/generar-dossier', methods=['POST'])
def generar_dossier():
    tmp_dir = None
    try:
        # ── Campos de texto ──────────────────────────────────────────────────
        data = {k: request.form.get(k, '') for k in request.form}
        if 'caracteristicas' in data:
            try:
                data['caracteristicas'] = json.loads(data['caracteristicas'])
            except Exception:
                data['caracteristicas'] = []

        if not data.get('email_destinatario', '').strip():
            return jsonify({'success': False, 'error': 'Email obligatorio'}), 400

        if not data.get('nombre_agente'):
            data['nombre_agente'] = data.get('nombre_destinatario', '')

        # ── Fotos ────────────────────────────────────────────────────────────
        tmp_dir = tempfile.mkdtemp(prefix='dossier_')
        foto_paths = []
        num_fotos = int(data.get('num_fotos', 0))
        for i in range(num_fotos):
            f = request.files.get(f'foto_{i}')
            if f and f.filename:
                safe = re.sub(r'[^\w\.\-]', '_', f.filename)
                path = os.path.join(tmp_dir, safe)
                f.save(path)
                foto_paths.append(path)
        data['foto_paths'] = foto_paths

        # ── Generar contenido y PDF(s) ───────────────────────────────────────
        lang       = data.get('idioma', 'es')
        tipo       = data.get('tipo_dossier', 'inversores')
        barrio     = (data.get('barrio') or data.get('ciudad', '')).replace(' ', '_')
        ts         = datetime.now().strftime('%Y%m%d_%H%M')

        if tipo == 'ambos':
            # Generar ambos dossieres y empaquetar en ZIP
            zip_buf = io.BytesIO()
            with zipfile.ZipFile(zip_buf, 'w', zipfile.ZIP_DEFLATED) as zf:
                for t in ('inversores', 'particulares'):
                    data_t = dict(data, tipo_dossier=t)
                    content_t  = generate_all_content(data_t)
                    pdf_t      = generate_dossier(data_t, content_t, lang)
                    label      = 'Inversores' if t == 'inversores' else 'Particulares'
                    fname      = re.sub(r'[^\w\.\-]', '_', f"Dossier_{label}_{barrio}_{ts}.pdf")
                    zf.writestr(fname, pdf_t)
            zip_buf.seek(0)
            zipname = re.sub(r'[^\w\.\-]', '_', f"Dossieres_{barrio}_{ts}.zip")
            response = make_response(zip_buf.read())
            response.headers['Content-Type']        = 'application/zip'
            response.headers['Content-Disposition'] = f'attachment; filename="{zipname}"'
            response.headers['X-Filename']          = zipname
            return response
        else:
            content   = generate_all_content(data)
            pdf_bytes = generate_dossier(data, content, lang)
            filename  = re.sub(r'[^\w\.\-]', '_', f"Dossier_Premium_{barrio}_{ts}.pdf")
            response  = make_response(pdf_bytes)
            response.headers['Content-Type']        = 'application/pdf'
            response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
            response.headers['X-Filename']          = filename
            return response

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if tmp_dir:
            shutil.rmtree(tmp_dir, ignore_errors=True)


# ── MANEJADOR GLOBAL DE ERRORES (siempre devuelve JSON) ──────────────────────
@app.errorhandler(404)
def handle_404(e):
    return jsonify({'success': False, 'error': 'Ruta no encontrada'}), 404


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("=" * 62)
    print("  DOSSIER PREMIUM INMOBILIARIO  —  Sistema Infraltum")
    print(f"  Servidor: http://localhost:{port}")
    print("=" * 62)
    app.run(debug=False, port=port, host='0.0.0.0')
