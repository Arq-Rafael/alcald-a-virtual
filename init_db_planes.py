from app import create_app, db
from app.models.plan_contingencia_v2 import PlanContingenciaV2

app = create_app()
with app.app_context():
    db.create_all()
    print('✓ Tabla planes_contingencia_v2 creada exitosamente')
    print('✓ Base de datos lista para usar')
