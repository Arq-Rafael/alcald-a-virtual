# Checklist de Optimización para Producción
## Alcaldía Virtual Supatá - Railway Deployment

## 🔒 Seguridad (Prioridad Crítica)

### SSL/HTTPS
- [x] HTTPS habilitado (Railway lo provee automáticamente)
- [ ] Forzar redirección HTTP → HTTPS en Flask
- [ ] Configurar Content Security Policy (CSP)
- [ ] Headers de seguridad (X-Frame-Options, X-Content-Type-Options)

```python
# En app/__init__.py o middleware
@app.after_request
def set_security_headers(response):
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response
```

### Autenticación
- [x] Sistema de login implementado
- [ ] Rate limiting en login (prevenir fuerza bruta)
- [ ] Captcha después de X intentos fallidos
- [ ] Logs de intentos de acceso
- [ ] Sesiones seguras con timeout

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    # Tu código de login
    pass
```

### Variables de Entorno
- [ ] SECRET_KEY fuerte y única (mínimo 32 caracteres)
- [ ] DATABASE_URL protegida
- [ ] RESEND_API_KEY en Railway secrets
- [ ] No exponer claves en logs

## ⚡ Rendimiento

### Assets Estáticos
- [ ] Minificar CSS en producción
- [ ] Minificar JavaScript
- [ ] Optimizar imágenes (WebP, compresión)
- [ ] Implementar cache de navegador
- [ ] CDN para assets si es posible

```python
# En config.py
if os.getenv('RAILWAY_ENVIRONMENT'):
    # Producción
    SEND_FILE_MAX_AGE_DEFAULT = 31536000  # 1 año cache
```

### Base de Datos
- [ ] Índices en columnas frecuentemente consultadas
- [ ] Pool de conexiones configurado
- [ ] Queries optimizadas (usar EXPLAIN)
- [ ] Backups automáticos habilitados

```python
# En config.py para PostgreSQL
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 10,
    'pool_recycle': 3600,
    'pool_pre_ping': True
}
```

### Caché
- [ ] Implementar Redis para sesiones (opcional)
- [ ] Cache de templates renderizados
- [ ] Cache de queries frecuentes

## 📊 Monitoreo y Logs

### Logging
- [ ] Logs estructurados (JSON)
- [ ] Niveles de log apropiados (ERROR en producción)
- [ ] Rotación de logs
- [ ] No loguear información sensible

```python
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    handler = RotatingFileHandler(
        'logs/alcaldia.log',
        maxBytes=10240000,
        backupCount=10
    )
    handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    ))
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)
```

### Monitoreo
- [ ] Implementar health check endpoint
- [ ] Monitoreo de uptime (UptimeRobot, Better Uptime)
- [ ] Alerts por email/Slack si la app cae
- [ ] Métricas de rendimiento (tiempos de respuesta)

```python
@app.route('/health')
def health_check():
    try:
        # Verificar DB
        db.session.execute('SELECT 1')
        return jsonify({'status': 'healthy', 'database': 'connected'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500
```

### Error Tracking
- [ ] Implementar Sentry o similar
- [ ] Páginas de error personalizadas (404, 500)
- [ ] Notificaciones de errores críticos

```python
# Sentry integration
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

if os.getenv('SENTRY_DSN'):
    sentry_sdk.init(
        dsn=os.getenv('SENTRY_DSN'),
        integrations=[FlaskIntegration()],
        traces_sample_rate=1.0
    )
```

## 🎨 Frontend

### Performance
- [ ] Lazy loading de imágenes
- [ ] Defer/async en scripts no críticos
- [ ] Minimizar reflows y repaints
- [ ] Service Worker para PWA (opcional)

```html
<!-- Lazy loading -->
<img src="imagen.jpg" loading="lazy" alt="...">

<!-- Async scripts -->
<script src="analytics.js" async></script>
```

### Accesibilidad
- [ ] Alt text en todas las imágenes
- [ ] Labels en todos los inputs
- [ ] Navegación por teclado funcional
- [ ] Contraste de colores AA o AAA
- [ ] ARIA labels donde corresponda

### SEO (si aplica)
- [ ] Meta tags configurados
- [ ] Sitemap.xml
- [ ] Robots.txt
- [ ] Open Graph tags para compartir

```html
<head>
    <title>Alcaldía Virtual Supatá - Gestión Municipal</title>
    <meta name="description" content="Sistema de gestión municipal para Supatá, Cundinamarca">
    <meta property="og:title" content="Alcaldía Virtual Supatá">
    <meta property="og:image" content="/static/img/rana_supata.png">
</head>
```

## 🧪 Testing

### Tests Automatizados
- [ ] Tests unitarios para funciones críticas
- [ ] Tests de integración para flujos principales
- [ ] Tests de regresión
- [ ] CI/CD con GitHub Actions

```python
# tests/test_auth.py
def test_login_success(client):
    response = client.post('/login', data={
        'usuario': 'admin',
        'clave': 'correct_password'
    })
    assert response.status_code == 302  # Redirect

def test_login_failure(client):
    response = client.post('/login', data={
        'usuario': 'admin',
        'clave': 'wrong_password'
    })
    assert b'credenciales' in response.data.lower()
```

## 📱 Mobile

### Responsive
- [ ] Probar en dispositivos reales
- [ ] Touch targets mínimo 44x44px
- [ ] Viewport meta tag configurado
- [ ] Sin scroll horizontal

```html
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0">
```

### PWA (Opcional)
- [ ] Manifest.json
- [ ] Service Worker
- [ ] Iconos de diferentes tamaños
- [ ] Offline fallback

## 🚀 Railway Específico

### Configuración
- [x] railway.json configurado
- [ ] Variables de entorno en Railway dashboard
- [ ] Build command optimizado
- [ ] Start command con Gunicorn

```json
// railway.json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "gunicorn run:app --workers 4 --bind 0.0.0.0:$PORT --timeout 120",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### Gunicorn
- [ ] Número de workers óptimo (2-4 × CPU cores)
- [ ] Timeout apropiado
- [ ] Graceful shutdown
- [ ] Access logs en producción

```python
# gunicorn.conf.py
workers = 4
worker_class = 'sync'
worker_connections = 1000
timeout = 120
keepalive = 5
graceful_timeout = 30

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'
```

## 📧 Email

### Configuración Resend
- [x] Resend API configurada
- [ ] Verificar dominio para emails
- [ ] Templates de email profesionales
- [ ] Rate limits configurados
- [ ] Logs de emails enviados

## 💾 Backups

### Base de Datos
- [ ] Backups automáticos diarios
- [ ] Backups antes de migraciones
- [ ] Plan de recuperación documentado
- [ ] Pruebas de restauración periódicas

### Archivos
- [ ] Backup de archivos subidos por usuarios
- [ ] Versionado de archivos críticos

## 📚 Documentación

### Para Usuarios
- [ ] Manual de usuario
- [ ] Video tutoriales
- [ ] FAQ
- [ ] Soporte técnico definido

### Para Desarrolladores
- [x] README.md completo
- [x] COMIENZA_AQUI.md
- [ ] Guía de contribución
- [ ] Changelog actualizado

## 🔄 Mantenimiento

### Actualizaciones
- [ ] Plan de actualizaciones de dependencias
- [ ] Revisar dependencias vulnerables (pip-audit)
- [ ] Changelog público
- [ ] Comunicación de cambios a usuarios

```bash
# Verificar vulnerabilidades
pip install pip-audit
pip-audit
```

### Escalabilidad
- [ ] Plan de escalado si usuarios crecen
- [ ] Considerar separar servicios (API, Workers)
- [ ] Load balancing si es necesario

## 📈 Analytics (Opcional)

- [ ] Google Analytics o alternativa
- [ ] Seguimiento de eventos clave
- [ ] Dashboard de métricas de uso
- [ ] GDPR/Cookie consent si aplica

## ✅ Checklist Prioritario para Esta Semana

1. **Seguridad**
   - [ ] Configurar headers de seguridad
   - [ ] Rate limiting en login
   - [ ] Verificar SECRET_KEY en Railway

2. **Monitoreo**
   - [ ] Endpoint /health
   - [ ] Configurar UptimeRobot o similar
   - [ ] Logging estructurado

3. **Performance**
   - [ ] Minificar CSS/JS
   - [ ] Optimizar imágenes
   - [ ] Cache headers

4. **UX**
   - [ ] Página 404 personalizada
   - [ ] Página 500 personalizada
   - [ ] Loading states en botones

5. **Testing**
   - [ ] Test del flujo de login
   - [ ] Test de funcionalidades críticas

## 📞 Contacto y Soporte

- **Documentación técnica**: Ver COMIENZA_AQUI.md
- **Reportar bugs**: [GitHub Issues si aplica]
- **Soporte**: [Email de contacto]

---

**Última actualización**: 2026-02-15
**Versión del sistema**: 2.0
**Ambiente**: Producción (Railway)
