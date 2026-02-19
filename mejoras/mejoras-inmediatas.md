# Mejoras Inmediatas - Código Listo para Implementar
## Alcaldía Virtual Supatá

## 🔒 1. Middleware de Seguridad

### Archivo: `app/middleware/security.py`

```python
"""
Middleware de seguridad para headers HTTP
"""
from functools import wraps
from flask import request, abort
import time

# Diccionario para rate limiting simple (considera Redis para producción)
login_attempts = {}

def add_security_headers(response):
    """
    Agrega headers de seguridad a todas las respuestas
    """
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # Content Security Policy
    csp = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
        "img-src 'self' data: https:; "
        "connect-src 'self' https://api.anthropic.com;"
    )
    response.headers['Content-Security-Policy'] = csp
    
    return response


def rate_limit(max_attempts=5, window=300):
    """
    Rate limiting decorator
    max_attempts: intentos permitidos
    window: ventana de tiempo en segundos (default: 5 minutos)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            ip = request.remote_addr
            current_time = time.time()
            
            # Limpiar intentos antiguos
            if ip in login_attempts:
                login_attempts[ip] = [
                    timestamp for timestamp in login_attempts[ip]
                    if current_time - timestamp < window
                ]
            
            # Verificar límite
            if ip in login_attempts and len(login_attempts[ip]) >= max_attempts:
                abort(429)  # Too Many Requests
            
            # Registrar intento
            if ip not in login_attempts:
                login_attempts[ip] = []
            login_attempts[ip].append(current_time)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def force_https():
    """
    Fuerza HTTPS en producción
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.url.startswith('http://') and not request.host.startswith('localhost'):
                url = request.url.replace('http://', 'https://', 1)
                return redirect(url, code=301)
            return f(*args, **kwargs)
        return decorated_function
    return decorator
```

### Integración en `app/__init__.py`:

```python
from app.middleware.security import add_security_headers, rate_limit

def create_app():
    app = Flask(__name__)
    
    # ... tu código existente ...
    
    # Aplicar middleware de seguridad
    @app.after_request
    def apply_security_headers(response):
        return add_security_headers(response)
    
    return app
```

### Uso en rutas de login (`app/routes/auth.py`):

```python
from app.middleware.security import rate_limit

@auth_bp.route('/login', methods=['POST'])
@rate_limit(max_attempts=5, window=300)  # 5 intentos en 5 minutos
def login():
    # Tu código de login existente
    pass
```

## 📊 2. Health Check Endpoint

### Archivo: `app/routes/health.py`

```python
"""
Endpoint de health check para monitoreo
"""
from flask import Blueprint, jsonify
from app import db
import os

health_bp = Blueprint('health', __name__)

@health_bp.route('/health')
def health_check():
    """
    Verifica el estado de la aplicación
    """
    health_status = {
        'status': 'healthy',
        'environment': os.getenv('RAILWAY_ENVIRONMENT', 'development'),
        'checks': {}
    }
    
    # Check database
    try:
        db.session.execute('SELECT 1')
        health_status['checks']['database'] = 'connected'
    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['checks']['database'] = f'error: {str(e)}'
        return jsonify(health_status), 500
    
    # Check email service (Resend)
    resend_key = os.getenv('RESEND_API_KEY')
    health_status['checks']['email'] = 'configured' if resend_key else 'not configured'
    
    return jsonify(health_status), 200


@health_bp.route('/ping')
def ping():
    """
    Endpoint simple para verificar que la app responde
    """
    return jsonify({'status': 'pong'}), 200
```

### Registrar en `app/__init__.py`:

```python
from app.routes.health import health_bp

app.register_blueprint(health_bp)
```

## 🎨 3. Páginas de Error Personalizadas

### Archivo: `app/templates/errors/404.html`

```html
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Página no encontrada - Alcaldía Supatá</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(-45deg, #1b5e20, #4caf50, #f9a825, #66bb6a);
            background-size: 400% 400%;
            animation: gradient 15s ease infinite;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 2rem;
        }
        
        @keyframes gradient {
            0%, 100% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
        }
        
        .error-container {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 24px;
            padding: 3rem;
            max-width: 500px;
            text-align: center;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
        }
        
        .error-code {
            font-size: 6rem;
            font-weight: 800;
            background: linear-gradient(135deg, #1b5e20, #4caf50);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 1rem;
        }
        
        h1 {
            font-size: 1.8rem;
            color: #1b5e20;
            margin-bottom: 1rem;
        }
        
        p {
            color: #666;
            margin-bottom: 2rem;
            line-height: 1.6;
        }
        
        .btn-home {
            display: inline-block;
            padding: 1rem 2rem;
            background: linear-gradient(135deg, #1b5e20, #4caf50);
            color: white;
            text-decoration: none;
            border-radius: 12px;
            font-weight: 600;
            transition: transform 0.3s ease;
        }
        
        .btn-home:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(27, 94, 32, 0.4);
        }
        
        .rana {
            width: 120px;
            margin: 0 auto 2rem;
            opacity: 0.8;
        }
    </style>
</head>
<body>
    <div class="error-container">
        <img src="{{ url_for('static', filename='img/rana_supata.png') }}" alt="Rana Supatá" class="rana">
        <div class="error-code">404</div>
        <h1>Página no encontrada</h1>
        <p>Lo sentimos, la página que buscas no existe o ha sido movida.</p>
        <a href="{{ url_for('main.dashboard') }}" class="btn-home">
            <i class="fas fa-home"></i> Volver al inicio
        </a>
    </div>
</body>
</html>
```

### Archivo: `app/templates/errors/500.html`

```html
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Error del servidor - Alcaldía Supatá</title>
    <style>
        /* Mismo estilo que 404.html */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(-45deg, #1b5e20, #4caf50, #f9a825, #66bb6a);
            background-size: 400% 400%;
            animation: gradient 15s ease infinite;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 2rem;
        }
        
        @keyframes gradient {
            0%, 100% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
        }
        
        .error-container {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 24px;
            padding: 3rem;
            max-width: 500px;
            text-align: center;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
        }
        
        .error-code {
            font-size: 6rem;
            font-weight: 800;
            background: linear-gradient(135deg, #ef4444, #dc2626);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 1rem;
        }
        
        h1 {
            font-size: 1.8rem;
            color: #dc2626;
            margin-bottom: 1rem;
        }
        
        p {
            color: #666;
            margin-bottom: 2rem;
            line-height: 1.6;
        }
        
        .btn-home {
            display: inline-block;
            padding: 1rem 2rem;
            background: linear-gradient(135deg, #1b5e20, #4caf50);
            color: white;
            text-decoration: none;
            border-radius: 12px;
            font-weight: 600;
            transition: transform 0.3s ease;
        }
        
        .btn-home:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(27, 94, 32, 0.4);
        }
    </style>
</head>
<body>
    <div class="error-container">
        <div class="error-code">500</div>
        <h1>Error del servidor</h1>
        <p>Lo sentimos, algo salió mal en nuestro servidor. Estamos trabajando para solucionarlo.</p>
        <a href="{{ url_for('main.dashboard') }}" class="btn-home">
            <i class="fas fa-home"></i> Volver al inicio
        </a>
    </div>
</body>
</html>
```

### Registrar handlers de error en `app/__init__.py`:

```python
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()  # Rollback cualquier transacción pendiente
    return render_template('errors/500.html'), 500

@app.errorhandler(429)
def ratelimit_error(error):
    return jsonify({
        'error': 'Demasiados intentos',
        'message': 'Por favor espera unos minutos antes de intentar nuevamente'
    }), 429
```

## 📝 4. Logging Mejorado

### Archivo: `app/utils/logging_config.py`

```python
"""
Configuración de logging estructurado
"""
import logging
import os
from logging.handlers import RotatingFileHandler
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """
    Formatea logs en JSON para mejor parsing
    """
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


def setup_logging(app):
    """
    Configura el sistema de logging
    """
    # Crear directorio de logs si no existe
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    # Handler para archivo
    file_handler = RotatingFileHandler(
        'logs/alcaldia.log',
        maxBytes=10240000,  # 10MB
        backupCount=10
    )
    file_handler.setFormatter(JSONFormatter())
    file_handler.setLevel(logging.INFO)
    
    # Handler para consola (Railway)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    ))
    console_handler.setLevel(logging.INFO)
    
    # Configurar logger de la app
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(logging.INFO)
    
    app.logger.info('Sistema de logging inicializado')
```

### Usar en `app/__init__.py`:

```python
from app.utils.logging_config import setup_logging

def create_app():
    app = Flask(__name__)
    
    # ... configuración ...
    
    # Setup logging
    if not app.debug:
        setup_logging(app)
    
    return app
```

## 🚀 5. Configuración de Gunicorn

### Archivo: `gunicorn.conf.py` (en raíz del proyecto)

```python
"""
Configuración de Gunicorn para producción en Railway
"""
import os
import multiprocessing

# Número de workers (2-4 × CPU cores)
workers = int(os.getenv('WEB_CONCURRENCY', multiprocessing.cpu_count() * 2))

# Tipo de worker
worker_class = 'sync'

# Número de conexiones simultáneas por worker
worker_connections = 1000

# Timeout
timeout = 120

# Keepalive
keepalive = 5

# Graceful timeout
graceful_timeout = 30

# Max requests por worker (previene memory leaks)
max_requests = 1000
max_requests_jitter = 50

# Bind
bind = f"0.0.0.0:{os.getenv('PORT', '5000')}"

# Logging
accesslog = '-'  # Log a stdout para Railway
errorlog = '-'   # Log a stderr para Railway
loglevel = 'info'

# Preload app (reduce memory usage)
preload_app = True

# PID file
pidfile = '/tmp/gunicorn.pid'
```

### Actualizar `railway.json`:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "gunicorn run:app -c gunicorn.conf.py",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

## 📦 6. Actualizar requirements.txt

```txt
# Agregar estas dependencias
flask-limiter>=3.5.0  # Rate limiting
sentry-sdk>=1.40.0    # Error tracking (opcional)
python-dotenv>=1.0.0  # Variables de entorno
```

## 🔐 7. Variables de Entorno en Railway

### En Railway Dashboard → Variables:

```
# Obligatorias
SECRET_KEY=tu-clave-super-secreta-de-minimo-32-caracteres
DATABASE_URL=postgresql://...
RESEND_API_KEY=re_...

# Opcionales
SENTRY_DSN=https://...  # Si usas Sentry
FLASK_ENV=production
```

## ✅ Orden de Implementación

1. **Primero**: Security headers y rate limiting
2. **Segundo**: Health check endpoint
3. **Tercero**: Páginas de error personalizadas
4. **Cuarto**: Logging mejorado
5. **Quinto**: Configuración de Gunicorn

## 🧪 Testing

### Probar rate limiting:

```bash
# Hacer múltiples requests rápidos al login
for i in {1..10}; do
  curl -X POST https://alcaldia-virtual-supata.up.railway.app/login \
    -d "usuario=test&clave=test"
done
```

### Probar health check:

```bash
curl https://alcaldia-virtual-supata.up.railway.app/health
```

---

**Nota**: Implementa estos cambios uno por uno, testeando en cada paso.
