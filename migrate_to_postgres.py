#!/usr/bin/env python
"""
Script para migrar de SQLite a PostgreSQL en Railway
Uso: python migrate_to_postgres.py
"""

import os
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from app import create_app, db
from app.models.usuario import Usuario
from app.models.meta import Meta

def migrate():
    """Migra la BD local (SQLite) a PostgreSQL en Railway"""
    
    app = create_app()
    
    with app.app_context():
        print("🔄 Iniciando migración de BD...")
        print(f"📊 BD actual: {app.config['SQLALCHEMY_DATABASE_URI'][:50]}...")
        
        # 1. Verificar conexión
        try:
            with db.engine.connect() as conn:
                print("✅ Conexión a BD exitosa")
        except Exception as e:
            print(f"❌ Error de conexión: {e}")
            return False
        
        # 2. Crear todas las tablas (si no existen)
        print("📝 Creando tablas...")
        db.create_all()
        print("✅ Tablas creadas/verificadas")
        
        # 3. Verificar datos
        usuario_count = Usuario.query.count()
        meta_count = Meta.query.count()
        
        print(f"\n📊 Estado actual:")
        print(f"   - Usuarios: {usuario_count}")
        print(f"   - Metas: {meta_count}")
        
        print("\n✅ Base de datos lista para PostgreSQL")
        return True

if __name__ == '__main__':
    success = migrate()
    sys.exit(0 if success else 1)
