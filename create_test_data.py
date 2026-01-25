#!/usr/bin/env python
"""Script para crear datos de prueba en solicitudes.csv"""
import pandas as pd
from datetime import datetime
import os

# Cambiar a directorio del proyecto
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Crear datos de prueba
data = {
    'municipio': ['Zipaquirá', 'Cajicá', 'Ubaté'],
    'nit': ['890123456-7', '890234567-8', '890345678-9'],
    'fecha': [datetime.now().strftime('%Y-%m-%d')] * 3,
    'secretaria': ['Planeación', 'Planeación', 'Hacienda'],
    'objeto': [
        'Certificado del Banco de Programas y Proyectos: Modernización de alumbrado público',
        'Certificado del Banco de Programas y Proyectos: Mejoramiento de vías terciarias',
        'Certificado del Banco de Programas y Proyectos: Adecuación de infraestructura educativa'
    ],
    'justificacion': [
        'Proyecto priorizado del Plan de Desarrollo Municipal para eficiencia energética',
        'Intervención vial alineada con el plan de movilidad rural',
        'Adecuación de sedes educativas según metas de calidad y cobertura'
    ],
    'valor': ['75000000', '180000000', '220000000'],
    'meta_producto': [
        'Puntos de luz LED instalados: 350',
        'Kilómetros de vía mejorada: 12',
        'Aulas intervenidas: 18'
    ],
    'eje': ['Gobierno y gestión', 'Competitividad y desarrollo', 'Bienestar social'],
    'sector': ['Servicios públicos', 'Transporte', 'Educación'],
    'codigo_bpim': ['BPIM-001', 'BPIM-002', 'BPIM-003'],
    'estado': ['nuevo', 'nuevo', 'nuevo']
}

df = pd.DataFrame(data)
df.to_csv('datos/solicitudes.csv', index=False, encoding='utf-8')

print("✅ Datos de prueba creados:")
print(f"Total: {len(df)} solicitudes")
print("\nContenido:")
print(df.to_string())
