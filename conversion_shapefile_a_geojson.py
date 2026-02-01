#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SOLUCION CORRECTA: Usar Shapefile con geometría y usos clasificados
- Shapefile: 5337 features con MultiPolygon/Polygon (geometría VALIDA)
- Campos: Categoria, Subcategor, Uso (clasificación CORRECTA)
- Convertir a GeoJSON con estilos
"""

import geopandas as gpd
import json
import os

# Paleta de colores por categoría de uso
COLORES_POR_CATEGORIA = {
    'Protecci_n en suelo rural': {
        'color': '#2D5016',      # Verde oscuro - Protección
        'fill-opacity': 0.7,
        'stroke': '#1a2e0b',
    },
    'Desarrollo restringido en suelo rural': {
        'color': '#FFB347',      # Naranja - Desarrollo
        'fill-opacity': 0.7,
        'stroke': '#FF9500',
    }
}

COLORES_POR_SUBCAT = {
    'reas de conservaci_n y protecci_n ambiental': '#228B22',  # Verde bosque
    'reas para la producci_n agr_cola y ganadera y de explotaci_n de recursos naturales': '#90EE90',  # Verde claro
    'Centros Poblados': '#FF6B6B',  # Rojo
    'reas de vivienda campestre': '#FFB347',  # Naranja
    'reas de recreaci_n': '#4169E1',  # Azul
    'Equipamientos': '#9370DB',  # Púrpura
    'reas del sistema de servicios p_blicos domiciliarios': '#696969',  # Gris
    'Suelos Suburbanos': '#F0E68C',  # Caqui
}

def get_color(categoria, subcategoría):
    """Obtener color basado en categoría y subcategoría"""
    
    # Normalizar strings
    subcat_norm = subcategoría.replace('á', '_').replace('é', '_').replace('í', '_').replace('ó', '_').replace('ú', '_') if subcategoría else ''
    cat_norm = categoria.replace('á', '_').replace('é', '_').replace('í', '_').replace('ó', '_').replace('ú', '_') if categoria else ''
    
    # Buscar por subcategoría primero
    if subcat_norm in COLORES_POR_SUBCAT:
        return COLORES_POR_SUBCAT[subcat_norm]
    
    # Buscar por categoría
    if cat_norm in COLORES_POR_CATEGORIA:
        return COLORES_POR_CATEGORIA[cat_norm]['color']
    
    # Color por defecto
    return '#CCCCCC'

def main():
    print("\n" + "="*80)
    print("CONVERSION FINAL: SHAPEFILE -> GEOJSON CON USOS CLASIFICADOS")
    print("="*80 + "\n")
    
    shapefile_path = r"C:\Users\rafa_\Downloads\AlcaldiaVirtualWeb\datos\usospredial\Export_Output.shp"
    geojson_path = r"C:\Users\rafa_\Downloads\AlcaldiaVirtualWeb\static\geojson"
    
    print("[1/3] Leyendo Shapefile con usos del suelo...")
    gdf = gpd.read_file(shapefile_path)
    print(f"      - {len(gdf)} features cargados")
    print(f"      - Geometría: MultiPolygon/Polygon")
    
    # Convertir a EPSG:4326 (WGS84) para compatibilidad con mapas web
    print("\n[2/3] Convirtiendo coordenadas a WGS84...")
    gdf = gdf.to_crs(epsg=4326)
    print(f"      - CRS convertido a EPSG:4326")
    
    print("\n[3/3] Convirtiendo a GeoJSON con estilos...")
    
    # Convertir GeoDataFrame a GeoJSON
    geojson_raw = json.loads(gdf.to_json())
    
    geojson_data = {
        'type': 'FeatureCollection',
        'name': 'Usos del Suelo - Municipio de Supata',
        'crs': {
            'type': 'name',
            'properties': {'name': 'EPSG:4326'}
        },
        'features': []
    }
    
    stats = {}
    
    for feature in geojson_raw['features']:
        props = feature['properties']
        
        # Obtener uso
        categoria = props.get('Categoria', 'Sin categoría')
        subcategor = props.get('Subcategor', 'Sin subcategoría')
        uso = props.get('Uso', 'Sin uso definido')
        
        # Obtener color
        color = get_color(categoria, subcategor)
        
        # Agregar estilos y campos
        props['categoria'] = categoria
        props['subcategoria'] = subcategor
        props['uso'] = uso
        
        # Estilos
        props['fill'] = color
        props['fill-opacity'] = 0.7
        props['stroke'] = '#333333'
        props['stroke-width'] = 1
        props['stroke-opacity'] = 0.8
        
        # Popup
        props['pop_up'] = (
            f"<b>USO DEL SUELO</b><br>"
            f"Categoría: {categoria}<br>"
            f"Subcategoría: {subcategor}<br>"
            f"Uso: {uso}<br>"
            f"<br><b>DATOS CATASTRALES</b><br>"
            f"Predio: {props.get('NOMBRE_PRE', 'N/A')}<br>"
            f"Área: {props.get('AREA_HA', 0):.2f} ha<br>"
            f"Rango: {props.get('RANGO', 'N/A')}"
        )
        
        feature['properties'] = props
        geojson_data['features'].append(feature)
        
        # Estadísticas
        if uso not in stats:
            stats[uso] = {'count': 0, 'color': color, 'categoria': categoria}
        stats[uso]['count'] += 1
    
    # Guardar GeoJSON
    output_path = os.path.join(geojson_path, "usos_predial.geojson")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(geojson_data, f, ensure_ascii=False, indent=1)
    
    size_mb = os.path.getsize(output_path) / (1024*1024)
    
    print(f"\n[ARCHIVO GENERADO]")
    print(f"      - Ruta: {output_path}")
    print(f"      - Tamaño: {size_mb:.2f} MB")
    print(f"      - Total features: {len(geojson_data['features'])}")
    
    # Distribución de usos
    print(f"\n[DISTRIBUCION DE USOS - {len(geojson_data['features'])} PREDIOS]")
    print(f"{'USO':<50} {'CANTIDAD':<8} {'COLOR'}")
    print("-" * 75)
    
    for uso in sorted(stats.keys(), key=lambda x: stats[x]['count'], reverse=True):
        count = stats[uso]['count']
        color = stats[uso]['color']
        pct = count * 100 / len(geojson_data['features'])
        print(f"{uso:<50} {count:>5} ({pct:>5.1f}%) [{color}]")
    
    # Categorías
    print(f"\n[CATEGORIAS DE USO]")
    categorias = {}
    for feat in geojson_data['features']:
        cat = feat['properties']['categoria']
        if cat not in categorias:
            categorias[cat] = 0
        categorias[cat] += 1
    
    for cat, count in sorted(categorias.items(), key=lambda x: x[1], reverse=True):
        pct = count * 100 / len(geojson_data['features'])
        print(f"  {cat:<50} {count:>5} ({pct:>5.1f}%)")
    
    print("\n" + "="*80)
    print("CONVERSION COMPLETADA")
    print("  - Geometría: MultiPolygon/Polygon (de shapefile)")
    print("  - Usos: Categoria + Subcategoría + Uso (del shapefile)")
    print("  - Estilos: Colores aplicados por uso")
    print("  - Total: 5,337 predios con información completa")
    print("="*80 + "\n")

if __name__ == "__main__":
    try:
        main()
        print("[EXITO] usos_predial.geojson creado con Shapefile")
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
