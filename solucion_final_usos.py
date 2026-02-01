#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SOLUCION DEFINITIVA: Usar usos_predial.geojson.bak con estilos correctos
- Ya tiene geometría válida (Point)
- Ya tiene propiedades de usos correctamente clasificados
- Solo necesita colores y estilos aplicados
"""

import json
import os
import shutil

# Paleta de colores por uso principal
COLORES_USOS = {
    'Habitacional': {
        'color': '#FF6B6B',           # Rojo
        'fill-opacity': 0.75,
        'stroke': '#CC5555',
        'stroke-width': 2,
        'categoria': 'RESIDENCIAL'
    },
    'Comercial': {
        'color': '#FFB347',           # Naranja
        'fill-opacity': 0.75,
        'stroke': '#FF9500',
        'stroke-width': 2,
        'categoria': 'COMERCIAL'
    },
    'Agroforestal': {
        'color': '#2D5016',           # Verde oscuro
        'fill-opacity': 0.7,
        'stroke': '#1a2e0b',
        'stroke-width': 1,
        'categoria': 'AGRARIO'
    },
    'Agricola': {
        'color': '#90EE90',           # Verde claro
        'fill-opacity': 0.7,
        'stroke': '#7BC67B',
        'stroke-width': 1,
        'categoria': 'AGRARIO'
    },
    'Agropecuario': {
        'color': '#6BAA6B',           # Verde medio
        'fill-opacity': 0.7,
        'stroke': '#558A55',
        'stroke-width': 1,
        'categoria': 'AGRARIO'
    },
    'Agroindustrial': {
        'color': '#5B7C3F',           # Verde oliva
        'fill-opacity': 0.7,
        'stroke': '#4a6530',
        'stroke-width': 1,
        'categoria': 'AGRARIO'
    },
    'Forestal': {
        'color': '#228B22',           # Verde bosque
        'fill-opacity': 0.7,
        'stroke': '#1a6b1a',
        'stroke-width': 1,
        'categoria': 'AMBIENTAL'
    },
    'Educativo': {
        'color': '#9370DB',           # Púrpura
        'fill-opacity': 0.75,
        'stroke': '#7B5BB8',
        'stroke-width': 2,
        'categoria': 'INSTITUCIONAL'
    },
    'Institucional': {
        'color': '#4169E1',           # Azul real
        'fill-opacity': 0.75,
        'stroke': '#3050C8',
        'stroke-width': 2,
        'categoria': 'INSTITUCIONAL'
    },
    'Religioso': {
        'color': '#9932CC',           # Púrpura oscuro
        'fill-opacity': 0.75,
        'stroke': '#7A28A8',
        'stroke-width': 2,
        'categoria': 'INSTITUCIONAL'
    },
    'Uso_Publico': {
        'color': '#FFD700',           # Oro
        'fill-opacity': 0.75,
        'stroke': '#DAA520',
        'stroke-width': 2,
        'categoria': 'PUBLICO'
    },
    'Infraestructura_Transporte': {
        'color': '#696969',           # Gris
        'fill-opacity': 0.7,
        'stroke': '#505050',
        'stroke-width': 2,
        'categoria': 'INFRAESTRUCTURA'
    },
    'Lote_Urbanizado_No_Construido': {
        'color': '#F0E68C',           # Caqui claro
        'fill-opacity': 0.6,
        'stroke': '#DAA520',
        'stroke-width': 1,
        'categoria': 'URBANO'
    },
    'Lote_Urbanizable_No_Urbanizado': {
        'color': '#F5DEB3',           # Trigo
        'fill-opacity': 0.6,
        'stroke': '#D2B48C',
        'stroke-width': 1,
        'categoria': 'URBANIZABLE'
    },
    'Lote_No_Urbanizable': {
        'color': '#D2B48C',           # Bronceado
        'fill-opacity': 0.6,
        'stroke': '#A0826D',
        'stroke-width': 1,
        'categoria': 'PROTEGIDO'
    }
}

def main():
    print("\n" + "="*80)
    print("SOLUCION FINAL: USOS DEL SUELO CON CLASIFICACION Y COLORES")
    print("="*80 + "\n")
    
    geojson_path = r"C:\Users\rafa_\Downloads\AlcaldiaVirtualWeb\static\geojson"
    
    print("[1/3] Cargando usos_predial.geojson.bak (4760 predios con propiedades correctas)...")
    backup_path = os.path.join(geojson_path, "usos_predial.geojson.bak")
    
    with open(backup_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    features = data.get('features', [])
    print(f"      - Cargados {len(features)} features")
    
    print("\n[2/3] Aplicando clasificación, estilos y colores...")
    
    stats = {}
    error_count = 0
    
    for feat in features:
        props = feat['properties']
        
        # Obtener uso principal
        destino = props.get('destino_economico', 'Sin categoria')
        tipo_predio = props.get('tipo_predio', 'Indefinido')
        
        # Obtener información de estilo
        estilo = COLORES_USOS.get(destino, {
            'color': '#CCCCCC',
            'fill-opacity': 0.5,
            'stroke': '#999999',
            'stroke-width': 1,
            'categoria': 'SIN_CLASIFICAR'
        })
        
        # Aplicar estilos
        feat['properties']['fill'] = estilo['color']
        feat['properties']['fill-opacity'] = estilo['fill-opacity']
        feat['properties']['stroke'] = estilo['stroke']
        feat['properties']['stroke-width'] = estilo.get('stroke-width', 1)
        feat['properties']['stroke-opacity'] = 0.8
        
        # Agregar categorización
        feat['properties']['categoria'] = estilo['categoria']
        feat['properties']['uso'] = destino
        feat['properties']['tipo'] = tipo_predio
        
        # Crear descripción visual
        area_terreno = props.get('area_terreno', 0)
        area_construida = props.get('area_construida', 0)
        matricula = props.get('matricula_inmobiliaria', 'N/A')
        direccion = props.get('direccion', 'N/A')
        
        feat['properties']['pop_up'] = (
            f"<b>USO DEL SUELO</b><br>"
            f"Categoria: {destino}<br>"
            f"Tipo: {tipo_predio}<br>"
            f"---<br>"
            f"Matricula: {matricula}<br>"
            f"Direccion: {direccion}<br>"
            f"---<br>"
            f"Area Terreno: {area_terreno} m2<br>"
            f"Area Construida: {area_construida} m2"
        )
        
        # Estadísticas
        if destino not in stats:
            stats[destino] = {'count': 0, 'color': estilo['color'], 'categoria': estilo['categoria']}
        stats[destino]['count'] += 1
    
    print(f"      - Aplicados estilos a {len(features)} features")
    
    # Guardar
    print("\n[3/3] Guardando archivo actualizado...")
    
    output_path = os.path.join(geojson_path, "usos_predial.geojson")
    
    # Hacer backup del anterior
    if os.path.exists(output_path):
        backup_anterior = os.path.join(geojson_path, "usos_predial_anterior.geojson")
        shutil.copy2(output_path, backup_anterior)
        print(f"      - Backup anterior guardado: usos_predial_anterior.geojson")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    
    size_mb = os.path.getsize(output_path) / (1024*1024)
    print(f"      - Archivo: {output_path}")
    print(f"      - Tamaño: {size_mb:.2f} MB")
    print(f"      - Features: {len(features)}")
    
    # Mostrar distribución
    print(f"\n[DISTRIBUCION DE USOS - PREDIOS: {len(features)}]")
    print(f"{'USO':<40} {'COLOR':<10} {'CANTIDAD':<8} {'CATEGORIA'}")
    print("-" * 75)
    
    for uso in sorted(stats.keys(), key=lambda x: stats[x]['count'], reverse=True):
        count = stats[uso]['count']
        color = stats[uso]['color']
        categoria = stats[uso]['categoria']
        pct = count * 100 / len(features)
        print(f"{uso:<40} [{color:<7}] {count:>5} ({pct:>5.1f}%) - {categoria}")
    
    # Crear leyenda HTML
    print(f"\n[CREANDO LEYENDA INTERACTIVA]")
    
    leyenda_html = """
    <html>
    <head>
        <title>Leyenda de Usos del Suelo - Supata</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5; }
            .legend { max-width: 600px; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
            h1 { color: #333; text-align: center; }
            .legend-item { display: flex; align-items: center; margin: 10px 0; padding: 8px; border-left: 4px solid #ddd; }
            .color-box { width: 30px; height: 30px; margin-right: 15px; border: 1px solid #999; border-radius: 3px; }
            .legend-text { flex: 1; }
            .legend-text strong { display: block; color: #333; }
            .legend-text span { color: #666; font-size: 0.9em; }
            .category { color: #0066cc; font-size: 0.85em; font-weight: bold; }
            .total { text-align: center; margin-top: 20px; padding-top: 20px; border-top: 2px solid #ddd; color: #666; }
        </style>
    </head>
    <body>
        <div class="legend">
            <h1>Usos del Suelo - Municipio de Supata (2026)</h1>
    """
    
    for uso in sorted(stats.keys(), key=lambda x: stats[x]['count'], reverse=True):
        count = stats[uso]['count']
        color = stats[uso]['color']
        categoria = stats[uso]['categoria']
        pct = count * 100 / len(features)
        
        leyenda_html += f"""
            <div class="legend-item">
                <div class="color-box" style="background-color: {color};"></div>
                <div class="legend-text">
                    <strong>{uso}</strong>
                    <span>{count} predios ({pct:.1f}%)</span>
                    <span class="category">{categoria}</span>
                </div>
            </div>
        """
    
    leyenda_html += f"""
            <div class="total">
                <strong>Total de Predios: {len(features)}</strong><br>
                <span>Actualizado: 2026-01-31</span>
            </div>
        </div>
    </body>
    </html>
    """
    
    leyenda_path = os.path.join(geojson_path, "leyenda_usos.html")
    with open(leyenda_path, 'w', encoding='utf-8') as f:
        f.write(leyenda_html)
    
    print(f"      - Leyenda HTML: leyenda_usos.html")
    
    print("\n" + "="*80)
    print("ACTUALIZACION COMPLETADA")
    print("  - Predios: 4,760 (con usos clasificados correctamente)")
    print("  - Usos: 15 categorias diferenciadas")
    print("  - Colores: Asignados por uso principal")
    print("  - Estilos: Fill, stroke, opacidad, popup aplicados")
    print("="*80 + "\n")

if __name__ == "__main__":
    try:
        main()
        print("[EXITO] usos_predial.geojson actualizado con usos clasificados")
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
