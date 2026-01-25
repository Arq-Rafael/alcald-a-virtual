#!/usr/bin/env python
"""Script para crear un plan de contingencia de ejemplo y probar la generación del PDF"""
import os
import sys
import json
from datetime import datetime, timedelta

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.plan_contingencia import PlanContingencia

def crear_plan_ejemplo():
    """Crea un plan de contingencia de ejemplo"""
    app = create_app()
    
    with app.app_context():
        # Verificar si ya existe
        existing = PlanContingencia.query.filter_by(nombre_plan='Plan de Ejemplo - Prueba PDF').first()
        if existing:
            print(f"Plan de ejemplo ya existe con ID: {existing.id}")
            return existing.id
        
        # Crear un nuevo plan
        plan = PlanContingencia(
            nombre_plan='Plan de Ejemplo - Prueba PDF',
            tipo_evento='Lluvias',
            version='1.0',
            ambito='Municipio de Ejemplo',
            municipio='Ejemplo',
            area_cobertura='Zona urbana y rural',
            poblacion_objetivo=50000,
            responsable_principal='Dr. Juan Pérez García',
            correo_responsable='juan.perez@alcaldia.local',
            telefono_responsable='3001234567',
            entidad_responsable='Alcaldía Municipal',
            estado='Vigente',
            descripcion_peligro='Este plan de contingencia ha sido diseñado para responder a eventos de lluvia intensas que puedan generar inundaciones, deslizamientos y afectación de servicios básicos en el municipio.',
            antecedentes_historicos='En el año 2023 se presentaron lluvias que generaron 15 damnificados y afectación de vías principales.',
            poblacion_expuesta='Personas en zonas bajas y ribereñas',
            activos_expuestos='Viviendas, infraestructura vial, servicios de acueducto y electricidad',
            supuestos_limitaciones='Se supone disponibilidad de recursos para respuesta. Limitación: terreno accidentado',
            puntos_criticos=json.dumps([
                {'nombre': 'Puente principal', 'ubicacion': 'Carrera 5 con Calle 10', 'riesgo': 'Alto'},
                {'nombre': 'Zona ribereña', 'ubicacion': 'Barrio El Bosque', 'riesgo': 'Muy Alto'}
            ]),
            umbrales_alertas=json.dumps({
                'lluvia': [
                    {'nivel': 'Verde', 'mm_24h': '0-50 mm'},
                    {'nivel': 'Amarillo', 'mm_24h': '50-100 mm'},
                    {'nivel': 'Naranja', 'mm_24h': '100-150 mm'},
                    {'nivel': 'Rojo', 'mm_24h': '> 150 mm'}
                ]
            }),
            sistema_alerta=json.dumps({
                'canales': ['Radio local', 'SMS', 'Sirena', 'WhatsApp municipal'],
                'frecuencia': 'Cada 6 horas o ante cambios significativos'
            }),
            estructura_organizativa=json.dumps({
                'estructura_comando': 'Alcalde → Coordinador UNGRD → Sectores',
                'roles': [
                    {'sector': 'Salud', 'responsable': 'Dra. María López', 'telefono': '3002345678', 'correo': 'maria@example.com'},
                    {'sector': 'Infraestructura', 'responsable': 'Ing. Carlos Ruiz', 'telefono': '3003456789', 'correo': 'carlos@example.com'},
                    {'sector': 'Seguridad', 'responsable': 'Cap. Roberto Silva', 'telefono': '3004567890', 'correo': 'roberto@example.com'}
                ]
            }),
            fase_preparacion=json.dumps({
                'acciones': [
                    'Capacitación de brigadas comunitarias',
                    'Mantenimiento de equipos de respuesta',
                    'Actualización de rutas de evacuación'
                ]
            }),
            fase_alistamiento=json.dumps({
                'acciones': [
                    'Activación de centro de operaciones',
                    'Comunicación a sectores',
                    'Prepara recursos en puntos estratégicos'
                ]
            }),
            fase_respuesta=json.dumps({
                'salud': 'Activar puesto de salud de emergencia',
                'logistica': 'Distribuir kits de emergencia',
                'seguridad': 'Controlar acceso a zonas de riesgo',
                'tito': 'Desvíos viales'
            }),
            fase_rehabilitacion=json.dumps({
                'acciones': ['Evaluación de daños', 'Limpieza y desinfección', 'Reconstrucción']
            }),
            inventario_recursos=json.dumps({
                'equipos': ['Bombas de agua (5)', 'Generadores (3)', 'Tiendas de campaña (20)'],
                'vehiculos': ['Ambulancias (3)', 'Camiones de carga (5)', 'Moto taxis (10)'],
                'epp': ['Chalecos salvavidas (100)', 'Cascos (150)', 'Botas impermeables (100)']
            }),
            puntos_acopio=json.dumps([
                {'nombre': 'Coliseo municipal', 'ubicacion': 'Centro', 'capacidad': 500, 'responsable': 'Junta de Acción Comunal'},
                {'nombre': 'Parque principal', 'ubicacion': 'Zona sur', 'capacidad': 300, 'responsable': 'Policía local'}
            ]),
            rutas_abastecimiento='Ruta 1: Municipio cercano (30 km). Ruta 2: Capital departamental (120 km)',
            vocerías=json.dumps([
                {'nombre': 'Alcalde', 'funciones': 'Comunicados generales', 'disponibilidad': '24/7'},
                {'nombre': 'Director UNGRD', 'funciones': 'Información operativa', 'disponibilidad': '24/7'}
            ]),
            canales_comunicacion=json.dumps(['Radio FM local', 'Televisión local', 'WhatsApp', 'Perifoneo']),
            formatos_boletines='Formato estandarizado con hora, lugar, acciones y próxima actualización',
            protocolos_salud='Primeros auxilios básicos, atención de traumas, vigilancia de enfermedades transmisibles',
            grupos_vulnerables='Niños, adultos mayores, personas con discapacidad, gestantes',
            kits_humanitarios=json.dumps({
                'contenido': ['Agua', 'Alimentos no perecederos', 'Botiquín', 'Ropa', 'Cobijas'],
                'ubicaciones': ['Coliseo municipal', 'Centro de salud', 'Cuartel de bomberos']
            }),
            presupuesto_total=50000000.00,
            presupuesto_por_fase=json.dumps({
                'preparacion': 10000000,
                'alistamiento': 5000000,
                'respuesta': 25000000,
                'rehabilitacion': 10000000
            }),
            fuentes_financiamiento='Presupuesto municipal (60%), Fondo de calamidad (40%)',
            instituciones_participantes=json.dumps([
                {'nombre': 'Defensa Civil', 'enlace': 'Capitán López', 'telefono': '3005678901'},
                {'nombre': 'Bomberos', 'enlace': 'Teniente Martínez', 'telefono': '3006789012'},
                {'nombre': 'Cruz Roja', 'enlace': 'Enfermera García', 'telefono': '3007890123'}
            ]),
            indicadores_activacion='Precipitación > 100mm en 24 horas. Desbordamiento de ríos. Reporte de deslizamientos activos.',
            cronograma_simulacros='Simulacro trimestral (marzo, junio, septiembre, diciembre)',
            lecciones_aprendidas='Mejorar comunicación inter-institucional. Aumentar capacitación de brigadas.'
        )
        
        db.session.add(plan)
        db.session.commit()
        
        print(f"✓ Plan de ejemplo creado con ID: {plan.id}")
        print(f"  Número de plan: {plan.numero_plan}")
        print(f"  Nombre: {plan.nombre_plan}")
        
        return plan.id

if __name__ == '__main__':
    plan_id = crear_plan_ejemplo()
    print(f"\n✓ Para probar el PDF, accede a: /api/contingencia/{plan_id}/pdf")
    sys.exit(0)
