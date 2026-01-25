#!/usr/bin/env python
"""Script para inicializar la tabla planes_contingencia en la BD"""
import os
import sys

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.plan_contingencia import PlanContingencia

def init_contingencia_table():
    """Crea la tabla planes_contingencia si no existe"""
    app = create_app()
    
    with app.app_context():
        # Crear todas las tablas que falten
        db.create_all()
        
        # Verificar que la tabla existe
        inspector = db.inspect(db.engine)
        if 'planes_contingencia' in inspector.get_table_names():
            print("✓ Tabla 'planes_contingencia' creada exitosamente")
            return True
        else:
            print("✗ Error: La tabla 'planes_contingencia' no se creó")
            return False

if __name__ == '__main__':
    success = init_contingencia_table()
    sys.exit(0 if success else 1)
