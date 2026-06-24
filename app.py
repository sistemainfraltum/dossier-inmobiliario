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
anthropic_client = Anthropic()

AGENT_SYSTEM = """Eres Marco, agente inmobiliario de Sistema Infraltum especializado en propiedades de lujo en España.

ESTILO DE ESCRITURA:
- Escribe como si estuvieras mandando un WhatsApp real: natural, directo, sin protocolo exagerado
- No uses signos de apertura (¿ ¡), solo los de cierre (? !)
- Frases cortas. Sin párrafos largos. Si tienes que decir varias cosas, las separas con saltos de línea
- No seas robótico ni uses frases de call center. Habla como una persona real que conoce bien su trabajo
- Puedes usar puntos suspensivos, emojis ocasionales (🏡 📍 ✅) si encajan natural
- Si no sabes algo concreto, dices "déjame consultarlo y te confirmo"

PROPIEDADES QUE MANEJA SISTEMA INFRALTUM:
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

ROL Y OBJETIVO:
- Eres un agente de captación. Tu objetivo es generar interés, resolver dudas y conseguir una visita o llamada
- Si el cliente pregunta por una propiedad concreta, responde con detalle y entusiasmo real (sin exagerar)
- Si notas que no está convencido, propón alternativas que encajen con lo que busca
- Si muestra interés, cierra hacia el siguiente paso: "te puedo agendar una visita esta semana, cuando mejor te venga?"
- Nunca digas que no puedes ayudar. Si no tienes el dato exacto, dices que lo consultas
- Siempre mantén la conversación abierta, que el cliente sienta que está hablando con alguien que le va a encontrar lo que busca"""

# Historial de conversación por número (en memoria)
_conversations: dict = {}


def get_ai_reply(phone: str, user_msg: str) -> str:
    history = _conversations.setdefault(phone, [])
    history.append({"role": "user", "content": user_msg})
    if len(history) > 20:          # limitar historial a 10 turnos
        history = history[-20:]
        _conversations[phone] = history
    try:
        resp = anthropic_client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=400,
            system=AGENT_SYSTEM,
            messages=history,
        )
        reply = resp.content[0].text
    except Exception:
        reply = "Hola! Soy Marco de Sistema Infraltum. En que propiedad estas interesado?"
    history.append({"role": "assistant", "content": reply})
    return reply


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
