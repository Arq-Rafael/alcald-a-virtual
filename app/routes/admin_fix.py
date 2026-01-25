from flask import Blueprint, jsonify
from app import db
from app.models.usuario import Usuario
from werkzeug.security import generate_password_hash

admin_fix_bp = Blueprint('admin_fix', __name__)

@admin_fix_bp.route('/crear-admin-emergencia', methods=['GET'])
def crear_admin():
    try:
        # Verificar si existe
        admin = Usuario.query.filter_by(username='admin').first()
        msg = ""
        
        if not admin:
            admin = Usuario(
                username='admin',
                password_hash=generate_password_hash('admin123'),
                nombre='Administrador',
                apellidos='Sistema',
                role='admin',
                email='admin@supata.gov.co'
            )
            db.session.add(admin)
            msg = "Usuario admin creado exitosamente"
        else:
            admin.password_hash = generate_password_hash('admin123')
            msg = "Contraseña de admin restablecida"
            
        db.session.commit()
        return jsonify({"success": True, "message": msg, "user": "admin", "pass": "admin123"})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
