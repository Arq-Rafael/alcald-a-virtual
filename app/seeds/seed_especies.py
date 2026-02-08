"""
Script para poblar la base de datos con especies de árboles nativos y comunes en Colombia
Ejecutar con: python app/seeds/seed_especies.py
"""
from app.models.riesgo_arborea import ArbolEspecie

# Datos de especies colombianas
ESPECIES = [
    {
        'nombre_comun': 'Roble',
        'nombre_cientifico': 'Quercus humboldtii',
        'familia': 'Fagaceae',
        'forma_copa': 'Redonda',
        'edad_promedio_anos': 300,
        'altura_promedio_m': 35,
        'dap_promedio_cm': 60,
        'copa_promedio_m': 25,
        'categoria': 'Nativa',
        'coeficiente_compensacion': 1.5,
        'es_nativa': True,
        'descripcion': 'Árbol noble, muy resistente, especie importante en bosques andinos'
    },
    {
        'nombre_comun': 'Cedro Rosado',
        'nombre_cientifico': 'Acrocarpus fraxinifolius',
        'familia': 'Fabaceae',
        'forma_copa': 'Piramidal',
        'edad_promedio_anos': 80,
        'altura_promedio_m': 30,
        'dap_promedio_cm': 50,
        'copa_promedio_m': 20,
        'categoria': 'Nativa',
        'coeficiente_compensacion': 1.2,
        'es_nativa': True,
        'descripcion': 'Árbol maderable, madera de excelente calidad'
    },
    {
        'nombre_comun': 'Guanacaste',
        'nombre_cientifico': 'Enterolobium cyclocarpum',
        'familia': 'Fabaceae',
        'forma_copa': 'Redonda',
        'edad_promedio_anos': 150,
        'altura_promedio_m': 25,
        'dap_promedio_cm': 80,
        'copa_promedio_m': 35,
        'categoria': 'Nativa',
        'coeficiente_compensacion': 2.0,
        'es_nativa': True,
        'descripcion': 'Árbol muy grande, frondoso, proporciona buena sombra'
    },
    {
        'nombre_comun': 'Samán',
        'nombre_cientifico': 'Albizia saman',
        'familia': 'Fabaceae',
        'forma_copa': 'Paraguas',
        'edad_promedio_anos': 100,
        'altura_promedio_m': 20,
        'dap_promedio_cm': 70,
        'copa_promedio_m': 40,
        'categoria': 'Nativa',
        'coeficiente_compensacion': 1.8,
        'es_nativa': True,
        'descripcion': 'Árbol típico de llanuras, muy resistente'
    },
    {
        'nombre_comun': 'Laurel de la India',
        'nombre_cientifico': 'Ficus nitida',
        'familia': 'Moraceae',
        'forma_copa': 'Piramidal',
        'edad_promedio_anos': 60,
        'altura_promedio_m': 18,
        'dap_promedio_cm': 40,
        'copa_promedio_m': 15,
        'categoria': 'Exótica',
        'coeficiente_compensacion': 0.8,
        'es_nativa': False,
        'descripcion': 'Árbol ornamental, usado en jardinería urbana'
    },
    {
        'nombre_comun': 'Nogal Cafetero',
        'nombre_cientifico': 'Cordia alliodora',
        'familia': 'Boraginaceae',
        'forma_copa': 'Piramidal',
        'edad_promedio_anos': 80,
        'altura_promedio_m': 25,
        'dap_promedio_cm': 45,
        'copa_promedio_m': 18,
        'categoria': 'Nativa',
        'coeficiente_compensacion': 1.3,
        'es_nativa': True,
        'descripcion': 'Árbol maderable, multipropósito, resistente'
    },
    {
        'nombre_comun': 'Pino Pátula',
        'nombre_cientifico': 'Pinus patula',
        'familia': 'Pinaceae',
        'forma_copa': 'Piramidal',
        'edad_promedio_anos': 40,
        'altura_promedio_m': 30,
        'dap_promedio_cm': 35,
        'copa_promedio_m': 12,
        'categoria': 'Exótica',
        'coeficiente_compensacion': 0.6,
        'es_nativa': False,
        'descripcion': 'Conífero plantado para reforestación comercial'
    },
    {
        'nombre_comun': 'Eucalipto',
        'nombre_cientifico': 'Eucalyptus globulus',
        'familia': 'Myrtaceae',
        'forma_copa': 'Piramidal',
        'edad_promedio_anos': 30,
        'altura_promedio_m': 35,
        'dap_promedio_cm': 40,
        'copa_promedio_m': 10,
        'categoria': 'Exótica',
        'coeficiente_compensacion': 0.5,
        'es_nativa': False,
        'descripcion': 'Árbol de crecimiento rápido, para producción de madera'
    },
    {
        'nombre_comun': 'Mango',
        'nombre_cientifico': 'Mangifera indica',
        'familia': 'Anacardiaceae',
        'forma_copa': 'Redonda',
        'edad_promedio_anos': 50,
        'altura_promedio_m': 15,
        'dap_promedio_cm': 50,
        'copa_promedio_m': 20,
        'categoria': 'Frutales',
        'coeficiente_compensacion': 1.0,
        'es_nativa': False,
        'descripcion': 'Árbol frutal, de valor comercial'
    },
    {
        'nombre_comun': 'Aguacate',
        'nombre_cientifico': 'Persea americana',
        'familia': 'Lauraceae',
        'forma_copa': 'Redonda',
        'edad_promedio_anos': 40,
        'altura_promedio_m': 12,
        'dap_promedio_cm': 35,
        'copa_promedio_m': 15,
        'categoria': 'Frutales',
        'coeficiente_compensacion': 0.8,
        'es_nativa': False,
        'descripcion': 'Árbol frutal de importancia comercial en zonas cafeteras'
    },
    {
        'nombre_comun': 'Cítrico',
        'nombre_cientifico': 'Citrus aurantium',
        'familia': 'Rutaceae',
        'forma_copa': 'Redonda',
        'edad_promedio_anos': 35,
        'altura_promedio_m': 8,
        'dap_promedio_cm': 25,
        'copa_promedio_m': 10,
        'categoria': 'Frutales',
        'coeficiente_compensacion': 0.6,
        'es_nativa': False,
        'descripcion': 'Árbol frutal para producción comercial'
    },
    {
        'nombre_comun': 'Guayacán Amarillo',
        'nombre_cientifico': 'Tabebuia chrysantha',
        'familia': 'Bignoniaceae',
        'forma_copa': 'Redonda',
        'edad_promedio_anos': 120,
        'altura_promedio_m': 18,
        'dap_promedio_cm': 55,
        'copa_promedio_m': 22,
        'categoria': 'Nativa',
        'coeficiente_compensacion': 1.8,
        'es_nativa': True,
        'descripcion': 'Árbol maderable de gran valor, madera muy durable'
    },
    {
        'nombre_comun': 'Palma de Cera',
        'nombre_cientifico': 'Ceroxylon quindiuense',
        'familia': 'Arecaceae',
        'forma_copa': 'Columnar',
        'edad_promedio_anos': 60,
        'altura_promedio_m': 40,
        'dap_promedio_cm': 30,
        'copa_promedio_m': 5,
        'categoria': 'Nativa',
        'coeficiente_compensacion': 2.0,
        'es_nativa': True,
        'descripcion': 'Árbol emblemático colombiano, árbol nacional'
    },
    {
        'nombre_comun': 'Sende',
        'nombre_cientifico': 'Erythroxylum coca',
        'familia': 'Erythroxylaceae',
        'forma_copa': 'Redonda',
        'edad_promedio_anos': 50,
        'altura_promedio_m': 5,
        'dap_promedio_cm': 15,
        'copa_promedio_m': 8,
        'categoria': 'Nativa',
        'coeficiente_compensacion': 0.4,
        'es_nativa': True,
        'descripcion': 'Árbol pequeño, crecimiento lento'
    },
    {
        'nombre_comun': 'Comino',
        'nombre_cientifico': 'Aniba rosaeodora',
        'familia': 'Lauraceae',
        'forma_copa': 'Piramidal',
        'edad_promedio_anos': 80,
        'altura_promedio_m': 20,
        'dap_promedio_cm': 40,
        'copa_promedio_m': 12,
        'categoria': 'Nativa',
        'coeficiente_compensacion': 1.4,
        'es_nativa': True,
        'descripcion': 'Árbol maderable del Amazonas colombiano'
    },
]

def seed_especies(db_instance):
    """Crea las especies en la base de datos"""
    # Verificar si ya existen
    if ArbolEspecie.query.first():
        print("Las especies ya existen en la base de datos")
        return
    
    count = 0
    for especie_data in ESPECIES:
        especie = ArbolEspecie(**especie_data)
        db_instance.session.add(especie)
        count += 1
    
    db_instance.session.commit()
    print(f"✓ {count} especies agregadas a la base de datos")

if __name__ == '__main__':
    from app import create_app, db
    app = create_app()
    with app.app_context():
        seed_especies(db)
