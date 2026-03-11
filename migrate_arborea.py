"""One-time migration: add new columns to radicado_arborea table."""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'data.db')
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute('PRAGMA table_info(radicado_arborea)')
cols = [row[1] for row in cur.fetchall()]
print('Existing columns:', cols)

new_cols = [
    ('criticidad', 'TEXT'),
    ('historial_estados', 'TEXT'),
    ('sla_dias', 'INTEGER'),
    ('fecha_vencimiento_sla', 'DATETIME'),
]

for col_name, col_def in new_cols:
    if col_name not in cols:
        try:
            cur.execute(f'ALTER TABLE radicado_arborea ADD COLUMN {col_name} {col_def}')
            print(f'Added: {col_name}')
        except Exception as e:
            print(f'Error adding {col_name}: {e}')
    else:
        print(f'Already exists: {col_name}')

conn.commit()
conn.close()
print('Migration complete.')
