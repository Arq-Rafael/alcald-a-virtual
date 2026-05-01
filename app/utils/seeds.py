from app import db
from app.models.metas import MetaPlan
import datetime as dt

def seed_metas():
    """Inicializa metas del plan de desarrollo si no existen"""
    try:
        # Verificar si hay metas
        if MetaPlan.query.first():
            print("✅ [SEEDS] Las metas ya existen. Saltando seed.")
            return

        print("🌱 [SEEDS] Sembrando metas del Plan de Desarrollo...")
        
        metas = [
            {
                "linea_estrategica": "Seguridad y Convivencia",
                "sector": "Justicia y Seguridad",
                "programa": "Fortalecimiento de la seguridad ciudadana",
                "unidad": "Porcentaje",
                "meta_cuatrenio": 100,
                "meta_producto": "Implementar estrategia de seguridad integral",
                "avance_actual": 25
            },
            {
                "linea_estrategica": "Infraestructura para el Desarrollo",
                "sector": "Transporte",
                "programa": "Mantenimiento vial",
                "unidad": "Kilómetros",
                "meta_cuatrenio": 50,
                "meta_producto": "Mantenimiento de 50km de vías terciarias",
                "avance_actual": 10
            },
            {
                "linea_estrategica": "Bienestar Social",
                "sector": "Salud",
                "programa": "Salud Pública",
                "unidad": "Porcentaje",
                "meta_cuatrenio": 100,
                "meta_producto": "Cobertura universal de vacunación",
                "avance_actual": 80
            },
            {
                "linea_estrategica": "Desarrollo Económico",
                "sector": "Agricultura",
                "programa": "Apoyo al campo",
                "unidad": "Familias",
                "meta_cuatrenio": 200,
                "meta_producto": "Asistencia técnica a 200 familias campesinas",
                "avance_actual": 45
            },
             {
                "linea_estrategica": "Educación de Calidad",
                "sector": "Educación",
                "programa": "Infraestructura Educativa",
                "unidad": "Sedes",
                "meta_cuatrenio": 10,
                "meta_producto": "Mejoramiento de 10 sedes educativas rurales",
                "avance_actual": 2
            },
            {
                "linea_estrategica": "POR EL SUPATÁ SOÑADO AVANZAMOS JUNTOS EN LA LÍNEA ESTRATÉGICA INSTITUCIONAL",
                "sector": "Desarrollo Comunitario",
                "programa": "Infraestructura Comunitaria",
                "unidad": "Adecuaciones",
                "meta_cuatrenio": 3,
                "meta_producto": "Realizar 3 adecuaciones a salones comunales",
                "avance_actual": 0
            },
            {
                "linea_estrategica": "POR EL SUPATÁ SOÑADO AVANZAMOS JUNTOS EN LA LÍNEA ESTRATÉGICA INSTITUCIONAL",
                "sector": "Desarrollo Comunitario",
                "programa": "Asesoría y Asistencia Comunitaria",
                "unidad": "Oficina",
                "meta_cuatrenio": 1,
                "meta_producto": "Crear la oficina de asesoria y asistencia a organismos comunales",
                "avance_actual": 0
            }
        ]
        
        for data in metas:
            nueva_meta = MetaPlan(**data)
            db.session.add(nueva_meta)
            
        db.session.commit()
        print(f"✅ [SEEDS] Se crearon {len(metas)} metas iniciales.")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ [SEEDS ERROR] {e}")
