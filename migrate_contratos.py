"""
Script de migración para crear la tabla de contratos
Ejecutar: python migrate_contratos.py
"""
from app import create_app, db
from app.models.contrato import Contrato

def crear_tabla_contratos():
    """Crea la tabla de contratos en la base de datos"""
    app = create_app()
    
    with app.app_context():
        try:
            # Crear tabla si no existe
            db.create_all()
            print('✓ Tabla "contratos" creada exitosamente')
            
            # Verificar que la tabla existe
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'contratos' in tables:
                print('✓ Tabla verificada en la base de datos')
                
                # Mostrar columnas
                columns = inspector.get_columns('contratos')
                print(f'\n✓ Columnas creadas: {len(columns)}')
                for col in columns[:10]:  # Mostrar primeras 10
                    print(f'  - {col["name"]} ({col["type"]})')
                if len(columns) > 10:
                    print(f'  ... y {len(columns) - 10} columnas más')
            else:
                print('✗ Error: La tabla no fue creada')
                return False
            
            return True
            
        except Exception as e:
            print(f'✗ Error al crear la tabla: {e}')
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    print('=== Migración: Tabla de Contratos SECOP ===\n')
    exito = crear_tabla_contratos()
    
    if exito:
        print('\n✓ Migración completada exitosamente')
        print('\nAhora puedes:')
        print('1. Importar contratos desde SECOP I o SECOP II')
        print('2. Acceder al módulo en: http://127.0.0.1:5000/contratacion')
    else:
        print('\n✗ Error en la migración')
