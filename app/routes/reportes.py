"""
Rutas para Panel de Reportes y Estadísticas
Permite ver estadísticas de acceso, sesiones activas, etc.
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify
from flask import current_app
from app import db
from app.models.usuario import Usuario, AuditoriaAcceso, Sesion
from datetime import datetime, timedelta
from sqlalchemy import func, and_

reportes_bp = Blueprint('reportes', __name__, url_prefix='/reportes')

# Decorador para verificar que sea admin
def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            flash('Acceso denegado. Se requieren permisos de administrador.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@reportes_bp.route('/dashboard')
@admin_required
def dashboard():
    """Panel principal de reportes y estadísticas"""
    
    # Estadísticas generales
    total_usuarios = Usuario.query.count()
    usuarios_activos = Usuario.query.filter_by(activo=True).count()
    usuarios_bloqueados = Usuario.query.filter_by(bloqueado=True).count()
    sesiones_activas = Sesion.query.filter_by(activa=True).count()
    
    # Accesos últimos 7 días
    hace_7_dias = datetime.utcnow() - timedelta(days=7)
    accesos_7_dias = AuditoriaAcceso.query.filter(
        AuditoriaAcceso.timestamp > hace_7_dias,
        AuditoriaAcceso.accion == 'login'
    ).count()
    
    # Intentos fallidos últimos 7 días
    intentos_fallidos = AuditoriaAcceso.query.filter(
        AuditoriaAcceso.timestamp > hace_7_dias,
        AuditoriaAcceso.accion == 'failed_login'
    ).count()
    
    # Top 10 usuarios más activos
    usuarios_activos_list = db.session.query(
        AuditoriaAcceso.usuario_nombre,
        func.count(AuditoriaAcceso.id).label('total_accesos')
    ).filter(
        AuditoriaAcceso.timestamp > hace_7_dias,
        AuditoriaAcceso.accion == 'login'
    ).group_by(AuditoriaAcceso.usuario_nombre).order_by(
        func.count(AuditoriaAcceso.id).desc()
    ).limit(10).all()
    
    # Accesos por día (últimos 7 días)
    accesos_por_dia = []
    for i in range(7, -1, -1):
        fecha = (datetime.utcnow() - timedelta(days=i)).date()
        count = AuditoriaAcceso.query.filter(
            func.date(AuditoriaAcceso.timestamp) == fecha,
            AuditoriaAcceso.accion == 'login'
        ).count()
        accesos_por_dia.append({
            'fecha': fecha.strftime('%d/%m'),
            'accesos': count
        })
    
    # Sesiones activas del usuario actual
    username = session.get('user')
    mis_sesiones = Sesion.query.filter_by(
        usuario_nombre=username,
        activa=True
    ).order_by(Sesion.inicio_sesion.desc()).all()
    
    stats = {
        'total_usuarios': total_usuarios,
        'usuarios_activos': usuarios_activos,
        'usuarios_bloqueados': usuarios_bloqueados,
        'sesiones_activas': sesiones_activas,
        'accesos_7_dias': accesos_7_dias,
        'intentos_fallidos': intentos_fallidos,
        'usuarios_top': usuarios_activos_list,
        'accesos_por_dia': accesos_por_dia,
        'mis_sesiones': mis_sesiones
    }
    
    return render_template('reportes_dashboard.html', stats=stats)


@reportes_bp.route('/auditoria')
@admin_required
def auditoria():
    """Log completo de auditoría"""
    
    # Paginación
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    # Filtros
    usuario = request.args.get('usuario', '').strip()
    accion = request.args.get('accion', '').strip()
    dias = request.args.get('dias', 30, type=int)
    
    # Query base
    query = AuditoriaAcceso.query
    
    # Aplicar filtros
    if usuario:
        query = query.filter(AuditoriaAcceso.usuario_nombre.ilike(f'%{usuario}%'))
    
    if accion:
        query = query.filter_by(accion=accion)
    
    if dias:
        fecha_limite = datetime.utcnow() - timedelta(days=dias)
        query = query.filter(AuditoriaAcceso.timestamp > fecha_limite)
    
    # Ordenar por fecha descendente
    logs = query.order_by(AuditoriaAcceso.timestamp.desc()).paginate(
        page=page,
        per_page=per_page
    )
    
    # Acciones únicas para filtro
    acciones_disponibles = db.session.query(
        AuditoriaAcceso.accion
    ).distinct().order_by(AuditoriaAcceso.accion).all()
    
    return render_template(
        'reportes_auditoria.html',
        logs=logs,
        acciones=acciones_disponibles,
        filtro_usuario=usuario,
        filtro_accion=accion,
        filtro_dias=dias
    )


@reportes_bp.route('/sesiones')
@admin_required
def sesiones():
    """Gestión de sesiones activas"""
    
    # Sesiones activas
    sesiones_activas = Sesion.query.filter_by(activa=True).order_by(
        Sesion.ultimo_acceso.desc()
    ).all()
    
    # Sesiones cerradas (últimos 7 días)
    hace_7_dias = datetime.utcnow() - timedelta(days=7)
    sesiones_cerradas = Sesion.query.filter(
        Sesion.activa == False,
        Sesion.cierre_sesion > hace_7_dias
    ).order_by(Sesion.cierre_sesion.desc()).all()
    
    return render_template(
        'reportes_sesiones.html',
        sesiones_activas=sesiones_activas,
        sesiones_cerradas=sesiones_cerradas
    )


@reportes_bp.route('/sesion/<int:sesion_id>/cerrar', methods=['POST'])
@admin_required
def cerrar_sesion_admin(sesion_id):
    """Cerrar sesión de usuario (admin)"""
    
    sesion = Sesion.query.get(sesion_id)
    
    if not sesion:
        return jsonify({'error': 'Sesión no encontrada'}), 404
    
    # Registrar auditoría
    auditoria = AuditoriaAcceso(
        usuario_nombre=session.get('user'),
        accion='cerrar_sesion_usuario',
        ip_address=request.remote_addr,
        detalles=f'Admin cerró sesión de {sesion.usuario_nombre} desde {sesion.ip_address}',
        exitoso=True
    )
    
    sesion.cerrar_sesion()
    db.session.add(auditoria)
    db.session.commit()
    
    return jsonify({'success': True, 'mensaje': 'Sesión cerrada'})


@reportes_bp.route('/contrasenas-expirando')
@admin_required
def contrasenas_expirando():
    """Usuarios con contraseñas próximas a expirar"""
    
    ahora = datetime.utcnow()
    proximos_30_dias = ahora + timedelta(days=30)
    
    usuarios_expirando = Usuario.query.filter(
        and_(
            Usuario.clave_expira_en > ahora,
            Usuario.clave_expira_en <= proximos_30_dias
        )
    ).order_by(Usuario.clave_expira_en).all()
    
    usuarios_expiradas = Usuario.query.filter(
        Usuario.clave_expira_en <= ahora
    ).order_by(Usuario.clave_expira_en.desc()).all()
    
    return render_template(
        'reportes_contrasenas.html',
        usuarios_expirando=usuarios_expirando,
        usuarios_expiradas=usuarios_expiradas
    )


@reportes_bp.route('/exportar/csv')
@admin_required
def exportar_auditoria_csv():
    """Exportar auditoría a CSV"""
    import csv
    from io import StringIO
    from flask import make_response
    
    dias = request.args.get('dias', 30, type=int)
    fecha_limite = datetime.utcnow() - timedelta(days=dias)
    
    logs = AuditoriaAcceso.query.filter(
        AuditoriaAcceso.timestamp > fecha_limite
    ).order_by(AuditoriaAcceso.timestamp.desc()).all()
    
    # Crear CSV
    output = StringIO()
    writer = csv.writer(output)
    
    writer.writerow(['Usuario', 'Acción', 'IP Address', 'Timestamp', 'Exitoso', 'Detalles'])
    
    for log in logs:
        writer.writerow([
            log.usuario_nombre,
            log.accion,
            log.ip_address,
            log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'Sí' if log.exitoso else 'No',
            log.detalles or ''
        ])
    
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = f'attachment; filename=auditoria_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    response.headers['Content-type'] = 'text/csv'
    
    return response
