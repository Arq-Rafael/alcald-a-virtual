#!/usr/bin/env python3
"""
Script de integración de datos catastrales 2026 con el módulo GeoPortal
Actualiza y sincroniza los datos de predios con el sistema
"""

import json
import os
import sys
import pandas as pd
from datetime import datetime
from pathlib import Path

# Agregar path de la app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def cargar_datos_catastro(json_path):
    """Carga datos del registro catastral 2026"""
    
    print(f"\n📂 Cargando datos catastrales de: {os.path.basename(json_path)}")
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Navegar la estructura
        if 'registro_catastral' in data:
            reg = data['registro_catastral']
            
            if 'predio' in reg:
                predio = reg['predio']
                
                # Convertir a DataFrame
                if isinstance(predio, dict):
                    # Un solo predio
                    df = pd.DataFrame([predio])
                elif isinstance(predio, list):
                    # Múltiples predios
                    df = pd.DataFrame(predio)
                else:
                    print("❌ Formato de predio no reconocido")
                    return None
                
                print(f"✅ Cargados {len(df)} predios")
                print(f"   Columnas: {list(df.columns)[:10]}")
                
                return df
        
        print("⚠️  Estructura catastral no encontrada")
        return None
        
    except Exception as e:
        print(f"❌ Error cargando datos: {e}")
        import traceback
        traceback.print_exc()
        return None


def validar_predios(df):
    """Valida calidad de datos de predios"""
    
    print(f"\n✔️  Validando {len(df)} predios...")
    
    # Campos críticos esperados
    campos_criticos = [
        'cedula_catastral', 'codigo_catastral', 'cc', 'cod_pred',
        'matricula', 'matricula_inmobiliaria', 'num_mat'
    ]
    
    # Buscar identificadores
    col_cc = None
    for campo in campos_criticos:
        if campo in df.columns:
            col_cc = campo
            break
    
    if not col_cc:
        print(f"⚠️  No se encontró columna de cédula catastral")
        print(f"   Columnas disponibles: {list(df.columns)}")
        col_cc = df.columns[0]  # Usar la primera columna
    
    print(f"   ID Catastral: {col_cc}")
    print(f"   Total predios: {len(df)}")
    print(f"   Predios sin ID: {df[col_cc].isna().sum()}")
    print(f"   Duplicados: {df[col_cc].duplicated().sum()}")
    
    # Muestreo
    print(f"\n   Muestra de datos (primeros 3):")
    for idx, row in df.head(3).iterrows():
        print(f"     [{idx}] CC: {row.get(col_cc, 'N/A')} - {list(row.values)[:5]}")
    
    return col_cc


def exportar_a_excel(df, output_path):
    """Exporta datos a Excel para integración"""
    
    print(f"\n💾 Exportando a Excel...")
    
    try:
        # Renombrar columnas a estándar
        rename_map = {
            'cedula_catastral': 'cc',
            'codigo_catastral': 'cc',
            'cod_pred': 'cc',
            'matricula_inmobiliaria': 'matricula',
            'num_mat': 'matricula'
        }
        
        df_export = df.rename(columns=rename_map)
        
        # Seleccionar columnas principales
        columnas = []
        for col in ['cc', 'matricula', 'uso', 'uso_predio', 'direccion', 'barrio', 'sector']:
            if col in df_export.columns:
                columnas.append(col)
        
        df_export = df_export[columnas] if columnas else df_export
        
        df_export.to_excel(output_path, index=False, sheet_name='Predios 2026')
        
        print(f"✅ Guardado: {output_path}")
        print(f"   Filas: {len(df_export)}")
        print(f"   Columnas: {len(df_export.columns)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error exportando a Excel: {e}")
        return False


def crear_geojson_optimizado(df, col_cc, output_path):
    """Crea GeoJSON optimizado para el visor 3D"""
    
    print(f"\n🗺️  Creando GeoJSON optimizado...")
    
    try:
        features = []
        
        for idx, row in df.iterrows():
            
            # Propiedades del predio
            props = {}
            for col in df.columns:
                val = row[col]
                # Convertir valores válidos
                if pd.notna(val):
                    if isinstance(val, (int, float)):
                        props[col] = val
                    else:
                        props[col] = str(val)
            
            # Crear feature con Point geometry (para inicio)
            feature = {
                "type": "Feature",
                "properties": props,
                "geometry": {
                    "type": "Point",
                    "coordinates": [0, 0]  # Placeholder, se actualizará con datos geoespaciales reales
                }
            }
            
            features.append(feature)
            
            if (idx + 1) % 100 == 0:
                print(f"  ✓ {idx + 1}/{len(df)}")
        
        # FeatureCollection
        geojson = {
            "type": "FeatureCollection",
            "crs": {
                "type": "name",
                "properties": {
                    "name": "EPSG:4326"  # WGS84
                }
            },
            "features": features,
            "metadata": {
                "source": "Registro Catastral Supatá 2026",
                "date": datetime.now().isoformat(),
                "total_features": len(features)
            }
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(geojson, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Guardado: {output_path}")
        print(f"   Features: {len(features)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creando GeoJSON: {e}")
        return False


def generar_reporte(df, col_cc):
    """Genera reporte de calidad de datos"""
    
    print(f"\n📊 REPORTE DE DATOS CATASTRALES 2026")
    print("="*60)
    
    print(f"\n📈 Estadísticas Generales:")
    print(f"   • Total de predios: {len(df)}")
    print(f"   • Columnas: {len(df.columns)}")
    
    # Cobertura de datos
    print(f"\n📉 Cobertura por Campo:")
    for col in df.columns[:10]:
        total = len(df)
        completos = df[col].notna().sum()
        pct = (completos / total * 100) if total > 0 else 0
        print(f"   • {col}: {pct:.1f}% ({completos}/{total})")
    
    print(f"\n✅ Datos listos para integración con GeoPortal")
    print(f"   Ver: /app/routes/usos.py -> cargar_df_predios()")
    
    return True


def main():
    
    print("\n" + "="*70)
    print("⚙️  INTEGRADOR DE DATOS CATASTRALES 2026")
    print("="*70)
    
    # Rutas
    input_json = r"C:\Users\rafa_\Downloads\AlcaldiaVirtualWeb\static\geojson\actualiziacion 2026\Registro_catastral_25777.json"
    output_excel = r"C:\Users\rafa_\Downloads\AlcaldiaVirtualWeb\datos\tabla_predios_2026_ACTUALIZADO.xlsx"
    output_geojson = r"C:\Users\rafa_\Downloads\AlcaldiaVirtualWeb\static\geojson\predios_2026_ACTUALIZADO.geojson"
    
    # Crear directorios si no existen
    os.makedirs(os.path.dirname(output_excel), exist_ok=True)
    os.makedirs(os.path.dirname(output_geojson), exist_ok=True)
    
    # 1. Cargar datos
    df = cargar_datos_catastro(input_json)
    if df is None or df.empty:
        print("❌ No se pudieron cargar los datos. Abortando.")
        return
    
    # 2. Validar
    col_cc = validar_predios(df)
    
    # 3. Exportar a Excel
    exportar_a_excel(df, output_excel)
    
    # 4. Generar GeoJSON
    crear_geojson_optimizado(df, col_cc, output_geojson)
    
    # 5. Reporte
    generar_reporte(df, col_cc)
    
    print(f"\n{'='*70}")
    print("🎉 PROCESO COMPLETADO")
    print(f"{'='*70}")
    print(f"\n📝 PRÓXIMOS PASOS:")
    print(f"1. Verificar datos en: {output_excel}")
    print(f"2. Actualizar tabla_predios.xlsx en app/datos/")
    print(f"3. Reiniciar la aplicación para cargar nuevos datos")
    print(f"4. El GeoPortal utilizará automáticamente los nuevos predios")


if __name__ == '__main__':
    main()
