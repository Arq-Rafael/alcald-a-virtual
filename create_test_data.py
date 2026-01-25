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
    'secretaria': ['Ambiente', 'Planeación', 'Hacienda'],
    'objeto': [
        'Certificado de Uso del Suelo para proyecto residencial',
        'Certificado de Uso del Suelo para proyecto comercial',
        'Certificado de Uso del Suelo para proyecto industrial'
    ],
    'justificacion': [
        'Proyecto de vivienda de interés social',
        'Centro comercial en zona urbana',
        'Planta de procesamiento de alimentos'
    ],
    'valor': ['150000000', '250000000', '500000000'],
    'meta_producto': ['Viviendas construidas: 100', 'Empleos generados: 50', 'Empleos generados: 150'],
    'eje': ['Desarrollo social', 'Reactivación económica', 'Reactivación económica'],
    'sector': ['Vivienda', 'Comercio', 'Industria'],
    'codigo_bpim': ['3001', '3002', '3003'],
    'estado': ['nuevo', 'nuevo', 'nuevo']
}

df = pd.DataFrame(data)
df.to_csv('datos/solicitudes.csv', index=False, encoding='utf-8')

print("✅ Datos de prueba creados:")
print(f"Total: {len(df)} solicitudes")
print("\nContenido:")
print(df.to_string())
