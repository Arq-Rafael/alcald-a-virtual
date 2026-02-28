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
                # Permisos granulares de Gestión del Riesgo (DEFAULT FALSE = sin acceso)
                'can_risk_arborea': ('BOOLEAN DEFAULT FALSE', 'BOOLEAN DEFAULT 0'),
                'can_risk_actas':   ('BOOLEAN DEFAULT FALSE', 'BOOLEAN DEFAULT 0'),
                'can_risk_planes':  ('BOOLEAN DEFAULT FALSE', 'BOOLEAN DEFAULT 0'),
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

    # ── ACTAS CMGR – crear tablas nuevas si no existen ─────────────────────
    with app.app_context():
        try:
            inspector = inspect(db.engine)
            existing_tables = inspector.get_table_names()
            db_url = app.config.get('DATABASE_URL', '') or ''
            is_pg  = 'postgresql' in db_url

            # acta_cmgr
            if 'acta_cmgr' not in existing_tables:
                sql = """
                CREATE TABLE IF NOT EXISTS acta_cmgr (
                    id               SERIAL PRIMARY KEY,
                    numero_acta      VARCHAR(30) UNIQUE,
                    fecha            DATE NOT NULL,
                    tema_principal   VARCHAR(200),
                    asistentes       TEXT,
                    acuerdos         TEXT,
                    compromisos      TEXT,
                    archivo_pdf      VARCHAR(255),
                    resumen          TEXT,
                    observaciones    TEXT,
                    usuario_creador  VARCHAR(150),
                    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """ if is_pg else """
                CREATE TABLE IF NOT EXISTS acta_cmgr (
                    id               INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero_acta      VARCHAR(30) UNIQUE,
                    fecha            DATE NOT NULL,
                    tema_principal   VARCHAR(200),
                    asistentes       TEXT,
                    acuerdos         TEXT,
                    compromisos      TEXT,
                    archivo_pdf      VARCHAR(255),
                    resumen          TEXT,
                    observaciones    TEXT,
                    usuario_creador  VARCHAR(150),
                    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
                db.session.execute(text(sql))
                logging.info("[MIGRATION] ✅ Tabla acta_cmgr creada")

            # riesgo_damnificado
            if 'riesgo_damnificado' not in existing_tables:
                sql = """
                CREATE TABLE IF NOT EXISTS riesgo_damnificado (
                    id               SERIAL PRIMARY KEY,
                    nombre           VARCHAR(150) NOT NULL,
                    documento        VARCHAR(20),
                    contacto         VARCHAR(30),
                    vereda           VARCHAR(100),
                    tipo_afectacion  VARCHAR(100),
                    descripcion      TEXT,
                    evidencia        TEXT,
                    estado_ayuda     VARCHAR(50) DEFAULT 'Pendiente',
                    observaciones    TEXT,
                    usuario_creador  VARCHAR(150),
                    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """ if is_pg else """
                CREATE TABLE IF NOT EXISTS riesgo_damnificado (
                    id               INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre           VARCHAR(150) NOT NULL,
                    documento        VARCHAR(20),
                    contacto         VARCHAR(30),
                    vereda           VARCHAR(100),
                    tipo_afectacion  VARCHAR(100),
                    descripcion      TEXT,
                    evidencia        TEXT,
                    estado_ayuda     VARCHAR(50) DEFAULT 'Pendiente',
                    observaciones    TEXT,
                    usuario_creador  VARCHAR(150),
                    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
                db.session.execute(text(sql))
                logging.info("[MIGRATION] ✅ Tabla riesgo_damnificado creada")

            # riesgo_dano
            if 'riesgo_dano' not in existing_tables:
                sql = """
                CREATE TABLE IF NOT EXISTS riesgo_dano (
                    id               SERIAL PRIMARY KEY,
                    tipo             VARCHAR(50),
                    descripcion      TEXT,
                    vereda           VARCHAR(100),
                    direccion        VARCHAR(200),
                    lat              FLOAT,
                    lng              FLOAT,
                    criticidad       VARCHAR(20) DEFAULT 'Media',
                    costo_estimado   FLOAT,
                    prioridad        INTEGER DEFAULT 3,
                    estado           VARCHAR(50) DEFAULT 'Reportado',
                    evidencia        TEXT,
                    usuario_creador  VARCHAR(150),
                    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """ if is_pg else """
                CREATE TABLE IF NOT EXISTS riesgo_dano (
                    id               INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo             VARCHAR(50),
                    descripcion      TEXT,
                    vereda           VARCHAR(100),
                    direccion        VARCHAR(200),
                    lat              REAL,
                    lng              REAL,
                    criticidad       VARCHAR(20) DEFAULT 'Media',
                    costo_estimado   REAL,
                    prioridad        INTEGER DEFAULT 3,
                    estado           VARCHAR(50) DEFAULT 'Reportado',
                    evidencia        TEXT,
                    usuario_creador  VARCHAR(150),
                    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
                db.session.execute(text(sql))
                logging.info("[MIGRATION] ✅ Tabla riesgo_dano creada")

            db.session.commit()

        except Exception as e:
            logging.error(f"[MIGRATION] Error creando tablas Actas CMGR: {e}")
            try:
                db.session.rollback()
            except:
                pass
