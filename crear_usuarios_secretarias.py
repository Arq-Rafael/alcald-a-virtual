"""
Script para crear usuarios por secretaría/departamento
Ejecutar con: python crear_usuarios_secretarias.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.usuario import Usuario
import secrets
import string

def generar_password_segura(longitud=12):
    """Genera una contraseña segura con letras, números y símbolos"""
    caracteres = string.ascii_letters + string.digits + "!@#$%&*"
    return ''.join(secrets.choice(caracteres) for _ in range(longitud))

def crear_usuarios_secretarias():
    """Crea usuarios para cada secretaría"""
    print("\n" + "="*70)
    print("CREACIÓN DE USUARIOS POR SECRETARÍA")
    print("="*70)
    
    app = create_app()
    
    # Definir usuarios por secretaría
    usuarios_crear = [
        {
            'usuario': 'planeacion',
            'nombre': 'Usuario',
            'apellidos': 'Planeación',
            'secretaria': 'Secretaría de Planeación y Obras Públicas',
            'role': 'planeacion'
        },
        {
            'usuario': 'gobierno',
            'nombre': 'Usuario',
            'apellidos': 'Gobierno',
            'secretaria': 'Secretaría General y de Gobierno',
            'role': 'gobierno'
        },
        {
            'usuario': 'hacienda',
            'nombre': 'Usuario',
            'apellidos': 'Hacienda',
            'secretaria': 'Secretaría de Hacienda y Gestión Financiera',
            'role': 'hacienda'
        },
        {
            'usuario': 'desarrollo_rural',
            'nombre': 'Usuario',
            'apellidos': 'Desarrollo Rural',
            'secretaria': 'Secretaría de Desarrollo Rural Medio Ambiente y Competitividad',
            'role': 'user'
        },
        {
            'usuario': 'desarrollo_social',
            'nombre': 'Usuario',
            'apellidos': 'Desarrollo Social',
            'secretaria': 'Secretaría de Desarrollo Social y Comunitario',
            'role': 'user'
        }
    ]
    
    credenciales = []
    
    with app.app_context():
        print("\n📝 Procesando usuarios...\n")
        
        for datos in usuarios_crear:
            # Verificar si el usuario ya existe
            usuario_existente = Usuario.query.filter_by(usuario=datos['usuario']).first()
            
            # Generar contraseña segura
            password = generar_password_segura(12)
            
            if usuario_existente:
                # Actualizar usuario existente con nueva contraseña
                usuario_existente.nombre = datos['nombre']
                usuario_existente.apellidos = datos['apellidos']
                usuario_existente.nombre_completo = f"{datos['nombre']} {datos['apellidos']}"
                usuario_existente.secretaria = datos['secretaria']
                usuario_existente.role = datos['role']
                usuario_existente.email = None
                usuario_existente.set_password(password)
                
                print(f"🔄 Usuario '{datos['usuario']}' actualizado con nueva contraseña")
            else:
                # Crear nuevo usuario
                nuevo_usuario = Usuario(
                    usuario=datos['usuario'],
                    nombre=datos['nombre'],
                    apellidos=datos['apellidos'],
                    nombre_completo=f"{datos['nombre']} {datos['apellidos']}",
                    secretaria=datos['secretaria'],
                    role=datos['role'],
                    email=None  # Sin email
                )
                nuevo_usuario.set_password(password)
                
                db.session.add(nuevo_usuario)
                print(f"✅ Usuario '{datos['usuario']}' creado exitosamente")
            
            # Guardar credenciales
            credenciales.append({
                'usuario': datos['usuario'],
                'password': password,
                'secretaria': datos['secretaria'],
                'role': datos['role']
            })
        
        # Commit de todos los cambios
        try:
            db.session.commit()
            print("\n" + "="*70)
            print("✅ USUARIOS CREADOS CORRECTAMENTE")
            print("="*70)
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error al guardar usuarios: {e}")
            return
    
    # Mostrar credenciales
    print("\n" + "="*70)
    print("🔐 CREDENCIALES DE ACCESO")
    print("="*70 + "\n")
    
    for cred in credenciales:
        print(f"📋 {cred['secretaria']}")
        print(f"   Usuario:  {cred['usuario']}")
        print(f"   Clave:    {cred['password']}")
        print(f"   Rol:      {cred['role']}")
        print()
    
    print("="*70)
    print("⚠️  IMPORTANTE: Guarda estas credenciales en un lugar seguro")
    print("="*70 + "\n")
    
    # Guardar en archivo
    with open('CREDENCIALES_SECRETARIAS.txt', 'w', encoding='utf-8') as f:
        f.write("="*70 + "\n")
        f.write("CREDENCIALES DE ACCESO - USUARIOS POR SECRETARÍA\n")
        f.write("="*70 + "\n\n")
        
        for cred in credenciales:
            f.write(f"{cred['secretaria']}\n")
            f.write(f"Usuario: {cred['usuario']}\n")
            f.write(f"Clave:   {cred['password']}\n")
            f.write(f"Rol:     {cred['role']}\n")
            f.write("\n" + "-"*70 + "\n\n")
        
        f.write("USUARIO ADMIN (YA EXISTENTE - NO MODIFICAR)\n")
        f.write("Usuario: admin\n")
        f.write("Clave:   admin123\n")
        f.write("Rol:     admin\n")
    
    print("💾 Credenciales guardadas en: CREDENCIALES_SECRETARIAS.txt\n")

if __name__ == '__main__':
    try:
        crear_usuarios_secretarias()
    except Exception as e:
        print(f"\n❌ Error durante la creación: {e}")
        import traceback
        traceback.print_exc()
