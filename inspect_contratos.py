from app import create_app, db
from app.models.contrato import Contrato

app = create_app()
with app.app_context():
    contratos = Contrato.query.all()
    print(f'\n=== TOTAL CONTRATOS: {len(contratos)} ===\n')
    
    for c in contratos:
        print(f'ID: {c.id}')
        print(f'  Numero proceso: {c.numero_proceso}')
        print(f'  Plataforma: {c.plataforma}')
        print(f'  Entidad: {c.entidad_nombre}')
        print(f'  Cuantia: {c.cuantia}')
        print(f'  Estado: {c.estado}')
        print(f'  Objeto: {c.objeto_contrato[:50] if c.objeto_contrato else None}...')
        print(f'  Fecha pub: {c.fecha_publicacion}')
        print()
