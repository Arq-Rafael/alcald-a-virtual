# Solución: Configurar RESEND_API_KEY en Railway

## Problema
```
ERROR: invalid key-value pair "=`\u200bRESEND_API_KEY`=re_...": empty key
```
Hay caracteres invisibles o el formato es incorrecto.

## Solución correcta

### Opción 1: Via Railway Dashboard (RECOMENDADO)

1. Ve a tu app en **Railway Dashboard**
2. Click en **Settings** (engranaje)
3. Ve a **Variables**
4. Click en **+ New Variable**
5. En el campo **Key** escribe exactamente:
   ```
   RESEND_API_KEY
   ```
6. En el campo **Value** escribe:
   ```
   re_ZaMbDSms_MHXJ3AiUWEWLFqi3czG3ChuG
   ```
7. Click en **Add**
8. Click en **Deploy** (arriba)
9. Espera a que termine el deploy

### Opción 2: Via archivo .env en Railway

Si prefieres usar archivo `.env`:

1. En Railway, ve a **Settings**
2. Busca **Build & Deploy**
3. En **Environment** agrega:
   ```
   RESEND_API_KEY=re_ZaMbDSms_MHXJ3AiUWEWLFqi3czG3ChuG
   EMAIL_PROVIDER=resend
   ```

### Opción 3: Via railway.json

En la raíz del proyecto, edita o crea `railway.json`:

```json
{
  "build": {
    "builder": "dockerfile"
  },
  "deploy": {
    "numReplicas": 1,
    "restartPolicyMaxRetries": 2,
    "variables": {
      "RESEND_API_KEY": "re_ZaMbDSms_MHXJ3AiUWEWLFqi3czG3ChuG",
      "EMAIL_PROVIDER": "resend"
    }
  }
}
```

Luego haz:
```bash
git add railway.json
git commit -m "Add RESEND_API_KEY to railway.json"
git push origin main
```

---

## ✅ Verificación

Después de configurar, verifica en Railway:

1. Ve a **Deployments**
2. Click en el último deploy
3. Abre la consola y busca:
   ```
   RESEND_API_KEY=re_...
   ```

Debe aparecer en los logs sin errores.

---

## 🔑 Tu API Key (guardada aquí para ref)

```
re_ZaMbDSms_MHXJ3AiUWEWLFqi3czG3ChuG
```

**⚠️ IMPORTANTE:** Esta key está expuesta aquí por claridad. En producción:
1. Cambiaría esta key en Resend
2. Usaría una variable segura en Railway
3. Nunca la pondría en repositorios públicos

---

## Si el error persiste

**Limpia la variable completamente:**

1. Railway Dashboard → Settings → Variables
2. Busca `RESEND_API_KEY`
3. Click en el ❌ para borrar
4. Espera 5 segundos
5. Agrega la variable nueva nuevamente
6. Deploy

---

## Local (.env)

Para probar localmente, en tu `.env` local:

```env
FLASK_ENV=development
SECRET_KEY=tu_clave_secreta_aqui
DATABASE_URL=
RESEND_API_KEY=re_ZaMbDSms_MHXJ3AiUWEWLFqi3czG3ChuG
EMAIL_PROVIDER=resend
```

Luego:
```bash
python run.py
```

---

**Creado:** 28/01/2026
**Estado:** ✅ Guía de resolución
