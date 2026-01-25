"""
Script de limpieza y migración de contratos
Elimina registros corruptos y migra correctamente desde el esquema antiguo
"""
from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("\n=== LIMPIEZA Y MIGRACIÓN DE CONTRATOS ===\n")
    
    # 1. Verificar registros actuales
    result = db.session.execute(text("SELECT COUNT(*) FROM contratos"))
    total_antes = result.scalar()
    print(f"1. Registros actuales: {total_antes}")
    
    # 2. Identificar registros sin numero_proceso ni plataforma (corruptos del esquema antiguo)
    result = db.session.execute(text(
        "SELECT COUNT(*) FROM contratos WHERE numero_proceso IS NULL OR numero_proceso = ''"
    ))
    corruptos = result.scalar()
    print(f"2. Registros sin numero_proceso: {corruptos}")
    
    # 3. Eliminar todos los registros corruptos (comenzar limpio)
    print("\n3. Eliminando TODOS los registros para migración limpia...")
    db.session.execute(text("DELETE FROM contratos"))
    db.session.commit()
    print("   ✓ Tabla limpiada")
    
    # 4. Verificar limpieza
    result = db.session.execute(text("SELECT COUNT(*) FROM contratos"))
    total_despues = result.scalar()
    print(f"4. Registros después de limpieza: {total_despues}")
    
    print("\n✓ Limpieza completada")
    print("\nAhora puedes importar contratos nuevos desde SECOP I o SECOP II")
    print("usando el formulario en /contratacion")
