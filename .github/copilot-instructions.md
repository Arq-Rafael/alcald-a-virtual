# Alcaldía Virtual - AI Agent Instructions

## Project Overview
Flask-based municipal management system for Supatá, Colombia. Manages certificates, permits, contracts, risk management, citizen participation, and includes AI-powered document generation.

## Architecture

### Stack
- **Backend**: Flask 2.2+ with SQLAlchemy ORM
- **Database**: SQLite (local) / PostgreSQL (Railway production)
- **Frontend**: Jinja2 templates + Vanilla JavaScript (ES6+)
- **PDF Generation**: ReportLab (structured documents) + PyPDF2 (overlay/merge)
- **Email**: Resend API (not SMTP - Railway blocks port 587)
- **Deployment**: Railway (production) with Gunicorn

### Directory Structure
```
app/
├── __init__.py          # App factory with blueprint registration
├── config.py            # Environment-aware config (DB, paths, flags)
├── migrations.py        # Auto-migrations on startup (before blueprints)
├── models/              # SQLAlchemy models (Usuario, Plan, Contrato, etc.)
├── routes/              # Flask Blueprints (auth, main, certificados, ia, etc.)
├── utils/               # Helpers (email_resend.py, pdf_*, seguridad.py)
└── templates/           # Jinja2 HTML templates
```

## Critical Patterns

### 1. Database Migrations
Auto-migrations run **before blueprint registration** in `app/__init__.py`:
```python
with app.app_context():
    from .migrations import run_migrations
    run_migrations(app, db)  # Must execute BEFORE registering blueprints
```
- Migrations are SQL-based, not Alembic
- Check column existence before `ALTER TABLE ADD COLUMN`
- Use `IF NOT EXISTS` for PostgreSQL, handle `duplicate column` errors for SQLite

### 2. Email System (Resend, not SMTP)
Always use `app/utils/email_resend.py`, never SMTP:
```python
from app.utils.email_resend import send_first_login_code_email
send_first_login_code_email(email, username, code)
```
- Railway blocks SMTP ports - Resend uses HTTPS API
- Requires `RESEND_API_KEY` environment variable
- Default sender: `onboarding@resend.dev` (test mode)

### 3. Authentication Flow
Multi-step verification for first-time users:
1. Login → Password check
2. If `primer_acceso == True` → Generate 6-digit code
3. Email code via Resend → Redirect to `/verificar-primer-acceso`
4. Code validation → Mark `primer_acceso_verificado`
5. Dashboard access granted

See [app/routes/auth.py](app/routes/auth.py) lines 12-137.

### 4. iOS-Style UI Components
Templates use iOS 26 design patterns:
- Buttons: `.btn-ios` with standardized colors (`#34C759` green, `#007AFF` blue, `#FFB800` yellow)
- Modals: Bottom-sheet design (`.ios-modal`)
- Animations: `slideInFromBottom`, `bubbleIn`, `fadeOut` keyframes
- JavaScript: Inline `onclick` handlers, no frameworks

Example from [templates/riesgo_planes_contingencia.html](templates/riesgo_planes_contingencia.html):
```html
<button class="btn-ios btn-secciones" onclick="mostrarMenuSecciones({{ plan.id }})">
```

### 5. PDF Generation Workflow
Two-step process for official documents:
1. **Generate content PDF** using ReportLab Platypus (tables, paragraphs)
2. **Overlay with template** using PyPDF2 (merge with `FORMATO.pdf`)

See [app/utils/pdf_plans_generator.py](app/utils/pdf_plans_generator.py) line 382+ for approved plan covers.

### 6. Feature Access Control
Permission system based on `config.json`:
```python
from app.utils import can_access
if can_access('certificados'):
    # User has access
```
- Roles: `admin`, `superadmin`, `user`, `gobierno`, `planeacion`
- `ALWAYS_ADMIN=True` in dev mode bypasses checks

### 7. Static Assets
Serve from root `/static`:
- JavaScript: `/static/js/` (vanilla ES6, no bundlers)
- CSS: Inline in templates or `/static/css/`
- Images: `/static/img/` (e.g., `rana_supata.png` for PDFs)

## Development Workflows

### Run Locally
```powershell
# Activate venv (Windows)
.\venv\Scripts\Activate.ps1

# Run app
python run.py
# Accessible at http://localhost:5000
```

### Database Changes
1. Edit model in `app/models/*.py`
2. Add migration logic to `app/migrations.py`
3. Restart app - migrations auto-apply on startup

### Deploy to Railway
- Push to GitHub → Auto-deploy via `railway.json`
- Environment variables: `DATABASE_URL`, `RESEND_API_KEY`, `SECRET_KEY`
- Start command: `gunicorn run:app --bind 0.0.0.0:$PORT --timeout 120`

### Test Users (Local)
```python
# In Python shell
from app import create_app, db
from app.models.usuario import Usuario
app = create_app()
with app.app_context():
    user = Usuario(usuario='admin', clave='admin123', role='admin')
    db.session.add(user)
    db.session.commit()
```

## Common Tasks

### Add New Module
1. Create Blueprint in `app/routes/module_name.py`
2. Register in `app/__init__.py` (after migrations)
3. Create template in `templates/module_name.html`
4. Add route to main menu in `templates/base.html`

### Generate PDF Document
Use ReportLab for structured content:
```python
from reportlab.platypus import SimpleDocTemplate, Table, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
```
See existing generators: `pdf_plans_generator.py`, `pdf_generator.py`, `pdf_generador.py`

### Add Email Template
Add function to `app/utils/email_resend.py`:
```python
def send_custom_email(email, username, data):
    html = f"""
    <h1>Hello {username}</h1>
    <p>{data}</p>
    """
    return send_email_resend(email, "Subject", html)
```

## Anti-Patterns (Avoid)

❌ **Don't use SMTP** - Railway blocks it, use Resend  
❌ **Don't use Alembic** - Custom migration system in place  
❌ **Don't edit files via terminal** - Use file editing tools  
❌ **Don't create React/Vue components** - Pure Jinja2 + vanilla JS  
❌ **Don't install pytest** - No test suite currently  

## Key Files to Read

- [app/__init__.py](app/__init__.py) - App factory and blueprint registry
- [app/config.py](app/config.py) - Environment configuration
- [app/models/usuario.py](app/models/usuario.py) - User model with 2FA
- [app/routes/auth.py](app/routes/auth.py) - Authentication logic
- [COMIENZA_AQUI.md](COMIENZA_AQUI.md) - Quick start guide
- [INDICE_DOCUMENTACION.md](INDICE_DOCUMENTACION.md) - Documentation index
- [RESUMEN_FINAL.md](RESUMEN_FINAL.md) - Recent implementation summary

## Environment Variables

Required in production (Railway):
- `DATABASE_URL` - PostgreSQL connection string
- `RESEND_API_KEY` - Email API key (from resend.com)
- `SECRET_KEY` - Flask session encryption key
- `EMAIL_PROVIDER=resend` - Force Resend over SMTP

Optional:
- `RAILWAY_ENVIRONMENT` - Auto-set by Railway
- `PORT` - Auto-set by Railway (default: 5000)
