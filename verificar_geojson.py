#!/usr/bin/env python3
"""
Script para verificar y validar archivos GeoJSON del catastro 2026
"""

import json
import os
from pathlib import Path

def verificar_geojson(filepath):
    """Verifica estructura y validez de un archivo GeoJSON"""
    
    print(f"\n{'='*70}")
    print(f"Verificando: {os.path.basename(filepath)}")
    print(f"{'='*70}")
    
    if not os.path.exists(filepath):
        print(f"❌ ARCHIVO NO ENCONTRADO: {filepath}")
        return False
    
    # Tamaño
    size_mb = os.path.getsize(filepath) / (1024 * 1024)
    print(f"📦 Tamaño: {size_mb:.2f} MB")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validar estructura GeoJSON
        if not isinstance(data, dict):
            print(f"❌ Estructura inválida: debe ser JSON object")
            return False
        
        print(f"✅ JSON válido")
        
        # Verificar type
        geo_type = data.get('type', 'unknown')
        print(f"📋 Type: {geo_type}")
        
        # Si es FeatureCollection
        if geo_type == 'FeatureCollection':
            features = data.get('features', [])
            print(f"📍 Total Features: {len(features)}")
            
            if features:
                first_feat = features[0]
                print(f"\n🔍 Primer Feature:")
                print(f"   - Type: {first_feat.get('type')}")
                
                if 'properties' in first_feat:
                    props = first_feat['properties']
                    print(f"   - Propiedades ({len(props)}): {list(props.keys())[:10]}")
                    
                    # Mostrar algunos valores
                    for key in list(props.keys())[:5]:
                        val = props[key]
                        if isinstance(val, str):
                            val_display = val[:50] + ('...' if len(val) > 50 else '')
                        else:
                            val_display = str(val)[:50]
                        print(f"     • {key}: {val_display}")
                
                if 'geometry' in first_feat:
                    geom = first_feat['geometry']
                    print(f"   - Geometry type: {geom.get('type')}")
                    if geom.get('coordinates'):
                        print(f"   - Coordinates: {len(geom['coordinates'])} elementos")
            
            # Estadísticas básicas
            print(f"\n📊 Estadísticas:")
            
            # Contar por tipo de geometría
            geom_types = {}
            for feat in features:
                gtype = feat.get('geometry', {}).get('type', 'unknown')
                geom_types[gtype] = geom_types.get(gtype, 0) + 1
            
            for gtype, count in geom_types.items():
                print(f"   - {gtype}: {count}")
            
            return True
        
        else:
            print(f"⚠️  No es FeatureCollection (type={geo_type})")
            return False
            
    except json.JSONDecodeError as e:
        print(f"❌ ERROR JSON: {e}")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def main():
    base_path = r"C:\Users\rafa_\Downloads\AlcaldiaVirtualWeb\static\geojson\actualiziacion 2026"
    
    print("\n" + "="*70)
    print("VALIDACIÓN DE ARCHIVOS GEOJSON - CATASTRO 2026")
    print("="*70)
    
    # Listar archivos
    if os.path.exists(base_path):
        archivos = [f for f in os.listdir(base_path) if f.endswith('.json') or f.endswith('.geojson')]
        print(f"\n📂 Archivos encontrados en {base_path}:")
        for arch in archivos:
            full_path = os.path.join(base_path, arch)
            size_mb = os.path.getsize(full_path) / (1024 * 1024)
            print(f"   • {arch} ({size_mb:.2f} MB)")
        
        # Verificar cada archivo
        resultados = {}
        for arch in archivos:
            full_path = os.path.join(base_path, arch)
            resultados[arch] = verificar_geojson(full_path)
        
        # Resumen
        print(f"\n{'='*70}")
        print("RESUMEN")
        print(f"{'='*70}")
        for arch, valido in resultados.items():
            estado = "✅ VÁLIDO" if valido else "❌ INVÁLIDO"
            print(f"{estado}: {arch}")
    
    else:
        print(f"❌ Carpeta no encontrada: {base_path}")


if __name__ == '__main__':
    main()
