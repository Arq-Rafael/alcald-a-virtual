"""
Migraciones automáticas de base de datos
Se ejecuta antes de registrar las blueprints para evitar errores de schema
"""
import logging
from sqlalchemy import text, inspect

def run_migrations(app, db):
    """
    Ejecutar migraciones automáticas al iniciar la aplicación
    """
    with app.app_context():
        try:
            # Obtener información de la base de datos
            inspector = inspect(db.engine)
            
            # Verificar si la tabla usuarios existe
            if 'usuarios' not in inspector.get_table_names():
                logging.info("[MIGRATION] Tabla 'usuarios' no existe, se creará con db.create_all()")
                return
            
            existing_columns = {col['name']: col for col in inspector.get_columns('usuarios')}
            
            # Columnas necesarias y sus definiciones
            required_columns = {
                'primer_acceso': ('BOOLEAN DEFAULT TRUE', 'BOOLEAN DEFAULT 1'),
                'codigo_primer_acceso': ('VARCHAR(6)', 'VARCHAR(6)'),
                'codigo_primer_acceso_expira': ('TIMESTAMP', 'TIMESTAMP'),
                'primer_acceso_verificado': ('TIMESTAMP', 'TIMESTAMP'),
            }
            
            # Columnas a agregar
            columns_to_add = [col for col in required_columns if col not in existing_columns]
            
            if columns_to_add:
                logging.info(f"[MIGRATION] Agregando columnas faltantes: {columns_to_add}")
                
                # Detectar tipo de BD
                db_url = app.config.get('DATABASE_URL', '') or ''
                is_postgresql = 'postgresql' in db_url
                
                for column_name in columns_to_add:
                    pg_def, sqlite_def = required_columns[column_name]
                    
                    try:
                        if is_postgresql:
                            sql = f"ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS {column_name} {pg_def}"
                        else:
                            sql = f"ALTER TABLE usuarios ADD COLUMN {column_name} {sqlite_def}"
                        
                        logging.info(f"[MIGRATION] Ejecutando: {sql}")
                        db.session.execute(text(sql))
                        logging.info(f"[MIGRATION] ✅ Columna '{column_name}' agregada")
                        
                    except Exception as e:
                        error_str = str(e).lower()
                        if 'already exists' in error_str or 'duplicate' in error_str:
                            logging.info(f"[MIGRATION] Columna '{column_name}' ya existe")
                        else:
                            logging.error(f"[MIGRATION] Error agregando '{column_name}': {e}")
                            raise
                
                db.session.commit()
                logging.info("[MIGRATION] ✅ Todas las migraciones completadas")
            else:
                logging.info("[MIGRATION] Base de datos está actualizada")
                
        except Exception as e:
            logging.error(f"[MIGRATION] Error durante migraciones: {e}")
            try:
                db.session.rollback()
            except:
                pass
            # No fallar si las migraciones fallan - permitir que continúe la app
            # pero registrar el error para debugging

    # ── RADICADO ARBÓREA – columnas nuevas ─────────────────────────────────
    with app.app_context():
        try:
            inspector = inspect(db.engine)
            if 'radicado_arborea' not in inspector.get_table_names():
                logging.info("[MIGRATION] Tabla 'radicado_arborea' no existe aún – se creará con create_all()")
                return

            existing = {col['name'] for col in inspector.get_columns('radicado_arborea')}
            db_url   = app.config.get('DATABASE_URL', '') or ''
            is_pg    = 'postgresql' in db_url

            new_cols = {
                'fase_actual':              ('INTEGER DEFAULT 1',     'INTEGER DEFAULT 1'),
                'planeacion_decision':      ('VARCHAR(20)',            'VARCHAR(20)'),
                'planeacion_usuario':       ('VARCHAR(150)',           'VARCHAR(150)'),
                'planeacion_fecha':         ('TIMESTAMP',              'TIMESTAMP'),
                'planeacion_observaciones': ('TEXT',                   'TEXT'),
                'archivos_fotos':           ('TEXT',                   'TEXT'),
                'dictamen_acta_archivo':    ('VARCHAR(255)',           'VARCHAR(255)'),
                'solicitante_rol':          ('VARCHAR(50)',            'VARCHAR(50)'),
                'arbol_afectacion':         ('VARCHAR(100)',           'VARCHAR(100)'),
                'arbol_riesgo_inicial':     ('VARCHAR(20)',            'VARCHAR(20)'),
                'diagnostico_recomendaciones': ('TEXT',               'TEXT'),
                'compensacion_plazo':       ('VARCHAR(100)',           'VARCHAR(100)'),
                'compensacion_calculo_json': ('TEXT',                  'TEXT'),
                'archivos_radicacion':      ('TEXT',                   'TEXT'),
                'archivos_visita':          ('TEXT',                   'TEXT'),
                'archivos_compensacion':    ('TEXT',                   'TEXT'),
                'pdf_completo':             ('VARCHAR(255)',           'VARCHAR(255)'),
                'pdf_compensacion':         ('VARCHAR(255)',           'VARCHAR(255)'),
                'permiso_firmante2':        ('VARCHAR(150)',           'VARCHAR(150)'),
                'permiso_fecha_limite':     ('TIMESTAMP',              'TIMESTAMP'),
            }

            added = []
            for col_name, (pg_def, lite_def) in new_cols.items():
                if col_name not in existing:
                    try:
                        if is_pg:
                            sql = f"ALTER TABLE radicado_arborea ADD COLUMN IF NOT EXISTS {col_name} {pg_def}"
                        else:
                            sql = f"ALTER TABLE radicado_arborea ADD COLUMN {col_name} {lite_def}"
                        db.session.execute(text(sql))
                        added.append(col_name)
                    except Exception as col_e:
                        err_s = str(col_e).lower()
                        if 'already exists' in err_s or 'duplicate' in err_s:
                            pass
                        else:
                            logging.warning(f"[MIGRATION] No se pudo agregar {col_name}: {col_e}")

            if added:
                db.session.commit()
                logging.info(f"[MIGRATION] radicado_arborea ✅ columnas agregadas: {added}")
            else:
                logging.info("[MIGRATION] radicado_arborea – sin columnas nuevas")

        except Exception as e:
            logging.error(f"[MIGRATION] Error en radicado_arborea: {e}")
            try:
                db.session.rollback()
            except:
                pass
