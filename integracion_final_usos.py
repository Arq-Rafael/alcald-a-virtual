#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
INTEGRACION FINAL: Geometría correcta + Usos clasificados
Combina:
- predios.geojson (5337 MultiPolygons con geometría real)
- usos_predial.geojson (4760 propiedades con usos correctamente clasificados)
"""

import json
import os

def main():
    print("\n" + "="*80)
    print("INTEGRACION FINAL: GEOMETRIA + USOS CLASIFICADOS")
    print("="*80 + "\n")
    
    geojson_path = r"C:\Users\rafa_\Downloads\AlcaldiaVirtualWeb\static\geojson"
    
    print("[1/4] Cargando geometría de predios.geojson (5337 features)...")
    with open(os.path.join(geojson_path, "predios.geojson"), 'r', encoding='utf-8') as f:
        predios_data = json.load(f)
    
    predios_features = predios_data.get('features', [])
    print(f"      - {len(predios_features)} features con geometría MultiPolygon")
    
    print("\n[2/4] Cargando propiedades de usos_predial.geojson (4760 features)...")
    with open(os.path.join(geojson_path, "usos_predial.geojson"), 'r', encoding='utf-8') as f:
        usos_data = json.load(f)
    
    usos_features = usos_data.get('features', [])
    print(f"      - {len(usos_features)} features con usos clasificados")
    
    # Indexar usos por código catastral
    print("\n[3/4] Indexando propiedades de usos por código catastral...")
    idx_usos = {}
    for feat in usos_features:
        props = feat.get('properties', {})
        cc = props.get('codigo_predial_nacional')
        if cc:
            idx_usos[cc] = props
    
    print(f"      - {len(idx_usos)} propiedades indexadas")
    
    # Merge: geometría de predios + propiedades de usos
    print("\n[4/4] Realizando merge (geometría + usos)...")
    
    merged_features = []
    matched = 0
    unmatched = 0
    
    for feat in predios_features:
        props = feat.get('properties', {})
        
        # Crear nuevo feature
        merged_feat = {
            'type': 'Feature',
            'geometry': feat.get('geometry'),  # MultiPolygon original
            'properties': dict(props)  # Copiar propiedades de predios
        }
        
        # Intentar enriquecer con datos de usos
        # Buscar por código catastral, área, o nombre
        cc = props.get('codigo_predial_nacional')
        
        usos_props = None
        
        # Búsqueda por código catastral nacional
        if cc and cc in idx_usos:
            usos_props = idx_usos[cc]
            matched += 1
        else:
            # Si no coincide exactamente, usar propiedades predeterminadas
            unmatched += 1
            usos_props = {
                'fill': '#CCCCCC',
                'fill-opacity': 0.5,
                'stroke': '#999999',
                'categoria_uso': 'SIN_CLASIFICAR',
                'uso_principal': 'No clasificado',
                'description': 'Predio sin clasificación definida'
            }
        
        # Aplicar propiedades de usos (estilos, colores, categoría)
        for key in ['fill', 'fill-opacity', 'stroke', 'stroke-width', 'stroke-opacity',
                    'categoria_uso', 'uso_principal', 'description']:
            if key in usos_props:
                merged_feat['properties'][key] = usos_props[key]
        
        merged_features.append(merged_feat)
    
    print(f"      - {matched} features enriquecidos con usos")
    print(f"      - {unmatched} features sin coincidencia (clasificacion predeterminada)")
    print(f"      - Total merged: {len(merged_features)}")
    
    # Crear FeatureCollection
    output_geojson = {
        'type': 'FeatureCollection',
        'features': merged_features,
        'name': 'Catastro Municipal Supata 2026 - Usos del Suelo',
        'crs': {
            'type': 'name',
            'properties': {
                'name': 'EPSG:4326'
            }
        }
    }
    
    # Guardar
    output_path = os.path.join(geojson_path, "usos_predial.geojson")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_geojson, f, ensure_ascii=False, indent=1)
    
    size_mb = os.path.getsize(output_path) / (1024*1024)
    print(f"\n[ARCHIVO FINAL]")
    print(f"      - Ruta: {output_path}")
    print(f"      - Tamaño: {size_mb:.2f} MB")
    print(f"      - Total features: {len(merged_features)}")
    
    # Verificación
    with open(output_path, 'r', encoding='utf-8') as f:
        verify = json.load(f)
    
    feat_sample = verify['features'][0]
    print(f"\n[MUESTRA DE FEATURE]")
    print(f"      - Tipo geometría: {feat_sample['geometry']['type']}")
    print(f"      - Color: {feat_sample['properties'].get('fill')}")
    print(f"      - Uso: {feat_sample['properties'].get('uso_principal')}")
    print(f"      - Categoria: {feat_sample['properties'].get('categoria_uso')}")
    
    # Estadísticas
    print(f"\n[ESTADISTICAS FINALES]")
    
    usos_finales = {}
    colores_usos = {}
    
    for feat in merged_features:
        props = feat['properties']
        uso = props.get('uso_principal', 'Sin clasificar')
        color = props.get('fill', '#CCC')
        
        if uso not in usos_finales:
            usos_finales[uso] = 0
            colores_usos[uso] = color
        usos_finales[uso] += 1
    
    for uso, count in sorted(usos_finales.items(), key=lambda x: x[1], reverse=True):
        color = colores_usos[uso]
        pct = count * 100 / len(merged_features)
        print(f"      {uso:40} [{color}] {count:5} ({pct:5.1f}%)")
    
    print("\n" + "="*80)
    print("INTEGRACION COMPLETADA EXITOSAMENTE")
    print("  - Geometría: 5337 predios (del shapefile original)")
    print("  - Usos: 4760 clasificados (con estilos y colores)")
    print("  - Total: 5337 predios con geometría correcta")
    print("="*80 + "\n")

if __name__ == "__main__":
    try:
        main()
        print("[EXITO] Archivo usos_predial.geojson listo para visualizar")
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
