import pandas as pd
import os

excel_path = r"C:\Users\rafa_\Downloads\AlcaldiaVirtualWeb\documentos_generados\plan de desarollo\BASE_RENDICION_PLAN_DESARROLLO_SUPATA.xlsx"

print("=" * 80)
print("INSPECCIÓN DEL EXCEL DEL PLAN DE DESARROLLO")
print("=" * 80)

# Leer todas las hojas
excel_file = pd.ExcelFile(excel_path)
print(f"\n📋 HOJAS DISPONIBLES: {excel_file.sheet_names}\n")

# Inspeccionar cada hoja
for sheet_name in excel_file.sheet_names:
    print("\n" + "=" * 80)
    print(f"📄 HOJA: {sheet_name}")
    print("=" * 80)
    
    try:
        df = pd.read_excel(excel_path, sheet_name=sheet_name, header=0)
        
        print(f"\n✓ Dimensiones: {df.shape[0]} filas x {df.shape[1]} columnas")
        print(f"\n✓ Columnas disponibles:")
        for i, col in enumerate(df.columns, 1):
            print(f"   {i:2d}. {col}")
        
        print(f"\n✓ Primeras 3 filas:")
        print(df.head(3).to_string())
        
        # Si tiene columna de año, mostrar años únicos
        for col in df.columns:
            if 'AÑO' in str(col).upper() or 'ANO' in str(col).upper() or 'YEAR' in str(col).upper():
                anos_unicos = df[col].dropna().unique()
                print(f"\n✓ Años encontrados en '{col}': {sorted(anos_unicos.tolist()) if len(anos_unicos) > 0 else 'N/A'}")
        
        # Si tiene columna de estado, mostrar estados únicos
        for col in df.columns:
            if 'ESTADO' in str(col).upper():
                estados = df[col].dropna().unique()
                print(f"\n✓ Estados en '{col}': {list(estados)}")
                print(f"   Distribución:")
                for estado, count in df[col].value_counts().items():
                    print(f"      - {estado}: {count}")
        
    except Exception as e:
        print(f"\n❌ Error leyendo hoja '{sheet_name}': {e}")

print("\n" + "=" * 80)
print("FIN DE LA INSPECCIÓN")
print("=" * 80)
