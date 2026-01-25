"""
Analizar estructura específica de tablas en SECOP I
"""
from bs4 import BeautifulSoup

with open('secop_sample.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

print("=== ANÁLISIS DETALLADO DE TABLAS ===\n")

tables = soup.find_all('table')

for idx, table in enumerate(tables):
    print(f"\n--- TABLA {idx+1} ---")
    
    # Buscar todas las filas
    rows = table.find_all('tr')
    print(f"Filas: {len(rows)}")
    
    # Mostrar primeras 3 filas
    for i, row in enumerate(rows[:3]):
        cells = row.find_all(['td', 'th'])
        if cells:
            textos = [c.get_text(strip=True)[:50] for c in cells]
            print(f"  Fila {i+1}: {textos}")
    
    # Buscar atributos de la tabla
    attrs = table.attrs
    if attrs:
        print(f"  Atributos: {attrs}")

print("\n\n=== BÚSQUEDA DE PATRONES ESPECÍFICOS ===\n")

# Buscar texto "Objeto a Contratar"
objeto_text = soup.find(string=lambda t: t and 'Objeto a Contratar' in t)
if objeto_text:
    print(f"✓ Encontrado: 'Objeto a Contratar'")
    parent = objeto_text.parent
    print(f"  Tag padre: {parent.name}")
    print(f"  Clase: {parent.get('class')}")
    siguiente = parent.find_next_sibling()
    if siguiente:
        print(f"  Siguiente hermano: {siguiente.name} - {siguiente.get_text(strip=True)[:100]}")
    
    # Buscar el valor en la misma fila
    row = parent.find_parent('tr')
    if row:
        cells = row.find_all('td')
        print(f"  Celdas en la fila: {len(cells)}")
        for i, cell in enumerate(cells):
            texto = cell.get_text(strip=True)
            if texto and texto != 'Objeto a Contratar':
                print(f"    TD {i+1}: {texto[:150]}")

print("\n\n=== BUSCAR LABELS/CAMPOS ===\n")

# Buscar todos los td que contienen texto con ":"
labels = soup.find_all('td', string=lambda t: t and ':' in t)
print(f"TDs con ':' encontrados: {len(labels)}")

for label in labels[:15]:
    texto = label.get_text(strip=True)
    siguiente_td = label.find_next_sibling('td')
    valor = siguiente_td.get_text(strip=True)[:80] if siguiente_td else "N/A"
    print(f"{texto} -> {valor}")
