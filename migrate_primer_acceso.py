"""
Migración para agregar campos de primer acceso
Ejecutar este script una vez en Railway o localmente con PostgreSQL
"""

import os
import sys

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app, db
from sqlalchemy import text

def migrate_add_primer_acceso_fields():
    """Agrega campos de primer_acceso a la tabla usuarios"""
    
    app = create_app()
    
    with app.app_context():
        print("🔄 Verificando columnas de primer_acceso...")
        
        # Verificar si estamos usando PostgreSQL
        database_url = app.config.get('DATABASE_URL', '')
        if not database_url or 'postgresql' not in database_url:
            print("⚠️  No se detectó PostgreSQL. Saltando migración.")
            return
        
        try:
            # Verificar si las columnas ya existen
            result = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'usuarios' 
                AND column_name IN ('primer_acceso', 'codigo_primer_acceso', 'codigo_primer_acceso_expira', 'primer_acceso_verificado')
            """))
            
            existing_columns = [row[0] for row in result]
            
            if len(existing_columns) == 4:
                print("✅ Las columnas ya existen. No se requiere migración.")
                return
            
            print(f"📝 Columnas existentes: {existing_columns}")
            print("🔨 Agregando columnas faltantes...")
            
            # Agregar columnas una por una (más seguro)
            migrations = [
                ("primer_acceso", "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS primer_acceso BOOLEAN DEFAULT TRUE"),
                ("codigo_primer_acceso", "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS codigo_primer_acceso VARCHAR(6)"),
                ("codigo_primer_acceso_expira", "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS codigo_primer_acceso_expira TIMESTAMP"),
                ("primer_acceso_verificado", "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS primer_acceso_verificado TIMESTAMP"),
            ]
            
            for col_name, sql in migrations:
                if col_name not in existing_columns:
                    print(f"  ➕ Agregando columna: {col_name}")
                    db.session.execute(text(sql))
            
            db.session.commit()
            print("✅ Migración completada exitosamente")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error durante la migración: {e}")
            raise

if __name__ == '__main__':
    migrate_add_primer_acceso_fields()
