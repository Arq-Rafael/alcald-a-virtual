# Splash Screen & Screen Saver - Alcaldía Virtual de Supatá

## 📋 Descripción

Sistema de animación futurista integrado en el aplicativo con dos funcionalidades principales:

### 1. **Splash Screen (Pantalla de Carga Inicial)**
- Se muestra automáticamente al abrir el aplicativo
- Duración: 4 segundos
- Diseño futurista con:
  - Partículas animadas (red de nodos conectados)
  - Anillos HUD rotativos
  - Logo central con efecto flotante
  - Colores: Verde neón (#39ff14) y Dorado (#ffd700)

### 2. **Screen Saver (Protector de Pantalla)**
- Se activa automáticamente después de **10 minutos** de inactividad
- Mismo diseño que el splash screen
- Protege la privacidad en computadores públicos de la alcaldía
- Se desactiva con cualquier interacción (clic, tecla, movimiento del mouse)

---

## 🛠️ Archivos Creados

### CSS
```
/static/css/splash-screen.css
```
- Estilos completos para splash y screen saver
- Animaciones de rotación, flotación y fade
- Diseño responsive (móvil, tablet, desktop)

### JavaScript
```
/static/js/splash-screen.js
```
- Controlador principal del sistema
- Gestión de partículas con Canvas 2D
- Detector de inactividad
- Sistema de timers y eventos

### Imagen
```
/static/imagenes/logo_new.png
```
- Logo de la alcaldía en alta resolución
- Usado en ambas animaciones

---

## ⚙️ Configuración

Puedes ajustar los tiempos editando el archivo `/static/js/splash-screen.js`:

```javascript
const CONFIG = {
    splashDuration: 4000,        // Duración del splash (ms)
    inactivityTimeout: 600000,   // Tiempo de inactividad (ms)
    particleCount: 100,          // Cantidad de partículas
    connectionDistance: 150      // Distancia de conexión
};
```

### Valores recomendados:

| Parámetro | Valor Actual | Alternativas |
|-----------|--------------|--------------|
| **splashDuration** | 4000 ms (4 seg) | 3000 ms (más rápido) / 5000 ms (más lento) |
| **inactivityTimeout** | 600000 ms (10 min) | 300000 ms (5 min) / 900000 ms (15 min) |
| **particleCount** | 100 | 60 (menos carga) / 150 (más denso) |
| **connectionDistance** | 150px | 120px (menos líneas) / 180px (más conexiones) |

---

## 🎨 Características Técnicas

### Animaciones CSS
- **rotate-cw**: Rotación horaria de anillos (20-40s)
- **rotate-ccw**: Rotación antihoraria (25s)
- **hover-float**: Efecto flotante del logo (6s)
- **pulse-text**: Pulso de texto (2-3s)
- **fadeOut**: Desvanecimiento suave (0.8s)

### Canvas Particles
- Sistema de partículas con física simple
- Colisión en bordes con rebote
- Conexiones dinámicas basadas en distancia
- Optimizado con requestAnimationFrame

### Responsive Design
```css
Desktop:  Anillos 650px/500px/750px
Tablet:   Anillos 450px/350px/550px  
Mobile:   Anillos 320px/250px/400px
```

---

## 🚀 Funcionamiento

### Al cargar la página:
1. Splash screen se muestra sobre todo el contenido (z-index: 99999)
2. Canvas inicia animación de partículas
3. Anillos HUD rotan continuamente
4. Logo flota con efecto 3D
5. Después de 4s: fade-out y se oculta
6. Sistema de inactividad inicia monitoreo

### Durante el uso:
1. Detector escucha eventos: mouse, teclado, scroll, touch
2. Cada evento resetea el timer de inactividad
3. Si pasan 10 minutos sin actividad → Screen Saver aparece
4. Cualquier interacción cierra el screen saver

---

## 🎯 Beneficios

✅ **Profesionalismo**: Imagen moderna tipo aplicación móvil premium  
✅ **Branding**: Refuerza identidad visual de la alcaldía  
✅ **Seguridad**: Protege privacidad en equipos compartidos  
✅ **UX**: Feedback visual durante carga del sistema  
✅ **Performance**: Optimizado con Canvas 2D nativo  

---

## 🔧 Mantenimiento

### Cambiar logo:
Reemplaza el archivo `/static/imagenes/logo_new.png` con una imagen del mismo nombre.

### Desactivar temporalmente:
Comenta estas líneas en `/templates/base.html`:
```html
<!-- <link rel="stylesheet" href="{{ url_for('static', filename='css/splash-screen.css') }}"> -->
<!-- <script src="{{ url_for('static', filename='js/splash-screen.js') }}"></script> -->
```

### Modificar colores:
Edita las variables CSS en `/static/css/splash-screen.css`:
```css
:root {
    --neon-green: #39ff14;      /* Verde principal */
    --neon-gold: #ffd700;       /* Dorado */
    --bg-dark: #000205;         /* Fondo oscuro */
}
```

---

## 📱 Compatibilidad

- ✅ Chrome/Edge (Chromium)
- ✅ Firefox
- ✅ Safari (iOS/macOS)
- ✅ Navegadores móviles
- ✅ Responsive (320px - 4K)

---

## 👨‍💻 Integración

Sistema totalmente integrado en `base.html` - se carga automáticamente en todas las páginas del aplicativo sin necesidad de configuración adicional.

**Ubicación en base.html:**
- CSS: Entre los otros stylesheets en el `<head>`
- HTML: Primeros elementos después del `<body>`
- JS: Antes del cierre del `</body>`

---

**Desarrollado para:** Alcaldía Virtual de Supatá, Cundinamarca  
**Fecha:** Enero 2026  
**Tecnologías:** HTML5 Canvas, CSS3 Animations, Vanilla JavaScript
