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
