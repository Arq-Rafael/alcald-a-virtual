"""
Sistema de Backup y Restauración de Base de Datos
Preserva datos ante actualizaciones del sistema
"""
import os
import shutil
import json
from datetime import datetime
from pathlib import Path
import zipfile
import logging

logger = logging.getLogger(__name__)

class BackupManager:
    """Gestiona backups de la base de datos"""
    
    def __init__(self, app):
        self.app = app
        # Directorio de backups
        self.backup_dir = Path(app.config.get('BACKUPS_DIR', 'backups'))
        self.backup_dir.mkdir(exist_ok=True, parents=True)
        
        # Directorio de BD
        self.instance_dir = Path(app.config.get('SQLALCHEMY_DATABASE_URI', '').replace('sqlite:///', ''))
        self.db_file = self.instance_dir / 'app.db' if self.instance_dir.is_dir() else self.instance_dir
        
        logger.info(f"[BACKUP] Sistema de backup inicializado en {self.backup_dir}")
    
    def crear_backup(self, nombre_custom=None):
        """
        Crea un backup comprimido de la BD actual
        Retorna ruta del backup creado
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            nombre_backup = nombre_custom or f"backup_{timestamp}"
            ruta_backup = self.backup_dir / f"{nombre_backup}.zip"
            
            # Crear archivo ZIP con la BD y metadatos
            with zipfile.ZipFile(ruta_backup, 'w', zipfile.ZIP_DEFLATED) as zf:
                # Agregar archivo de BD
                if self.db_file.exists():
                    zf.write(self.db_file, arcname='app.db')
                    logger.info(f"[BACKUP] BD añadida al backup")
                
                # Metadatos del backup
                metadata = {
                    'timestamp': timestamp,
                    'fecha': datetime.now().isoformat(),
                    'tamaño_kb': self.db_file.stat().st_size / 1024 if self.db_file.exists() else 0,
                    'nombre_archivo': nombre_backup
                }
                
                zf.writestr('metadata.json', json.dumps(metadata, indent=2))
                logger.info(f"[BACKUP] Metadatos añadidos")
            
            logger.info(f"[BACKUP] ✅ Backup creado: {ruta_backup}")
            return {
                'success': True,
                'archivo': str(ruta_backup),
                'nombre': nombre_backup,
                'timestamp': timestamp,
                'tamaño_kb': ruta_backup.stat().st_size / 1024
            }
        except Exception as e:
            logger.error(f"[BACKUP] ❌ Error creando backup: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def listar_backups(self):
        """Lista todos los backups disponibles"""
        try:
            backups = []
            for archivo in sorted(self.backup_dir.glob('backup_*.zip'), reverse=True):
                # Extraer metadata
                try:
                    with zipfile.ZipFile(archivo, 'r') as zf:
                        meta_str = zf.read('metadata.json').decode('utf-8')
                        metadata = json.loads(meta_str)
                        backups.append({
                            'archivo': archivo.name,
                            'ruta': str(archivo),
                            'fecha': metadata.get('fecha'),
                            'tamaño_kb': metadata.get('tamaño_kb'),
                            'timestamp': metadata.get('timestamp'),
                            'tamaño_archivo_kb': archivo.stat().st_size / 1024
                        })
                except Exception as e:
                    logger.warning(f"[BACKUP] No se pudo leer metadata de {archivo}: {e}")
                    # Agregar sin metadata
                    backups.append({
                        'archivo': archivo.name,
                        'ruta': str(archivo),
                        'tamaño_archivo_kb': archivo.stat().st_size / 1024
                    })
            
            logger.info(f"[BACKUP] {len(backups)} backups disponibles")
            return {'success': True, 'backups': backups}
        except Exception as e:
            logger.error(f"[BACKUP] Error listando backups: {e}")
            return {'success': False, 'error': str(e)}
    
    def restaurar_backup(self, archivo_backup):
        """
        Restaura una BD desde un backup
        Primero crea un backup de seguridad de la BD actual
        """
        try:
            ruta_backup = self.backup_dir / archivo_backup
            
            if not ruta_backup.exists():
                return {
                    'success': False,
                    'error': f'Archivo de backup no encontrado: {archivo_backup}'
                }
            
            # 1. Crear backup de seguridad de la BD actual (por si acaso)
            logger.info("[BACKUP] Creando backup de seguridad de BD actual...")
            backup_actual = self.crear_backup(f"backup_before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            
            if not backup_actual['success']:
                return {
                    'success': False,
                    'error': 'No se pudo crear backup de seguridad'
                }
            
            # 2. Restaurar desde ZIP
            logger.info(f"[BACKUP] Extrayendo backup desde {archivo_backup}...")
            
            with zipfile.ZipFile(ruta_backup, 'r') as zf:
                # Extraer app.db
                if 'app.db' in zf.namelist():
                    # Respaldar BD actual
                    if self.db_file.exists():
                        self.db_file.rename(f"{self.db_file}.old")
                    
                    # Extraer nuevo
                    zf.extract('app.db', path=self.db_file.parent)
                    logger.info(f"[BACKUP] ✅ BD restaurada desde backup")
                    
                    return {
                        'success': True,
                        'mensaje': 'Datos restaurados exitosamente',
                        'backup_seguridad': backup_actual.get('archivo'),
                        'fecha_restauracion': datetime.now().isoformat()
                    }
                else:
                    return {
                        'success': False,
                        'error': 'El archivo de backup no contiene app.db'
                    }
        
        except Exception as e:
            logger.error(f"[BACKUP] ❌ Error restaurando backup: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def eliminar_backup(self, archivo_backup):
        """Elimina un archivo de backup"""
        try:
            ruta_backup = self.backup_dir / archivo_backup
            
            if ruta_backup.exists():
                ruta_backup.unlink()
                logger.info(f"[BACKUP] Backup eliminado: {archivo_backup}")
                return {'success': True, 'mensaje': 'Backup eliminado'}
            else:
                return {'success': False, 'error': 'Backup no encontrado'}
        except Exception as e:
            logger.error(f"[BACKUP] Error eliminando backup: {e}")
            return {'success': False, 'error': str(e)}
    
    def auto_backup(self):
        """Crea un backup automático (para ejecutar antes de actualizaciones)"""
        logger.info("[BACKUP] Iniciando backup automático...")
        resultado = self.crear_backup(f"auto_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        # Limpiar backups antiguos (mantener solo últimos 10)
        self._limpiar_backups_antiguos()
        
        return resultado
    
    def _limpiar_backups_antiguos(self, max_backups=10):
        """Elimina backups antiguos, manteniendo solo los últimos N"""
        try:
            backups = sorted(self.backup_dir.glob('backup_*.zip'), 
                           key=lambda x: x.stat().st_mtime, 
                           reverse=True)
            
            for backup_antiguo in backups[max_backups:]:
                backup_antiguo.unlink()
                logger.info(f"[BACKUP] Backup antiguo eliminado: {backup_antiguo.name}")
        except Exception as e:
            logger.warning(f"[BACKUP] Error limpiando backups antiguos: {e}")
    
    def exportar_datos(self, formato='json', tablas=None):
        """
        Exporta datos a JSON o CSV para respaldo adicional
        tablas: None = todas, o lista de nombres de tabla
        """
        try:
            from app import db
            from app.models.usuario import Usuario
            from app.models.participacion import Radicado
            from app.models.riesgo_arborea import RadicadoArborea
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            nombre_export = f"export_{timestamp}.json"
            ruta_export = self.backup_dir / nombre_export
            
            datos_export = {
                'timestamp': timestamp,
                'tablas': {}
            }
            
            # Mapeo de modelos
            modelos = {
                'usuarios': Usuario,
                'radicados': Radicado,
                'radicados_arborea': RadicadoArborea
            }
            
            # Exportar cada tabla
            for nombre_tabla, modelo in modelos.items():
                if tablas and nombre_tabla not in tablas:
                    continue
                
                registros = modelo.query.all()
                datos_export['tablas'][nombre_tabla] = {
                    'cantidad': len(registros),
                    'datos': [r.__dict__ for r in registros]
                }
                logger.info(f"[BACKUP] Exportados {len(registros)} registros de {nombre_tabla}")
            
            # Guardar JSON
            with open(ruta_export, 'w', encoding='utf-8') as f:
                json.dump(datos_export, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"[BACKUP] ✅ Datos exportados: {ruta_export}")
            return {
                'success': True,
                'archivo': nombre_export,
                'ruta': str(ruta_export)
            }
        except Exception as e:
            logger.error(f"[BACKUP] Error exportando datos: {e}")
            return {'success': False, 'error': str(e)}
