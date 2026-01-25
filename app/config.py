import os
from pathlib import Path

class Config:
    # Basic Flask Config
    SECRET_KEY = os.environ.get('SECRET_KEY') or "TuClaveSecretaMuySeguraPremium2026"
    JSON_AS_ASCII = False
    
    # Path Configuration
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = BASE_DIR / "datos"
    STATIC_DIR = BASE_DIR / "static"
    TEMPLATES_DIR = BASE_DIR / "templates"
    UPLOADS_DIR = BASE_DIR / "uploads"
    DOCUMENTOS_DIR = BASE_DIR / "documentos_generados"
    
    # Database
    # Database - Usar /tmp en Railway para garantizar escritura
    DB_NAME = "data.db"
    if os.environ.get('RAILWAY_ENVIRONMENT'):
        DB_PATH = os.path.join('/tmp', DB_NAME)
    else:
        DB_PATH = os.path.join(BASE_DIR, DB_NAME)
        
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DB_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # External/Shared Paths - Migrated to local per user request
    # SHARED_DRIVE_PATH = Path(os.environ.get('SHARED_DRIVE_PATH', r"G:\Unidades compartidas\Planeacion"))
    
    # Using centralized documentos_generados folder
    SOLICITUDES_PATH = DATA_DIR / "solicitudes.csv"
    SOLICITUDES_OUTPUT_DIR = DOCUMENTOS_DIR / "solicitudes"
    CERTIFICADOS_OUTPUT_DIR = DOCUMENTOS_DIR / "certificados"
    LICENCIAS_OUTPUT_DIR = DOCUMENTOS_DIR / "licencias"
    CONTRATOS_OUTPUT_DIR = DOCUMENTOS_DIR / "contratos"
    REPORTES_OUTPUT_DIR = DOCUMENTOS_DIR / "reportes"
    TALA_OUTPUT_DIR = DOCUMENTOS_DIR / "tala"
    
    # Feature Flags / Permissions
    ALWAYS_ADMIN = True # Dev mode
    
    # ===== CONFIGURACIÓN DE CORREO SMTP =====
    # Para que funcionen las notificaciones por correo, configura estos valores:
    
    # Opción 1: Usar Gmail (más común)
    SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
    SMTP_USER = os.environ.get('SMTP_USER', 'alcaldiavirtual2026@gmail.com')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', 'fvgqrsacjnjhzfcn')
    
    # Opción 2: Usar Outlook/Hotmail (descomenta si usas Outlook)
    # SMTP_SERVER = 'smtp-mail.outlook.com'
    # SMTP_PORT = 587
    # SMTP_USER = 'tu_correo@outlook.com'
    # SMTP_PASSWORD = 'tu_contraseña'
    
    # Email del administrador para recibir alertas
    ADMIN_ALERT_EMAIL = os.environ.get('ADMIN_ALERT_EMAIL', 'alcaldiavirtual2026@gmail.com')
    
    # Restricción de IPs (opcional - dejar vacío para permitir todas)
    ALLOWED_IPS = []  # Ejemplo: ['192.168.1.100', '10.0.0.50']
    
    # Module Access Configuration - Define who can access each module
    APP_FEATURES = {
        'solicitudes': {'admin', 'formulador', '*'},  # Todos
        'certificados': {'admin', 'formulador', '*'}, # Todos
        'participacion': {'admin', 'formulador', '*'}, # Todos
        'usos_suelo': {'admin', 'formulador', '*'}, # Todos
        'ia': {'*'},  # Todos los usuarios - IA Municipal
        'seguimiento': {'admin', 'formulador', '*'}, # Todos
        'configuracion': {'admin'}, # Solo admin
    }
    
    @staticmethod
    def init_app(app):
        # Ensure directories exist
        os.makedirs(Config.DATA_DIR, exist_ok=True)
        os.makedirs(Config.UPLOADS_DIR, exist_ok=True)
        os.makedirs(Config.DOCUMENTOS_DIR, exist_ok=True)
        os.makedirs(Config.SOLICITUDES_OUTPUT_DIR, exist_ok=True)
        os.makedirs(Config.CERTIFICADOS_OUTPUT_DIR, exist_ok=True)
        os.makedirs(Config.LICENCIAS_OUTPUT_DIR, exist_ok=True)
        os.makedirs(Config.CONTRATOS_OUTPUT_DIR, exist_ok=True)
        os.makedirs(Config.REPORTES_OUTPUT_DIR, exist_ok=True)
        os.makedirs(Config.TALA_OUTPUT_DIR, exist_ok=True)
