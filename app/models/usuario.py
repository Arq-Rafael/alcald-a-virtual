"""
Modelo de Usuario - Sistema de Seguridad Mejorado
Implementa seguridad robusta con bcrypt, perfiles y 2FA
"""

from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import secrets
import json

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(100), unique=True, nullable=False, index=True)
    email = db.Column(db.String(150), unique=True, nullable=True, index=True)
    clave_hash = db.Column(db.String(255), nullable=False)
    
    # Roles y permisos
    role = db.Column(db.String(50), default='user', nullable=False)  # admin, superadmin, user
    secretaria = db.Column(db.String(150), nullable=True)
    rol_descripcion = db.Column(db.String(200), default='Usuario')
    
    # Perfil de usuario
    nombre_completo = db.Column(db.String(200), nullable=True)
    foto_perfil = db.Column(db.String(255), nullable=True)  # Ruta al archivo
    
    # Preferencias de interfaz
    preferencias = db.Column(db.Text, nullable=True)  # JSON con configuración UI
    
    # Seguridad
    ultimo_acceso = db.Column(db.DateTime, nullable=True)
    intentos_fallidos = db.Column(db.Integer, default=0)
    bloqueado = db.Column(db.Boolean, default=False)
    bloqueado_hasta = db.Column(db.DateTime, nullable=True)
    
    # 2FA (Two-Factor Authentication)
    email_verificado = db.Column(db.Boolean, default=False)
    email_ultimo_verificado = db.Column(db.DateTime, nullable=True)  # Última verificación 2FA (válido por 30 días)
    codigo_verificacion = db.Column(db.String(6), nullable=True)
    codigo_expira = db.Column(db.DateTime, nullable=True)
    requiere_2fa = db.Column(db.Boolean, default=False)
    
    # Contraseña - Expiración y cambios
    fecha_ultimo_cambio_clave = db.Column(db.DateTime, default=datetime.utcnow)  # Cuándo se cambió la contraseña
    clave_expira_en = db.Column(db.DateTime, nullable=True)  # Cuándo vence la contraseña (90 días)
    requiere_cambio_clave = db.Column(db.Boolean, default=False)  # Forzar cambio en próximo login
    
    # Tokens de sesión
    token_sesion = db.Column(db.String(255), nullable=True)
    token_expira = db.Column(db.DateTime, nullable=True)
    
    # Auditoría
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
    actualizado_en = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    creado_por = db.Column(db.String(100), nullable=True)
    
    # Activo/Inactivo
    activo = db.Column(db.Boolean, default=True)
    
    def __init__(self, usuario, clave=None, role='user', email=None, **kwargs):
        """Inicializa usuario con contraseña hasheada"""
        self.usuario = usuario
        if clave:
            self.set_password(clave)
        self.role = role
        self.email = email
        
        # Establecer otros campos
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def set_password(self, clave):
        """Hashea la contraseña usando bcrypt (vía werkzeug)"""
        from datetime import timedelta
        if len(clave) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres")
        
        # Guardar contraseña anterior en historial
        if self.clave_hash:
            historial = HistorialClaves(
                usuario_id=self.id,
                clave_hash=self.clave_hash,
                creado_en=datetime.utcnow()
            )
            db.session.add(historial)
        
        # Hashear nueva contraseña
        self.clave_hash = generate_password_hash(clave, method='pbkdf2:sha256')
        self.fecha_ultimo_cambio_clave = datetime.utcnow()
        self.clave_expira_en = datetime.utcnow() + timedelta(days=90)  # Vence en 90 días
        self.requiere_cambio_clave = False
    
    def check_password(self, clave):
        """Verifica la contraseña"""
        return check_password_hash(self.clave_hash, clave)
    
    def generar_codigo_verificacion(self):
        """Genera código de 6 dígitos para 2FA"""
        from datetime import timedelta
        self.codigo_verificacion = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        self.codigo_expira = datetime.utcnow() + timedelta(minutes=10)
        return self.codigo_verificacion
    
    def verificar_codigo(self, codigo):
        """Verifica código 2FA"""
        if not self.codigo_verificacion or not self.codigo_expira:
            return False
        if datetime.utcnow() > self.codigo_expira:
            return False
        return self.codigo_verificacion == codigo
    
    def necesita_2fa_nuevamente(self):
        """Verifica si necesita verificar 2FA nuevamente (cada 30 días)"""
        from datetime import timedelta
        if not self.requiere_2fa or not self.email:
            return False
        # Si nunca ha sido verificado, sí necesita
        if not self.email_ultimo_verificado:
            return True
        # Si ha pasado más de 30 días desde la última verificación
        dias_pasados = (datetime.utcnow() - self.email_ultimo_verificado).days
        return dias_pasados >= 30
    
    def clave_expirada(self):
        """Verifica si la contraseña ha expirado (más de 90 días)"""
        if not self.clave_expira_en:
            return False
        return datetime.utcnow() > self.clave_expira_en
    
    def dias_para_expiracion_clave(self):
        """Devuelve días restantes para que expire la contraseña"""
        if not self.clave_expira_en:
            return None
        dias = (self.clave_expira_en - datetime.utcnow()).days
        return max(0, dias)
    
    def validar_nueva_clave(self, nueva_clave):
        """Valida que la nueva contraseña no sea igual a las últimas 3"""
        if not check_password_hash(self.clave_hash, nueva_clave):
            # OK - No es igual a la actual
            pass
        else:
            raise ValueError("La nueva contraseña no puede ser igual a la actual")
        
        # Verificar historial (últimas 3 contraseñas)
        historial_reciente = HistorialClaves.query.filter_by(usuario_id=self.id).order_by(
            HistorialClaves.creado_en.desc()
        ).limit(3).all()
        
        for anterior in historial_reciente:
            if check_password_hash(anterior.clave_hash, nueva_clave):
                raise ValueError("No puedes usar una contraseña anterior. Intenta con una diferente.")
    
    def generar_token_sesion(self):
        """Genera token único de sesión"""
        from datetime import timedelta
        self.token_sesion = secrets.token_urlsafe(32)
        self.token_expira = datetime.utcnow() + timedelta(hours=12)
        return self.token_sesion
    
    def validar_token(self, token):
        """Valida token de sesión"""
        if not self.token_sesion or not self.token_expira:
            return False
        if datetime.utcnow() > self.token_expira:
            return False
        return self.token_sesion == token
    
    def get_preferencias(self):
        """Obtiene preferencias como diccionario"""
        if not self.preferencias:
            return {
                'tema': 'light',
                'tamano_fuente': 'medium',
                'tipo_fuente': 'system',
                'idioma': 'es',
                'notificaciones': True
            }
        try:
            return json.loads(self.preferencias)
        except:
            return {}
    
    def set_preferencias(self, prefs_dict):
        """Guarda preferencias como JSON"""
        self.preferencias = json.dumps(prefs_dict, ensure_ascii=False)
    
    def registrar_acceso_exitoso(self):
        """Registra acceso exitoso"""
        self.ultimo_acceso = datetime.utcnow()
        self.intentos_fallidos = 0
        self.bloqueado = False
        self.bloqueado_hasta = None
    
    def registrar_acceso_fallido(self):
        """Registra intento fallido y bloquea si excede límite"""
        from datetime import timedelta
        self.intentos_fallidos += 1
        
        if self.intentos_fallidos >= 5:
            self.bloqueado = True
            self.bloqueado_hasta = datetime.utcnow() + timedelta(minutes=30)
    
    def puede_acceder(self):
        """Verifica si el usuario puede acceder"""
        if not self.activo:
            return False, "Usuario inactivo"
        
        if self.bloqueado:
            if self.bloqueado_hasta and datetime.utcnow() < self.bloqueado_hasta:
                return False, f"Usuario bloqueado hasta {self.bloqueado_hasta.strftime('%H:%M')}"
            else:
                # Desbloquear automáticamente
                self.bloqueado = False
                self.bloqueado_hasta = None
                self.intentos_fallidos = 0
        
        return True, "OK"
    
    def to_dict(self, incluir_sensible=False):
        """Convierte a diccionario (sin datos sensibles por defecto)"""
        data = {
            'id': self.id,
            'usuario': self.usuario,
            'email': self.email,
            'role': self.role,
            'secretaria': self.secretaria,
            'rol_descripcion': self.rol_descripcion,
            'nombre_completo': self.nombre_completo,
            'foto_perfil': self.foto_perfil,
            'activo': self.activo,
            'email_verificado': self.email_verificado,
            'requiere_2fa': self.requiere_2fa,
            'ultimo_acceso': self.ultimo_acceso.isoformat() if self.ultimo_acceso else None,
            'creado_en': self.creado_en.isoformat() if self.creado_en else None
        }
        
        if incluir_sensible:
            data['bloqueado'] = self.bloqueado
            data['intentos_fallidos'] = self.intentos_fallidos
            data['preferencias'] = self.get_preferencias()
        
        return data
    
    def __repr__(self):
        return f'<Usuario {self.usuario} ({self.role})>'


class AuditoriaAcceso(db.Model):
    """Registro de auditoría de accesos"""
    __tablename__ = 'auditoria_accesos'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    usuario_nombre = db.Column(db.String(100), nullable=False)
    accion = db.Column(db.String(100), nullable=False)  # login, logout, failed_login, etc.
    ip_address = db.Column(db.String(50), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    detalles = db.Column(db.Text, nullable=True)
    exitoso = db.Column(db.Boolean, default=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<Auditoria {self.usuario_nombre} - {self.accion} - {self.timestamp}>'


class HistorialClaves(db.Model):
    """Historial de contraseñas anteriores - Evita reutilización"""
    __tablename__ = 'historial_claves'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False, index=True)
    clave_hash = db.Column(db.String(255), nullable=False)  # Contraseña hasheada anterior
    creado_en = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<HistorialClaves usuario_id={self.usuario_id} creado={self.creado_en}>'


class Sesion(db.Model):
    """Sesiones activas de usuarios - Rastrear dónde está logueado"""
    __tablename__ = 'sesiones'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False, index=True)
    usuario_nombre = db.Column(db.String(100), nullable=False)
    token = db.Column(db.String(255), unique=True, nullable=False, index=True)
    ip_address = db.Column(db.String(50), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)  # Navegador/dispositivo
    ubicacion = db.Column(db.String(100), nullable=True)  # País/ciudad si es disponible
    inicio_sesion = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    ultimo_acceso = db.Column(db.DateTime, default=datetime.utcnow)
    cierre_sesion = db.Column(db.DateTime, nullable=True)  # Cuándo se cerró la sesión
    activa = db.Column(db.Boolean, default=True, index=True)
    dispositivo = db.Column(db.String(50), nullable=True)  # mobile, desktop, tablet
    
    def __repr__(self):
        return f'<Sesion usuario={self.usuario_nombre} ip={self.ip_address} activa={self.activa}>'
    
    def actualizar_ultimo_acceso(self):
        """Actualiza el timestamp del último acceso"""
        self.ultimo_acceso = datetime.utcnow()
    
    def cerrar_sesion(self):
        """Marca la sesión como cerrada"""
        self.activa = False
        self.cierre_sesion = datetime.utcnow()
    
    def segundos_activa(self):
        """Devuelve cuántos segundos lleva la sesión activa"""
        duracion = self.ultimo_acceso - self.inicio_sesion
        return int(duracion.total_seconds())


class RecuperacionClave(db.Model):
    """Tokens para recuperación de contraseña vía email"""
    __tablename__ = 'recuperacion_clave'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False, index=True)
    token = db.Column(db.String(100), unique=True, nullable=False, index=True)
    email = db.Column(db.String(150), nullable=False)  # Email a donde se envió
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
    expira_en = db.Column(db.DateTime, nullable=False)  # Token válido por 1 hora
    usado = db.Column(db.Boolean, default=False)
    usado_en = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<RecuperacionClave usuario_id={self.usuario_id} usado={self.usado}>'
    
    def es_valido(self):
        """Verifica si el token aún es válido"""
        return not self.usado and datetime.utcnow() < self.expira_en
