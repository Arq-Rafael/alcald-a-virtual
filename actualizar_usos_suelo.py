#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ACTUALIZACION CORRECTA DE USOS DEL SUELO
Clasifica por:
- destino_economico (USO PRINCIPAL)
- tipo_predio (URBANO/RURAL)
- condicion_predio (NPH, PH, etc)

Con colores y estilos apropiados
"""

import json
import os

# Paleta de colores por uso principal
COLORES_USOS = {
    'Habitacional': {
        'color': '#FF6B6B',           # Rojo
        'fill-opacity': 0.7,
        'stroke': '#CC5555',
        'categoria': 'USO_RESIDENCIAL'
    },
    'Comercial': {
        'color': '#FFB347',           # Naranja
        'fill-opacity': 0.7,
        'stroke': '#FF9500',
        'categoria': 'USO_COMERCIAL'
    },
    'Agroforestal': {
        'color': '#2D5016',           # Verde oscuro
        'fill-opacity': 0.7,
        'stroke': '#1a2e0b',
        'categoria': 'USO_AGRARIO'
    },
    'Agricola': {
        'color': '#90EE90',           # Verde claro
        'fill-opacity': 0.7,
        'stroke': '#7BC67B',
        'categoria': 'USO_AGRARIO'
    },
    'Agropecuario': {
        'color': '#6BAA6B',           # Verde medio
        'fill-opacity': 0.7,
        'stroke': '#558A55',
        'categoria': 'USO_AGRARIO'
    },
    'Agroindustrial': {
        'color': '#5B7C3F',           # Verde oliva
        'fill-opacity': 0.7,
        'stroke': '#4a6530',
        'categoria': 'USO_AGRARIO'
    },
    'Forestal': {
        'color': '#228B22',           # Verde bosque
        'fill-opacity': 0.7,
        'stroke': '#1a6b1a',
        'categoria': 'USO_AMBIENTAL'
    },
    'Educativo': {
        'color': '#9370DB',           # Púrpura
        'fill-opacity': 0.7,
        'stroke': '#7B5BB8',
        'categoria': 'USO_INSTITUCIONAL'
    },
    'Institucional': {
        'color': '#4169E1',           # Azul real
        'fill-opacity': 0.7,
        'stroke': '#3050C8',
        'categoria': 'USO_INSTITUCIONAL'
    },
    'Religioso': {
        'color': '#9932CC',           # Púrpura oscuro
        'fill-opacity': 0.7,
        'stroke': '#7A28A8',
        'categoria': 'USO_INSTITUCIONAL'
    },
    'Uso_Publico': {
        'color': '#FFD700',           # Oro
        'fill-opacity': 0.7,
        'stroke': '#DAA520',
        'categoria': 'USO_PUBLICO'
    },
    'Infraestructura_Transporte': {
        'color': '#696969',           # Gris
        'fill-opacity': 0.7,
        'stroke': '#505050',
        'categoria': 'USO_INFRAESTRUCTURA'
    },
    'Lote_Urbanizado_No_Construido': {
        'color': '#F0E68C',           # Caqui claro
        'fill-opacity': 0.6,
        'stroke': '#DAA520',
        'categoria': 'SUELO_URBANO'
    },
    'Lote_Urbanizable_No_Urbanizado': {
        'color': '#F5DEB3',           # Trigo
        'fill-opacity': 0.6,
        'stroke': '#D2B48C',
        'categoria': 'SUELO_URBANIZABLE'
    },
    'Lote_No_Urbanizable': {
        'color': '#D2B48C',           # Bronceado
        'fill-opacity': 0.6,
        'stroke': '#A0826D',
        'categoria': 'SUELO_PROTEGIDO'
    }
}

def main():
    print("\n" + "="*80)
    print("ACTUALIZACION DE USOS DEL SUELO CON CLASIFICACION CORRECTA")
    print("="*80 + "\n")
    
    geojson_path = r"C:\Users\rafa_\Downloads\AlcaldiaVirtualWeb\static\geojson"
    
    print("[1/3] Cargando datos con propiedades de usos correcto...")
    with open(os.path.join(geojson_path, "usos_predial.geojson.bak"), 'r', encoding='utf-8') as f:
        usos_data = json.load(f)
    
    features = usos_data.get('features', [])
    print(f"      - Cargados {len(features)} features con propiedades de usos")
    
    print("\n[2/3] Aplicando clasificación, estilos y colores...")
    
    stats = {}
    
    for feat in features:
        props = feat['properties']
        
        # Obtener uso principal
        destino = props.get('destino_economico', 'Sin categoria')
        
        # Obtener información de estilo
        estilo = COLORES_USOS.get(destino, {
            'color': '#CCCCCC',
            'fill-opacity': 0.5,
            'stroke': '#999999',
            'categoria': 'SIN_CLASIFICAR'
        })
        
        # Aplicar estilos
        feat['properties']['fill'] = estilo['color']
        feat['properties']['fill-opacity'] = estilo['fill-opacity']
        feat['properties']['stroke'] = estilo['stroke']
        feat['properties']['stroke-width'] = 1
        feat['properties']['stroke-opacity'] = 0.8
        
        # Agregar categorización
        feat['properties']['categoria_uso'] = estilo['categoria']
        feat['properties']['uso_principal'] = destino
        
        # Agregar descripción
        tipo_predio = props.get('tipo_predio', 'Indefinido')
        condicion = props.get('condicion_predio', 'N/A')
        area_terreno = props.get('area_terreno', 0)
        area_construida = props.get('area_construida', 0)
        
        feat['properties']['description'] = (
            f"USO: {destino}\n"
            f"TIPO: {tipo_predio}\n"
            f"CONDICION: {condicion}\n"
            f"AREA TERRENO: {area_terreno} m2\n"
            f"AREA CONSTRUIDA: {area_construida} m2"
        )
        
        # Estadísticas
        if destino not in stats:
            stats[destino] = 0
        stats[destino] += 1
    
    print(f"      - Aplicados estilos a {len(features)} features")
    
    # Mostrar distribución
    print(f"\n[DISTRIBUCION DE USOS]")
    for uso, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
        estilo = COLORES_USOS.get(uso, {})
        color = estilo.get('color', '#CCC')
        categoria = estilo.get('categoria', 'SIN_CLASIFICAR')
        print(f"  {uso:40} [{color}] {count:5} predios - {categoria}")
    
    print("\n[3/3] Guardando archivo actualizado...")
    
    output_path = os.path.join(geojson_path, "usos_predial.geojson")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(usos_data, f, ensure_ascii=False, indent=1)
    
    size_mb = os.path.getsize(output_path) / (1024*1024)
    print(f"      - Archivo: {output_path}")
    print(f"      - Tamaño: {size_mb:.2f} MB")
    print(f"      - Features: {len(features)}")
    
    # Crear archivo de leyenda
    print("\n[CREANDO LEYENDA DE COLORES]")
    leyenda = {
        'titulo': 'Usos del Suelo - Municipio de Supata',
        'fecha': '2026-01-31',
        'total_predios': len(features),
        'colores': {}
    }
    
    for uso, count in sorted(stats.items()):
        estilo = COLORES_USOS.get(uso, {})
        leyenda['colores'][uso] = {
            'color': estilo.get('color'),
            'categoria': estilo.get('categoria'),
            'cantidad': count,
            'porcentaje': round(count * 100 / len(features), 1)
        }
    
    leyenda_path = os.path.join(geojson_path, "leyenda_usos.json")
    with open(leyenda_path, 'w', encoding='utf-8') as f:
        json.dump(leyenda, f, ensure_ascii=False, indent=2)
    
    print(f"      - Leyenda guardada: leyenda_usos.json")
    
    print("\n" + "="*80)
    print("ACTUALIZACION COMPLETADA")
    print("  - Clasificacion: Uso principal + Tipo predio + Condicion")
    print("  - Colores: 15 categorias diferenciadas")
    print("  - Estilos: Fill, stroke, opacidad aplicados")
    print("="*80 + "\n")

if __name__ == "__main__":
    try:
        main()
        print("[EXITO] Usos del suelo actualizados correctamente")
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
