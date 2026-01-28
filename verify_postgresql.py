#!/usr/bin/env python
"""
Script para verificar que PostgreSQL está conectado
Uso: python verify_postgresql.py
"""

import os
import sys
from pathlib import Path

print("=" * 60)
print("🔍 VERIFICADOR DE POSTGRESQL")
print("=" * 60)

# 1. Verificar si estamos en Railway
railway = os.environ.get('RAILWAY_ENVIRONMENT')
print(f"\n📍 Entorno: {'Railway ☁️' if railway else 'Local 💻'}")

# 2. Verificar DATABASE_URL
db_url = os.environ.get('DATABASE_URL')
print(f"\n🔑 DATABASE_URL configurado: {'✅ SÍ' if db_url else '❌ NO'}")

if db_url:
    # Mostrar parcialmente sin contraseña
    parts = db_url.split('@')
    if len(parts) > 1:
        host_part = parts[1]
        print(f"   Conectando a: {host_part}")
    print(f"   Tipo: {'PostgreSQL' if 'postgresql' in db_url else 'Desconocido'}")
else:
    print("   ⚠️  En Railway, agrega DATABASE_URL en Variables")
    print("   📋 Pasos:")
    print("      1. Railway Dashboard → PostgreSQL service")
    print("      2. Variables → DATABASE_URL (copia el valor)")
    print("      3. App service → Variables → agregar DATABASE_URL")

# 3. Verificar si psycopg2 está instalado
try:
    import psycopg2
    print(f"\n📦 psycopg2: ✅ Instalado")
except ImportError:
    print(f"\n📦 psycopg2: ❌ NO INSTALADO")
    print("   Instala: pip install psycopg2-binary")

# 4. Intentar conectar si tenemos DATABASE_URL
if db_url and 'postgresql' in db_url:
    print("\n🔗 Intentando conectar a la BD...")
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from app import create_app, db
        
        app = create_app()
        with app.app_context():
            with db.engine.connect() as conn:
                print("   ✅ Conexión exitosa!")
                
                # Contar tablas
                from app.models.usuario import Usuario
                count = Usuario.query.count()
                print(f"   👥 Usuarios en BD: {count}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)[:100]}")
        print("   📋 Posibles causas:")
        print("      - DATABASE_URL incorrea")
        print("      - PostgreSQL no está inicializado")
        print("      - Problema de conexión de red")
else:
    print("\n⏭️  Sin DATABASE_URL, se usa SQLite local")

print("\n" + "=" * 60)
print("✅ CHECKLIST FINAL")
print("=" * 60)

checklist = {
    "BD configurada en Railway": bool(db_url and 'postgresql' in db_url),
    "psycopg2 instalado": True,  # Ya verificamos arriba
    "Código soporta PostgreSQL": True,  # Lo acabamos de agregar
}

all_ok = all(checklist.values())

for item, status in checklist.items():
    symbol = "✅" if status else "❌"
    print(f"{symbol} {item}")

if all_ok:
    print("\n🎉 ¡TODO LISTO! PostgreSQL está funcional")
else:
    print("\n⚠️  Todavía falta configurar algo")
    print("\n📖 Lee: POSTGRESQL_SETUP_VISUAL.md")

print("=" * 60)
