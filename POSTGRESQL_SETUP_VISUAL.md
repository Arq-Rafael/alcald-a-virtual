# 🚀 CONFIGURAR POSTGRESQL EN RAILWAY - GUÍA VISUAL

## ⏱️ Tiempo total: 5 minutos

---

## PASO 1️⃣ - Ir a Railroad.app

👉 Abre: https://railway.app/dashboard

---

## PASO 2️⃣ - Seleccionar tu proyecto

1. Busca tu proyecto **"alcald-a-virtual"** (o similar)
2. Haz clic en él

---

## PASO 3️⃣ - Crear servicio PostgreSQL

1. En la esquina superior derecha: **"+ New"**
2. Selecciona **"Database"**
3. Selecciona **"PostgreSQL"**
4. **Espera 30 segundos** hasta que aparezca ✅

---

## PASO 4️⃣ - Copiar la URL de conexión

1. El nuevo servicio PostgreSQL aparecerá en el dashboard
2. Haz clic en **"PostgreSQL"** (el nuevo servicio)
3. Ve a la pestaña **"Variables"**
4. Busca: **`DATABASE_URL`**
5. Copia el valor completo (empieza con `postgresql://`)

**Se vería así:**
```
postgresql://postgres:PASSWORD@host:5432/railway
```

---

## PASO 5️⃣ - Agregar a tu app (Flask)

1. En el dashboard, haz clic en tu app **"web"** (la que tiene gunicorn)
2. Ve a **"Variables"**
3. Haz clic en **"+ New Variable"**
4. **Nombre:** `DATABASE_URL`
5. **Valor:** Pega lo que copiaste del paso anterior
6. Haz clic en **"Add"** o **"Save"**

---

## PASO 6️⃣ - Redeploy

1. La app debería redeployarse automáticamente
2. **Espera 2-3 minutos** a que termine
3. Cuando aparezca ✅ verde, está listo

---

## VERIFICACIÓN ✅

### Test 1: La app inicia sin errores
- Abre tu app: https://tu-app.railway.app
- ¿Carga? → ✅ Bien

### Test 2: Los datos persisten
1. Crea un usuario nuevo
2. Anota el nombre exacto
3. Ve a Railway → App → Deploy → Redeploy (el botón)
4. Espera a que termine
5. Vuelve a la app y busca ese usuario
6. ¿Sigue ahí? → ✅ PostgreSQL funciona

---

## 🆘 Si algo sale mal

**Error: "can't connect to database"**
→ Revisa que `DATABASE_URL` esté correcta en Variables

**Error: "psycopg2 not found"**
→ Ya está instalado, pero Railway necesita redeployar completamente

**Los datos seguían borrándose**
→ Revisa que NO haya `DATABASE_URL` en el código (solo en Variables)

---

## 📊 Resultado final

| Lo que pasa | Antes | Ahora |
|------------|-------|-------|
| Base de datos | SQLite efímera | PostgreSQL persistente ✅ |
| Deploy de código | Pierde datos | Mantiene datos ✅ |
| TOTP de usuarios | Se borra | Se mantiene ✅ |
| Historial | Nada | Todo guardado ✅ |

---

## ✅ LISTO

Una vez que veas el usuario que creaste después del redeploy:
✅ PostgreSQL está funcionando
✅ Los datos persisten
✅ Puedes hacer updates sin miedo de perder nada

**¿Problemas? Pega aquí el error del logs de Railway y lo arreglamos.**
