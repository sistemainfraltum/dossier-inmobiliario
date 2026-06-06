"""
Dossier Premium Inmobiliario — Servidor Flask
Recibe el formulario multipart (con fotos), genera el PDF y lo envía por Resend.

Configuración (variables de entorno en Railway):
  RESEND_API_KEY → clave API de resend.com (gratis)
"""
import os, json, re, shutil, tempfile, traceback, base64
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
import resend

from content_generator import generate_all_content
from dossier_generator   import generate_dossier

# ── CONFIGURACIÓN ─────────────────────────────────────────────────────────────
RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '')

app = Flask(__name__, static_folder='.')


# ── RUTAS ─────────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


@app.route('/generar-dossier', methods=['POST'])
def generar_dossier():
    tmp_dir = None
    try:
        # ── Recibir campos de texto ──────────────────────────────────────────
        data = {}
        for key in request.form:
            data[key] = request.form.get(key, '')

        # Desempaquetar lista de características (JSON array)
        if 'caracteristicas' in data:
            try:
                data['caracteristicas'] = json.loads(data['caracteristicas'])
            except Exception:
                data['caracteristicas'] = []

        # Validaciones básicas
        if not data.get('email_destinatario', '').strip():
            return jsonify({'success': False, 'error': 'Campo obligatorio: email_destinatario'}), 400

        # El nombre del agente/presentador es el mismo que rellena el formulario
        if not data.get('nombre_agente'):
            data['nombre_agente'] = data.get('nombre_destinatario', '')

        # ── Guardar fotos subidas ────────────────────────────────────────────
        tmp_dir = tempfile.mkdtemp(prefix='dossier_')
        foto_paths = []
        num_fotos = int(data.get('num_fotos', 0))
        for i in range(num_fotos):
            key = f'foto_{i}'
            if key in request.files:
                f = request.files[key]
                if f and f.filename:
                    safe_name = re.sub(r'[^\w\.\-]', '_', f.filename)
                    path = os.path.join(tmp_dir, safe_name)
                    f.save(path)
                    foto_paths.append(path)
        data['foto_paths'] = foto_paths

        # ── Generar contenido ────────────────────────────────────────────────
        content = generate_all_content(data)

        # ── Generar PDF ──────────────────────────────────────────────────────
        lang = data.get('idioma', 'es')
        pdf_bytes = generate_dossier(data, content, lang)

        # ── Nombre del archivo ───────────────────────────────────────────────
        barrio    = (data.get('barrio') or data.get('ciudad', '')).replace(' ', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        filename  = f"Dossier_Premium_{barrio}_{timestamp}.pdf"
        filename  = re.sub(r'[^\w\.\-]', '_', filename)

        # ── Enviar email ─────────────────────────────────────────────────────
        send_email(data, pdf_bytes, filename, lang)

        return jsonify({'success': True, 'filename': filename})

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if tmp_dir:
            shutil.rmtree(tmp_dir, ignore_errors=True)


# ── EMAIL ─────────────────────────────────────────────────────────────────────
def send_email(data, pdf_bytes, filename, lang='es'):
    resend.api_key = RESEND_API_KEY
    to_email  = data.get('email_destinatario', '')
    to_name   = data.get('nombre_destinatario', '')
    from_name = data.get('nombre_destinatario', 'Dossier Premium')
    direccion = data.get('direccion', '')
    mensaje   = data.get('mensaje_personalizado', '')

    html = _html_body(from_name, to_name, direccion, mensaje, filename, lang)
    pdf_b64 = base64.b64encode(pdf_bytes).decode()

    params = {
        "from": "Dossier Premium <onboarding@resend.dev>",
        "to": [to_email],
        "subject": _subject(direccion, lang),
        "html": html,
        "attachments": [{"filename": filename, "content": pdf_b64}],
    }
    resend.Emails.send(params)


def _subject(direccion, lang):
    if lang == 'en':
        return f"Premium Investment Dossier · {direccion[:50]}" if direccion else "Premium Investment Dossier"
    return f"Dossier Premium de Inversión · {direccion[:50]}" if direccion else "Dossier Premium de Inversión"


def _html_body(from_name, to_name, direccion, mensaje, filename, lang):
    saludo = (f"Estimado/a {to_name}," if to_name else "Estimado/a inversor/a:") if lang == 'es' else (f"Dear {to_name}," if to_name else "Dear Investor,")
    intro = (f"Le adjuntamos el <strong>Dossier Premium de Inversión</strong> correspondiente a la propiedad:<br/><strong style='color:#C9A84C;'>{direccion}</strong>"
             if lang == 'es' else
             f"Please find attached the <strong>Premium Investment Dossier</strong> for the property:<br/><strong style='color:#C9A84C;'>{direccion}</strong>")
    msg_blk = (f'<p style="margin:14px 0;padding:12px 16px;background:#0D1A2B;border-left:3px solid #C9A84C;border-radius:4px;color:#8BA5C5;font-style:italic;">{mensaje}</p>'
               if mensaje else '')
    footer = ("Este dossier es confidencial. No lo distribuya sin autorización del agente." if lang == 'es' else
              "This dossier is confidential. Do not distribute without the agent's authorisation.")
    file_lbl = "Archivo adjunto:" if lang == 'es' else "Attached file:"
    contact_lbl = "Contacto:" if lang == 'es' else "Contact:"
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#07101D;font-family:'Segoe UI',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="padding:28px 0;">
<tr><td align="center">
<table width="580" cellpadding="0" cellspacing="0" style="background:#0D1A2B;border-radius:12px;overflow:hidden;border:1px solid #1A2E44;max-width:580px;">
  <tr><td style="background:linear-gradient(135deg,#07101D 0%,#0D1A2B 100%);padding:28px 36px;border-bottom:3px solid #C9A84C;">
    <p style="margin:0 0 4px;color:#C9A84C;font-size:10px;letter-spacing:3px;text-transform:uppercase;font-weight:700;">DOSSIER PREMIUM</p>
    <h1 style="margin:0;color:#fff;font-size:20px;font-weight:700;">{from_name}</h1>
  </td></tr>
  <tr><td style="padding:32px 36px;color:#C8D8E8;">
    <p style="font-size:15px;font-weight:600;margin:0 0 14px;">{saludo}</p>
    <p style="margin:0 0 14px;font-size:14px;line-height:1.7;">{intro}</p>
    {msg_blk}
    <p style="margin:18px 0 6px;font-size:12px;color:#6B82A0;">{file_lbl}</p>
    <table cellpadding="0" cellspacing="0">
    <tr><td style="background:#111F30;border:1px solid #1A2E44;border-radius:8px;padding:10px 16px;">
      <span style="font-size:18px;">📄</span>
      <span style="margin-left:8px;font-size:12px;font-weight:600;color:#E8EFF8;">{filename}</span>
    </td></tr></table>
  </td></tr>
  <tr><td style="padding:0 36px;"><hr style="border:none;border-top:1px solid #1A2E44;margin:0;"></td></tr>
  <tr><td style="padding:18px 36px;background:#07101D;">
    <p style="margin:0 0 5px;font-size:10px;font-weight:700;color:#6B82A0;text-transform:uppercase;letter-spacing:1px;">{contact_lbl}</p>
    <p style="margin:0;font-size:13px;color:#C8D8E8;font-weight:600;">{from_name}</p>
  </td></tr>
  <tr><td style="background:#040A12;padding:16px 36px;border-top:2px solid #C9A84C;">
    <p style="margin:0;font-size:11px;color:#3A5060;line-height:1.6;">{footer}</p>
  </td></tr>
</table></td></tr></table></body></html>"""


def _strip_html(html):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', html)).strip()


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("=" * 62)
    print("  DOSSIER PREMIUM INMOBILIARIO  —  Sistema Infraltum")
    print(f"  Servidor: http://localhost:{port}")
    print("=" * 62)
    if not RESEND_API_KEY:
        print("\n  ⚠️  Añade RESEND_API_KEY en las variables de entorno\n")
    app.run(debug=False, port=port, host='0.0.0.0')
