"""
Sistema de Backups Automáticos
Gestiona backups de base de datos y archivos importantes
"""

import os
import shutil
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import zipfile
import json

class BackupManager:
    """Gestor de backups del sistema"""
    
    def __init__(self, app=None):
        self.app = app
        self.backup_dir = None
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Inicializa el gestor con la aplicación Flask"""
        self.app = app
        base_dir = app.config.get('BASE_DIR', os.getcwd())
        self.backup_dir = os.path.join(base_dir, 'backups')
        
        # Crear directorio de backups si no existe
        os.makedirs(self.backup_dir, exist_ok=True)
        os.makedirs(os.path.join(self.backup_dir, 'database'), exist_ok=True)
        os.makedirs(os.path.join(self.backup_dir, 'archivos'), exist_ok=True)
        os.makedirs(os.path.join(self.backup_dir, 'completo'), exist_ok=True)
    
    def backup_database(self, descripcion=''):
        """
        Crea backup de la base de datos
        
        Returns:
            tuple: (exito: bool, ruta: str, mensaje: str)
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Obtener ruta de la base de datos
            db_path = self.app.config.get('SQLALCHEMY_DATABASE_URI', '').replace('sqlite:///', '')
            if not os.path.exists(db_path):
                return False, None, "Base de datos no encontrada"
            
            # Nombre del backup
            backup_filename = f"db_backup_{timestamp}.db"
            if descripcion:
                backup_filename = f"db_backup_{timestamp}_{descripcion}.db"
            
            backup_path = os.path.join(self.backup_dir, 'database', backup_filename)
            
            # Hacer copia de la base de datos
            shutil.copy2(db_path, backup_path)
            
            # Comprimir
            zip_path = backup_path + '.zip'
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(backup_path, os.path.basename(backup_path))
            
            # Eliminar archivo sin comprimir
            os.remove(backup_path)
            
            # Guardar metadata
            self._guardar_metadata_backup(zip_path, 'database', descripcion)
            
            return True, zip_path, f"Backup creado: {os.path.basename(zip_path)}"
            
        except Exception as e:
            return False, None, f"Error al crear backup: {str(e)}"
    
    def backup_archivos(self, directorios=None, descripcion=''):
        """
        Crea backup de archivos importantes
        
        Args:
            directorios: Lista de directorios a respaldar (por defecto: datos, uploads)
        
        Returns:
            tuple: (exito: bool, ruta: str, mensaje: str)
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if not directorios:
                base_dir = self.app.config.get('BASE_DIR', os.getcwd())
                data_dir = self.app.config.get('DATA_DIR', 'datos')
                directorios = [
                    os.path.join(base_dir, data_dir),
                    os.path.join(base_dir, 'uploads'),
                    os.path.join(base_dir, 'documentos_generados')
                ]
            
            # Nombre del backup
            backup_filename = f"archivos_backup_{timestamp}"
            if descripcion:
                backup_filename += f"_{descripcion}"
            
            backup_path = os.path.join(self.backup_dir, 'archivos', backup_filename + '.zip')
            
            # Crear archivo ZIP
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for directorio in directorios:
                    if os.path.exists(directorio):
                        for root, dirs, files in os.walk(directorio):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arcname = os.path.relpath(file_path, self.app.config.get('BASE_DIR', os.getcwd()))
                                zipf.write(file_path, arcname)
            
            # Guardar metadata
            self._guardar_metadata_backup(backup_path, 'archivos', descripcion)
            
            return True, backup_path, f"Backup creado: {os.path.basename(backup_path)}"
            
        except Exception as e:
            return False, None, f"Error al crear backup de archivos: {str(e)}"
    
    def backup_completo(self, descripcion=''):
        """
        Crea un backup completo del sistema
        
        Returns:
            tuple: (exito: bool, ruta: str, mensaje: str)
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Backup de BD
            exito_db, path_db, msg_db = self.backup_database(f"completo_{timestamp}")
            if not exito_db:
                return False, None, f"Error en backup de BD: {msg_db}"
            
            # Backup de archivos
            exito_files, path_files, msg_files = self.backup_archivos(descripcion=f"completo_{timestamp}")
            if not exito_files:
                return False, None, f"Error en backup de archivos: {msg_files}"
            
            # Crear ZIP maestro
            backup_filename = f"completo_backup_{timestamp}"
            if descripcion:
                backup_filename += f"_{descripcion}"
            
            backup_path = os.path.join(self.backup_dir, 'completo', backup_filename + '.zip')
            
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(path_db, f"database/{os.path.basename(path_db)}")
                zipf.write(path_files, f"archivos/{os.path.basename(path_files)}")
            
            # Guardar metadata
            self._guardar_metadata_backup(backup_path, 'completo', descripcion)
            
            return True, backup_path, f"Backup completo creado: {os.path.basename(backup_path)}"
            
        except Exception as e:
            return False, None, f"Error al crear backup completo: {str(e)}"
    
    def listar_backups(self, tipo='todos'):
        """
        Lista todos los backups disponibles
        
        Args:
            tipo: 'database', 'archivos', 'completo', o 'todos'
        
        Returns:
            list: Lista de diccionarios con información de backups
        """
        backups = []
        
        tipos_buscar = ['database', 'archivos', 'completo'] if tipo == 'todos' else [tipo]
        
        for tipo_backup in tipos_buscar:
            directorio = os.path.join(self.backup_dir, tipo_backup)
            if not os.path.exists(directorio):
                continue
            
            for filename in os.listdir(directorio):
                if filename.endswith('.zip'):
                    filepath = os.path.join(directorio, filename)
                    stat = os.stat(filepath)
                    
                    # Intentar cargar metadata
                    metadata_path = filepath + '.meta'
                    metadata = {}
                    if os.path.exists(metadata_path):
                        try:
                            with open(metadata_path, 'r') as f:
                                metadata = json.load(f)
                        except:
                            pass
                    
                    backups.append({
                        'nombre': filename,
                        'tipo': tipo_backup,
                        'ruta': filepath,
                        'tamaño': stat.st_size,
                        'tamaño_mb': round(stat.st_size / (1024 * 1024), 2),
                        'fecha': datetime.fromtimestamp(stat.st_mtime),
                        'descripcion': metadata.get('descripcion', ''),
                        'creado_por': metadata.get('creado_por', 'Sistema')
                    })
        
        # Ordenar por fecha (más recientes primero)
        backups.sort(key=lambda x: x['fecha'], reverse=True)
        
        return backups
    
    def restaurar_database(self, backup_path):
        """
        Restaura la base de datos desde un backup
        
        Args:
            backup_path: Ruta al archivo de backup
        
        Returns:
            tuple: (exito: bool, mensaje: str)
        """
        try:
            if not os.path.exists(backup_path):
                return False, "Archivo de backup no encontrado"
            
            # Crear backup de seguridad antes de restaurar
            self.backup_database('pre_restauracion')
            
            # Descomprimir
            temp_dir = os.path.join(self.backup_dir, 'temp_restore')
            os.makedirs(temp_dir, exist_ok=True)
            
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                zipf.extractall(temp_dir)
            
            # Encontrar el archivo .db
            db_file = None
            for file in os.listdir(temp_dir):
                if file.endswith('.db'):
                    db_file = os.path.join(temp_dir, file)
                    break
            
            if not db_file:
                return False, "No se encontró archivo de base de datos en el backup"
            
            # Restaurar
            db_path = self.app.config.get('SQLALCHEMY_DATABASE_URI', '').replace('sqlite:///', '')
            shutil.copy2(db_file, db_path)
            
            # Limpiar archivos temporales
            shutil.rmtree(temp_dir)
            
            return True, "Base de datos restaurada correctamente"
            
        except Exception as e:
            return False, f"Error al restaurar: {str(e)}"
    
    def limpiar_backups_antiguos(self, dias=30, mantener_minimo=5):
        """
        Elimina backups más antiguos que X días, manteniendo un mínimo
        
        Args:
            dias: Días de antigüedad
            mantener_minimo: Cantidad mínima de backups a mantener
        
        Returns:
            int: Cantidad de backups eliminados
        """
        fecha_limite = datetime.now() - timedelta(days=dias)
        eliminados = 0
        
        for tipo in ['database', 'archivos', 'completo']:
            directorio = os.path.join(self.backup_dir, tipo)
            if not os.path.exists(directorio):
                continue
            
            backups = []
            for filename in os.listdir(directorio):
                if filename.endswith('.zip'):
                    filepath = os.path.join(directorio, filename)
                    stat = os.stat(filepath)
                    backups.append({
                        'path': filepath,
                        'fecha': datetime.fromtimestamp(stat.st_mtime)
                    })
            
            # Ordenar por fecha
            backups.sort(key=lambda x: x['fecha'], reverse=True)
            
            # Mantener los más recientes
            for i, backup in enumerate(backups):
                if i < mantener_minimo:
                    continue  # No eliminar los X más recientes
                
                if backup['fecha'] < fecha_limite:
                    try:
                        os.remove(backup['path'])
                        # Eliminar metadata si existe
                        meta_path = backup['path'] + '.meta'
                        if os.path.exists(meta_path):
                            os.remove(meta_path)
                        eliminados += 1
                    except:
                        pass
        
        return eliminados
    
    def _guardar_metadata_backup(self, backup_path, tipo, descripcion):
        """Guarda metadata del backup"""
        metadata = {
            'tipo': tipo,
            'fecha': datetime.now().isoformat(),
            'descripcion': descripcion,
            'creado_por': 'Sistema',
            'version': '1.0'
        }
        
        meta_path = backup_path + '.meta'
        with open(meta_path, 'w') as f:
            json.dump(metadata, f, indent=2)
