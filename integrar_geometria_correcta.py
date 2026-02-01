#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
INTEGRACION AVANZADA CON GEOMETRIA CORRECTA
Usa geometría de predios.geojson (5337 MultiPolygons)
+ datos de actualización 2026
+ propiedades de usos_predial.geojson
"""

import json
import os
from typing import Dict, Any
import traceback

def main():
    print("\n" + "="*70)
    print("INTEGRACION AVANZADA CON GEOMETRIA CORRECTA")
    print("="*70 + "\n")
    
    geojson_path = r"C:\Users\rafa_\Downloads\AlcaldiaVirtualWeb\static\geojson"
    
    # Cargar archivos fuente
    print("[1/5] Cargando archivos fuente...")
    
    # Predios original con geometría
    with open(os.path.join(geojson_path, "predios.geojson"), 'r', encoding='utf-8') as f:
        predios_geojson = json.load(f)
    base_features = predios_geojson.get('features', [])
    print(f"      - predios.geojson: {len(base_features)} features con geometría MultiPolygon")
    
    # Usos predial con propiedades
    with open(os.path.join(geojson_path, "usos_predial.geojson.bak"), 'r', encoding='utf-8') as f:
        usos_data = json.load(f)
    usos_features = usos_data.get('features', [])
    print(f"      - usos_predial.geojson.bak: {len(usos_features)} features con propiedades")
    
    # Registro 2026
    actualizacion_path = os.path.join(geojson_path, "actualiziacion 2026")
    with open(os.path.join(actualizacion_path, "Registro_catastral_25777.json"), 'r', encoding='utf-8') as f:
        reg_data = json.load(f)
    nuevos_predios = reg_data['registro_catastral'].get('predio', [])
    print(f"      - Registro 2026: {len(nuevos_predios)} predios nuevos")
    
    # Indexar archivos para búsqueda rápida
    print("\n[2/5] Indexando datos...")
    
    # Índice de predios por FID (ID del shapefile)
    idx_predios_fid = {}
    for feat in base_features:
        props = feat.get('properties', {})
        fid = props.get('FID_Predia', props.get('OBJECTID'))
        if fid:
            idx_predios_fid[fid] = feat
    
    # Índice de usos
    idx_usos_cc = {}
    idx_usos_matricula = {}
    for feat in usos_features:
        props = feat.get('properties', {})
        cc = props.get('codigo_predial_nacional')
        matricula = props.get('matricula_inmobiliaria')
        if cc:
            idx_usos_cc[cc] = props
        if matricula:
            idx_usos_matricula[matricula] = props
    
    # Índice de 2026 por código
    idx_2026_cc = {}
    idx_2026_homo = {}
    for predio in nuevos_predios:
        cc = predio.get('codigo_predial_nacional')
        homo = predio.get('codigo_homologado')
        if cc:
            idx_2026_cc[cc] = predio
        if homo:
            idx_2026_homo[homo] = predio
    
    print(f"      - {len(idx_predios_fid)} predios indexados por FID")
    print(f"      - {len(idx_usos_cc)} usos indexados por código catastral")
    print(f"      - {len(idx_2026_cc)} registros 2026 por código")
    
    # Merge: usar geometría de predios + enriquecer con usos + actualizar con 2026
    print("\n[3/5] Realizando merge de datos (geometría + usos + 2026)...")
    
    merged_features = []
    matched_count = 0
    
    for feat in base_features:
        merged_feat = {
            'type': 'Feature',
            'geometry': feat.get('geometry'),  # Mantener MultiPolygon original
            'properties': {}
        }
        
        props = feat.get('properties', {})
        
        # Copiar propiedades originales
        merged_feat['properties'].update(props)
        
        # Intentar enriquecer con datos de usos
        cc = props.get('codigo_predial_nacional')
        
        if cc and cc in idx_usos_cc:
            uso_props = idx_usos_cc[cc]
            # Agregar campos de usos (destino_económico, área, etc)
            for key in ['codigo_homologado', 'matricula_inmobiliaria', 'direccion', 
                       'area_terreno', 'area_construida', 'destino_economico']:
                if key in uso_props:
                    merged_feat['properties'][key] = uso_props[key]
            matched_count += 1
        
        # Actualizar con datos 2026 si disponible
        if cc and cc in idx_2026_cc:
            registro_2026 = idx_2026_cc[cc]
            # Agregar datos 2026
            for key in ['condicion_predio', 'tipo_predio', 'tipo_derecho', 'avaluos_catastrales']:
                if key in registro_2026:
                    merged_feat['properties'][key] = registro_2026[key]
        
        merged_features.append(merged_feat)
    
    print(f"      - {matched_count}/{len(base_features)} features enriquecidos con datos de usos")
    print(f"      - Geometría: MultiPolygon")
    print(f"      - Total features en salida: {len(merged_features)}")
    
    # Crear FeatureCollection
    print("\n[4/5] Creando FeatureCollection...")
    output_geojson = {
        'type': 'FeatureCollection',
        'features': merged_features,
        'name': 'Catastro Municipal Supata 2026',
        'crs': {
            'type': 'name',
            'properties': {
                'name': 'EPSG:4326'
            }
        }
    }
    
    # Guardar
    print("\n[5/5] Guardando archivo...")
    output_path = os.path.join(geojson_path, "usos_predial.geojson")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_geojson, f, ensure_ascii=False, indent=1)
    
    size_mb = os.path.getsize(output_path) / (1024*1024)
    print(f"      - Archivo: usos_predial.geojson")
    print(f"      - Tamaño: {size_mb:.2f} MB")
    print(f"      - Features: {len(merged_features)}")
    
    # Verificar
    with open(output_path, 'r', encoding='utf-8') as f:
        verify = json.load(f)
    
    verify_features = verify.get('features', [])
    if verify_features:
        sample = verify_features[0]
        geom_type = sample['geometry']['type']
        props_keys = list(sample['properties'].keys())
        print(f"\n[VERIFICACION]")
        print(f"      - Tipo de geometría: {geom_type}")
        print(f"      - Propiedades por feature: {len(props_keys)}")
        print(f"      - Muestra de propiedades: {props_keys[:8]}")
    
    print("\n" + "="*70)
    print("INTEGRACION COMPLETADA EXITOSAMENTE")
    print("Archivo listo para visualizar en geoportal")
    print("="*70 + "\n")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("[EXITO] Archivo usos_predial.geojson actualizado")
        else:
            print("[ERROR] Integracion no completada")
    except Exception as e:
        print(f"\n[ERROR CRITICO] {e}")
        traceback.print_exc()
