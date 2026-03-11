from datetime import datetime
import json
from datetime import timedelta

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, session, url_for
from sqlalchemy import func, or_

from app import db
from app.models.correo_inteligente import (
    CorreoInstitucionalBorrador,
    CorreoInstitucionalCuenta,
    CorreoInstitucionalMensaje,
)
from app.models.usuario import Usuario
from app.services.institutional_mail_ai import InstitutionalMailAIService
from app.services.institutional_mail_gmail import GmailIntegrationError, GmailIntegrationService
from app.services.institutional_mail_sla import calculate_attention_status
from app.utils import can_access


correo_inteligente_bp = Blueprint('correo_inteligente', __name__, url_prefix='/correo-inteligente')

AVAILABLE_TONES = [
    'formal_institucional',
    'tecnica',
    'breve_ejecutiva',
    'cordial',
    'estricta',
]


def _current_user():
    username = session.get('user')
    if not username:
        return None
    return Usuario.query.filter_by(usuario=username).first()


def _require_session_and_permission():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    if not can_access('correo_inteligente'):
        flash('No tienes permisos para acceder a Correo Inteligente Institucional.', 'danger')
        return redirect(url_for('main.dashboard'))
    return None


def _get_or_create_account(user):
    account = CorreoInstitucionalCuenta.query.filter_by(usuario_id=user.id).first()
    if account:
        return account

    account = CorreoInstitucionalCuenta(
        usuario_id=user.id,
        email_institucional=user.email or f"{user.usuario}@supata-cundinamarca.gov.co",
        proveedor='gmail',
        conectada=False,
        estado='desconectada',
    )
    db.session.add(account)
    db.session.commit()
    return account


def _get_message_for_user(message_id):
    user = _current_user()
    if not user:
        return None
    account = CorreoInstitucionalCuenta.query.filter_by(usuario_id=user.id).first()
    if not account:
        return None
    return CorreoInstitucionalMensaje.query.filter_by(id=message_id, cuenta_id=account.id).first()


def _apply_ai_and_sla(message):
    ai_service = InstitutionalMailAIService()
    ai_result = ai_service.analyze_email(
        asunto=message.asunto,
        cuerpo_texto=message.cuerpo_texto,
        remitente=message.remitente_email,
    )

    message.categoria = ai_result.get('tipo_correo', 'otro')
    message.urgencia = ai_result.get('nivel_urgencia', 'media')
    message.requiere_respuesta = bool(ai_result.get('requiere_respuesta', True))
    message.tema_principal = ai_result.get('tema_principal', '')
    message.resumen_ejecutivo = ai_result.get('resumen_ejecutivo', '')
    message.recomendacion_gestion = ai_result.get('recomendacion_gestion', '')
    message.analizado_at = datetime.utcnow()

    sla = calculate_attention_status(
        fecha_recepcion=message.fecha_recepcion,
        categoria=message.categoria,
        requiere_respuesta=message.requiere_respuesta,
        urgencia=message.urgencia,
    )
    message.semaforo = sla['semaforo']
    message.dias_transcurridos = sla['dias_transcurridos']
    message.prioridad = sla['prioridad']
    message.riesgo_vencimiento = sla['riesgo_vencimiento']


@correo_inteligente_bp.route('', methods=['GET'])
def inbox():
    denial = _require_session_and_permission()
    if denial:
        return denial

    user = _current_user()
    if not user:
        return redirect(url_for('auth.login'))

    account = _get_or_create_account(user)

    q = (request.args.get('q') or '').strip()
    categoria = (request.args.get('categoria') or '').strip()
    estado = (request.args.get('estado') or '').strip()
    semaforo = (request.args.get('semaforo') or '').strip()
    requiere = (request.args.get('requiere') or '').strip()
    order_by = (request.args.get('order') or 'fecha_desc').strip()

    messages_query = CorreoInstitucionalMensaje.query.filter_by(cuenta_id=account.id)

    if q:
        like = f"%{q}%"
        messages_query = messages_query.filter(
            or_(
                CorreoInstitucionalMensaje.asunto.ilike(like),
                CorreoInstitucionalMensaje.remitente.ilike(like),
                CorreoInstitucionalMensaje.snippet.ilike(like),
            )
        )

    if categoria:
        messages_query = messages_query.filter_by(categoria=categoria)
    if estado:
        messages_query = messages_query.filter_by(estado=estado)
    if semaforo:
        messages_query = messages_query.filter_by(semaforo=semaforo)
    if requiere in ('si', 'no'):
        messages_query = messages_query.filter_by(requiere_respuesta=(requiere == 'si'))

    if order_by == 'fecha_asc':
        messages_query = messages_query.order_by(CorreoInstitucionalMensaje.fecha_recepcion.asc())
    elif order_by == 'prioridad':
        messages_query = messages_query.order_by(CorreoInstitucionalMensaje.prioridad.asc(), CorreoInstitucionalMensaje.fecha_recepcion.desc())
    elif order_by == 'estado':
        messages_query = messages_query.order_by(CorreoInstitucionalMensaje.estado.asc(), CorreoInstitucionalMensaje.fecha_recepcion.desc())
    else:
        messages_query = messages_query.order_by(CorreoInstitucionalMensaje.fecha_recepcion.desc())

    messages = messages_query.limit(250).all()

    selected_id = request.args.get('msg_id', type=int)
    selected_message = None
    if selected_id:
        selected_message = CorreoInstitucionalMensaje.query.filter_by(id=selected_id, cuenta_id=account.id).first()
    if not selected_message and messages:
        selected_message = messages[0]

    total = CorreoInstitucionalMensaje.query.filter_by(cuenta_id=account.id).count()
    requieren_respuesta = CorreoInstitucionalMensaje.query.filter_by(cuenta_id=account.id, requiere_respuesta=True).count()
    criticos = CorreoInstitucionalMensaje.query.filter_by(cuenta_id=account.id, semaforo='rojo').count()
    pendientes = CorreoInstitucionalMensaje.query.filter(
        CorreoInstitucionalMensaje.cuenta_id == account.id,
        CorreoInstitucionalMensaje.estado.in_(['nuevo', 'en_gestion'])
    ).count()

    categoria_stats = db.session.query(
        CorreoInstitucionalMensaje.categoria,
        func.count(CorreoInstitucionalMensaje.id)
    ).filter(
        CorreoInstitucionalMensaje.cuenta_id == account.id
    ).group_by(CorreoInstitucionalMensaje.categoria).all()

    estado_stats = db.session.query(
        CorreoInstitucionalMensaje.estado,
        func.count(CorreoInstitucionalMensaje.id)
    ).filter(
        CorreoInstitucionalMensaje.cuenta_id == account.id
    ).group_by(CorreoInstitucionalMensaje.estado).all()

    analytics = {
        'total': total,
        'requieren_respuesta': requieren_respuesta,
        'criticos': criticos,
        'pendientes': pendientes,
        'categoria': {k or 'otro': v for k, v in categoria_stats},
        'estado': {k or 'nuevo': v for k, v in estado_stats},
        'tendencia_7d': _build_trend_last_7_days(account.id),
    }

    return render_template(
        'correo_inteligente.html',
        account=account,
        messages=messages,
        selected_message=selected_message,
        analytics=analytics,
        filters={
            'q': q,
            'categoria': categoria,
            'estado': estado,
            'semaforo': semaforo,
            'requiere': requiere,
            'order': order_by,
        },
        categories=[
            'derecho_peticion', 'peticion', 'queja', 'reclamo', 'solicitud',
            'requerimiento', 'invitacion', 'informativo', 'interno', 'urgente', 'otro'
        ],
        tones=AVAILABLE_TONES,
    )


@correo_inteligente_bp.route('/oauth/connect', methods=['POST'])
def oauth_connect():
    denial = _require_session_and_permission()
    if denial:
        return denial

    user = _current_user()
    if not user:
        return redirect(url_for('auth.login'))

    account = _get_or_create_account(user)

    try:
        gmail = GmailIntegrationService(current_app.config)
        state_payload = json.dumps({'uid': user.id, 'aid': account.id})
        auth_url, _state, code_verifier = gmail.get_authorization_url(state_payload=state_payload)
        if code_verifier:
            session['oauth_code_verifier'] = code_verifier
        return redirect(auth_url)
    except GmailIntegrationError as exc:
        flash(str(exc), 'danger')
    except Exception as exc:
        flash(f'No fue posible iniciar OAuth con Gmail: {exc}', 'danger')

    return redirect(url_for('correo_inteligente.inbox'))


@correo_inteligente_bp.route('/oauth/callback', methods=['GET'])
def oauth_callback():
    denial = _require_session_and_permission()
    if denial:
        return denial

    user = _current_user()
    if not user:
        return redirect(url_for('auth.login'))

    code = request.args.get('code')
    if not code:
        flash('Gmail no devolvio codigo de autorizacion.', 'danger')
        return redirect(url_for('correo_inteligente.inbox'))

    account = _get_or_create_account(user)

    try:
        gmail = GmailIntegrationService(current_app.config)
        code_verifier = session.pop('oauth_code_verifier', None)
        token_payload = gmail.exchange_code_for_token(code, code_verifier=code_verifier)
        account.token_encriptado = gmail.encrypt_token_payload(token_payload)
        account.set_scopes(token_payload.get('scopes') or [])
        account.conectada = True
        account.estado = 'conectada'
        account.mensaje_estado = 'Cuenta autorizada correctamente.'
        db.session.commit()
        flash('Conexion Gmail completada. Ya puedes sincronizar correos.', 'success')
    except GmailIntegrationError as exc:
        flash(str(exc), 'danger')
    except Exception as exc:
        account.estado = 'error'
        account.mensaje_estado = str(exc)
        db.session.commit()
        flash(f'Error al finalizar autorizacion Gmail: {exc}', 'danger')

    return redirect(url_for('correo_inteligente.inbox'))


@correo_inteligente_bp.route('/sync', methods=['POST'])
def sync_messages():
    denial = _require_session_and_permission()
    if denial:
        return denial

    user = _current_user()
    if not user:
        return redirect(url_for('auth.login'))

    account = _get_or_create_account(user)
    if not account.conectada or not account.token_encriptado:
        flash('Debes conectar primero la cuenta Gmail institucional.', 'warning')
        return redirect(url_for('correo_inteligente.inbox'))

    try:
        gmail = GmailIntegrationService(current_app.config)
        token_payload = gmail.decrypt_token_payload(account.token_encriptado)
        raw_messages = gmail.list_message_details(token_payload, max_results=150)

        inserted = 0
        updated = 0
        for item in raw_messages:
            msg = CorreoInstitucionalMensaje.query.filter_by(gmail_message_id=item['gmail_message_id']).first()
            if not msg:
                msg = CorreoInstitucionalMensaje(
                    cuenta_id=account.id,
                    gmail_message_id=item['gmail_message_id'],
                    gmail_thread_id=item.get('gmail_thread_id'),
                    remitente=item.get('remitente'),
                    remitente_email=item.get('remitente_email'),
                    destinatarios=item.get('destinatarios'),
                    cc=item.get('cc'),
                    asunto=item.get('asunto'),
                    snippet=item.get('snippet'),
                    cuerpo_texto=item.get('cuerpo_texto'),
                    fecha_recepcion=item.get('fecha_recepcion') or datetime.utcnow(),
                    tiene_adjuntos=bool(item.get('tiene_adjuntos')),
                )
                msg.set_adjuntos(item.get('adjuntos', []))
                _apply_ai_and_sla(msg)
                db.session.add(msg)
                inserted += 1
            else:
                msg.remitente = item.get('remitente') or msg.remitente
                msg.remitente_email = item.get('remitente_email') or msg.remitente_email
                msg.destinatarios = item.get('destinatarios') or msg.destinatarios
                msg.cc = item.get('cc') or msg.cc
                msg.asunto = item.get('asunto') or msg.asunto
                msg.snippet = item.get('snippet') or msg.snippet
                msg.cuerpo_texto = item.get('cuerpo_texto') or msg.cuerpo_texto
                msg.tiene_adjuntos = bool(item.get('tiene_adjuntos'))
                msg.set_adjuntos(item.get('adjuntos', []))
                _apply_ai_and_sla(msg)
                updated += 1

        account.ultima_sincronizacion = datetime.utcnow()
        account.estado = 'conectada'
        account.mensaje_estado = f'Sincronizacion exitosa. Nuevos: {inserted}, actualizados: {updated}'
        db.session.commit()

        flash(account.mensaje_estado, 'success')
    except Exception as exc:
        db.session.rollback()
        account.estado = 'error'
        account.mensaje_estado = str(exc)
        db.session.commit()
        flash(f'Error al sincronizar correos: {exc}', 'danger')

    return redirect(url_for('correo_inteligente.inbox'))


@correo_inteligente_bp.route('/api/message/<int:message_id>/reanalyze', methods=['POST'])
def reanalyze_message(message_id):
    denial = _require_session_and_permission()
    if denial:
        return jsonify({'error': 'unauthorized'}), 401

    msg = _get_message_for_user(message_id)
    if not msg:
        return jsonify({'error': 'not_found'}), 404
    _apply_ai_and_sla(msg)
    db.session.commit()
    return jsonify({'success': True, 'message': msg.to_dict()})


@correo_inteligente_bp.route('/api/message/<int:message_id>/draft', methods=['POST'])
def generate_draft(message_id):
    denial = _require_session_and_permission()
    if denial:
        return jsonify({'error': 'unauthorized'}), 401

    tone = (request.get_json(silent=True) or {}).get('tone', 'formal_institucional')
    if tone not in AVAILABLE_TONES:
        tone = 'formal_institucional'

    msg = _get_message_for_user(message_id)
    if not msg:
        return jsonify({'error': 'not_found'}), 404

    email_context = msg.to_dict()
    pdf_text_agg = []
    
    # Extraer texto de adjuntos PDF, si los hay
    try:
        user = _current_user()
        account = CorreoInstitucionalCuenta.query.filter_by(usuario_id=user.id).first()
        gmail = GmailIntegrationService(current_app.config)
        token_payload = gmail.decrypt_token_payload(account.token_encriptado)
        
        for adj in msg.get_adjuntos():
            if 'pdf' in str(adj.get('mimeType')).lower() or str(adj.get('filename')).lower().endswith('.pdf'):
                att_id = adj.get('attachmentId')
                if att_id:
                    text_extracted = gmail.download_attachment_text(token_payload, msg.gmail_message_id, att_id)
                    if text_extracted:
                        pdf_text_agg.append(f"Contenido de {adj.get('filename')}:\n{text_extracted}")
                        
        if pdf_text_agg:
            email_context['pdf_text'] = '\n\n---\n\n'.join(pdf_text_agg)
    except Exception as e:
        print(f"Error procesando PDF para contexto IA: {e}")

    ai_service = InstitutionalMailAIService()
    draft_text = ai_service.generate_draft(email_context=email_context, tone=tone)

    latest = CorreoInstitucionalBorrador.query.filter_by(mensaje_id=msg.id, tono=tone).order_by(
        CorreoInstitucionalBorrador.version.desc()
    ).first()
    next_version = (latest.version + 1) if latest else 1

    draft = CorreoInstitucionalBorrador(
        mensaje_id=msg.id,
        tono=tone,
        version=next_version,
        contenido=draft_text,
        generado_por_ia=True,
        generado_por=session.get('user'),
    )
    db.session.add(draft)
    db.session.commit()

    return jsonify({'success': True, 'draft': draft.to_dict()})


@correo_inteligente_bp.route('/api/message/<int:message_id>/status', methods=['POST'])
def update_status(message_id):
    denial = _require_session_and_permission()
    if denial:
        return jsonify({'error': 'unauthorized'}), 401

    payload = request.get_json(silent=True) or {}
    status = (payload.get('status') or '').strip()

    if status not in ('nuevo', 'en_gestion', 'respondido', 'informativo'):
        return jsonify({'success': False, 'error': 'Estado no valido'}), 400

    msg = _get_message_for_user(message_id)
    if not msg:
        return jsonify({'error': 'not_found'}), 404
    msg.estado = status
    if status == 'respondido':
        msg.respondido_at = datetime.utcnow()
    db.session.commit()

    return jsonify({'success': True, 'message': msg.to_dict()})


@correo_inteligente_bp.route('/api/message/<int:message_id>/send_reply', methods=['POST'])
def send_reply(message_id):
    denial = _require_session_and_permission()
    if denial:
        return jsonify({'error': 'unauthorized'}), 401

    payload = request.get_json(silent=True) or {}
    reply_body = (payload.get('body') or '').strip()
    
    if not reply_body:
        return jsonify({'success': False, 'error': 'El cuerpo del correo está vacío'}), 400

    msg = _get_message_for_user(message_id)
    if not msg:
        return jsonify({'error': 'not_found'}), 404
        
    user = _current_user()
    account = CorreoInstitucionalCuenta.query.filter_by(usuario_id=user.id).first()
    
    if not account or not account.conectada or not account.token_encriptado:
        return jsonify({'success': False, 'error': 'La cuenta Gmail no está conectada'}), 400

    try:
        gmail = GmailIntegrationService(current_app.config)
        token_payload = gmail.decrypt_token_payload(account.token_encriptado)
        
        # Get recipients
        to_email = msg.remitente_email
        if not to_email:
            # try to parse from remitente if remitente_email is empty for some reason
            import re
            m = re.search(r'<([^>]+)>', msg.remitente or '')
            if m:
                to_email = m.group(1)
            else:
                to_email = msg.remitente
                
        subject = msg.asunto if (msg.asunto and msg.asunto.lower().startswith('re:')) else f"Re: {msg.asunto}"
        
        # Obtenemos los headers del mensaje original si están disponibles, para el threading. En este caso enviaremos el message-id de Gmail como Referencia/In-Reply-To si es necesario.
        # Ya que fetch_message no guarda todos los headers, lo asociamos por Asunto y le pasamos los parametros de threading si los tuvieramos.
        
        gmail.send_email(
            token_payload=token_payload,
            to=to_email,
            subject=subject,
            body=reply_body
        )
        
        msg.estado = 'respondido'
        msg.respondido_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'success': True, 'message': msg.to_dict()})

    except Exception as e:
        print(f"Error sending email reply: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@correo_inteligente_bp.route('/api/analytics', methods=['GET'])
def analytics_api():
    denial = _require_session_and_permission()
    if denial:
        return jsonify({'error': 'unauthorized'}), 401

    user = _current_user()
    if not user:
        return jsonify({'error': 'unauthorized'}), 401

    account = CorreoInstitucionalCuenta.query.filter_by(usuario_id=user.id).first()
    if not account:
        return jsonify({'total': 0, 'categoria': {}, 'estado': {}, 'semaforo': {}})

    base = CorreoInstitucionalMensaje.query.filter_by(cuenta_id=account.id)

    categoria = db.session.query(
        CorreoInstitucionalMensaje.categoria,
        func.count(CorreoInstitucionalMensaje.id)
    ).filter(CorreoInstitucionalMensaje.cuenta_id == account.id).group_by(CorreoInstitucionalMensaje.categoria).all()

    estado = db.session.query(
        CorreoInstitucionalMensaje.estado,
        func.count(CorreoInstitucionalMensaje.id)
    ).filter(CorreoInstitucionalMensaje.cuenta_id == account.id).group_by(CorreoInstitucionalMensaje.estado).all()

    semaforo = db.session.query(
        CorreoInstitucionalMensaje.semaforo,
        func.count(CorreoInstitucionalMensaje.id)
    ).filter(CorreoInstitucionalMensaje.cuenta_id == account.id).group_by(CorreoInstitucionalMensaje.semaforo).all()

    avg_days = db.session.query(func.avg(CorreoInstitucionalMensaje.dias_transcurridos)).filter(
        CorreoInstitucionalMensaje.cuenta_id == account.id,
        CorreoInstitucionalMensaje.requiere_respuesta.is_(True)
    ).scalar() or 0

    return jsonify({
        'total': base.count(),
        'requieren_respuesta': base.filter_by(requiere_respuesta=True).count(),
        'criticos': base.filter_by(semaforo='rojo').count(),
        'promedio_dias': round(float(avg_days), 2),
        'categoria': {k or 'otro': v for k, v in categoria},
        'estado': {k or 'nuevo': v for k, v in estado},
        'semaforo': {k or 'gris': v for k, v in semaforo},
        'tendencia_7d': _build_trend_last_7_days(account.id),
    })


def _build_trend_last_7_days(account_id):
    today = datetime.utcnow().date()
    labels = [(today - timedelta(days=offset)) for offset in range(6, -1, -1)]
    counters = {d.isoformat(): 0 for d in labels}

    since_dt = datetime.combine(labels[0], datetime.min.time())
    rows = CorreoInstitucionalMensaje.query.filter(
        CorreoInstitucionalMensaje.cuenta_id == account_id,
        CorreoInstitucionalMensaje.fecha_recepcion >= since_dt,
    ).all()

    for row in rows:
        key = row.fecha_recepcion.date().isoformat()
        if key in counters:
            counters[key] += 1

    return counters
