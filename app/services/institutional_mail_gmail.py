"""Integracion Gmail OAuth2 para Correo Inteligente Institucional."""

import base64
from datetime import datetime
import hashlib
import importlib
import json
import os
import re
from email.message import EmailMessage


class GmailIntegrationError(Exception):
    pass


class GmailIntegrationService:
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.modify',
    ]

    def __init__(self, app_config):
        self.client_id = os.environ.get('GOOGLE_CLIENT_ID', '').strip()
        self.client_secret = os.environ.get('GOOGLE_CLIENT_SECRET', '').strip()
        self.redirect_uri = os.environ.get(
            'GOOGLE_REDIRECT_URI',
            'http://localhost:5000/correo-inteligente/oauth/callback'
        ).strip()

        self.app_config = app_config
        # Lazy init para evitar fallar en endpoints que no usan cifrado.
        self._cipher = None

    def is_configured(self):
        return bool(self.client_id and self.client_secret and self.redirect_uri)

    def missing_config_fields(self):
        missing = []
        if not self.client_id:
            missing.append('GOOGLE_CLIENT_ID')
        if not self.client_secret:
            missing.append('GOOGLE_CLIENT_SECRET')
        if not self.redirect_uri:
            missing.append('GOOGLE_REDIRECT_URI')
        return missing

    def get_authorization_url(self, state_payload):
        flow = self._build_flow()
        auth_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent',
            state=state_payload,
        )
        return auth_url, state, getattr(flow, 'code_verifier', None)

    def exchange_code_for_token(self, code, code_verifier=None):
        flow = self._build_flow()
        if code_verifier:
            flow.code_verifier = code_verifier
        flow.fetch_token(code=code)
        credentials = flow.credentials
        token_payload = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': list(credentials.scopes or self.SCOPES),
            'expiry': credentials.expiry.isoformat() if credentials.expiry else None,
        }
        return token_payload

    def encrypt_token_payload(self, token_payload):
        raw = json.dumps(token_payload, ensure_ascii=False).encode('utf-8')
        return self._get_cipher().encrypt(raw).decode('utf-8')

    def decrypt_token_payload(self, encrypted_payload):
        if not encrypted_payload:
            return None
        raw = self._get_cipher().decrypt(encrypted_payload.encode('utf-8'))
        return json.loads(raw.decode('utf-8'))

    def _get_cipher(self):
        if self._cipher is None:
            self._cipher = self._build_cipher()
        return self._cipher

    def list_message_details(self, token_payload, max_results=40, query='newer_than:30d'):
        service = self._build_gmail_service(token_payload)

        response = service.users().messages().list(
            userId='me',
            maxResults=max_results,
            q=query,
        ).execute()

        items = response.get('messages', [])
        messages = []

        for item in items:
            detail = service.users().messages().get(
                userId='me',
                id=item['id'],
                format='full',
            ).execute()
            messages.append(self._normalize_message(detail))

        return messages

    def _build_gmail_service(self, token_payload):
        try:
            credentials_mod = importlib.import_module('google.oauth2.credentials')
            discovery_mod = importlib.import_module('googleapiclient.discovery')
            Credentials = getattr(credentials_mod, 'Credentials')
            build = getattr(discovery_mod, 'build')
        except Exception as exc:
            raise GmailIntegrationError(
                'Dependencias Gmail no instaladas. Agrega google-api-python-client y google-auth-oauthlib.'
            ) from exc

        payload = dict(token_payload)
        expiry = payload.get('expiry')
        if expiry:
            try:
                from datetime import datetime as dt
                payload['expiry'] = dt.fromisoformat(expiry)
            except Exception:
                payload['expiry'] = None

        credentials = Credentials(
            token=payload.get('token'),
            refresh_token=payload.get('refresh_token'),
            token_uri=payload.get('token_uri', 'https://oauth2.googleapis.com/token'),
            client_id=payload.get('client_id') or self.client_id,
            client_secret=payload.get('client_secret') or self.client_secret,
            scopes=payload.get('scopes') or self.SCOPES,
        )
        if payload.get('expiry'):
            credentials.expiry = payload['expiry']

        return build('gmail', 'v1', credentials=credentials, cache_discovery=False)

    def _build_flow(self):
        if not self.is_configured():
            missing = self.missing_config_fields()
            missing_txt = ', '.join(missing) if missing else 'GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET y GOOGLE_REDIRECT_URI'
            raise GmailIntegrationError(
                f'Falta configurar: {missing_txt}.'
            )

        try:
            flow_mod = importlib.import_module('google_auth_oauthlib.flow')
            Flow = getattr(flow_mod, 'Flow')
        except Exception as exc:
            raise GmailIntegrationError(
                'Dependencias OAuth de Google no instaladas. Agrega google-auth-oauthlib.'
            ) from exc

        client_config = {
            'web': {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                'token_uri': 'https://oauth2.googleapis.com/token',
                'redirect_uris': [self.redirect_uri],
            }
        }

        flow = Flow.from_client_config(
            client_config=client_config,
            scopes=self.SCOPES,
            redirect_uri=self.redirect_uri,
        )
        return flow

    def _build_fernet_key(self):
        key_seed = (
            os.environ.get('MAIL_ENCRYPTION_KEY')
            or self.app_config.get('SECRET_KEY', 'alcaldia-mail-fallback-secret')
        )
        digest = hashlib.sha256(str(key_seed).encode('utf-8')).digest()
        return base64.urlsafe_b64encode(digest)

    def _build_cipher(self):
        try:
            fernet_mod = importlib.import_module('cryptography.fernet')
            fernet_cls = getattr(fernet_mod, 'Fernet')
            return fernet_cls(self._build_fernet_key())
        except Exception as exc:
            raise GmailIntegrationError(
                'Dependencia cryptography no instalada. Agrega cryptography>=44.0.0.'
            ) from exc

    def _normalize_message(self, gmail_message):
        payload = gmail_message.get('payload', {})
        headers = {h.get('name', '').lower(): h.get('value', '') for h in payload.get('headers', [])}

        raw_from = headers.get('from', '')
        remitente, remitente_email = self._extract_sender(raw_from)

        internal_date = gmail_message.get('internalDate')
        fecha_recepcion = datetime.utcnow()
        if internal_date:
            try:
                fecha_recepcion = datetime.utcfromtimestamp(int(internal_date) / 1000.0)
            except Exception:
                pass

        body_text, attachments = self._extract_body_and_attachments(payload)

        return {
            'gmail_message_id': gmail_message.get('id'),
            'gmail_thread_id': gmail_message.get('threadId'),
            'remitente': remitente,
            'remitente_email': remitente_email,
            'destinatarios': headers.get('to', ''),
            'cc': headers.get('cc', ''),
            'asunto': headers.get('subject', '(Sin asunto)'),
            'snippet': gmail_message.get('snippet', ''),
            'cuerpo_texto': body_text,
            'fecha_recepcion': fecha_recepcion,
            'tiene_adjuntos': len(attachments) > 0,
            'adjuntos': attachments,
        }

    def _extract_body_and_attachments(self, payload):
        text_chunks = []
        attachments = []

        def walk(part):
            mime_type = part.get('mimeType', '')
            filename = part.get('filename', '')
            body = part.get('body', {})

            if filename and body.get('attachmentId'):
                attachments.append({
                    'filename': filename,
                    'mimeType': mime_type,
                    'size': body.get('size', 0),
                    'attachmentId': body.get('attachmentId')
                })

            data = body.get('data')
            if data and mime_type in ('text/plain', 'text/html'):
                decoded = self._decode_base64_urlsafe(data)
                if decoded:
                    if mime_type == 'text/html':
                        decoded = re.sub(r'<[^>]+>', ' ', decoded)
                    text_chunks.append(decoded)

            for child in part.get('parts', []) or []:
                walk(child)

        walk(payload)

        joined = '\n'.join(chunk.strip() for chunk in text_chunks if chunk and chunk.strip())
        if not joined:
            joined = '(Sin cuerpo legible)'

        return joined[:30000], attachments

    def _decode_base64_urlsafe(self, value):
        try:
            padding = '=' * (-len(value) % 4)
            return base64.urlsafe_b64decode(value + padding).decode('utf-8', errors='ignore')
        except Exception:
            return ''

    def download_attachment_text(self, token_payload, message_id, attachment_id):
        """Descarga un archivo adjunto PDF vía Gmail API y extrae su texto usando pypdf."""
        try:
            service = self._build_gmail_service(token_payload)
            attachment = service.users().messages().attachments().get(
                userId='me',
                messageId=message_id,
                id=attachment_id
            ).execute()
            
            data = attachment.get('data')
            if not data:
                return ''
                
            padding = '=' * (-len(data) % 4)
            file_bytes = base64.urlsafe_b64decode(data + padding)
            
            import io
            from pypdf import PdfReader
            
            pdf_stream = io.BytesIO(file_bytes)
            reader = PdfReader(pdf_stream)
            text_extracted = []
            
            for page in reader.pages:
                text_ext = page.extract_text()
                if text_ext:
                    text_extracted.append(text_ext)
                    
            return '\n'.join(text_extracted)
            
        except Exception as e:
            print(f"Error extracting PDF: {e}")
            return ''

    def send_email(self, token_payload, to, subject, body, in_reply_to=None, references=None):
        """Envía un correo electrónico a través de la API de Gmail, con soporte HTML y firma institucional."""
        try:
            service = self._build_gmail_service(token_payload)
            
            message = EmailMessage()
            message['To'] = to
            message['Subject'] = subject
            
            if in_reply_to:
                message['In-Reply-To'] = in_reply_to
            if references:
                message['References'] = references
                
            # Construir versión texto plano
            message.set_content(body)
            
            # Construir versión HTML
            body_html = body.replace('\n', '<br>')
            
            signature_html = """
            <br><br>
            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:700px; font-family:Arial,sans-serif; border-top:1px solid #e2e8f0; margin-top:18px; padding-top:10px;">
                <tr>
                    <td style="padding:10px 0; font-size:10px; color:#6b7280; line-height:1.5; text-align:justify;">
                        <strong>AVISO DE CONFIDENCIALIDAD:</strong> Este correo electrónico contiene información de la ALCALDÍA MUNICIPAL DE SUPATÁ. Si no es el destinatario, comuníquelo de inmediato al remitente y elimine cualquier copia. Su contenido no puede ser usado por personas no autorizadas. Puede ejercer sus derechos de acceso, corrección o supresión escribiendo a <a href="mailto:alcaldia@supata-cundinamarca.gov.co" style="color:#0b4a2c;">alcaldia@supata-cundinamarca.gov.co</a> — Ley 1273/2009, Ley 1581/2012, Decreto 1377/2013.
                    </td>
                </tr>
                <tr>
                    <td style="padding-top:8px; font-size:10px; color:#9ca3af; text-align:center; border-top:1px dashed #e2e8f0;">
                        Correo generado desde la <strong>Alcaldía Virtual del Municipio de Supatá</strong> — Sistema de Gestión de Correo Institucional.
                    </td>
                </tr>
            </table>
            """


            
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; font-size: 14px; color: #1e293b; line-height: 1.6;">
                    {body_html}
                    {signature_html}
                </body>
            </html>
            """
            message.add_alternative(html_content, subtype='html')
                
            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            create_message = {
                'raw': encoded_message
            }
            
            # Si es respuesta a un hilo y tenemos las referencias, intentamos asociarlo
            # NOTA: send() acepta raw pero también threadId si queremos forzar el hilo de gmail
            
            sent_message = service.users().messages().send(
                userId='me',
                body=create_message
            ).execute()
            
            return sent_message
        except Exception as e:
            self.logger.error(f"Error sending email: {e}")
            raise GmailIntegrationError(f"No se pudo enviar el correo: {e}")

    def _extract_sender(self, raw_from):
        if '<' in raw_from and '>' in raw_from:
            name = raw_from.split('<', 1)[0].strip().strip('"')
            email = raw_from.split('<', 1)[1].split('>', 1)[0].strip()
            return name or email, email
        return raw_from, raw_from
