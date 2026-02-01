#!/usr/bin/env python3
"""
Script para convertir y optimizar archivos GeoJSON del catastro 2026
"""

import json
import os
from pathlib import Path

def inspeccionar_estructura(filepath):
    """Inspecciona la estructura real del archivo"""
    
    print(f"\n🔍 Inspeccionando estructura...")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"Tipo raíz: {type(data).__name__}")
        
        if isinstance(data, dict):
            keys = list(data.keys())
            print(f"Claves principales: {keys[:10]}")
            
            # Si es un dict con claves numéricas o propiedades
            for key in keys[:3]:
                val = data[key]
                print(f"\n  [{key}]: {type(val).__name__}")
                if isinstance(val, dict):
                    print(f"    Propiedades: {list(val.keys())[:8]}")
                elif isinstance(val, list):
                    print(f"    Elementos: {len(val)}")
                    if val and isinstance(val[0], dict):
                        print(f"    Primer elemento: {list(val[0].keys())[:5]}")
        
        elif isinstance(data, list):
            print(f"Total elementos: {len(data)}")
            if data:
                print(f"Tipo del primer elemento: {type(data[0]).__name__}")
                if isinstance(data[0], dict):
                    print(f"Propiedades: {list(data[0].keys())[:10]}")
        
        return data
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def convertir_a_geojson(datos_originales, output_path):
    """Convierte datos al formato GeoJSON estándar"""
    
    print(f"\n🔄 Convertiendo a GeoJSON...")
    
    features = []
    
    try:
        # Si es un dict con propiedades
        if isinstance(datos_originales, dict) and not 'type' in datos_originales:
            # Podría ser datos_originales['features'] o lista de predios
            
            # Intentar obtener features
            if 'features' in datos_originales:
                datos_list = datos_originales['features']
            elif 'data' in datos_originales:
                datos_list = datos_originales['data']
            else:
                # Asumir que cada valor es un predio
                datos_list = list(datos_originales.values())
        
        elif isinstance(datos_originales, list):
            datos_list = datos_originales
        
        else:
            print("⚠️  Formato no reconocido")
            return False
        
        print(f"Procesando {len(datos_list)} registros...")
        
        # Convertir cada predio a feature GeoJSON
        for idx, predio in enumerate(datos_list):
            
            if not isinstance(predio, dict):
                continue
            
            # Extraer coordenadas si existen
            coords = None
            geometry = None
            
            # Buscar coordenadas en diferentes formatos
            coord_keys = ['geometry', 'coordinates', 'coord', 'coords', 'lat', 'lon', 'latitude', 'longitude']
            
            for key in coord_keys:
                if key in predio:
                    val = predio[key]
                    if key == 'geometry' and isinstance(val, dict):
                        geometry = val
                        break
                    elif isinstance(val, (list, tuple)) and len(val) >= 2:
                        if isinstance(val[0], (int, float)):
                            coords = [val[1], val[0]]  # [lon, lat]
                        break
            
            # Si no hay geometry pero sí coordenadas
            if not geometry and coords:
                geometry = {
                    "type": "Point",
                    "coordinates": coords
                }
            
            # Si no hay geometry, crear polygon vacío
            if not geometry:
                geometry = {
                    "type": "Polygon",
                    "coordinates": []
                }
            
            # Crear feature
            feature = {
                "type": "Feature",
                "properties": {k: v for k, v in predio.items() if k not in ['geometry', 'coordinates']},
                "geometry": geometry
            }
            
            features.append(feature)
            
            if (idx + 1) % 100 == 0:
                print(f"  ✓ {idx + 1}/{len(datos_list)}")
        
        # Crear FeatureCollection
        geojson = {
            "type": "FeatureCollection",
            "features": features
        }
        
        # Guardar
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(geojson, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Guardado: {output_path}")
        print(f"   Features: {len(features)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en conversión: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    input_file = r"C:\Users\rafa_\Downloads\AlcaldiaVirtualWeb\static\geojson\actualiziacion 2026\Registro_catastral_25777.json"
    output_file = r"C:\Users\rafa_\Downloads\AlcaldiaVirtualWeb\static\geojson\predios_2026.geojson"
    
    print("\n" + "="*70)
    print("CONVERTIDOR DE CATASTRO A GEOJSON - 2026")
    print("="*70)
    
    if not os.path.exists(input_file):
        print(f"❌ Archivo no encontrado: {input_file}")
        return
    
    # Inspeccionar
    datos = inspeccionar_estructura(input_file)
    
    if datos:
        # Convertir
        convertir_a_geojson(datos, output_file)


if __name__ == '__main__':
    main()
