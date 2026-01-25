import os
import datetime
import csv
import io
import base64
import copy
from flask import Blueprint, render_template, request, flash, redirect, url_for, session, current_app, jsonify, send_file
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.utils import ImageReader
from PyPDF2 import PdfReader, PdfWriter
# import openai # Optional, only if installed

ia_bp = Blueprint('ia', __name__)

@ia_bp.route('/ia', methods=['GET'], endpoint='index')
def index():
    """Página principal del módulo IA - Rediseñada iOS 26"""
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    return render_template('ia.html')

# ============================================
# MÓDULOS PRINCIPALES (Mantenidos)
# ============================================

@ia_bp.route('/ia/internal', methods=['GET'], endpoint='internal')
def internal():
    """Chat Interno - Comunicación entre funcionarios"""
    if 'user' not in session: 
        return redirect(url_for('auth.login'))
    return render_template('ia_internal.html')

# ============================================
# CHAT APIs - iMessage Style
# ============================================

@ia_bp.route('/api/chat/users', methods=['GET'])
def get_chat_users():
    """Obtener lista de usuarios para el chat"""
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        users_path = os.path.join(current_app.config['DATA_DIR'], 'usuarios.csv')
        users = []
        
        with open(users_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                users.append({
                    'usuario': row.get('usuario', ''),
                    'rol': row.get('rol', 'Usuario')
                })
        
        return jsonify(users)
    except Exception as e:
        print(f"Error loading users: {e}")
        return jsonify([])

@ia_bp.route('/api/chat/messages', methods=['GET'])
def get_chat_messages():
    """Obtener mensajes entre dos usuarios"""
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    current_user = session['user']
    contact_user = request.args.get('user', '')
    
    if not contact_user:
        return jsonify({'messages': []})
    
    try:
        messages_path = os.path.join(current_app.config['DATA_DIR'], 'mensajes.csv')
        messages = []
        
        # Ensure file exists with headers
        if not os.path.exists(messages_path):
            with open(messages_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['timestamp', 'sender', 'recipient', 'message'])
                writer.writeheader()
        
        with open(messages_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                sender = row.get('sender', '')
                recipient = row.get('recipient', '')
                
                # Get messages between current user and contact
                if (sender == current_user and recipient == contact_user) or \
                   (sender == contact_user and recipient == current_user):
                    messages.append({
                        'from': sender,
                        'to': recipient,
                        'message': row.get('message', ''),
                        'timestamp': row.get('timestamp', '')
                    })
        
        return jsonify({'messages': messages})
    except Exception as e:
        print(f"Error loading messages: {e}")
        return jsonify({'messages': []})

@ia_bp.route('/api/chat/last', methods=['GET'])
def get_last_incoming_message():
    """Devuelve el último mensaje recibido por el usuario actual.
    Útil para notificaciones de 'nuevo mensaje'.
    """
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    current_user = session['user']
    try:
        messages_path = os.path.join(current_app.config['DATA_DIR'], 'mensajes.csv')
        last_msg = None
        
        if not os.path.exists(messages_path):
            return jsonify({'message': None})
        
        with open(messages_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                sender = row.get('sender', '')
                recipient = row.get('recipient', '')
                if recipient == current_user and sender != current_user:
                    ts = row.get('timestamp') or ''
                    try:
                        dt = datetime.datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')
                    except Exception:
                        dt = None
                    candidate = {
                        'from': sender,
                        'to': recipient,
                        'message': row.get('message', ''),
                        'timestamp': ts,
                        'dt': dt
                    }
                    if last_msg is None:
                        last_msg = candidate
                    else:
                        # Compare datetimes; if missing, keep existing
                        if candidate['dt'] and (not last_msg['dt'] or candidate['dt'] > last_msg['dt']):
                            last_msg = candidate
        
        if last_msg:
            # Remove dt from response
            last_msg.pop('dt', None)
            return jsonify({'message': last_msg})
        return jsonify({'message': None})
    except Exception as e:
        print(f"Error reading last message: {e}")
        return jsonify({'message': None})

@ia_bp.route('/api/chat/send', methods=['POST'])
def send_chat_message():
    """Enviar un mensaje en el chat"""
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        current_user = session['user']
        recipient = data.get('to', '')
        message = data.get('message', '')
        
        if not recipient or not message:
            return jsonify({'error': 'Missing data'}), 400
        
        messages_path = os.path.join(current_app.config['DATA_DIR'], 'mensajes.csv')
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Append message to CSV
        with open(messages_path, 'a', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['timestamp', 'sender', 'recipient', 'message'])
            writer.writerow({
                'timestamp': timestamp,
                'sender': current_user,
                'recipient': recipient,
                'message': message
            })
        
        return jsonify({
            'status': 'success',
            'message': 'Message sent',
            'timestamp': timestamp
        })
    except Exception as e:
        print(f"Error sending message: {e}")
        return jsonify({'error': 'Failed to send message'}), 500

@ia_bp.route('/api/chat/delete', methods=['POST'])
def delete_chat_messages():
    """Eliminar mensajes del chat (solo admin)"""
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Verificar que el usuario sea admin
    role = (session.get('role') or session.get('user_role') or '').lower()
    if role not in ['admin', 'administrador', 'superadmin']:
        return jsonify({'error': 'No autorizado. Solo administradores pueden eliminar mensajes.'}), 403
    
    try:
        data = request.get_json()
        delete_type = data.get('type', 'conversation')  # 'conversation' o 'all'
        user1 = data.get('user1', '')
        user2 = data.get('user2', '')
        
        messages_path = os.path.join(current_app.config['DATA_DIR'], 'mensajes.csv')
        
        if not os.path.exists(messages_path):
            return jsonify({'error': 'No existe historial de mensajes'}), 404
        
        messages = []
        
        # Leer todos los mensajes
        with open(messages_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            
            for row in reader:
                if delete_type == 'all':
                    # No agregar ningún mensaje (borrar todo)
                    continue
                elif delete_type == 'conversation':
                    # Filtrar conversación entre user1 y user2
                    sender = row.get('sender', '')
                    recipient = row.get('recipient', '')
                    
                    # Mantener si NO es parte de la conversación a eliminar
                    is_conversation = (
                        (sender == user1 and recipient == user2) or
                        (sender == user2 and recipient == user1)
                    )
                    if not is_conversation:
                        messages.append(row)
                else:
                    messages.append(row)
        
        # Reescribir el archivo
        with open(messages_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(messages)
        
        deleted_count = 0 if delete_type != 'all' else 'all'
        return jsonify({
            'success': True,
            'message': f'Mensajes eliminados exitosamente',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        print(f'Error al eliminar mensajes: {e}')
        return jsonify({'error': str(e)}), 500

@ia_bp.route('/api/chat/conversations', methods=['GET'])
def get_chat_conversations():
    """Obtener lista de conversaciones para administración (solo admin)"""
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Verificar que el usuario sea admin
    role = (session.get('role') or session.get('user_role') or '').lower()
    if role not in ['admin', 'administrador', 'superadmin']:
        return jsonify({'error': 'No autorizado'}), 403
    
    try:
        messages_path = os.path.join(current_app.config['DATA_DIR'], 'mensajes.csv')
        
        if not os.path.exists(messages_path):
            return jsonify([])
        
        conversations = {}
        
        with open(messages_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                sender = row.get('sender', '')
                recipient = row.get('recipient', '')
                timestamp = row.get('timestamp', '')
                
                # Crear clave única para la conversación (orden alfabético)
                users = tuple(sorted([sender, recipient]))
                
                if users not in conversations:
                    conversations[users] = {
                        'users': users,
                        'last_message': timestamp,
                        'message_count': 0
                    }
                
                conversations[users]['message_count'] += 1
                conversations[users]['last_message'] = timestamp
        
        # Convertir a lista
        result = [
            {
                'user1': conv['users'][0],
                'user2': conv['users'][1],
                'message_count': conv['message_count'],
                'last_message': conv['last_message']
            }
            for conv in conversations.values()
        ]
        
        # Ordenar por última actividad
        result.sort(key=lambda x: x['last_message'], reverse=True)
        
        return jsonify(result)
        
    except Exception as e:
        print(f'Error al obtener conversaciones: {e}')
        return jsonify({'error': str(e)}), 500

# ============================================
# OTROS MÓDULOS
# ============================================

def generate_oficio_pdf(data: dict) -> io.BytesIO:
    """Genera un Oficio usando el FORMATO.pdf como base con formato profesional mejorado"""
    
    # Rol y secretaría en sesión
    role_session = (session.get('role') or session.get('user_role') or '').lower()
    secretaria_session = session.get('secretaria', '')

    # Ruta del formato oficial
    formato_path = os.path.join(current_app.config['DATA_DIR'], 'FORMATO.pdf')
    
    # Crear canvas para el overlay
    overlay_buffer = io.BytesIO()
    c = canvas.Canvas(overlay_buffer, pagesize=letter)
    w, h = letter
    margin = 85  # Márgenes mejorados para mejor distribución
    header_margin = 180  # Margen superior seguro para encabezado
    footer_margin = 180  # Margen inferior seguro para pie de página
    y_position = h - header_margin
    
    # ============================================
    # ESTILOS PROFESIONALES MEJORADOS
    # ============================================
    styles = getSampleStyleSheet()
    
    # Estilo para títulos (Arial)
    style_title = ParagraphStyle(
        'title_arial',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',  # Helvetica aproxima Arial en PDF
        fontSize=12,
        leading=16,
        textColor=colors.black,
        alignment=4,  # Justified (Ajuste solicitado)
        spaceAfter=6,
        spaceBefore=4
    )
    
    # Estilo para cuerpo de texto (Arial)
    style_body = ParagraphStyle(
        'body_arial',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=18,  # Aproximado a 1.5 line spacing
        textColor=colors.black,
        alignment=4,  # Justified
        spaceAfter=12,
        firstLineIndent=36  # Sangría de primera línea
    )
    
    # Estilo específico para viñetas para forzar punto visible y alineado
    style_bullet = ParagraphStyle(
        'body_bullet',
        parent=style_body,
        leftIndent=24,
        bulletIndent=12,
        firstLineIndent=0,
        leading=16,
        bulletFontName='Helvetica-Bold',
        bulletFontSize=12,
        spaceAfter=10
    )
    
    style_label = ParagraphStyle(
        'label',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=colors.black,
        leading=16,
        spaceAfter=6
    )
    
    style_value = ParagraphStyle(
        'value',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        textColor=colors.black,
        leading=16,
        alignment=0,
        spaceAfter=4
    )
    
    # ============================================
    # INFORMACIÓN GENERAL DEL OFICIO
    # ============================================
    y_position -= 5  # Reducido de 10
    
    c.setFont('Helvetica-Bold', 12)
    c.setFillColor(colors.black)
    oficio_line = f"Oficio No.: {data.get('numero', '')}        Fecha: {data.get('fecha', '')}"
    c.drawString(margin, y_position, oficio_line)
    y_position -= 18  # Reducido de 24
    
    # Línea separadora
    c.setStrokeColor(colors.black)
    c.setLineWidth(1.0)
    c.line(margin, y_position, w - margin, y_position)
    y_position -= 20  # Reducido de 30
    
    # ============================================
    # DESTINATARIO
    # ============================================
    c.setFont('Helvetica', 12)
    c.setFillColor(colors.black)
    
    dest_lines = [
        f"{data.get('destinatario', 'Señor(a)')}",
        f"{data.get('cargo_dest', '')}",
        f"{data.get('entidad_dest', '')}",
        f"{data.get('ciudad_dest', '')}"
    ]
    
    for line in dest_lines:
        if line.strip():
            # Usar Paragraph para permitir wrapping si es muy largo
            p_dest = Paragraph(line, style_value)
            w_dest, h_dest = p_dest.wrap(w - 2*margin, 100)
            
            p_dest.drawOn(c, margin, y_position - h_dest)
            y_position -= (h_dest + 2) # Reducido de 4
    
    y_position -= 10 # Reducido de 15
    
    # ============================================
    # ASUNTO Y REFERENCIA
    # ============================================
    asunto_text = f"<b>ASUNTO:</b>&nbsp;&nbsp;{data.get('asunto', '')}"
    p_asunto = Paragraph(asunto_text, style_title)
    w_asunto, h_asunto = p_asunto.wrap(w - 2*margin, 100)
    p_asunto.drawOn(c, margin, y_position - h_asunto)
    y_position -= (h_asunto + 8) # Reducido de 16
    
    if data.get('referencia'):
        ref_text = f"<b>REFERENCIA:</b>&nbsp;&nbsp;{data.get('referencia', '')}"
        p_ref = Paragraph(ref_text, style_title)
        w_ref, h_ref = p_ref.wrap(w - 2*margin, 100)
        p_ref.drawOn(c, margin, y_position - h_ref)
        y_position -= (h_ref + 18)
    
    # ============================================
    # SALUDO
    # ============================================
    c.setFont('Helvetica', 12)
    c.drawString(margin, y_position, 'Respetado(a) Señor(a),')
    y_position -= 28
    
    # ============================================
    # CUERPO DEL OFICIO CON FORMATO PROFESIONAL
    # ============================================
    min_bottom_margin = footer_margin  # Margen inferior seguro para evitar sobreposición con pie de página
    cuerpo = data.get('cuerpo', '')
    if cuerpo:
        paragraphs = cuerpo.split('\n')
        for parrafo in paragraphs:
            if parrafo.strip():
                stripped = parrafo.strip()
                bullet_markers = ('•', '-', '*', '·')
                if stripped.startswith(bullet_markers):
                    texto_viñeta = stripped.lstrip('•*-·').strip()
                    p_body = Paragraph(texto_viñeta, style_bullet, bulletText='•')
                else:
                    p_body = Paragraph(stripped, style_body)
                w_body, h_body = p_body.wrap(w - 2*margin, 500)
                # Si no hay suficiente espacio, salto de página y reinicio y_position
                if y_position - h_body < min_bottom_margin:
                    c.showPage()
                    y_position = h - header_margin
                p_body.drawOn(c, margin, y_position - h_body)
                y_position -= (h_body + 8)
    
    # ============================================
    # IMÁGENES (si existen)
    # ============================================
    imagenes = data.get('imagenes', [])
    if imagenes:
        y_position -= 20
        for img_data in imagenes:
            try:
                # Decodificar base64
                if img_data.startswith('data:image'):
                    img_data = img_data.split(',')[1]
                img_bytes = base64.b64decode(img_data)
                img_buffer = io.BytesIO(img_bytes)
                img = ImageReader(img_buffer)
                # Calcular dimensiones (max 400px de ancho)
                img_width = 300
                img_height = 200
                # Verificar espacio
                if y_position - img_height < min_bottom_margin:
                    c.showPage()
                    y_position = h - header_margin
                # Centrar imagen
                x_offset = (w - img_width) / 2
                c.drawImage(img, x_offset, y_position - img_height, 
                           width=img_width, height=img_height, 
                           preserveAspectRatio=True, mask='auto')
                y_position -= (img_height + 15)
            except Exception as e:
                print(f"Error al insertar imagen: {e}")
                continue
    
    # ============================================
    # FIRMA
    # ============================================
    # Asegurar espacio para firma
    if y_position < footer_margin + 40: # Más espacio para la firma
        c.showPage()
        y_position = h - header_margin
    
    y_position -= 40
    
    c.setFont('Helvetica', 12)
    c.drawString(margin, y_position, 'Atentamente,')
    y_position -= 60
    
    # Línea de firma
    c.setLineWidth(1.5)
    c.setStrokeColor(colors.black)
    c.line(margin, y_position, margin + 280, y_position)
    y_position -= 18
    
    # Datos de firma
    c.setFont('Helvetica-Bold', 12)
    c.setFillColor(colors.black)
    c.drawString(margin, y_position, data.get('firmante_nombre', ''))
    y_position -= 16
    
    c.setFont('Helvetica', 12)
    c.setFillColor(colors.black)
    c.drawString(margin, y_position, data.get('firmante_cargo', ''))
    y_position -= 15
    
    c.setFont('Helvetica', 12)
    # Mostrar la entidad como Alcaldía por defecto (evita duplicado de dependencia)
    c.drawString(margin, y_position, data.get('entidad_firma', 'Alcaldia Municipal de Supata'))
    y_position -= 18
    
    c.setFont('Helvetica-Oblique', 12)
    c.setFillColor(colors.black)
    contacto = f"Tel: {data.get('telefono', '')} | {data.get('email', '')}"
    c.drawString(margin, y_position, contacto)
    
    # Anexos si existen
    if data.get('anexos'):
        y_position -= 30
        c.setFont('Helvetica-Bold', 12)
        c.setFillColor(colors.black)
        c.drawString(margin, y_position, 'ANEXOS:')
        y_position -= 16
        c.setFont('Helvetica', 12)
        c.setFillColor(colors.black)
        anexos_lines = data.get('anexos', '').split('\n')
        for anexo in anexos_lines:
            if anexo.strip():
                anexo_text = f"• {anexo.strip()}"
                p_anexo = Paragraph(anexo_text, style_value)
                w_anexo, h_anexo = p_anexo.wrap(w - 2*margin - 25, 200)
                # Verificar espacio antes de dibujar
                if y_position - h_anexo < min_bottom_margin:
                    c.showPage()
                    y_position = h - header_margin
                    c.setFont('Helvetica-Bold', 12)
                    c.drawString(margin, y_position, 'ANEXOS (Continuación):')
                    y_position -= 20
                p_anexo.drawOn(c, margin + 25, y_position - h_anexo)
                y_position -= (h_anexo + 6)
    
    c.showPage()
    c.save()
    overlay_buffer.seek(0)
    
    # ============================================
    # COMBINAR CON FORMATO OFICIAL
    # ============================================
    try:
        if os.path.exists(formato_path):
            template_pdf = PdfReader(formato_path)
            base_template_page = template_pdf.pages[0]
            overlay_pdf = PdfReader(overlay_buffer)
            output = PdfWriter()
            
            # Aplicar formato oficial a cada página del contenido sin reabrir archivo
            for page_num in range(len(overlay_pdf.pages)):
                template_page = copy.deepcopy(base_template_page)
                overlay_page = overlay_pdf.pages[page_num]
                template_page.merge_page(overlay_page)
                output.add_page(template_page)
            
            final_buffer = io.BytesIO()
            output.write(final_buffer)
            final_buffer.seek(0)
            return final_buffer
        else:
            overlay_buffer.seek(0)
            return overlay_buffer
    except Exception as e:
        print(f'Error al combinar con formato oficial: {e}')
        overlay_buffer.seek(0)
        return overlay_buffer

@ia_bp.route('/api/oficio/generar-pdf', methods=['POST'])
def generar_pdf_oficio():
    """Endpoint para generar PDF del oficio y guardar en historial"""
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()

        role_session = (session.get('role') or session.get('user_role') or '').lower()
        secretaria_session = session.get('secretaria', '').strip()
        mapa_secretarias = {
            'secretaría de gobierno': 'Secretaría General y de Gobierno',
            'secretaria de gobierno': 'Secretaría General y de Gobierno',
            'secretaría de planeación': 'Secretaría de Planeación y Obras Públicas',
            'secretaria de planeación': 'Secretaría de Planeación y Obras Públicas',
            'secretaría de planeacion': 'Secretaría de Planeación y Obras Públicas',
            'secretaria de planeacion': 'Secretaría de Planeación y Obras Públicas',
            'secretaría desarrollo rural': 'Secretaría de Desarrollo Rural Medio Ambiente y Competitividad',
            'secretaria desarrollo rural': 'Secretaría de Desarrollo Rural Medio Ambiente y Competitividad',
            'secretaría de hacienda': 'Secretaría de Hacienda y Gestión Financiera',
            'secretaria de hacienda': 'Secretaría de Hacienda y Gestión Financiera',
            'secretaría desarrollo social': 'Secretaría de Desarrollo Social y Comunitario',
            'secretaria desarrollo social': 'Secretaría de Desarrollo Social y Comunitario',
            'administrador': 'Despacho de la Alcaldía',
        }
        secretaria_larga = mapa_secretarias.get(secretaria_session.lower(), secretaria_session)

        # Si no es admin, forzar que la dependencia sea la de la secretaría del usuario
        if role_session not in ['admin', 'administrador', 'superadmin'] and secretaria_session:
            data['dependencia'] = secretaria_larga or secretaria_session
        # Normalizar dependencia si viene vacía
        if not data.get('dependencia'):
            data['dependencia'] = secretaria_larga or 'Despacho de la Alcaldía'
        
        # Generar PDF
        pdf_buffer = generate_oficio_pdf(data)
        
        # Guardar en historial
        historial_path = os.path.join(current_app.config['DATA_DIR'], 'historial_oficios.csv')
        
        # Crear archivo CSV si no existe
        if not os.path.exists(historial_path):
            with open(historial_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'numero', 'fecha', 'dependencia', 'destinatario', 
                    'cargo_dest', 'entidad_dest', 'ciudad_dest', 
                    'asunto', 'referencia', 'cuerpo', 
                    'firmante_nombre', 'firmante_cargo', 
                    'telefono', 'email', 'anexos', 
                    'usuario', 'fecha_creacion'
                ])
                writer.writeheader()
        
        # Agregar registro al historial
        with open(historial_path, 'a', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'numero', 'fecha', 'dependencia', 'destinatario', 
                'cargo_dest', 'entidad_dest', 'ciudad_dest', 
                'asunto', 'referencia', 'cuerpo', 
                'firmante_nombre', 'firmante_cargo', 
                'telefono', 'email', 'anexos', 
                'usuario', 'fecha_creacion'
            ])
            writer.writerow({
                'numero': data.get('numero', ''),
                'fecha': data.get('fecha', ''),
                'dependencia': data.get('dependencia', ''),
                'destinatario': data.get('destinatario', ''),
                'cargo_dest': data.get('cargo_dest', ''),
                'entidad_dest': data.get('entidad_dest', ''),
                'ciudad_dest': data.get('ciudad_dest', ''),
                'asunto': data.get('asunto', ''),
                'referencia': data.get('referencia', ''),
                'cuerpo': data.get('cuerpo', '')[:500],  # Limitar longitud
                'firmante_nombre': data.get('firmante_nombre', ''),
                'firmante_cargo': data.get('firmante_cargo', ''),
                'telefono': data.get('telefono', ''),
                'email': data.get('email', ''),
                'anexos': data.get('anexos', ''),
                'usuario': session.get('user', ''),
                'fecha_creacion': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        
        # Nombre del archivo
        numero_oficio = data.get('numero', '2026-001').replace('/', '-')
        filename = f'Oficio_{numero_oficio}.pdf'
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        print(f'Error: {e}')
        return jsonify({'error': str(e)}), 500

@ia_bp.route('/api/oficio/historial', methods=['GET'])
def obtener_historial_oficios():
    """Obtiene el historial de oficios generados"""
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        role_session = (session.get('role') or session.get('user_role') or '').lower()
        secretaria_session = session.get('secretaria', '').strip()
        
        # Mapeo a nombres largos para filtrado consistente
        mapa_secretarias = {
            'secretaría de gobierno': 'Secretaría General y de Gobierno',
            'secretaria de gobierno': 'Secretaría General y de Gobierno',
            'secretaría de planeación': 'Secretaría de Planeación y Obras Públicas',
            'secretaria de planeación': 'Secretaría de Planeación y Obras Públicas',
            'secretaría de planeacion': 'Secretaría de Planeación y Obras Públicas',
            'secretaria de planeacion': 'Secretaría de Planeación y Obras Públicas',
            'secretaría desarrollo rural': 'Secretaría de Desarrollo Rural Medio Ambiente y Competitividad',
            'secretaria desarrollo rural': 'Secretaría de Desarrollo Rural Medio Ambiente y Competitividad',
            'secretaría de hacienda': 'Secretaría de Hacienda y Gestión Financiera',
            'secretaria de hacienda': 'Secretaría de Hacienda y Gestión Financiera',
            'secretaría desarrollo social': 'Secretaría de Desarrollo Social y Comunitario',
            'secretaria desarrollo social': 'Secretaría de Desarrollo Social y Comunitario',
            'administrador': 'Despacho de la Alcaldía',
        }
        secretaria_larga = mapa_secretarias.get(secretaria_session.lower(), secretaria_session)
        
        historial_path = os.path.join(current_app.config['DATA_DIR'], 'historial_oficios.csv')
        
        if not os.path.exists(historial_path):
            return jsonify([])
        
        oficios = []
        with open(historial_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Si no es admin, mostrar solo los de su secretaría/dependencia (case-insensitive)
                if role_session not in ['admin', 'administrador', 'superadmin']:
                    dep_row = row.get('dependencia', '').strip()
                    # Comparación case-insensitive para evitar problemas de capitalización
                    if secretaria_larga and dep_row.lower() != secretaria_larga.lower():
                        continue
                oficios.append(row)
        
        # Ordenar por fecha de creación descendente
        oficios.reverse()
        
        return jsonify(oficios[:50])  # Últimos 50 oficios
    except Exception as e:
        print(f'Error: {e}')
        return jsonify([])

@ia_bp.route('/api/oficio/eliminar', methods=['POST'])
def eliminar_oficio():
    """Elimina un oficio del historial (solo admin)"""
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    # Verificar que el usuario sea admin
    role_session = (session.get('role') or session.get('user_role') or '').lower()
    if role_session not in ['admin', 'administrador', 'superadmin']:
        return jsonify({'error': 'No autorizado. Solo administradores pueden eliminar oficios.'}), 403

    try:
        data = request.get_json()
        numero_a_eliminar = data.get('numero', '')

        historial_path = os.path.join(current_app.config['DATA_DIR'], 'historial_oficios.csv')

        if not os.path.exists(historial_path):
            return jsonify({'error': 'No existe historial'}), 404

        # Leer todos los oficios
        oficios = []
        with open(historial_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            for row in reader:
                # Mantener todos EXCEPTO el que se va a eliminar
                if row.get('numero', '').strip() != numero_a_eliminar.strip():
                    oficios.append(row)

        # Reescribir el archivo sin el oficio eliminado
        with open(historial_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(oficios)

        return jsonify({'success': True, 'message': f'Oficio {numero_a_eliminar} eliminado exitosamente'})
    except Exception as e:
        print(f'Error al eliminar oficio: {e}')
        return jsonify({'error': str(e)}), 500

@ia_bp.route('/api/oficio/regenerar', methods=['POST'])
def regenerar_oficio():
    """Regenera un PDF de un oficio del historial"""
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        
        # Generar PDF con los datos del historial
        pdf_buffer = generate_oficio_pdf(data)
        
        # Nombre del archivo
        numero_oficio = data.get('numero', '2026-001').replace('/', '-')
        filename = f'Oficio_{numero_oficio}.pdf'
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        print(f'Error: {e}')
        return jsonify({'error': str(e)}), 500

@ia_bp.route('/ia/oficio', methods=['GET','POST'], endpoint='letter')
def oficio():
    """Redactar Oficios - Generación de documentos institucionales - iOS 26 Modern"""
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    
    return render_template('ia_letter_v2.html')

# ============================================
# NUEVOS MÓDULOS IA
# ============================================

@ia_bp.route('/ia/analysis', methods=['GET', 'POST'], endpoint='analysis')
def analysis():
    """Análisis Inteligente - Extracción de datos de documentos"""
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        # TODO: Implementar lógica de análisis de documentos
        flash('Análisis completado exitosamente', 'success')
        return render_template('ia_analysis.html', results={'status': 'completed'})
    
    return render_template('ia_analysis.html')

@ia_bp.route('/ia/normative', methods=['GET', 'POST'], endpoint='normative')
def normative():
    """Asistente Normativo - Búsqueda en leyes y normativas"""
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        query = request.form.get('query', '')
        # TODO: Implementar búsqueda en base de datos normativa
        results = []
        return render_template('ia_normative.html', query=query, results=results)
    
    return render_template('ia_normative.html')

@ia_bp.route('/ia/trends', methods=['GET'], endpoint='trends')
def trends():
    """Predicción de Tendencias - Análisis predictivo"""
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    
    # TODO: Implementar análisis de tendencias con datos históricos
    trend_data = {
        'solicitudes': {'trend': 'up', 'percentage': 15.3},
        'certificados': {'trend': 'down', 'percentage': -5.2},
        'participacion': {'trend': 'up', 'percentage': 23.7}
    }
    
    return render_template('ia_trends.html', trends=trend_data)

@ia_bp.route('/ia/reports', methods=['GET', 'POST'], endpoint='reports')
def reports():
    """Generador de Informes - Reportes ejecutivos en PDF"""
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        # TODO: Implementar generación de PDF con gráficos
        flash('Informe generado correctamente', 'success')
        return render_template('ia_reports.html', generated=True)
    
    return render_template('ia_reports.html')

# ============================================
# MÓDULOS LEGACY (Mantenidos para compatibilidad)
# ============================================

@ia_bp.route('/ia/chatbot', methods=['GET'], endpoint='chatbot')
def chatbot():
    """Chatbot Gobernanza (Legacy)"""
    if 'user' not in session: 
        return redirect(url_for('auth.login'))
    return render_template('ia_chatbot.html')

@ia_bp.route('/ia/chat', methods=['POST'], endpoint='chat')
def chat_api():
    """API de Chat (Legacy)"""
    return jsonify({'answer': "Funcionalidad de chat disponible en Chat Interno"})

@ia_bp.route('/ia/summary', methods=['GET'], endpoint='summary_page')
def summary_page():
    """Resumen de Documentos (Legacy)"""
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    return render_template('ia_summary.html')

@ia_bp.route('/ia/faq', methods=['GET'], endpoint='faq_page')
def faq_page():
    """FAQs Municipales (Legacy)"""
    if 'user' not in session: 
        return redirect(url_for('auth.login'))
    return render_template('ia_faq.html')

@ia_bp.route('/ia/map', methods=['GET'], endpoint='map_page')
def map_page():
    """Mapas Inteligentes (Legacy)"""
    if 'user' not in session: 
        return redirect(url_for('auth.login'))
    return render_template('ia_map.html')

@ia_bp.route('/ia/report', methods=['GET'], endpoint='report_page')
def report_page():
    """Reporte Ejecutivo (Legacy)"""
    if 'user' not in session: 
        return redirect(url_for('auth.login'))
    return render_template('ia_report.html')

@ia_bp.route('/docs', methods=['GET','POST'], endpoint='docs')
def docs():
    """Buscar en Documentos (Legacy)"""
    if 'user' not in session: 
        return redirect(url_for('auth.login'))
    return render_template('docs.html', docs_list=[], results=None)

@ia_bp.route('/docs/search', methods=['POST'], endpoint='docs_search')
def docs_search():
    """Búsqueda de documentos (Legacy)"""
    if 'user' not in session: 
        return redirect(url_for('auth.login'))
    return render_template('docs.html', docs_list=[], results=[])

@ia_bp.route('/insights', methods=['GET'], endpoint='insights')
def insights():
    """Dashboard de Insights (Legacy)"""
    if 'user' not in session: 
        return redirect(url_for('auth.login'))
    return render_template('insights.html')

