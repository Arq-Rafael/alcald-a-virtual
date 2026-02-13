"""
Script para poblar la base de datos con especies de árboles nativos y comunes en Colombia
Ejecutar con: python app/seeds/seed_especies.py
"""
from app.models.riesgo_arborea import ArbolEspecie

# Datos de especies de Cundinamarca y región Guaviare (80+ especies)
ESPECIES = [
    # ÁRBOLES NATIVOS DE GRAN VALOR
    {'nombre_comun': 'Roble', 'nombre_cientifico': 'Quercus humboldtii', 'familia': 'Fagaceae', 'forma_copa': 'Redonda', 'edad_promedio_anos': 150, 'altura_promedio_m': 30, 'dap_promedio_cm': 80, 'copa_promedio_m': 25, 'categoria': 'Nativa', 'coeficiente_compensacion': 2.0, 'es_nativa': True, 'descripcion': 'Árbol emblemático de Cundinamarca. Madera de excelente calidad'},
    {'nombre_comun': 'Cedro', 'nombre_cientifico': 'Cedrela odorata', 'familia': 'Meliaceae', 'forma_copa': 'Piramidal', 'edad_promedio_anos': 80, 'altura_promedio_m': 25, 'dap_promedio_cm': 60, 'copa_promedio_m': 18, 'categoria': 'Nativa', 'coeficiente_compensacion': 1.8, 'es_nativa': True, 'descripcion': 'Árbol valioso por su madera aromática'},
    {'nombre_comun': 'Guanacaste', 'nombre_cientifico': 'Enterolobium cyclocarpum', 'familia': 'Fabaceae', 'forma_copa': 'Redonda', 'edad_promedio_anos': 200, 'altura_promedio_m': 35, 'dap_promedio_cm': 100, 'copa_promedio_m': 35, 'categoria': 'Nativa', 'coeficiente_compensacion': 2.0, 'es_nativa': True, 'descripcion': 'Árbol de grandes dimensiones y copa muy amplia'},
    {'nombre_comun': 'Nogal', 'nombre_cientifico': 'Juglans neotropica', 'familia': 'Juglandaceae', 'forma_copa': 'Piramidal', 'edad_promedio_anos': 100, 'altura_promedio_m': 30, 'dap_promedio_cm': 70, 'copa_promedio_m': 20, 'categoria': 'Nativa', 'coeficiente_compensacion': 1.9, 'es_nativa': True, 'descripcion': 'Árbol precioso con maderable de gran valor'},
    {'nombre_comun': 'Caoba', 'nombre_cientifico': 'Swietenia macrophylla', 'familia': 'Meliaceae', 'forma_copa': 'Redonda', 'edad_promedio_anos': 90, 'altura_promedio_m': 35, 'dap_promedio_cm': 80, 'copa_promedio_m': 28, 'categoria': 'Nativa', 'coeficiente_compensacion': 1.9, 'es_nativa': True, 'descripcion': 'Maderable de gran demanda comercial'},
    {'nombre_comun': 'Pino Colombiano', 'nombre_cientifico': 'Podocarpus oleifolius', 'familia': 'Podocarpaceae', 'forma_copa': 'Piramidal', 'edad_promedio_anos': 150, 'altura_promedio_m': 30, 'dap_promedio_cm': 60, 'copa_promedio_m': 15, 'categoria': 'Nativa', 'coeficiente_compensacion': 1.7, 'es_nativa': True, 'descripcion': 'Conífera nativa de zonas altas'},
    {'nombre_comun': 'Samán', 'nombre_cientifico': 'Albizia saman', 'familia': 'Fabaceae', 'forma_copa': 'Redonda', 'edad_promedio_anos': 200, 'altura_promedio_m': 30, 'dap_promedio_cm': 90, 'copa_promedio_m': 35, 'categoria': 'Nativa', 'coeficiente_compensacion': 1.8, 'es_nativa': True, 'descripcion': 'Árbol de gran copa y sombra densa'},
    
    # ÁRBOLES DE ZONAS ALTAS
    {'nombre_comun': 'Aliso', 'nombre_cientifico': 'Alnus acuminata', 'familia': 'Betulaceae', 'forma_copa': 'Piramidal', 'edad_promedio_anos': 60, 'altura_promedio_m': 25, 'dap_promedio_cm': 50, 'copa_promedio_m': 12, 'categoria': 'Nativa', 'coeficiente_compensacion': 1.4, 'es_nativa': True, 'descripcion': 'Árbol utilizado en sistemas agroforestales'},
    {'nombre_comun': 'Chical', 'nombre_cientifico': 'Prumnopitys harmsiana', 'familia': 'Podocarpaceae', 'forma_copa': 'Piramidal', 'edad_promedio_anos': 120, 'altura_promedio_m': 25, 'dap_promedio_cm': 50, 'copa_promedio_m': 10, 'categoria': 'Nativa', 'coeficiente_compensacion': 1.6, 'es_nativa': True, 'descripcion': 'Conífera de zonas de niebla'},
    {'nombre_comun': 'Encenillo', 'nombre_cientifico': 'Weinmannia tomentosa', 'familia': 'Cunoniaceae', 'forma_copa': 'Piramidal', 'edad_promedio_anos': 80, 'altura_promedio_m': 20, 'dap_promedio_cm': 40, 'copa_promedio_m': 10, 'categoria': 'Nativa', 'coeficiente_compensacion': 1.3, 'es_nativa': True, 'descripcion': 'Árbol de zonas altas muy ramificado'},
    {'nombre_comun': 'Palma de Cera', 'nombre_cientifico': 'Ceroxylon quindiuense', 'familia': 'Arecaceae', 'forma_copa': 'Columnar', 'edad_promedio_anos': 250, 'altura_promedio_m': 20, 'dap_promedio_cm': 40, 'copa_promedio_m': 8, 'categoria': 'Nativa', 'coeficiente_compensacion': 1.8, 'es_nativa': True, 'descripcion': 'Palma más alta del mundo (endémica)'},
    {'nombre_comun': 'Árbol de Cera', 'nombre_cientifico': 'Ceroxylon eriophorum', 'familia': 'Arecaceae', 'forma_copa': 'Piramidal', 'edad_promedio_anos': 200, 'altura_promedio_m': 18, 'dap_promedio_cm': 35, 'copa_promedio_m': 7, 'categoria': 'Nativa', 'coeficiente_compensacion': 1.7, 'es_nativa': True, 'descripcion': 'Palma nativa de los Andes'},
    {'nombre_comun': 'Pumamaque', 'nombre_cientifico': 'Podocarpus lambertianus', 'familia': 'Podocarpaceae', 'forma_copa': 'Piramidal', 'edad_promedio_anos': 180, 'altura_promedio_m': 35, 'dap_promedio_cm': 70, 'copa_promedio_m': 15, 'categoria': 'Nativa', 'coeficiente_compensacion': 1.7, 'es_nativa': True, 'descripcion': 'Árbol sagrado para comunidades indígenas'},
    
    # ÁRBOLES MADERABLES
    {'nombre_comun': 'Guayacán', 'nombre_cientifico': 'Tabebuia serratifolia', 'familia': 'Bignoniaceae', 'forma_copa': 'Redonda', 'edad_promedio_anos': 150, 'altura_promedio_m': 25, 'dap_promedio_cm': 55, 'copa_promedio_m': 18, 'categoria': 'Nativa', 'coeficiente_compensacion': 1.6, 'es_nativa': True, 'descripcion': 'Maderable duro de color dorado'},
    {'nombre_comun': 'Guayacán Blanco', 'nombre_cientifico': 'Lapacho albo', 'familia': 'Bignoniaceae', 'forma_copa': 'Redonda', 'edad_promedio_anos': 100, 'altura_promedio_m': 20, 'dap_promedio_cm': 40, 'copa_promedio_m': 15, 'categoria': 'Nativa', 'coeficiente_compensacion': 1.4, 'es_nativa': True, 'descripcion': 'Árbol de madera muy dura'},
    {'nombre_comun': 'Guayacán Amarillo', 'nombre_cientifico': 'Tabebuia chrysantha', 'familia': 'Bignoniaceae', 'forma_copa': 'Redonda', 'edad_promedio_anos': 120, 'altura_promedio_m': 22, 'dap_promedio_cm': 45, 'copa_promedio_m': 16, 'categoria': 'Nativa', 'coeficiente_compensacion': 1.5, 'es_nativa': True, 'descripcion': 'Árbol de flores amarillas'},
    {'nombre_comun': 'Abarco', 'nombre_cientifico': 'Cariniana pyriformis', 'familia': 'Lecythidaceae', 'forma_copa': 'Piramidal', 'edad_promedio_anos': 300, 'altura_promedio_m': 40, 'dap_promedio_cm': 90, 'copa_promedio_m': 25, 'categoria': 'Nativa', 'coeficiente_compensacion': 1.9, 'es_nativa': True, 'descripcion': 'Árbol gigante de maderable valioso'},
    {'nombre_comun': 'Quebracho', 'nombre_cientifico': 'Aspidosperma quebracho-blanco', 'familia': 'Apocynaceae', 'forma_copa': 'Redonda', 'edad_promedio_anos': 150, 'altura_promedio_m': 25, 'dap_promedio_cm': 60, 'copa_promedio_m': 20, 'categoria': 'Nativa', 'coeficiente_compensacion': 1.7, 'es_nativa': True, 'descripcion': 'Árbol de madera extremadamente dura'},
    {'nombre_comun': 'Caracolí', 'nombre_cientifico': 'Anacardium excelsum', 'familia': 'Anacardiaceae', 'forma_copa': 'Redonda', 'edad_promedio_anos': 150, 'altura_promedio_m': 40, 'dap_promedio_cm': 100, 'copa_promedio_m': 35, 'categoria': 'Nativa', 'coeficiente_compensacion': 1.9, 'es_nativa': True, 'descripcion': 'Árbol gigante del trópico'},
    {'nombre_comun': 'Bálsamo', 'nombre_cientifico': 'Myroxylon balsamum', 'familia': 'Fabaceae', 'forma_copa': 'Piramidal', 'edad_promedio_anos': 300, 'altura_promedio_m': 30, 'dap_promedio_cm': 70, 'copa_promedio_m': 18, 'categoria': 'Nativa', 'coeficiente_compensacion': 1.8, 'es_nativa': True, 'descripcion': 'Árbol productor de resina aromática'},
    {'nombre_comun': 'Algarrobo', 'nombre_cientifico': 'Hymenaea courbaril', 'familia': 'Fabaceae', 'forma_copa': 'Redonda', 'edad_promedio_anos': 200, 'altura_promedio_m': 30, 'dap_promedio_cm': 80, 'copa_promedio_m': 25, 'categoria': 'Nativa', 'coeficiente_compensacion': 1.8, 'es_nativa': True, 'descripcion': 'Árbol longevo con maderable valioso'},
    
    # ÁRBOLES FRUTALES
    {'nombre_comun': 'Aguacate', 'nombre_cientifico': 'Persea americana', 'familia': 'Lauraceae', 'forma_copa': 'Redonda', 'edad_promedio_anos': 60, 'altura_promedio_m': 10, 'dap_promedio_cm': 30, 'copa_promedio_m': 12, 'categoria': 'Nativa', 'coeficiente_compensacion': 0.95, 'es_nativa': True, 'descripcion': 'Árbol frutal de importancia económica'},
    {'nombre_comun': 'Mango', 'nombre_cientifico': 'Mangifera indica', 'familia': 'Anacardiaceae', 'forma_copa': 'Redonda', 'edad_promedio_anos': 80, 'altura_promedio_m': 20, 'dap_promedio_cm': 60, 'copa_promedio_m': 25, 'categoria': 'Exótica', 'coeficiente_compensacion': 1.3, 'es_nativa': False, 'descripcion': 'Árbol frutal tropical de gran demanda'},
    {'nombre_comun': 'Zapote', 'nombre_cientifico': 'Manilkara sapota', 'familia': 'Sapotaceae', 'forma_copa': 'Redonda', 'edad_promedio_anos': 350, 'altura_promedio_m': 30, 'dap_promedio_cm': 70, 'copa_promedio_m': 20, 'categoria': 'Nativa', 'coeficiente_compensacion': 1.8, 'es_nativa': True, 'descripcion': 'Árbol frutal tropical de larga vida'},
    {'nombre_comun': 'Mamoncillo', 'nombre_cientifico': 'Melicoccus bijugatus', 'familia': 'Sapindaceae', 'forma_copa': 'Redonda', 'edad_promedio_anos': 100, 'altura_promedio_m': 15, 'dap_promedio_cm': 35, 'copa_promedio_m': 15, 'categoria': 'Nativa', 'coeficiente_compensacion': 1.1, 'es_nativa': True, 'descripcion': 'Árbol frutal de climas cálidos'},
    {'nombre_comun': 'Guanabana', 'nombre_cientifico': 'Annona muricata', 'familia': 'Annonaceae', 'forma_copa': 'Redonda', 'edad_promedio_anos': 20, 'altura_promedio_m': 6, 'dap_promedio_cm': 15, 'copa_promedio_m': 8, 'categoria': 'Nativa', 'coeficiente_compensacion': 0.8, 'es_nativa': True, 'descripcion': 'Arbusto frutal medicinal'},
    {'nombre_comun': 'Lúcumo', 'nombre_cientifico': 'Pouteria lucuma', 'familia': 'Sapotaceae', 'forma_copa': 'Redonda', 'edad_promedio_anos': 300, 'altura_promedio_m': 25, 'dap_promedio_cm': 50, 'copa_promedio_m': 18, 'categoria': 'Nativa', 'coeficiente_compensacion': 1.6, 'es_nativa': True, 'descripcion': 'Árbol frutal de importancia andina'},
    {'nombre_comun': 'Guayabo', 'nombre_cientifico': 'Psidium guajava', 'familia': 'Myrtaceae', 'forma_copa': 'Arbustiva', 'edad_promedio_anos': 30, 'altura_promedio_m': 8, 'dap_promedio_cm': 15, 'copa_promedio_m': 8, 'categoria': 'Nativa', 'coeficiente_compensacion': 0.8, 'es_nativa': True, 'descripcion': 'Árbol frutal muy productor'},
    {'nombre_comun': 'Naranja', 'nombre_cientifico': 'Citrus aurantium', 'familia': 'Rutaceae', 'forma_copa': 'Redonda', 'edad_promedio_anos': 40, 'altura_promedio_m': 8, 'dap_promedio_cm': 20, 'copa_promedio_m': 8, 'categoria': 'Exótica', 'coeficiente_compensacion': 0.8, 'es_nativa': False, 'descripcion': 'Árbol cítrico'},
    {'nombre_comun': 'Limón', 'nombre_cientifico': 'Citrus limon', 'familia': 'Rutaceae', 'forma_copa': 'Redonda', 'edad_promedio_anos': 35, 'altura_promedio_m': 6, 'dap_promedio_cm': 15, 'copa_promedio_m': 6, 'categoria': 'Exótica', 'coeficiente_compensacion': 0.8, 'es_nativa': False, 'descripcion': 'Árbol cítrico'},
    {'nombre_comun': 'Papayo', 'nombre_cientifico': 'Carica papaya', 'familia': 'Caricaceae', 'forma_copa': 'Arbustiva', 'edad_promedio_anos': 7, 'altura_promedio_m': 6, 'dap_promedio_cm': 12, 'copa_promedio_m': 6, 'categoria': 'Exótica', 'coeficiente_compensacion': 0.7, 'es_nativa': False, 'descripcion': 'Árbol frutal tropical'},
    
    # PLANTAS Y CULTIVOS HERBÁCEOS
    {'nombre_comun': 'Chachafruto', 'nombre_cientifico': 'Erythrina edulis', 'familia': 'Fabaceae', 'forma_copa': 'Redonda', 'edad_promedio_anos': 40, 'altura_promedio_m': 10, 'dap_promedio_cm': 25, 'copa_promedio_m': 10, 'categoria': 'Nativa', 'coeficiente_compensacion': 0.9, 'es_nativa': True, 'descripcion': 'Árbol utilizado en sistemas agroforestales'},
    {'nombre_comun': 'Cacao', 'nombre_cientifico': 'Theobroma cacao', 'familia': 'Sterculiaceae', 'forma_copa': 'Arbustiva', 'edad_promedio_anos': 100, 'altura_promedio_m': 7, 'dap_promedio_cm': 20, 'copa_promedio_m': 8, 'categoria': 'Nativa', 'coeficiente_compensacion': 0.8, 'es_nativa': True, 'descripcion': 'Arbusto cultivado de importancia económica'},
    {'nombre_comun': 'Café', 'nombre_cientifico': 'Coffea arabica', 'familia': 'Rubiaceae', 'forma_copa': 'Arbustiva', 'edad_promedio_anos': 50, 'altura_promedio_m': 3, 'dap_promedio_cm': 8, 'copa_promedio_m': 4, 'categoria': 'Exótica', 'coeficiente_compensacion': 0.5, 'es_nativa': False, 'descripcion': 'Arbusto cultivado emblemático'},
    {'nombre_comun': 'Plátano', 'nombre_cientifico': 'Musa × paradisiaca', 'familia': 'Musaceae', 'forma_copa': 'Arbustiva', 'edad_promedio_anos': 6, 'altura_promedio_m': 7, 'dap_promedio_cm': 15, 'copa_promedio_m': 8, 'categoria': 'Nativa', 'coeficiente_compensacion': 0.7, 'es_nativa': True, 'descripcion': 'Cultivo de importancia alimentaria'},
    {'nombre_comun': 'Granadilla', 'nombre_cientifico': 'Passiflora edulis', 'familia': 'Passifloraceae', 'forma_copa': 'Arbustiva', 'edad_promedio_anos': 10, 'altura_promedio_m': 5, 'dap_promedio_cm': 5, 'copa_promedio_m': 3, 'categoria': 'Nativa', 'coeficiente_compensacion': 0.5, 'es_nativa': True, 'descripcion': 'Vid frutal aromática'},
    {'nombre_comun': 'Gulupa', 'nombre_cientifico': 'Passiflora edulis var edulis', 'familia': 'Passifloraceae', 'forma_copa': 'Arbustiva', 'edad_promedio_anos': 8, 'altura_promedio_m': 3, 'dap_promedio_cm': 3, 'copa_promedio_m': 2, 'categoria': 'Nativa', 'coeficiente_compensacion': 0.5, 'es_nativa': True, 'descripcion': 'Fruto de demanda comercial'},
    {'nombre_comun': 'Mora', 'nombre_cientifico': 'Rubus fruticosus', 'familia': 'Rosaceae', 'forma_copa': 'Arbustiva', 'edad_promedio_anos': 15, 'altura_promedio_m': 2, 'dap_promedio_cm': 5, 'copa_promedio_m': 3, 'categoria': 'Nativa', 'coeficiente_compensacion': 0.4, 'es_nativa': True, 'descripcion': 'Arbusto espinoso productor de frutos'},
    
    # ÁRBOLES EXÓTICOS Y PLANTACIONES
    {'nombre_comun': 'Eucalipto', 'nombre_cientifico': 'Eucalyptus globulus', 'familia': 'Myrtaceae', 'forma_copa': 'Piramidal', 'edad_promedio_anos': 50, 'altura_promedio_m': 35, 'dap_promedio_cm': 60, 'copa_promedio_m': 15, 'categoria': 'Exótica', 'coeficiente_compensacion': 1.0, 'es_nativa': False, 'descripcion': 'Árbol de rápido crecimiento'},
    {'nombre_comun': 'Pino Pátula', 'nombre_cientifico': 'Pinus patula', 'familia': 'Pinaceae', 'forma_copa': 'Piramidal', 'edad_promedio_anos': 60, 'altura_promedio_m': 30, 'dap_promedio_cm': 55, 'copa_promedio_m': 12, 'categoria': 'Exótica', 'coeficiente_compensacion': 1.1, 'es_nativa': False, 'descripcion': 'Especie adaptada a climas templados'},
    {'nombre_comun': 'Acacia', 'nombre_cientifico': 'Acacia mangium', 'familia': 'Fabaceae', 'forma_copa': 'Redonda', 'edad_promedio_anos': 40, 'altura_promedio_m': 25, 'dap_promedio_cm': 45, 'copa_promedio_m': 18, 'categoria': 'Exótica', 'coeficiente_compensacion': 1.0, 'es_nativa': False, 'descripcion': 'Árbol utilizado en reforestación'},
    {'nombre_comun': 'Teak', 'nombre_cientifico': 'Tectona grandis', 'familia': 'Lamiaceae', 'forma_copa': 'Piramidal', 'edad_promedio_anos': 80, 'altura_promedio_m': 35, 'dap_promedio_cm': 70, 'copa_promedio_m': 20, 'categoria': 'Exótica', 'coeficiente_compensacion': 1.2, 'es_nativa': False, 'descripcion': 'Maderable de excelente calidad'},
    {'nombre_comun': 'Jacarandá', 'nombre_cientifico': 'Jacaranda mimosifolia', 'familia': 'Bignoniaceae', 'forma_copa': 'Redonda', 'edad_promedio_anos': 70, 'altura_promedio_m': 15, 'dap_promedio_cm': 40, 'copa_promedio_m': 15, 'categoria': 'Exótica', 'coeficiente_compensacion': 1.2, 'es_nativa': False, 'descripcion': 'Árbol ornamental de flores azules'},
    {'nombre_comun': 'Almendro', 'nombre_cientifico': 'Terminalia catappa', 'familia': 'Combretaceae', 'forma_copa': 'Redonda', 'edad_promedio_anos': 100, 'altura_promedio_m': 20, 'dap_promedio_cm': 45, 'copa_promedio_m': 20, 'categoria': 'Exótica', 'coeficiente_compensacion': 1.2, 'es_nativa': False, 'descripcion': 'Árbol ornamental de frutos secos'},
    {'nombre_comun': 'Brasilete', 'nombre_cientifico': 'Haematoxylon brasiletto', 'familia': 'Caesalpiniaceae', 'forma_copa': 'Redonda', 'edad_promedio_anos': 100, 'altura_promedio_m': 12, 'dap_promedio_cm': 30, 'copa_promedio_m': 12, 'categoria': 'Exótica', 'coeficiente_compensacion': 1.1, 'es_nativa': False, 'descripcion': 'Árbol tintóreo'},
    
    # ÁRBOLES DE RIBERA Y ESPECIALES
    {'nombre_comun': 'Sauce', 'nombre_cientifico': 'Salix humboldtiana', 'familia': 'Salicaceae', 'forma_copa': 'Llorona', 'edad_promedio_anos': 40, 'altura_promedio_m': 20, 'dap_promedio_cm': 35, 'copa_promedio_m': 15, 'categoria': 'Nativa', 'coeficiente_compensacion': 0.9, 'es_nativa': True, 'descripcion': 'Árbol ribereño de raíces profundas'},
    {'nombre_comun': 'Fresno', 'nombre_cientifico': 'Fraxinus excelsior', 'familia': 'Oleaceae', 'forma_copa': 'Piramidal', 'edad_promedio_anos': 70, 'altura_promedio_m': 25, 'dap_promedio_cm': 45, 'copa_promedio_m': 15, 'categoria': 'Nativa', 'coeficiente_compensacion': 1.3, 'es_nativa': True, 'descripcion': 'Árbol de madera flexible y resistente'},
    {'nombre_comun': 'Laurel', 'nombre_cientifico': 'Laurus nobilis', 'familia': 'Lauraceae', 'forma_copa': 'Redonda', 'edad_promedio_anos': 80, 'altura_promedio_m': 15, 'dap_promedio_cm': 35, 'copa_promedio_m': 15, 'categoria': 'Nativa', 'coeficiente_compensacion': 1.3, 'es_nativa': True, 'descripcion': 'Árbol aromático utilizado en cocina'},
    {'nombre_comun': 'Comino', 'nombre_cientifico': 'Aniba rosaeodora', 'familia': 'Lauraceae', 'forma_copa': 'Piramidal', 'edad_promedio_anos': 60, 'altura_promedio_m': 20, 'dap_promedio_cm': 40, 'copa_promedio_m': 12, 'categoria': 'Nativa', 'coeficiente_compensacion': 1.2, 'es_nativa': True, 'descripcion': 'Árbol aromático con propiedades medicinales'},
    {'nombre_comun': 'Quina', 'nombre_cientifico': 'Cinchona officinalis', 'familia': 'Rubiaceae', 'forma_copa': 'Redonda', 'edad_promedio_anos': 60, 'altura_promedio_m': 15, 'dap_promedio_cm': 30, 'copa_promedio_m': 12, 'categoria': 'Nativa', 'coeficiente_compensacion': 1.2, 'es_nativa': True, 'descripcion': 'Árbol medicinal históricamente importante'},
    {'nombre_comun': 'Ciruela', 'nombre_cientifico': 'Prunus serotina', 'familia': 'Rosaceae', 'forma_copa': 'Redonda', 'edad_promedio_anos': 50, 'altura_promedio_m': 20, 'dap_promedio_cm': 35, 'copa_promedio_m': 12, 'categoria': 'Nativa', 'coeficiente_compensacion': 1.1, 'es_nativa': True, 'descripcion': 'Árbol frutal con flores vistosas'},
    {'nombre_comun': 'Arrayán', 'nombre_cientifico': 'Myrcia popayanensis', 'familia': 'Myrtaceae', 'forma_copa': 'Arbustiva', 'edad_promedio_anos': 40, 'altura_promedio_m': 6, 'dap_promedio_cm': 15, 'copa_promedio_m': 5, 'categoria': 'Nativa', 'coeficiente_compensacion': 0.8, 'es_nativa': True, 'descripcion': 'Arbusto aromático de flores blancas'},
    {'nombre_comun': 'Murtilla', 'nombre_cientifico': 'Blepharocalyx salicifolius', 'familia': 'Myrtaceae', 'forma_copa': 'Arbustiva', 'edad_promedio_anos': 50, 'altura_promedio_m': 8, 'dap_promedio_cm': 20, 'copa_promedio_m': 6, 'categoria': 'Nativa', 'coeficiente_compensacion': 0.9, 'es_nativa': True, 'descripcion': 'Arbusto frutal nativo de páramo'},
    
    # ESPECIES ACUÁTICAS Y PALMAS
    {'nombre_comun': 'Chontaduro', 'nombre_cientifico': 'Bactris gasipaes', 'familia': 'Arecaceae', 'forma_copa': 'Piramidal', 'edad_promedio_anos': 30, 'altura_promedio_m': 10, 'dap_promedio_cm': 15, 'copa_promedio_m': 6, 'categoria': 'Nativa', 'coeficiente_compensacion': 0.7, 'es_nativa': True, 'descripcion': 'Palma frutal'},
    {'nombre_comun': 'Coco', 'nombre_cientifico': 'Cocos nucifera', 'familia': 'Arecaceae', 'forma_copa': 'Piramidal', 'edad_promedio_anos': 80, 'altura_promedio_m': 25, 'dap_promedio_cm': 30, 'copa_promedio_m': 10, 'categoria': 'Exótica', 'coeficiente_compensacion': 1.0, 'es_nativa': False, 'descripcion': 'Palma tropical'},
    {'nombre_comun': 'Dátil', 'nombre_cientifico': 'Phoenix dactylifera', 'familia': 'Arecaceae', 'forma_copa': 'Piramidal', 'edad_promedio_anos': 100, 'altura_promedio_m': 20, 'dap_promedio_cm': 30, 'copa_promedio_m': 8, 'categoria': 'Exótica', 'coeficiente_compensacion': 1.0, 'es_nativa': False, 'descripcion': 'Palma productor de frutos'},
    {'nombre_comun': 'Tepe', 'nombre_cientifico': 'Thrinax radiata', 'familia': 'Arecaceae', 'forma_copa': 'Redonda', 'edad_promedio_anos': 50, 'altura_promedio_m': 8, 'dap_promedio_cm': 15, 'copa_promedio_m': 8, 'categoria': 'Nativa', 'coeficiente_compensacion': 0.7, 'es_nativa': True, 'descripcion': 'Palma nativa del Caribe'},
]

def seed_especies(db_instance):
    """Crea las especies en la base de datos de forma segura"""
    # Verificar si ya existen especies
    existing_count = db_instance.session.query(ArbolEspecie).count()
    
    if existing_count >= len(ESPECIES):
        # Las especies ya están cargadas
        return
    
    # Si hay algunas pero no todas, solo agregar las que faltan
    existing_names = {e.nombre_comun for e in db_instance.session.query(ArbolEspecie.nombre_comun).all()}
    
    count = 0
    for especie_data in ESPECIES:
        if especie_data['nombre_comun'] not in existing_names:
            try:
                especie = ArbolEspecie(**especie_data)
                db_instance.session.add(especie)
                count += 1
            except Exception as e:
                # Si falla al insertar una especie, continúa con la siguiente
                print(f"Advertencia: No se pudo insertar {especie_data['nombre_comun']}: {e}")
                continue
    
    try:
        db_instance.session.commit()
        if count > 0:
            print(f"Cargadas {count} especies nuevas en la base de datos")
    except Exception as e:
        db_instance.session.rollback()
        print(f"Error al guardar especies: {e}")

if __name__ == '__main__':
    from app import create_app, db
    app = create_app()
    with app.app_context():
        seed_especies(db)
