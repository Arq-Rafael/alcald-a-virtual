# 🚀 PostgreSQL en Railway - Instrucciones

## ¿Por qué PostgreSQL?
- ✅ **Datos persisten** entre deployments
- ✅ **Mejor rendimiento** que SQLite
- ✅ **Escalable** para producción
- ✅ **Backups automáticos** en Railway

## 📋 Pasos para configurar

### 1️⃣ Crear servicio PostgreSQL en Railway

1. Ve a tu proyecto en [railway.app](https://railway.app)
2. Haz clic en **"+ New"** (esquina superior derecha)
3. Selecciona **"Database"**
4. Elige **"PostgreSQL"**
5. Espera a que se inicie (1-2 minutos)

### 2️⃣ Conectar PostgreSQL a tu app

1. En el servicio PostgreSQL, ve a **"Variables"**
2. Copia el valor de `DATABASE_URL` (algo como: `postgresql://user:pass@host:5432/db`)
3. En tu app (el servicio Flask), ve a **"Variables"**
4. Pega: `DATABASE_URL = postgresql://...`
5. Haz clic en **Deploy**

Tu app debería redeployarse automáticamente. ✅

### 3️⃣ Verificar que funciona

- Intenta acceder a tu app
- Intenta crear un usuario nuevo
- Haz un deploy pequeño (cambio en un archivo)
- Los usuarios **deben estar ahí** después del nuevo deploy

---

## 🔍 Debugging

**Si la app sigue sin cargar:**
```
En Railway → Logs de tu app
```
Busca errores como:
- `could not translate host name` → Base de datos no alcanzable
- `permission denied` → Variable `DATABASE_URL` incorrecta

**Si los datos se borran:**
- Verifica que `DATABASE_URL` esté en variables (no en el código)
- Recarga la página (a veces el caché engaña)

---

## 💡 Verificar que funciona desde terminal local

```bash
# Local (SQLite - para testing)
python run.py

# En Railway (PostgreSQL - automático)
# No necesitas hacer nada, está en config.py
```

---

## 📊 Lo que pasa ahora

| Antes | Ahora |
|-------|-------|
| SQLite en `/tmp` | PostgreSQL en Railway |
| Datos se borran con cada deploy | Datos persisten para siempre |
| Límite de usuarios | Escalable ∞ |

---

## ✅ Hecho

- [x] Código soporta PostgreSQL
- [x] Código soporta SQLite local
- [x] Automáticamente detecta cuál usar
- [ ] **Falta:** Crear PostgreSQL en Railway y agregar `DATABASE_URL`

**¿Necesitas ayuda con los pasos en Railway?** Avísame si hay algún error.
