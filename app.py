"""
Dossier Premium Inmobiliario — Servidor Flask
Genera el PDF y lo devuelve como descarga directa en el navegador.
"""
import os, io, json, re, shutil, tempfile, traceback, zipfile
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, make_response

from content_generator import generate_all_content
from dossier_generator  import generate_dossier

app = Flask(__name__, static_folder='.')


@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


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
