#!/usr/bin/env python3
"""Verificar configuración SMTP en todo tipo de entorno"""

import os
import sys

print("\n" + "="*70)
print("🔍 VERIFICACIÓN DE CONFIGURACIÓN SMTP")
print("="*70 + "\n")

# 1. Variables de entorno
print("1️⃣  VARIABLES DE ENTORNO:")
print("-" * 70)

smtp_server = os.environ.get('SMTP_SERVER')
smtp_port = os.environ.get('SMTP_PORT')
smtp_user = os.environ.get('SMTP_USER')
smtp_password = os.environ.get('SMTP_PASSWORD')

print(f"   SMTP_SERVER: {smtp_server or '❌ NO CONFIGURADO'}")
print(f"   SMTP_PORT: {smtp_port or '❌ NO CONFIGURADO'}")
print(f"   SMTP_USER: {smtp_user or '❌ NO CONFIGURADO'}")
print(f"   SMTP_PASSWORD: {'✅ Configurado' if smtp_password else '❌ NO CONFIGURADO'}")

# 2. Variables de entorno de Railway
print("\n2️⃣  VARIABLES DE RAILWAY:")
print("-" * 70)

railway_env = os.environ.get('RAILWAY_ENVIRONMENT')
port = os.environ.get('PORT')
print(f"   RAILWAY_ENVIRONMENT: {railway_env or 'N/A (Local)'}")
print(f"   PORT: {port or '5000 (default)'}")

# 3. Configuración en config.py
print("\n3️⃣  CONFIGURACIÓN EN app/config.py:")
print("-" * 70)

try:
    sys.path.insert(0, '/c/Users/rafa_/Downloads/AlcaldiaVirtualWeb')
    from app.config import Config
    
    print(f"   SMTP_SERVER: {Config.SMTP_SERVER}")
    print(f"   SMTP_PORT: {Config.SMTP_PORT}")
    print(f"   SMTP_USER: {Config.SMTP_USER}")
    print(f"   SMTP_PASSWORD: {'✅ Configurado' if Config.SMTP_PASSWORD else '❌ Vacío'}")
    
except Exception as e:
    print(f"   ❌ Error al leer config.py: {e}")

# 4. Resultado
print("\n4️⃣  RESULTADO:")
print("-" * 70)

if smtp_user and smtp_password:
    print("   ✅ SMTP ESTÁ CONFIGURADO CORRECTAMENTE")
    print(f"   \n   Usará:")
    print(f"   - Servidor: {smtp_server or 'smtp.gmail.com (default)'}")
    print(f"   - Puerto: {smtp_port or '587 (default)'}")
    print(f"   - Usuario: {smtp_user}")
else:
    print("   ❌ SMTP NO ESTÁ CONFIGURADO")
    print("\n   Para Railway, añade variables de entorno:")
    print("   - SMTP_SERVER=smtp.gmail.com")
    print("   - SMTP_PORT=587")
    print("   - SMTP_USER=alcaldiavirtual2026@gmail.com")
    print("   - SMTP_PASSWORD=fvgqrsacjnjhzfcn")

print("\n" + "="*70 + "\n")
