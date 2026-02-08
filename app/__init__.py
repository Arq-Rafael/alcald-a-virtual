
import logging
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from .config import Config

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

# Initialize extensions
db = SQLAlchemy()

def create_app(config_class=Config):
    app = Flask(__name__, 
                template_folder='../templates',
                static_folder='../static')
    
    app.config.from_object(config_class)
    config_class.init_app(app)
    
    # Initialize extensions
    db.init_app(app)
    
    # IMPORTANTE: Ejecutar migraciones ANTES de registrar blueprints
    # Esto evita errores de schema cuando las rutas hacen queries
    with app.app_context():
        try:
            from .migrations import run_migrations
            run_migrations(app, db)
        except Exception as e:
            logging.warning(f"[MIGRATIONS] Error durante inicialización de migraciones: {e}")
    
    # Register Blueprints
    from .routes.auth import auth_bp
    from .routes.main import main_bp
    from .routes.solicitudes import solicitudes_bp
    from .routes.certificados import certificados_bp
    from .routes.participacion import participacion_bp
    from .routes.usos import usos_bp
    from .routes.ia import ia_bp
    from .routes.seguimiento import seguimiento_bp
    from .routes.configuracion import configuracion_bp
    from .routes.perfil import perfil_bp
    from .routes.api_prefs import api_prefs_bp
    from .routes.recuperacion import recuperacion_bp
    from .routes.reportes import reportes_bp
    from .routes.avatares import avatares_bp
    from .routes.riesgo_api import riesgo_api
    from .routes.contingencia_api import contingencia_api
    from .routes.contingencia_views import contingencia_views
    from .routes.contratos_api import contratos_api
    from .routes.contratos_view import contratos_view
    from .routes.plan_contingencia_v2_routes import contingencia_bp
    from .routes.admin_fix import admin_fix_bp
    from .routes.totp_setup import totp_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(solicitudes_bp)
    app.register_blueprint(certificados_bp)
    app.register_blueprint(participacion_bp)
    app.register_blueprint(usos_bp)
    app.register_blueprint(ia_bp)
    app.register_blueprint(seguimiento_bp)
    app.register_blueprint(configuracion_bp)
    app.register_blueprint(perfil_bp)
    app.register_blueprint(api_prefs_bp)
    app.register_blueprint(recuperacion_bp)
    app.register_blueprint(reportes_bp)
    app.register_blueprint(avatares_bp)
    app.register_blueprint(riesgo_api)
    app.register_blueprint(contingencia_api)
    app.register_blueprint(contingencia_views)
    app.register_blueprint(contratos_api)
    app.register_blueprint(contratos_view)
    app.register_blueprint(contingencia_bp)
    app.register_blueprint(admin_fix_bp)
    app.register_blueprint(totp_bp)

    
    # Context Processors (for templates)
    @app.context_processor
    def inject_utilities():
        from .utils import can_access
        from .utils.preferencias import get_user_preferences
        from flask import session
        try:
            from .models.usuario import Usuario
        except Exception:
            Usuario = None

        prefs = get_user_preferences(session)

        # Foto de perfil del usuario actual (si disponible)
        current_user_foto = None
        if Usuario and 'user' in session:
            try:
                u = Usuario.query.filter_by(usuario=session['user']).first()
                if u and getattr(u, 'foto_perfil', None):
                    current_user_foto = u.foto_perfil
            except Exception:
                current_user_foto = None

        return dict(
            can=can_access,
            user_preferences=prefs,
            current_user_foto=current_user_foto
        )
        
    # Create database tables if they don't exist
    with app.app_context():
        # Ensure models are imported so metadata is populated
        from .models.metas import MetaPlan, InformeProgresoMetas, InformeProgresoMetasFoto  # noqa: F401
        from .models.calendario import EventoCalendario  # noqa: F401
        from .models.participacion import Radicado, RespuestaRadicado  # noqa: F401
        from .models.usuario import Usuario, AuditoriaAcceso  # noqa: F401
        from .models.riesgo_arborea import RadicadoArborea, ArbolEspecie  # noqa: F401
        db.create_all()
        
        # Seed especies de árboles
        try:
            from .seeds.seed_especies import seed_especies
            seed_especies(db)
            logging.info("[INIT] Especies de árboles cargadas")
        except Exception as e:
            logging.error(f"[INIT] Error al cargar especies: {e}")
    
    # Serve uploaded files (perfil photos, etc.)
    @app.route('/uploads/<path:filename>')
    def uploaded_files(filename):
        from flask import send_from_directory
        upload_dir = str(app.config.get('UPLOADS_DIR'))
        return send_from_directory(upload_dir, filename)

    # Inicializar datos en base de datos
    with app.app_context():
        try:
            from .models.usuario import Usuario
            admin = Usuario.query.filter_by(usuario='admin').first()
            if not admin:
                logging.warning("[RAILWAY LOG] Creando usuario admin por defecto...")
                admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
                
                admin = Usuario(
                    usuario='admin',
                    nombre='Administrador',
                    apellidos='Sistema',
                    role='admin',
                    email=None  # SIN EMAIL POR DEFECTO
                )
                admin.set_password(admin_password)
                db.session.add(admin)
                
                # Crear usuarios demo SIN EMAILS
                demo_users = [
                    ('planeacion', os.environ.get('PLANEACION_PASSWORD', 'planeacion123'), 'Planeación', 'Municipal', 'planeacion'),
                    ('gobierno', os.environ.get('GOBIERNO_PASSWORD', 'gobierno123'), 'Gobierno', 'Municipal', 'gobierno')
                ]
                for u, p, n, a, r in demo_users:
                    if not Usuario.query.filter_by(usuario=u).first():
                        nuevo = Usuario(usuario=u, nombre=n, apellidos=a, role=r, email=None)  # SIN EMAIL
                        nuevo.set_password(p)
                        db.session.add(nuevo)
                
                try:
                    db.session.commit()
                    logging.info("[RAILWAY LOG] Usuarios creados correctamente")
                except Exception as commit_error:
                    logging.warning(f"[RAILWAY] Algunos usuarios ya existían: {commit_error}")
                    db.session.rollback()
                
            # Sembrar metas
            from .utils.seeds import seed_metas
            seed_metas()
            
        except Exception as e:
            logging.error(f"[RAILWAY ERROR] Error inicializando DB: {e}")

    return app

