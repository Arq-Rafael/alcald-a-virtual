#!/usr/bin/env python3
"""Script para verificar y resetear usuarios en la BD"""

import sys
sys.path.insert(0, '/c/Users/rafa_/Downloads/AlcaldiaVirtualWeb')

from app import create_app, db
from app.models.usuario import Usuario

app = create_app()

with app.app_context():
    print("🔍 Verificando usuarios en la BD...")
    print()
    
    usuarios = Usuario.query.all()
    
    if not usuarios:
        print("❌ No hay usuarios en la BD. Creando usuarios por defecto...")
        print()
        
        # Crear admin
        admin = Usuario(
            usuario='admin',
            nombre='Administrador',
            apellidos='Sistema',
            role='admin',
            email='admin@supata.gov.co'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        
        # Crear planeacion
        planeacion = Usuario(
            usuario='planeacion',
            nombre='Planeación',
            apellidos='Municipal',
            role='planeacion',
            email='planeacion@supata.gov.co'
        )
        planeacion.set_password('planeacion123')
        db.session.add(planeacion)
        
        # Crear gobierno
        gobierno = Usuario(
            usuario='gobierno',
            nombre='Gobierno',
            apellidos='Municipal',
            role='gobierno',
            email='gobierno@supata.gov.co'
        )
        gobierno.set_password('gobierno123')
        db.session.add(gobierno)
        
        db.session.commit()
        print("✅ Usuarios creados exitosamente:")
        print()
        print("1️⃣  admin / admin123")
        print("2️⃣  planeacion / planeacion123")
        print("3️⃣  gobierno / gobierno123")
        print()
        print("🎯 Usa estas credenciales para ingresar")
        
    else:
        print(f"✅ Hay {len(usuarios)} usuario(s) en la BD:")
        print()
        for u in usuarios:
            print(f"   • {u.usuario} ({u.role})")
            print(f"     Email: {u.email}")
        print()
        print("⚠️  Si no puedes ingresar, intenta resetear la contraseña:")
        print("    python reset_user_password.py")
