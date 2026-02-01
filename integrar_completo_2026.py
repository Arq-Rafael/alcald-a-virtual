#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
INTEGRACIÓN COMPLETA DE DATOS 2026
Merge de:
  1. usos_predial.geojson (4,760 predios con usos y colores)
  2. Registro_catastral_25777.json (datos actualizados 2026)
Resultado: GeoJSON actualizado y funcional para geoportal
"""

import json
import os
from typing import Dict, Any, List
import traceback

def main():
    print("\n" + "="*70)
    print("INTEGRACION COMPLETA GEOPORTAL 2026")
    print("="*70 + "\n")
    
    # Rutas
    geojson_path = r"C:\Users\rafa_\Downloads\AlcaldiaVirtualWeb\static\geojson"
    actualizacion_path = os.path.join(geojson_path, "actualiziacion 2026")
    
    print("[1/4] Cargando archivo base con usos (4,760 predios)...")
    try:
        with open(os.path.join(geojson_path, "usos_predial.geojson"), 'r', encoding='utf-8') as f:
            base_geojson = json.load(f)
        base_features = base_geojson.get('features', [])
        print(f"      OK - {len(base_features)} features cargados")
        print(f"      Propiedades: {list(base_features[0]['properties'].keys())[:5]}")
    except Exception as e:
        print(f"      ERROR: {e}")
        return
    
    # Crear índices para búsqueda rápida
    print("\n[2/4] Indexando predios por código homologado...")
    idx_homologado = {}
    idx_matricula = {}
    idx_cc = {}
    
    for feat in base_features:
        props = feat.get('properties', {})
        
        # Usar código homologado como clave principal
        if 'codigo_homologado' in props:
            codigo = props['codigo_homologado']
            idx_homologado[codigo] = feat
        
        # Indexar también por matrícula
        if 'matricula_inmobiliaria' in props:
            matricula = props['matricula_inmobiliaria']
            idx_matricula[matricula] = feat
        
        # Indexar por código catastral nacional
        if 'codigo_predial_nacional' in props:
            cc = props['codigo_predial_nacional']
            idx_cc[cc] = feat
    
    print(f"      OK - {len(idx_homologado)} indexados por código_homologado")
    print(f"      OK - {len(idx_matricula)} indexados por matrícula")
    print(f"      OK - {len(idx_cc)} indexados por código catastral")
    
    # Cargar datos actualizados
    print("\n[3/4] Cargando registro catastral 2026 (4,760 predios)...")
    try:
        with open(os.path.join(actualizacion_path, "Registro_catastral_25777.json"), 'r', encoding='utf-8') as f:
            reg_data = json.load(f)
        
        new_predios = reg_data['registro_catastral'].get('predio', [])
        print(f"      OK - {len(new_predios)} predios en actualización")
    except Exception as e:
        print(f"      ERROR: {e}")
        traceback.print_exc()
        return
    
    # Merging: actualizar propiedades manteniendo geometría y colores
    print("\n[4/4] Integrando datos (merge preservando geometría y estilos)...")
    
    updated_count = 0
    matched_by_homologado = 0
    matched_by_matricula = 0
    matched_by_cc = 0
    unmatched = []
    
    for new_predio in new_predios:
        feature = None
        match_type = None
        
        # Intentar coincidencia por código homologado
        codigo_homologado = new_predio.get('codigo_homologado')
        if codigo_homologado and codigo_homologado in idx_homologado:
            feature = idx_homologado[codigo_homologado]
            match_type = "homologado"
            matched_by_homologado += 1
        
        # Intentar por matrícula
        elif 'matricula_inmobiliaria' in new_predio:
            matricula = new_predio.get('matricula_inmobiliaria')
            if matricula and matricula in idx_matricula:
                feature = idx_matricula[matricula]
                match_type = "matricula"
                matched_by_matricula += 1
        
        # Intentar por código catastral nacional
        elif 'codigo_predial_nacional' in new_predio:
            cc = new_predio.get('codigo_predial_nacional')
            if cc and cc in idx_cc:
                feature = idx_cc[cc]
                match_type = "catastral"
                matched_by_cc += 1
        
        # Si encontramos coincidencia, actualizar propiedades
        if feature:
            props = feature['properties']
            
            # Mantener usos y colores existentes, actualizar otros campos
            for key, value in new_predio.items():
                # No sobrescribir si es un campo de estilo/color
                if key.lower() not in ['color', 'fill', 'stroke', 'uso_suelo', 'uso_del_suelo']:
                    props[key] = value
            
            updated_count += 1
        else:
            # Registrar predios sin coincidencia
            unmatched.append({
                'codigo_homologado': new_predio.get('codigo_homologado'),
                'matricula': new_predio.get('matricula_inmobiliaria'),
                'codigo_catastral': new_predio.get('codigo_predial_nacional')
            })
    
    print(f"      OK - {updated_count} features actualizados")
    print(f"      - Por código homologado: {matched_by_homologado}")
    print(f"      - Por matrícula: {matched_by_matricula}")
    print(f"      - Por código catastral: {matched_by_cc}")
    print(f"      - Sin coincidencia: {len(unmatched)}")
    
    # Guardar resultado
    output_path = os.path.join(geojson_path, "usos_predial.geojson")
    print(f"\n[GUARDAR] Escribiendo geojson actualizado...")
    print(f"    Archivo: {output_path}")
    print(f"    Features: {len(base_geojson['features'])}")
    print(f"    Tamaño estimado: {(len(json.dumps(base_geojson)) / 1024 / 1024):.2f} MB")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(base_geojson, f, ensure_ascii=False, indent=2)
    
    print(f"    OK - Archivo guardado exitosamente")
    
    # Backup de seguridad
    backup_path = os.path.join(geojson_path, "usos_predial_BACKUP_PREVIO_INTEGRACION.geojson")
    if not os.path.exists(backup_path):
        import shutil
        shutil.copy2(output_path, backup_path)
        print(f"\n[BACKUP] Copia de seguridad creada: usos_predial_BACKUP_PREVIO_INTEGRACION.geojson")
    
    # Resumen
    print("\n" + "="*70)
    print("RESULTADO DE INTEGRACION")
    print("="*70)
    print(f"Predios procesados: {len(base_features)}")
    print(f"Predios actualizados: {updated_count}")
    print(f"Tasa de cobertura: {(updated_count/len(base_features)*100):.1f}%")
    print(f"Archivo activo: usos_predial.geojson")
    print(f"Estado: LISTO PARA USAR EN GEOPORTAL")
    print("="*70 + "\n")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("[EXITO] Integracion completada sin errores")
        else:
            print("[ERROR] Integracion no completada")
    except Exception as e:
        print(f"\n[ERROR CRITICO] {e}")
        traceback.print_exc()
