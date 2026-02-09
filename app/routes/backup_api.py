"""
API Endpoints para Backup y Restauración
Rutas: /api/backup/...
"""
from flask import Blueprint, request, jsonify, send_file, current_app
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

backup_api = Blueprint('backup_api', __name__, url_prefix='/api/backup')

def get_backup_manager():
    """Obtiene instancia del BackupManager desde la app"""
    from app.utils.backup_manager import BackupManager
    if not hasattr(current_app, 'backup_manager'):
        current_app.backup_manager = BackupManager(current_app)
    return current_app.backup_manager

# ============================================================================
# ENDPOINTS DE BACKUP
# ============================================================================

@backup_api.route('/crear', methods=['POST'])
def crear_backup():
    """Crea un backup manual de la BD"""
    try:
        bm = get_backup_manager()
        resultado = bm.crear_backup()
        
        if resultado['success']:
            return jsonify({
                'success': True,
                'mensaje': 'Backup creado exitosamente',
                'backup': resultado
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': resultado.get('error')
            }), 400
    except Exception as e:
        logger.error(f"Error en crear_backup: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@backup_api.route('/listar', methods=['GET'])
def listar_backups():
    """Lista todos los backups disponibles"""
    try:
        bm = get_backup_manager()
        resultado = bm.listar_backups()
        
        return jsonify(resultado), 200 if resultado['success'] else 400
    except Exception as e:
        logger.error(f"Error en listar_backups: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@backup_api.route('/restaurar/<nombre_backup>', methods=['POST'])
def restaurar_backup(nombre_backup):
    """Restaura una BD desde un backup específico"""
    try:
        # Confirmar acción (parámetro opcional)
        confirmar = request.json.get('confirmar', True) if request.json else True
        
        if not confirmar:
            return jsonify({
                'success': False,
                'error': 'Acción no confirmada'
            }), 400
        
        bm = get_backup_manager()
        resultado = bm.restaurar_backup(nombre_backup)
        
        if resultado['success']:
            return jsonify({
                'success': True,
                'mensaje': 'Base de datos restaurada exitosamente',
                'detalles': resultado
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': resultado.get('error')
            }), 400
    except Exception as e:
        logger.error(f"Error en restaurar_backup: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@backup_api.route('/eliminar/<nombre_backup>', methods=['DELETE'])
def eliminar_backup(nombre_backup):
    """Elimina un archivo de backup"""
    try:
        bm = get_backup_manager()
        resultado = bm.eliminar_backup(nombre_backup)
        
        return jsonify(resultado), 200 if resultado['success'] else 400
    except Exception as e:
        logger.error(f"Error en eliminar_backup: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@backup_api.route('/descargar/<nombre_backup>', methods=['GET'])
def descargar_backup(nombre_backup):
    """Descarga un archivo de backup"""
    try:
        from app.utils.backup_manager import BackupManager
        bm = get_backup_manager()
        
        ruta_backup = bm.backup_dir / nombre_backup
        
        if not ruta_backup.exists():
            return jsonify({'error': 'Backup no encontrado'}), 404
        
        return send_file(
            ruta_backup,
            as_attachment=True,
            download_name=nombre_backup,
            mimetype='application/zip'
        )
    except Exception as e:
        logger.error(f"Error en descargar_backup: {e}")
        return jsonify({'error': str(e)}), 500

@backup_api.route('/exportar', methods=['POST'])
def exportar_datos():
    """Exporta datos a JSON para respaldo adicional"""
    try:
        data = request.json or {}
        formato = data.get('formato', 'json')
        tablas = data.get('tablas')  # None = todas
        
        bm = get_backup_manager()
        resultado = bm.exportar_datos(formato=formato, tablas=tablas)
        
        return jsonify(resultado), 201 if resultado['success'] else 400
    except Exception as e:
        logger.error(f"Error en exportar_datos: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@backup_api.route('/auto-backup', methods=['POST'])
def auto_backup():
    """Crea un backup automático (para antes de actualizaciones)"""
    try:
        bm = get_backup_manager()
        resultado = bm.auto_backup()
        
        return jsonify({
            'success': True,
            'mensaje': 'Backup automático creado',
            'backup': resultado
        }), 201 if resultado['success'] else 400
    except Exception as e:
        logger.error(f"Error en auto_backup: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@backup_api.route('/estado', methods=['GET'])
def estado_backup():
    """Información sobre el estado del sistema de backup"""
    try:
        bm = get_backup_manager()
        backups = bm.listar_backups()
        
        return jsonify({
            'success': True,
            'backup_dir': str(bm.backup_dir),
            'db_file': str(bm.db_file),
            'db_existe': bm.db_file.exists() if hasattr(bm.db_file, 'exists') else False,
            'total_backups': len(backups.get('backups', [])),
            'backups': backups.get('backups', [])
        }), 200
    except Exception as e:
        logger.error(f"Error en estado_backup: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
