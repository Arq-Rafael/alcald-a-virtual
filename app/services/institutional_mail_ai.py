"""Capa de analitica y generacion de borradores para correo institucional."""

import json
import os
import re
import requests


CATEGORIES = [
    'derecho_peticion',
    'peticion',
    'queja',
    'reclamo',
    'solicitud',
    'requerimiento',
    'invitacion',
    'informativo',
    'interno',
    'urgente',
    'otro',
]


KEYWORD_HINTS = {
    'derecho_peticion': ['derecho de peticion', 'articulo 23', 'ley 1755', 'peticion formal'],
    'peticion': ['peticion', 'solicito', 'solicitamos'],
    'queja': ['queja', 'inconformidad', 'mal servicio'],
    'reclamo': ['reclamo', 'incumplimiento', 'exijo'],
    'solicitud': ['solicitud', 'tramite', 'requiero informacion'],
    'requerimiento': ['requerimiento', 'oficio', 'cumplimiento inmediato', 'subsanar'],
    'invitacion': ['invitacion', 'cordialmente invitado', 'evento'],
    'informativo': ['informamos', 'boletin', 'comunicado'],
    'interno': ['equipo', 'funcionarios', 'interno', 'memorando'],
    'urgente': ['urgente', 'inmediato', 'hoy', 'prioritario'],
}


class InstitutionalMailAIService:
    def __init__(self):
        self.openai_api_key = os.environ.get('OPENAI_API_KEY', '').strip()
        self.openai_model = os.environ.get('OPENAI_MODEL', 'gpt-4o-mini').strip()

    def analyze_email(self, asunto, cuerpo_texto, remitente=None):
        """Analiza un correo y retorna clasificacion institucional."""
        subject = (asunto or '').strip()
        body = (cuerpo_texto or '').strip()
        sender = (remitente or '').strip()

        llm_result = self._analyze_with_llm(subject, body, sender)
        if llm_result:
            return llm_result

        return self._heuristic_analysis(subject, body, sender)

    def generate_draft(self, email_context, tone='formal_institucional'):
        """Genera borrador de respuesta con tono configurable usando contexto rico."""
        return self._smart_local_draft(email_context, tone)

    def _heuristic_analysis(self, subject, body, sender):
        text = f"{subject}\n{body}".lower()

        best_category = 'otro'
        best_score = 0

        for category, hints in KEYWORD_HINTS.items():
            score = sum(1 for hint in hints if hint in text)
            if score > best_score:
                best_score = score
                best_category = category

        if best_score == 0 and 'supata-cundinamarca.gov.co' in sender.lower():
            best_category = 'interno'

        urgency = 'media'
        if any(tok in text for tok in ['urgente', 'inmediato', 'hoy', '48 horas']):
            urgency = 'alta'
        elif any(tok in text for tok in ['cuando sea posible', 'sin afan', 'informativo']):
            urgency = 'baja'

        requires_response = best_category not in ('informativo',)

        summary = self._compact_summary(subject, body)
        recommendation = self._build_recommendation(best_category, urgency, requires_response)

        return {
            'tipo_correo': best_category,
            'nivel_urgencia': urgency,
            'requiere_respuesta': requires_response,
            'tema_principal': subject[:180] if subject else 'Comunicacion institucional',
            'resumen_ejecutivo': summary,
            'recomendacion_gestion': recommendation,
        }

    def _build_recommendation(self, category, urgency, requires_response):
        if not requires_response:
            return 'Registrar como informativo y compartir con las areas interesadas.'

        if category == 'derecho_peticion':
            return 'Asignar a Secretaria competente y registrar fecha limite legal de respuesta.'
        if category in ('queja', 'reclamo'):
            return 'Abrir seguimiento con trazabilidad, responsable y fecha compromiso.'
        if urgency == 'alta':
            return 'Escalar a responsable institucional hoy y emitir acuse de recibido prioritario.'
        return 'Asignar responsable y elaborar respuesta institucional dentro del termino interno.'

    def _compact_summary(self, subject, body):
        cleaned = re.sub(r'\s+', ' ', body or '').strip()
        if not cleaned:
            cleaned = 'Mensaje sin cuerpo util para analisis detallado.'
        base = cleaned[:260]
        if subject:
            return f"{subject}. {base}"
        return base

    def _analyze_with_llm(self, subject, body, sender):
        if not self.openai_api_key:
            return None

        prompt = (
            "Clasifica el siguiente correo institucional en JSON valido con llaves exactas: "
            "tipo_correo, nivel_urgencia, requiere_respuesta, tema_principal, resumen_ejecutivo, recomendacion_gestion. "
            f"Categorias permitidas: {', '.join(CATEGORIES)}. "
            "nivel_urgencia: alta|media|baja. requiere_respuesta: true|false."
            f"\nRemitente: {sender}\nAsunto: {subject}\nContenido: {body[:6000]}"
        )

        payload = {
            'model': self.openai_model,
            'messages': [
                {'role': 'system', 'content': 'Eres un analista de correo institucional para entidad publica colombiana.'},
                {'role': 'user', 'content': prompt},
            ],
            'temperature': 0.2,
            'response_format': {'type': 'json_object'},
        }

        try:
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {self.openai_api_key}',
                    'Content-Type': 'application/json',
                },
                json=payload,
                timeout=20,
            )
            response.raise_for_status()
            data = response.json()
            content = data['choices'][0]['message']['content']
            parsed = json.loads(content)

            tipo = str(parsed.get('tipo_correo', 'otro')).lower().strip()
            if tipo not in CATEGORIES:
                tipo = 'otro'

            urg = str(parsed.get('nivel_urgencia', 'media')).lower().strip()
            if urg not in ('alta', 'media', 'baja'):
                urg = 'media'

            return {
                'tipo_correo': tipo,
                'nivel_urgencia': urg,
                'requiere_respuesta': bool(parsed.get('requiere_respuesta', True)),
                'tema_principal': str(parsed.get('tema_principal', 'Comunicacion institucional'))[:200],
                'resumen_ejecutivo': str(parsed.get('resumen_ejecutivo', ''))[:1200],
                'recomendacion_gestion': str(parsed.get('recomendacion_gestion', ''))[:1200],
            }
        except Exception as e:
            print(f"Error _analyze_with_llm: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"OpenAI Response: {e.response.text}")
            return None

    def _smart_local_draft(self, ctx, tone):
        """
        Genera borrador institucional siguiendo el estándar oficial de la
        Secretaría de Planeación y Obras Públicas de Supatá.
        """
        import re as _re
        from datetime import datetime as _dt

        # ── Datos básicos del contexto ──────────────────────────────────────────
        remitente_raw  = (ctx.get('remitente') or 'Ciudadano(a)').strip()
        remitente_mail = (ctx.get('remitente_email') or '').strip()
        asunto         = (ctx.get('asunto') or 'Comunicación institucional').strip()
        cuerpo         = (ctx.get('cuerpo_texto') or '').strip()
        categoria      = (ctx.get('categoria') or 'otro').lower()
        urgencia       = (ctx.get('urgencia') or 'media').lower()
        resumen        = (ctx.get('resumen_ejecutivo') or '').strip()
        pdf_text       = (ctx.get('pdf_text') or '').strip()

        # ── [a] Encabezado de lugar y fecha ─────────────────────────────────────
        meses = {
            1:'enero', 2:'febrero', 3:'marzo', 4:'abril', 5:'mayo', 6:'junio',
            7:'julio', 8:'agosto', 9:'septiembre', 10:'octubre', 11:'noviembre', 12:'diciembre'
        }
        hoy = _dt.now()
        fecha_str = f"Supatá, Cundinamarca, {hoy.day} de {meses[hoy.month]} de {hoy.year}."

        # ── [b] Destinatario ─────────────────────────────────────────────────────
        # Intentar extraer nombre y empresa del remitente
        nombre_dest = remitente_raw.upper()
        empresa_dest = ''
        if '<' in remitente_raw:
            partes = remitente_raw.split('<')
            nombre_dest = partes[0].strip().upper()
        # Detectar si es firma interventora / empresa en el cuerpo o asunto
        es_contractual = any(tok in asunto.upper() for tok in ['CTO-', 'COP-', 'CONTRATO', 'INTERVENTOR', 'SOSKEN', 'HISO', 'OBRA', 'ACTA', 'OFICIO'])
        if not es_contractual and pdf_text:
            es_contractual = any(tok in pdf_text.upper() for tok in ['CONTRATO', 'INTERVENTOR', 'OBRA N', 'SOSKEN', 'HISO'])

        # ── [c] Referencia ───────────────────────────────────────────────────────
        # Extraer número de radicado / oficio del asunto
        m_ref = _re.search(r'[A-Z]{2,}-[A-Z]{2,}-[A-Z\d-]+', asunto)
        ref_str = f" Referencia: {m_ref.group(0)}, radicado el {hoy.day} de {meses[hoy.month]} de {hoy.year}." if m_ref else f" Referencia: {asunto[:80]}."

        # ── [d] Saludo formal ────────────────────────────────────────────────────
        if es_contractual:
            saludo = "Respetados señores:"
        elif 'señora' in remitente_raw.lower() or any(t in remitente_raw.lower() for t in ['dra.', 'mg.', 'ing.', 'arq.']):
            saludo = "Respetada señora:"
        else:
            saludo = "Respetado señor:"

        # ── [e] Cuerpo ────────────────────────────────────────────────────────────
        # Párrafo 1 – Acuse de recibo / contexto
        if es_contractual:
            # Extraer número de contrato
            m_contrato = _re.search(r'COP-\d{3}-\d{4}|COP\d{3}\d{4}|N[°º\.]\s*COP-[\d-]+', asunto + ' ' + cuerpo + ' ' + pdf_text, _re.IGNORECASE)
            num_contrato = m_contrato.group(0).upper() if m_contrato else 'COP-XXX-XXXX'
            p1 = (
                f"En atención al oficio de la referencia, mediante el cual esa firma remite a esta Secretaría "
                f"comunicación relacionada con la ejecución del Contrato de Obra N.° {num_contrato}, "
                f"me permito acusar recibo del documento y confirmar su ingreso al expediente contractual correspondiente."
            )
        elif categoria == 'derecho_peticion':
            p1 = (
                f"En virtud del derecho fundamental de petición consagrado en el Artículo 23 de la Constitución "
                f"Política de Colombia y regulado por la Ley 1755 de 2015, esta Secretaría acusa recibo de su "
                f"comunicación de la referencia, radicada ante la Alcaldía Municipal de Supatá."
            )
        elif categoria in ('queja', 'reclamo'):
            p1 = (
                f"Esta Administración Municipal ha recibido su {'queja' if categoria == 'queja' else 'reclamo'} "
                f"de la referencia y procede a pronunciarse conforme a lo dispuesto en la Ley 1437 de 2011 "
                f"(Código de Procedimiento Administrativo y de lo Contencioso Administrativo — CPACA)."
            )
        elif categoria == 'solicitud':
            p1 = (
                f"Con ocasión de la solicitud presentada, esta Secretaría ha efectuado la revisión preliminar "
                f"de la información suministrada y ha dado inicio al proceso de verificación técnica "
                f"y administrativa correspondiente."
            )
        elif categoria == 'requerimiento':
            p1 = (
                f"En atención al requerimiento de la referencia, esta dependencia se permite acusar recibo "
                f"de la comunicación y confirmar que el asunto ha sido registrado y fue remitido al área técnica competente "
                f"para su revisión y respuesta de fondo."
            )
        else:
            p1 = (
                f"Esta Secretaría de Planeación y Obras Públicas acusa recibo de su comunicación de la referencia "
                f"y procede a dar respuesta conforme a las disposiciones administrativas vigentes."
            )

        # Párrafo 2 – Análisis / posición institucional
        if es_contractual:
            p2 = (
                f"La documentación adjunta ha sido verificada y será objeto de análisis técnico por parte de esta dependencia, "
                f"con el fin de determinar las acciones administrativas pertinentes conforme al clausulado del contrato "
                f"y a las disposiciones del Estatuto General de Contratación (Ley 80 de 1993, Ley 1150 de 2007 "
                f"y Decreto 1082 de 2015)."
            )
        elif categoria == 'derecho_peticion':
            p2 = (
                f"Conforme al artículo 14 de la Ley 1755 de 2015, su petición será resuelta dentro de los "
                f"quince (15) días hábiles siguientes a la fecha de su radicación. El área competente analizará "
                f"el fondo del asunto y emitirá respuesta motivada dentro del término establecido."
            )
        elif categoria in ('queja', 'reclamo'):
            p2 = (
                f"Esta administración ha aperturado un expediente de seguimiento con el fin de verificar los "
                f"hechos reportados y adoptar las medidas correctivas que resulten procedentes. "
                f"El funcionario responsable del proceso será notificado y se garantizará trazabilidad "
                f"en la gestión del caso."
            )
        elif categoria == 'solicitud':
            p2 = (
                f"Una vez se cuente con la totalidad de la documentación e información requerida, "
                f"esta dependencia emitirá concepto técnico de fondo, de conformidad con las normas "
                f"urbanísticas vigentes (Ley 388 de 1997, Decreto 1077 de 2015 y EOT municipal)."
            )
        else:
            p2 = (
                f"El asunto ha sido analizado preliminarmente por esta dependencia y será objeto de "
                f"pronunciamiento formal dentro de los términos institucionales establecidos, con plena "
                f"sujeción a las disposiciones del ordenamiento jurídico colombiano aplicable."
            )

        # Párrafo 3 – Compromisos, plazos, instrucciones
        if es_contractual:
            p3 = (
                f"Esta Secretaría se pronunciará formalmente sobre el contenido de las observaciones dentro de "
                f"los términos institucionales establecidos, y requerirá la participación de las partes contractuales "
                f"en caso de que resulte necesario para el esclarecimiento de los puntos planteados.\n\n"
                f"Se recuerda que toda comunicación oficial relativa al contrato deberá remitirse al correo "
                f"electrónico autorizado: planeacion@supata-cundinamarca.gov.co."
            )
        elif urgencia == 'alta':
            p3 = (
                f"Dado el carácter prioritario del asunto, esta dependencia ha solicitado atención inmediata "
                f"al área responsable, con el fin de dar respuesta dentro del menor tiempo posible y con la "
                f"calidad institucional que corresponde."
            )
        else:
            p3 = (
                f"Quedamos atentos a cualquier información adicional que sea requerida para el trámite del "
                f"asunto y reiteramos nuestro compromiso con la prestación de un servicio público eficiente, "
                f"transparente y oportuno en beneficio de los ciudadanos del Municipio de Supatá."
            )

        # Párrafo de contexto PDF ─────────────────────────────────────────────────
        pdf_parrafo = ''
        if pdf_text and len(pdf_text) > 50:
            fragmento = pdf_text[:350].replace('\n', ' ').strip()
            if len(pdf_text) > 350:
                fragmento += '...'
            pdf_parrafo = (
                f"\n\nEn relación con los documentos adjuntos remitidos, esta Secretaría ha revisado "
                f"su contenido y toma nota del siguiente elemento relevante para el trámite: "
                f"«{fragmento}». La documentación adjunta hace parte integral del expediente administrativo "
                f"que se adelanta para dar respuesta de fondo."
            )

        # ── [f] Cierre y [g] Firma ───────────────────────────────────────────────
        cierre_saludo = "Cordialmente," if es_contractual or categoria in ('requerimiento', 'tecnica') else "Atentamente,"

        firma = (
            "ARQ. RAFAEL ANTONIO PERAFÁN MEDINA\n"
            "Secretario de Planeación y Obras Públicas\n"
            "Alcaldía Municipal de Supatá — Cundinamarca\n"
            "📞 313 377 8741 — 313 379 9993\n"
            "✉️  planeacion@supata-cundinamarca.gov.co\n"
            "📍 Carrera 7 N.° 4-14, Supatá, Cundinamarca\n"
            "🌐 www.supata-cundinamarca.gov.co\n"
            "\"Unidos por el Supatá que soñamos\" 2024–2027"
        )

        draft = (
            f"{fecha_str}\n\n"
            f"{nombre_dest}\n"
            f"Ciudad.\n\n"
            f"{ref_str}\n\n"
            f"{saludo}\n\n"
            f"{p1}\n\n"
            f"{p2}\n\n"
            f"{p3}"
            f"{pdf_parrafo}\n\n"
            f"{cierre_saludo}\n\n"
            f"{firma}"
        )
        return draft
