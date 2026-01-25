from app import create_app, db
from app.models.usuario import Usuario
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # Crear tablas si no existen
    db.create_all()
    
    # Verificar si existe admin
    admin = Usuario.query.filter_by(username='admin').first()
    
    if not admin:
        print("Creando usuario admin...")
        admin = Usuario(
            username='admin',
            password_hash=generate_password_hash('admin123'),
            nombre='Administrador',
            apellidos='Sistema',
            role='admin',
            email='admin@supata.gov.co'
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ Usuario 'admin' creado con contraseña 'admin123'")
    else:
        print("⚠️ El usuario admin ya existe. Actualizando contraseña...")
        admin.password_hash = generate_password_hash('admin123')
        db.session.commit()
        print("✅ Contraseña de 'admin' restablecida a 'admin123'")

    # Verificar usuarios de prueba
    usuarios = [
        ('planeacion', 'planeacion123', 'Planeación', 'Municipal', 'planeacion'),
        ('gobierno', 'gobierno123', 'Gobierno', 'Municipal', 'gobierno')
    ]

    for user, pwd, nom, ape, rol in usuarios:
        u = Usuario.query.filter_by(username=user).first()
        if not u:
            print(f"Creando usuario {user}...")
            nuevo = Usuario(
                username=user,
                password_hash=generate_password_hash(pwd),
                nombre=nom,
                apellidos=ape,
                role=rol,
                email=f'{user}@supata.gov.co'
            )
            db.session.add(nuevo)
    
    db.session.commit()
    print("✅ Usuarios de prueba verificados/creados")
