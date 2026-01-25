"""
API de Contratos - Integración con SECOP I y SECOP II
Permite importar, sincronizar y gestionar contratos desde las plataformas oficiales
"""
from flask import Blueprint, request, jsonify, send_file
from datetime import datetime, timedelta
import json
import re
import requests
from bs4 import BeautifulSoup
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors

# Lazy imports para evitar dependencias circulares
def get_db():
    from app import db
    return db

def get_models():
    from app.models.contrato import Contrato
    return Contrato

contratos_api = Blueprint('contratos_api', __name__, url_prefix='/api/contratos')

# ============================================================================
# FUNCIONES DE INTEGRACIÓN CON SECOP
# ============================================================================

def detectar_plataforma_y_extraer_id(url_o_id):
    """
    Detecta si es SECOP I o SECOP II y extrae el ID del proceso
    
    URLs soportadas:
    - SECOP I: https://www.contratos.gov.co/consultas/detalleProceso.do?numConstancia=20-12-10668888
    - SECOP II: https://community.secop.gov.co/Public/Tendering/OpportunityDetail/Index?noticeUID=CO1.NTC.1234567
    - Solo ID: 20-12-10668888 o CO1.NTC.1234567
    """
    url = url_o_id.strip()
    
    # Detectar SECOP I
    if 'contratos.gov.co' in url or re.match(r'^\d{2}-\d{2}-\d+', url):
        if 'numConstancia=' in url:
            match = re.search(r'numConstancia=([^&]+)', url)
            proceso_id = match.group(1) if match else None
        else:
            proceso_id = url if re.match(r'^\d{2}-\d{2}-\d+', url) else None
        
        return 'SECOP_I', proceso_id
    
    # Detectar SECOP II
    elif 'secop.gov.co' in url or 'colombiacompra.gov.co' in url or url.startswith('CO1.'):
        if 'noticeUID=' in url:
            match = re.search(r'noticeUID=([^&]+)', url)
            proceso_id = match.group(1) if match else None
        else:
            proceso_id = url if url.startswith('CO1.') else None
        
        return 'SECOP_II', proceso_id
    
    return None, None


def importar_desde_secop_i(proceso_id):
    """
    Importa datos de un proceso desde SECOP I mediante web scraping
    Estructura: usa clases CSS tablaslistEven/tablaslistOdd en lugar de <th>
    """
    try:
        url = f'https://www.contratos.gov.co/consultas/detalleProceso.do?numConstancia={proceso_id}'
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        datos = {
            'numero_proceso': proceso_id,
            'url_secop': url,
            'plataforma': 'SECOP_I'
        }
        
        # Función auxiliar para extraer valor de tabla label-valor
        def extraer_campo(label_texto):
            # Buscar td que contenga el label
            label_td = soup.find('td', class_=['tablaslistEven', 'tablaslistOdd'], string=re.compile(label_texto, re.I))
            if label_td:
                # El valor está en el siguiente td
                valor_td = label_td.find_next_sibling('td')
                if valor_td:
                    # Verificar si hay textarea
                    textarea = valor_td.find('textarea')
                    if textarea:
                        return textarea.get_text(strip=True)
                    return valor_td.get_text(strip=True)
            return None
        
        # Extraer datos usando el nuevo método
        
        # Objeto del contrato
        objeto = extraer_campo('Objeto a Contratar')
        if objeto:
            datos['objeto_contrato'] = objeto
        
        # Descripción del proceso
        descripcion = extraer_campo('Descripción del Proceso')
        if descripcion:
            datos['descripcion'] = descripcion
        
        # Tipo de Proceso
        tipo_proceso = extraer_campo('Tipo de Proceso')
        if tipo_proceso:
            datos['tipo_proceso'] = tipo_proceso
        
        # Estado
        estado = extraer_campo('Estado del Proceso')
        if estado:
            datos['estado'] = estado
        
        # Modalidad
        modalidad = extraer_campo('Modalidad de Contratación')
        if modalidad:
            datos['modalidad'] = modalidad
        
        # Entidad - buscar en el encabezado
        entidad_elem = soup.find('p', class_='subtitulos')
        if entidad_elem:
            entidad_texto = entidad_elem.get_text(strip=True)
            # Formato: "DEPARTAMENTO - ENTIDAD"
            if ' - ' in entidad_texto:
                partes = entidad_texto.split(' - ')
                if len(partes) >= 2:
                    datos['entidad_departamento'] = partes[0].strip()
                    datos['entidad_nombre'] = partes[1].strip()
            else:
                datos['entidad_nombre'] = entidad_texto
        
        # Cuantía/Presupuesto
        cuantia = extraer_campo('Cuantía a Contratar')
        if not cuantia:
            cuantia = extraer_campo('Presupuesto Oficial')
        if not cuantia:
            cuantia = extraer_campo('Valor del Contrato')
        if not cuantia:
            cuantia = extraer_campo('Cuantía')
        if cuantia:
            # Extraer número (ej: $1.234.567 -> 1234567)
            cuantia_num = re.sub(r'[^\d]', '', cuantia)
            if cuantia_num:
                datos['cuantia'] = float(cuantia_num)
        
        # Fechas
        fecha_pub = extraer_campo('Fecha de Publicación')
        if fecha_pub:
            try:
                # Intentar varios formatos de fecha
                for fmt in ['%d/%m/%Y %H:%M', '%d/%m/%Y', '%Y-%m-%d']:
                    try:
                        datos['fecha_publicacion'] = datetime.strptime(fecha_pub.strip(), fmt)
                        break
                    except:
                        continue
            except:
                pass
        
        fecha_cierre = extraer_campo('Fecha de Cierre')
        if fecha_cierre:
            try:
                for fmt in ['%d/%m/%Y %H:%M', '%d/%m/%Y', '%Y-%m-%d']:
                    try:
                        datos['fecha_cierre'] = datetime.strptime(fecha_cierre.strip(), fmt)
                        break
                    except:
                        continue
            except:
                pass
        
        # Plazo
        plazo = extraer_campo('Plazo de Ejecución')
        if not plazo:
            plazo = extraer_campo('Plazo')
        if plazo:
            # Buscar número de días
            plazo_dias = re.search(r'(\d+)\s*día', plazo, re.I)
            if plazo_dias:
                datos['plazo_dias'] = int(plazo_dias.group(1))
            # Buscar número de meses
            plazo_meses = re.search(r'(\d+)\s*mes', plazo, re.I)
            if plazo_meses:
                datos['plazo_meses'] = int(plazo_meses.group(1))
        
        # Documentos - buscar tablas de documentos
        documentos = []
        # Típicamente hay una tabla con id que contiene "documento"
        docs_tables = soup.find_all('table')
        for table in docs_tables:
            rows = table.find_all('tr')
            for row in rows:
                link = row.find('a', href=True)
                if link and 'documento' in link.get('href', '').lower():
                    documentos.append({
                        'nombre': link.get_text(strip=True),
                        'url': link['href']
                    })
        
        if documentos:
            datos['documentos_json'] = json.dumps(documentos)
            datos['tiene_pliegos'] = any('pliego' in d['nombre'].lower() for d in documentos)
            datos['tiene_estudios_previos'] = any('estudio' in d['nombre'].lower() for d in documentos)
        
        # Guardar snapshot HTML parcial como backup
        datos['datos_completos_json'] = json.dumps({
            'html_snapshot': str(soup.find('div', id='contenidoCentral'))[:10000] if soup.find('div', id='contenidoCentral') else '',
            'fecha_extraccion': datetime.utcnow().isoformat()
        })
        
        datos['sincronizacion_exitosa'] = True
        return datos
    
    except Exception as e:
        print(f'Error importando SECOP I {proceso_id}: {e}')
        import traceback
        traceback.print_exc()
        return {
            'numero_proceso': proceso_id,
            'plataforma': 'SECOP_I',
            'sincronizacion_exitosa': False,
            'mensaje_error': str(e)
        }


def importar_desde_secop_ii(proceso_id):
    """
    Importa datos de un proceso desde SECOP II mediante API REST de Datos Abiertos
    """
    try:
        # API de Datos Abiertos Colombia - SECOP II
        # Dataset: https://www.datos.gov.co/resource/jbjy-vk9h.json
        api_url = 'https://www.datos.gov.co/resource/jbjy-vk9h.json'
        
        params = {
            '$where': f"reference_number='{proceso_id}' OR id_contrato='{proceso_id}'",
            '$limit': 1
        }
        
        response = requests.get(api_url, params=params, timeout=30)
        response.raise_for_status()
        
        resultados = response.json()
        
        if not resultados:
            # Intentar búsqueda alternativa
            params = {'$q': proceso_id, '$limit': 5}
            response = requests.get(api_url, params=params, timeout=30)
            resultados = response.json()
        
        if not resultados:
            raise Exception(f'No se encontró el proceso {proceso_id} en SECOP II')
        
        # Tomar el primer resultado (más relevante)
        dato_secop = resultados[0]
        
        datos = {
            'numero_proceso': dato_secop.get('reference_number') or proceso_id,
            'url_secop': f'https://community.secop.gov.co/Public/Tendering/OpportunityDetail/Index?noticeUID={proceso_id}',
            'plataforma': 'SECOP_II'
        }
        
        # Mapeo de campos de SECOP II
        datos['objeto_contrato'] = dato_secop.get('descripcion_del_proceo') or dato_secop.get('nombre_del_procedimiento')
        datos['entidad_nombre'] = dato_secop.get('nombre_entidad')
        datos['entidad_nit'] = dato_secop.get('nit_entidad')
        datos['entidad_departamento'] = dato_secop.get('departamento')
        datos['entidad_municipio'] = dato_secop.get('ciudad') or dato_secop.get('municipio')
        
        datos['tipo_proceso'] = dato_secop.get('tipo_de_contrato')
        datos['modalidad'] = dato_secop.get('modalidad_de_contratacion')
        datos['estado'] = dato_secop.get('estado_del_procedimiento') or dato_secop.get('estado_proceso')
        
        # Cuantía
        if 'precio_base' in dato_secop:
            try:
                datos['cuantia'] = float(dato_secop['precio_base'])
            except:
                pass
        
        if 'valor_del_contrato' in dato_secop:
            try:
                datos['valor_adjudicado'] = float(dato_secop['valor_del_contrato'])
            except:
                pass
        
        # Fechas
        if 'fecha_de_publicacion_del' in dato_secop:
            try:
                datos['fecha_publicacion'] = datetime.fromisoformat(dato_secop['fecha_de_publicacion_del'].replace('Z', '+00:00'))
            except:
                pass
        
        if 'fecha_de_cierre' in dato_secop:
            try:
                datos['fecha_cierre'] = datetime.fromisoformat(dato_secop['fecha_de_cierre'].replace('Z', '+00:00'))
            except:
                pass
        
        if 'fecha_de_firma_del_contrato' in dato_secop:
            try:
                datos['fecha_firma_contrato'] = datetime.fromisoformat(dato_secop['fecha_de_firma_del_contrato'].replace('Z', '+00:00'))
            except:
                pass
        
        # Contratista
        datos['contratista_nombre'] = dato_secop.get('proveedor_adjudicado') or dato_secop.get('nombre_proveedor')
        datos['contratista_nit'] = dato_secop.get('nit_del_proveedor_adjudicado')
        
        # Plazo
        if 'plazo_de_ejec_del_contrato' in dato_secop:
            try:
                plazo = int(dato_secop['plazo_de_ejec_del_contrato'])
                datos['plazo_dias'] = plazo
            except:
                pass
        
        # Guardar datos completos como JSON
        datos['datos_completos_json'] = json.dumps(dato_secop)
        datos['sincronizacion_exitosa'] = True
        
        return datos
    
    except Exception as e:
        print(f'Error importando SECOP II {proceso_id}: {e}')
        return {
            'numero_proceso': proceso_id,
            'plataforma': 'SECOP_II',
            'sincronizacion_exitosa': False,
            'mensaje_error': str(e)
        }


# ============================================================================
# CRUD - Contratos
# ============================================================================

@contratos_api.route('/importar', methods=['POST'])
def importar_contrato():
    """
    Importa un contrato desde SECOP I o SECOP II mediante URL o ID
    
    Body:
    {
        "url": "https://www.contratos.gov.co/consultas/detalleProceso.do?numConstancia=20-12-10668888",
        "usuario": "admin",
        "observaciones": "Contrato de prueba"
    }
    """
    data = request.get_json()
    url_o_id = data.get('url') or data.get('id')
    
    if not url_o_id:
        return jsonify({'success': False, 'error': 'Debe proporcionar una URL o ID del proceso'}), 400
    
    db = get_db()
    Contrato = get_models()
    
    try:
        # Detectar plataforma y extraer ID
        plataforma, proceso_id = detectar_plataforma_y_extraer_id(url_o_id)
        
        if not plataforma or not proceso_id:
            return jsonify({
                'success': False,
                'error': 'URL no reconocida. Use enlaces de SECOP I o SECOP II'
            }), 400
        
        # Verificar si ya existe
        contrato_existente = Contrato.query.filter_by(numero_proceso=proceso_id).first()
        if contrato_existente:
            return jsonify({
                'success': False,
                'error': f'El contrato {proceso_id} ya está registrado',
                'contrato_id': contrato_existente.id
            }), 409
        
        # Importar según plataforma
        if plataforma == 'SECOP_I':
            datos_importados = importar_desde_secop_i(proceso_id)
        else:
            datos_importados = importar_desde_secop_ii(proceso_id)
        
        if not datos_importados.get('sincronizacion_exitosa'):
            return jsonify({
                'success': False,
                'error': datos_importados.get('mensaje_error', 'Error al importar desde SECOP')
            }), 500
        
        # Crear contrato
        contrato = Contrato()
        for campo, valor in datos_importados.items():
            if hasattr(contrato, campo):
                setattr(contrato, campo, valor)
        
        # Agregar datos adicionales
        contrato.usuario_importacion = data.get('usuario', 'Sistema')
        contrato.observaciones = data.get('observaciones', '')
        contrato.responsable_seguimiento = data.get('responsable', '')
        
        print(f'DEBUG: Iniciando guardado de contrato {contrato.numero_proceso}')
        db.session.add(contrato)
        print(f'DEBUG: Contrato agregado a la sesión')
        db.session.flush()  # Genera el ID antes de serializar
        print(f'DEBUG: Flush ejecutado. ID asignado: {contrato.id}')
        contrato_dict = contrato.to_dict()
        print(f'DEBUG: Contrato serializado a dict')
        db.session.commit()
        print(f'DEBUG: Commit ejecutado')
        
        # Verificar que el registro realmente se guardó
        verificacion = Contrato.query.filter_by(numero_proceso=contrato.numero_proceso).first()
        if verificacion:
            print(f'DEBUG: Contrato verificado en BD: {verificacion.id}')
        else:
            print('DEBUG: ERROR - Contrato NO encontrado en BD despues del commit')
        
        return jsonify({
            'success': True,
            'mensaje': f'Contrato importado exitosamente desde {plataforma}',
            'contrato': contrato_dict
        }), 201
    
    except Exception as e:
        db.session.rollback()
        import traceback
        print(f'Error en importar_contrato: {e}')
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@contratos_api.route('', methods=['GET'])
def listar_contratos():
    """Lista contratos con filtros opcionales"""
    try:
        from app import db
        Contrato = get_models()
        
        # Filtros
        plataforma = request.args.get('plataforma')
        estado = request.args.get('estado')
        entidad = request.args.get('entidad')
        search = request.args.get('search')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        # Evita paginaciones enormes
        per_page = max(1, min(per_page, 100))
        
        query = Contrato.query
        
        if plataforma:
            query = query.filter_by(plataforma=plataforma)
        if estado:
            query = query.filter_by(estado=estado)
        if entidad:
            query = query.filter(Contrato.entidad_nombre.ilike(f'%{entidad}%'))
        if search:
            query = query.filter(
                db.or_(
                    Contrato.numero_proceso.ilike(f'%{search}%'),
                    Contrato.objeto_contrato.ilike(f'%{search}%'),
                    Contrato.entidad_nombre.ilike(f'%{search}%'),
                    Contrato.contratista_nombre.ilike(f'%{search}%')
                )
            )
        
        query = query.order_by(Contrato.fecha_publicacion.desc())
        pagination = db.paginate(query, page=page, per_page=per_page, error_out=False)
        
        # Serializar DENTRO de la sesión activa para evitar detached objects
        contratos_lista = []
        for c in pagination.items:
            try:
                contratos_lista.append(c.to_dict())
            except Exception:
                continue
        
        return jsonify({
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'contratos': contratos_lista
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'contratos': []}), 500


@contratos_api.route('/<int:contrato_id>', methods=['GET'])
def obtener_contrato(contrato_id):
    """Obtiene un contrato completo por ID"""
    try:
        Contrato = get_models()
        contrato = Contrato.query.get_or_404(contrato_id)
        
        resultado = contrato.to_dict()
        resultado.update(contrato.parse_json_fields())
        
        return jsonify(resultado)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@contratos_api.route('/<int:contrato_id>/sincronizar', methods=['POST'])
def sincronizar_contrato(contrato_id):
    """Re-sincroniza un contrato con SECOP"""
    try:
        Contrato = get_models()
        db = get_db()
        
        contrato = Contrato.query.get_or_404(contrato_id)
        
        # Re-importar datos
        if contrato.plataforma == 'SECOP_I':
            datos_nuevos = importar_desde_secop_i(contrato.numero_proceso)
        else:
            datos_nuevos = importar_desde_secop_ii(contrato.numero_proceso)
        
        if not datos_nuevos.get('sincronizacion_exitosa'):
            return jsonify({
                'success': False,
                'error': datos_nuevos.get('mensaje_error')
            }), 500
        
        # Actualizar campos
        for campo, valor in datos_nuevos.items():
            if hasattr(contrato, campo) and campo != 'id':
                setattr(contrato, campo, valor)
        
        contrato.ultima_sincronizacion = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'mensaje': 'Contrato sincronizado exitosamente',
            'contrato': contrato.to_dict()
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@contratos_api.route('/estadisticas', methods=['GET'])
def obtener_estadisticas():
    """Obtiene estadísticas generales de contratos"""
    try:
        Contrato = get_models()
        db = get_db()
        
        total_contratos = Contrato.query.count()

        plataformas_raw = db.session.query(
            Contrato.plataforma, db.func.count(Contrato.id)
        ).group_by(Contrato.plataforma).all()
        por_plataforma = {p or 'Desconocida': c for p, c in plataformas_raw}

        estados_raw = db.session.query(
            Contrato.estado, db.func.count(Contrato.id)
        ).group_by(Contrato.estado).all()
        estados = {e or 'Sin estado': c for e, c in estados_raw}

        cuantia_total = db.session.query(db.func.coalesce(db.func.sum(Contrato.cuantia), 0)).scalar() or 0
        
        return jsonify({
            'total_contratos': total_contratos,
            'por_plataforma': por_plataforma,
            'por_estado': estados,
            'cuantia_total': cuantia_total
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        # Retornar estructura válida incluso en error
        return jsonify({
            'total_contratos': 0,
            'por_plataforma': {'SECOP_I': 0, 'SECOP_II': 0},
            'por_estado': {},
            'cuantia_total': 0,
            'error': str(e)
        }), 500


@contratos_api.route('/<int:contrato_id>', methods=['DELETE'])
def eliminar_contrato(contrato_id):
    """Elimina un contrato"""
    try:
        Contrato = get_models()
        db = get_db()
        
        contrato = Contrato.query.get_or_404(contrato_id)
        db.session.delete(contrato)
        db.session.commit()
        
        return jsonify({'success': True, 'mensaje': 'Contrato eliminado'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
