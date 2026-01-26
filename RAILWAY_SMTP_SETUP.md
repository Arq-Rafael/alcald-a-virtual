# 🚀 Configuración en Railway - SMTP y Variables de Entorno

## Problema
En Railway, las variables de entorno de SMTP no se leen automáticamente. El sistema no puede enviar emails de 2FA.

## Solución
Debes configurar las variables de entorno directamente en Railway:

### Paso 1: Ve a Railway Dashboard
1. Abre https://railway.app
2. Selecciona tu proyecto "Alcaldía Virtual"
3. Haz clic en el servicio (deployment)

### Paso 2: Agregar Variables de Entorno
1. Haz clic en la pestaña **"Variables"** 
2. Haz clic en **"Add Variable"** o **"+ New Variable"**
3. Agrega estas variables exactamente como aparecen:

```
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=alcaldiavirtual2026@gmail.com
SMTP_PASSWORD=fvgqrsacjnjhzfcn
ADMIN_PASSWORD=admin123
PLANEACION_PASSWORD=planeacion123
GOBIERNO_PASSWORD=gobierno123
```

### Paso 3: Deploy
1. Railway redesplegará automáticamente
2. Espera a que termine (unos 2-3 minutos)
3. El servidor iniciará con las nuevas variables

### Paso 4: Verificar
1. Intenta hacer login en la plataforma
2. Si 2FA está habilitado, deberías recibir el código por email
3. Verifica el correo: alcaldiavirtual2026@gmail.com

## Variables Disponibles

| Variable | Valor | Obligatoria |
|----------|-------|-----------|
| `SMTP_SERVER` | `smtp.gmail.com` | ✅ Sí |
| `SMTP_PORT` | `587` | ✅ Sí |
| `SMTP_USER` | `alcaldiavirtual2026@gmail.com` | ✅ Sí |
| `SMTP_PASSWORD` | `fvgqrsacjnjhzfcn` | ✅ Sí |
| `ADMIN_PASSWORD` | Cualquier valor | ❌ No (usa default) |
| `PLANEACION_PASSWORD` | Cualquier valor | ❌ No (usa default) |
| `GOBIERNO_PASSWORD` | Cualquier valor | ❌ No (usa default) |

## Troubleshooting

### Si sigue sin funcionar:
1. Verifica que digitaste exactamente las variables
2. Recarga la página en el navegador
3. Limpia el caché (Ctrl+Shift+Del)
4. Intenta en incógnito
5. Revisa los logs en Railway Console

### Para ver logs en Railway:
1. Selecciona el servicio
2. Haz clic en **"Logs"**
3. Busca errores de SMTP

## Local Development

Para desarrollo local, copia `.env.example` a `.env`:
```bash
cp .env.example .env
```

Flask cargará automáticamente las variables de `.env`
