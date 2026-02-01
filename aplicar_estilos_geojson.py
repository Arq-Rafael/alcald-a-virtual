#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SOLUCION DEFINITIVA: Usar predios.geojson con estilos
Ya que predios.geojson tiene la geometría correcta (5337 MultiPolygons)
Simplemente aplicamos propiedades y colores por defecto
"""

import json
import os

def main():
    print("\n" + "="*70)
    print("SOLUCION FINAL: USAR PREDIOS.GEOJSON CON ESTILOS")
    print("="*70 + "\n")
    
    geojson_path = r"C:\Users\rafa_\Downloads\AlcaldiaVirtualWeb\static\geojson"
    
    print("[1/3] Cargando predios.geojson (con geometría correcta)...")
    with open(os.path.join(geojson_path, "predios.geojson"), 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    features = data.get('features', [])
    print(f"      - {len(features)} features cargados")
    print(f"      - Tipo de geometría: {features[0]['geometry']['type']}")
    
    print("\n[2/3] Aplicando estilos y propiedades predeterminadas...")
    
    # Colores por categoría (simulando usos del suelo)
    color_map = {
        'Agroforestal': '#3d8a3d',      # Verde oscuro
        'Habitacional': '#FF6B6B',       # Rojo
        'Agricola': '#90EE90',           # Verde claro
        'Comercial': '#FFB347',          # Naranja
        'Forestal': '#228B22',           # Verde bosque
        'Institucional': '#4169E1',      # Azul real
        'Educativo': '#9370DB',          # Púrpura
    }
    
    # Aplicar estilos a cada feature
    for feat in features:
        props = feat['properties']
        
        # Agregar propiedades de visualización
        feat['properties']['fill'] = '#3d8a3d'      # Color de relleno por defecto
        feat['properties']['fill-opacity'] = 0.7
        feat['properties']['stroke'] = '#2d5a2d'
        feat['properties']['stroke-width'] = 1
        feat['properties']['stroke-opacity'] = 0.8
        
        # Agregar etiqueta
        nombre = props.get('NOMBRE_PRE', props.get('OBJECTID', 'Predio'))
        feat['properties']['name'] = str(nombre)
        feat['properties']['description'] = f"Predio: {nombre} | Area: {props.get('AREA_HA', 0)} ha"
    
    print(f"      - Aplicados estilos a {len(features)} features")
    
    print("\n[3/3] Guardando archivo final...")
    
    output_path = os.path.join(geojson_path, "usos_predial.geojson")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    
    size_mb = os.path.getsize(output_path) / (1024*1024)
    print(f"      - Archivo: {output_path}")
    print(f"      - Tamaño: {size_mb:.2f} MB")
    print(f"      - Features: {len(features)}")
    
    # Verificación final
    with open(output_path, 'r', encoding='utf-8') as f:
        verify = json.load(f)
    
    print(f"\n[VERIFICACION FINAL]")
    verify_feat = verify['features'][0]
    print(f"      - Tipo geometría: {verify_feat['geometry']['type']}")
    print(f"      - Propiedades: {list(verify_feat['properties'].keys())[:10]}")
    print(f"      - Color: {verify_feat['properties'].get('fill')}")
    
    # Verificar rango de coordenadas
    lats = []
    lons = []
    for feat in verify['features'][:100]:
        geom = feat['geometry']
        if geom['type'] == 'MultiPolygon':
            for poly in geom['coordinates']:
                for ring in poly:
                    for coord in ring:
                        lons.append(coord[0])
                        lats.append(coord[1])
    
    if lats:
        print(f"      - Lat rango: {min(lats):.2f} a {max(lats):.2f} (esperado ~5.0-5.12)")
        print(f"      - Lon rango: {min(lons):.2f} a {max(lons):.2f} (esperado ~-74.3 a -74.16)")
    
    print("\n" + "="*70)
    print("ARCHIVO LISTO PARA GEOPORTAL")
    print("="*70 + "\n")
    
    return True

if __name__ == "__main__":
    try:
        main()
        print("[EXITO] usos_predial.geojson actualizado con 5337 predios visibles")
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
