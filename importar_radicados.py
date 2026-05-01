"""
Importa radicados desde PDFs en documentos_generados/licencias/radicacion/
Ejecutar desde la raiz del proyecto: python importar_radicados.py
"""
import os, sys, re, uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

PDF_DIR = os.path.join(os.path.dirname(__file__),
                       'documentos_generados', 'licencias', 'radicacion')

def _txt(pdf_path):
    try:
        import PyPDF2
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            return '\n'.join(p.extract_text() or '' for p in reader.pages)
    except Exception as e:
        print(f'  [!] Error leyendo PDF: {e}')
        return ''

def _first(patterns, text, default=''):
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE | re.DOTALL)
        if m:
            return m.group(1).strip()
    return default

def parse_pdf(path):
    fname = os.path.basename(path)
    m = re.search(r'SPO-([A-Z]{2})-(\d+)-(\d{8})-(\d+)', fname)
    if not m:
        return None
    tipo_cod = m.group(1)
    fecha_s  = m.group(3)
    consec   = int(m.group(4))

    tipo_map = {
        'LC': 'Licencia de Construcción',
        'LP': 'Licencia de Parcelación',
        'LS': 'Licencia de Subdivisión',
        'RE': 'Reconocimiento de Edificación',
    }
    tipo = tipo_map.get(tipo_cod, tipo_cod)

    try:
        fecha_dt = datetime.strptime(fecha_s, '%d%m%Y')
        fecha_iso = fecha_dt.date().isoformat()
    except Exception:
        fecha_iso = datetime.now().date().isoformat()

    txt = _txt(path)

    solicitante = _first([
        r'Nombre\s+del\s+Solicitante[:\s]+([^\n]+)',
        r'Solicitante[:\s]+([^\n]+)',
        r'Nombre[:\s]+([A-ZÁÉÍÓÚÑ][^\n]{5,60})',
    ], txt)

    direccion = _first([
        r'Direcci[oó]n\s+del\s+Predio[:\s]+([^\n]+)',
        r'Direcci[oó]n[:\s]+([^\n]+)',
        r'Ubicaci[oó]n[:\s]+([^\n]+)',
    ], txt)

    matricula = _first([
        r'Matr[ií]cula\s+Inmobiliaria[:\s]+([^\n]+)',
        r'Matr[ií]cula[:\s]+([^\n]+)',
    ], txt)

    chip = _first([
        r'Chip\s+Catastral[:\s]+([^\n]+)',
        r'Chip[:\s]+([^\n]+)',
    ], txt)

    area_str = _first([
        r'[Áá]rea\s+(?:de\s+)?Construcci[oó]n[:\s]+([\d.,]+)',
        r'[Áá]rea\s+Construida[:\s]+([\d.,]+)',
        r'[Áá]rea\s+Total[:\s]+([\d.,]+)',
    ], txt)
    try:
        area = float(area_str.replace(',', '.')) if area_str else None
    except Exception:
        area = None

    uso = _first([
        r'Uso\s+del\s+Suelo[:\s]+([^\n]+)',
        r'Uso[:\s]+([^\n]+)',
    ], txt)

    modalidad = _first([r'Modalidad[:\s]+([^\n]+)'], txt)

    return {
        'id': str(uuid.uuid4()),
        'consecutivo': consec,
        'tipo': tipo,
        'modalidad': modalidad or '',
        'solicitante': solicitante or '(sin nombre)',
        'direccion': direccion or '',
        'matricula': matricula or '',
        'chip': chip or '',
        'area_const': area,
        'uso': uso or '',
        'estado': 'Radicada',
        'creado_en': fecha_iso + 'T00:00:00',
        'creado_por': 'sistema',
    }


def main():
    from app import create_app
    from app.utils import get_sqlite

    app = create_app()
    with app.app_context():
        # Forzar creación del schema si no existe
        from app.routes.solicitudes import init_licencias_schema
        try:
            init_licencias_schema()
        except Exception as e:
            print(f'[SCHEMA] {e}')

        conn = get_sqlite()

        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        if 'licencias' not in tables:
            print('[ERROR] La tabla licencias sigue sin existir.')
            conn.close()
            return

        existing_consec = {r[0] for r in conn.execute(
            'SELECT consecutivo FROM licencias').fetchall()}
        print(f'Radicados existentes: {len(existing_consec)}')

        pdfs = sorted(f for f in os.listdir(PDF_DIR) if f.lower().endswith('.pdf'))
        inserted = 0
        skipped  = 0

        for pdf in pdfs:
            path = os.path.join(PDF_DIR, pdf)
            print(f'\nProcesando: {pdf}')
            rec = parse_pdf(path)
            if not rec:
                print('  [!] No se pudo parsear el nombre del archivo')
                continue

            if rec['consecutivo'] in existing_consec:
                print(f'  [=] Ya existe consecutivo: {rec["consecutivo"]}')
                skipped += 1
                continue

            print(f'  consecutivo : {rec["consecutivo"]}')
            print(f'  tipo        : {rec["tipo"]}')
            print(f'  solicitante : {rec["solicitante"]}')
            print(f'  dirección   : {rec["direccion"]}')
            print(f'  área        : {rec["area_const"]}')

            conn.execute("""
                INSERT INTO licencias
                  (id, consecutivo, tipo, modalidad, solicitante, direccion,
                   matricula, chip, area_const, uso, estado,
                   creado_en, creado_por, eliminado)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,0)
            """, (
                rec['id'], rec['consecutivo'], rec['tipo'], rec['modalidad'],
                rec['solicitante'], rec['direccion'], rec['matricula'], rec['chip'],
                rec['area_const'], rec['uso'], rec['estado'],
                rec['creado_en'], rec['creado_por'],
            ))

            conn.execute("""
                INSERT INTO licencias_log (id,licencia_id,evento,detalle,ts,user)
                VALUES (?,?,?,?,?,?)
            """, (str(uuid.uuid4()), rec['id'], 'Importado',
                  f'Importado desde PDF: {pdf}',
                  datetime.now().isoformat(), 'sistema'))

            inserted += 1
            existing_consec.add(rec['consecutivo'])

        # Actualizar secuencia al máximo consecutivo
        if inserted > 0:
            max_n = conn.execute(
                "SELECT MAX(consecutivo) FROM licencias").fetchone()[0] or 0
            conn.execute("UPDATE licencias_seq SET n=? WHERE k='seq' AND n<?",
                         (max_n, max_n))
            conn.commit()
            print(f'\n[OK] Importados: {inserted} | Omitidos: {skipped}')
            print(f'     Secuencia actualizada a: {max_n}')
        else:
            conn.commit()
            print(f'\n[OK] Sin nuevos registros. Omitidos: {skipped}')

        conn.close()


if __name__ == '__main__':
    main()
