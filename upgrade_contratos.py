from datetime import datetime
from sqlalchemy import inspect, text

from app import create_app, db

REQUIRED_COLUMNS = {
    # Identificación
    'numero_proceso': 'TEXT',
    'url_secop': 'TEXT',
    'plataforma': 'TEXT',
    'tipo_proceso': 'TEXT',
    'estado': 'TEXT',
    'modalidad': 'TEXT',
    # Entidad
    'entidad_nombre': 'TEXT',
    'entidad_nit': 'TEXT',
    'entidad_departamento': 'TEXT',
    'entidad_municipio': 'TEXT',
    # Objeto / descripción
    'objeto_contrato': 'TEXT',
    'descripcion': 'TEXT',
    # Valores
    'cuantia': 'REAL',
    'cuantia_minima': 'REAL',
    'cuantia_maxima': 'REAL',
    'moneda': 'TEXT',
    # UNSPSC
    'codigo_unspsc': 'TEXT',
    'familia_unspsc': 'TEXT',
    'clase_unspsc': 'TEXT',
    # Plazos y duración
    'plazo_dias': 'INTEGER',
    'plazo_meses': 'INTEGER',
    'duracion_estimada': 'INTEGER',
    # Fechas
    'fecha_publicacion': 'TEXT',
    'fecha_cierre': 'TEXT',
    'fecha_apertura_ofertas': 'TEXT',
    'fecha_adjudicacion': 'TEXT',
    'fecha_firma_contrato': 'TEXT',
    'fecha_inicio_ejecucion': 'TEXT',
    'fecha_fin_ejecucion': 'TEXT',
    'fecha_liquidacion': 'TEXT',
    # Contratista
    'contratista_nombre': 'TEXT',
    'contratista_nit': 'TEXT',
    'contratista_tipo': 'TEXT',
    # Resultados / ejecución
    'valor_adjudicado': 'REAL',
    'numero_proponentes': 'INTEGER',
    # JSON
    'proponentes_json': 'TEXT',
    'documentos_json': 'TEXT',
    'modificaciones_json': 'TEXT',
    'datos_completos_json': 'TEXT',
    # Flags
    'tiene_pliegos': 'INTEGER',
    'tiene_estudios_previos': 'INTEGER',
    'tiene_acta_adjudicacion': 'INTEGER',
    # Supervisión e interventoría
    'supervisor_nombre': 'TEXT',
    'interventor_nombre': 'TEXT',
    # Garantías
    'garantia_cumplimiento': 'TEXT',
    'garantia_anticipo': 'TEXT',
    'garantia_calidad': 'TEXT',
    # Adiciones / prórrogas
    'numero_adiciones': 'INTEGER',
    'valor_total_adiciones': 'REAL',
    'numero_prorrogas': 'INTEGER',
    # Pagos / ejecución
    'valor_total_pagado': 'REAL',
    'porcentaje_ejecucion': 'REAL',
    'ultimo_pago_fecha': 'TEXT',
    # Metadatos
    'fecha_importacion': 'TEXT',
    'ultima_sincronizacion': 'TEXT',
    'sincronizacion_exitosa': 'INTEGER',
    'mensaje_error': 'TEXT',
    'observaciones': 'TEXT',
    'responsable_seguimiento': 'TEXT',
    'alerta_vencimiento': 'INTEGER',
    'dias_para_vencimiento': 'INTEGER',
    'usuario_importacion': 'TEXT',
    'created_at': 'TEXT',
    'updated_at': 'TEXT',
}

# Mapeos desde columnas antiguas -> nuevas
BACKFILL_MAP = [
    ("numero_proceso", "numero"),
    ("url_secop", "secop_url"),
    ("entidad_nombre", "entidad"),
    ("cuantia", "valor"),
    ("contratista_nombre", "contratista"),
    ("contratista_nit", "nit"),
    ("supervisor_nombre", "supervisor"),
    ("plazo_meses", "meses"),
    ("plazo_dias", "dias"),
    ("fecha_inicio_ejecucion", "fecha_inicio"),
    ("fecha_fin_ejecucion", "fecha_fin"),
    ("created_at", "creado_en"),
    ("updated_at", "actualizado_en"),
    ("dias_para_vencimiento", "dias_restantes"),
    ("objeto_contrato", "objeto"),
]


def ensure_columns():
    insp = inspect(db.engine)
    existing = {c['name'] for c in insp.get_columns('contratos')}

    added = []
    for col, typ in REQUIRED_COLUMNS.items():
        if col not in existing:
            ddl = f"ALTER TABLE contratos ADD COLUMN {col} {typ}"
            db.session.execute(text(ddl))
            added.append(col)
    if added:
        db.session.commit()
    return existing, added


def backfill_from_legacy():
    insp = inspect(db.engine)
    existing = {c['name'] for c in insp.get_columns('contratos')}

    updates = []
    for new_col, old_col in BACKFILL_MAP:
        if new_col in existing and old_col in existing:
            # Solo actualiza si el nuevo está NULL o vacío
            sql = text(
                f"UPDATE contratos SET {new_col} = {old_col} "
                f"WHERE ({new_col} IS NULL OR {new_col} = '') AND {old_col} IS NOT NULL"
            )
            db.session.execute(sql)
            updates.append((new_col, old_col))
    if updates:
        db.session.commit()
    return updates


def main():
    app = create_app()
    with app.app_context():
        # Verifica existencia de la tabla
        insp = inspect(db.engine)
        tables = insp.get_table_names()
        if 'contratos' not in tables:
            # Si no existe, crea todas las tablas del modelo
            db.create_all()
            print('Tabla contratos creada (no existía)')
            return

        existing, added = ensure_columns()
        print(f"Columnas existentes: {len(existing)}")
        print(f"Columnas añadidas: {len(added)} -> {added}")

        updates = backfill_from_legacy()
        print(f"Campos migrados desde esquema antiguo: {updates}")

        print('✓ Migración/upgrade completado')


if __name__ == '__main__':
    main()
