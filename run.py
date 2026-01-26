from app import create_app
import os

# Cargar variables de entorno desde .env solo en local
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # En Railway, dotenv no está disponible (no es necesario)
    pass

print("🚀 [RAILWAY] Iniciando aplicación desde run.py...")
app = create_app()
print("✅ [RAILWAY] Aplicación creada correctamente.")

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
