"""
Dossier Premium Inmobiliario — Servidor Flask
Genera el PDF y lo devuelve como descarga directa en el navegador.
"""
import os, json, re, shutil, tempfile, traceback
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

        # ── Generar contenido y PDF ──────────────────────────────────────────
        content   = generate_all_content(data)
        lang      = data.get('idioma', 'es')
        pdf_bytes = generate_dossier(data, content, lang)

        barrio   = (data.get('barrio') or data.get('ciudad', '')).replace(' ', '_')
        ts       = datetime.now().strftime('%Y%m%d_%H%M')
        filename = re.sub(r'[^\w\.\-]', '_', f"Dossier_Premium_{barrio}_{ts}.pdf")

        # ── Devolver PDF como descarga directa ───────────────────────────────
        response = make_response(pdf_bytes)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.headers['X-Filename'] = filename
        return response

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if tmp_dir:
            shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("=" * 62)
    print("  DOSSIER PREMIUM INMOBILIARIO  —  Sistema Infraltum")
    print(f"  Servidor: http://localhost:{port}")
    print("=" * 62)
    app.run(debug=False, port=port, host='0.0.0.0')
