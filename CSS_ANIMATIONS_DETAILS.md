# CSS Animations & Visual Details - Planes de Contingencia iOS 26

## 🎬 Animaciones Implementadas

### 1. **slideInFromBottom** (Modales)
```css
@keyframes slideInFromBottom {
  from {
    opacity: 0;
    transform: translateY(100%);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
```
**Duración**: 0.3s ease-out
**Aplicado a**: `.ios-modal`
**Efecto**: El modal sube desde la parte inferior de la pantalla con fade-in

---

### 2. **bubbleIn** (Notificaciones)
```css
@keyframes bubbleIn {
  from {
    opacity: 0;
    transform: translateY(20px) scale(0.8);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}
```
**Duración**: 0.3s ease-out
**Aplicado a**: `.msg-bubble`
**Efecto**: La burbuja aparece en la esquina inferior derecha con escala suave

---

## 🎨 Esquema de Colores iOS 26

| Elemento | Color | Hex | Uso |
|----------|-------|-----|-----|
| Verde Éxito | System Green | #34C759 | Botón PDF, Badge Aprobado, Burbuja éxito |
| Azul Principal | System Blue | #007AFF | Botón Aprobar, Modal confirm |
| Amarillo | System Yellow | #FFB800 | Botón Revisar |
| Verde Oscuro | Custom Green | #1a472a | Botón Comité, Alcaldía branding |
| Rojo Eliminación | System Red | #FF3B30 | Botón Eliminar, Burbuja error |
| Gris Fondo | Light Gray | #f0f0f0 | Botón Cancel, backgrounds |

---

## 🔘 Estilos de Botones Detallados

### Botones iOS Generales
```css
.btn-ios {
  padding: 8px 14px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all 0.2s ease;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.btn-ios:active {
  transform: scale(0.95);
  box-shadow: 0 1px 4px rgba(0,0,0,0.15);
}
```

### Variantes de Color

#### Botón PDF (Verde)
```css
.btn-ios.btn-pdf {
  background: #34C759;
  color: white;
}
```

#### Botón Revisar (Amarillo)
```css
.btn-ios.btn-enviar {
  background: #FFB800;
  color: white;
}
```

#### Botón Aprobar (Azul)
```css
.btn-ios.btn-aprobar {
  background: #007AFF;
  color: white;
}
```

#### Botón Comité (Verde oscuro)
```css
.btn-ios.btn-comite {
  background: #1a472a;
  color: white;
}
```

#### Botón Eliminar (Rojo)
```css
.btn-ios.btn-eliminar {
  background: #FF3B30;
  color: white;
  width: 35px;
  height: 35px;
  padding: 0;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  line-height: 1;
}
```

---

## 📱 Modal iOS Completo

### Estructura HTML
```html
<div class="ios-modal">
  <div class="ios-modal-content">
    <div class="ios-modal-header">
      <h3>Título del Modal</h3>
    </div>
    <div class="ios-modal-body">
      Texto del cuerpo
    </div>
    <div class="ios-modal-buttons">
      <button class="ios-modal-btn cancel">Cancelar</button>
      <button class="ios-modal-btn confirm">Confirmar</button>
    </div>
  </div>
</div>
```

### Estilos CSS
```css
/* Contenedor principal (backdrop) */
.ios-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: flex-end;
  z-index: 1000;
  animation: slideInFromBottom 0.3s ease-out;
}

/* Contenedor del modal */
.ios-modal-content {
  background: white;
  width: 100%;
  border-radius: 14px 14px 0 0;
  box-shadow: 0 -3px 12px rgba(0, 0, 0, 0.15);
  overflow: hidden;
}

/* Encabezado */
.ios-modal-header {
  padding: 16px 16px 12px;
  text-align: center;
  border-bottom: 1px solid #e5e5e5;
}

.ios-modal-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

/* Cuerpo */
.ios-modal-body {
  padding: 12px 16px;
  font-size: 14px;
  color: #666;
  text-align: center;
}

/* Botones */
.ios-modal-buttons {
  display: flex;
  gap: 10px;
  padding: 12px 16px 16px;
}

.ios-modal-btn {
  flex: 1;
  padding: 12px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.ios-modal-btn.cancel {
  background: #f0f0f0;
  color: #333;
}

.ios-modal-btn.cancel:active {
  background: #e0e0e0;
  transform: scale(0.98);
}

.ios-modal-btn.confirm {
  background: #007AFF;
  color: white;
}

.ios-modal-btn.confirm:active {
  background: #0051D5;
  transform: scale(0.98);
}
```

---

## 💬 Burbujas de Notificación Detalladas

### Estructura HTML (generada por JS)
```html
<div class="msg-bubble success">
  ✓ Estado Actualizado
</div>
```

### Estilos CSS
```css
/* Burbuja base */
.msg-bubble {
  position: fixed;
  bottom: 30px;
  right: 20px;
  max-width: 300px;
  padding: 12px 16px;
  border-radius: 18px;
  font-size: 13px;
  font-weight: 500;
  z-index: 2000;
  animation: bubbleIn 0.3s ease-out;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* Variante éxito (verde) */
.msg-bubble.success {
  background: #34C759;
  color: white;
}

/* Variante error (rojo) */
.msg-bubble.error {
  background: #FF3B30;
  color: white;
}

/* Variante información (azul) */
.msg-bubble.info {
  background: #007AFF;
  color: white;
}
```

---

## 🎯 Transiciones Suaves

### Todas las transiciones usan easing estándar de iOS:
```css
transition: all 0.2s ease;     /* Para botones activos */
transition: all 0.3s ease-out; /* Para animaciones de entrada */
```

---

## 📐 Dimensiones Específicas

| Elemento | Ancho | Alto | Border Radius |
|----------|-------|------|--------------|
| Botón iOS | var | 36px | 20px |
| Botón Eliminar | 35px | 35px | 50% (círculo) |
| Modal | 100% | auto | 14px (arriba) |
| Burbuja | max 300px | auto | 18px |
| Icono Badge | - | 16px | - |

---

## 🖥️ Características Responsive

### Mobile First Design
```css
@media (max-width: 768px) {
  .ios-modal-content {
    border-radius: 16px 16px 0 0;
  }
  .msg-bubble {
    bottom: 20px;
    right: 15px;
    max-width: calc(100% - 30px);
  }
}
```

---

## 🎨 Tipografía iOS 26

```css
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
```

**Tamaños:**
- Títulos modales: 16px, font-weight 600
- Botones: 13-14px, font-weight 600
- Cuerpo: 14px, font-weight 400
- Burbujas: 13px, font-weight 500

---

## ✅ Checklist Visual

- [x] Botones con animación scale(0.95) al presionar
- [x] Modal con deslizamiento desde abajo (slideInFromBottom)
- [x] Burbuja con escala y fade simultáneos (bubbleIn)
- [x] Colores sistema iOS estandarizados
- [x] Sombras sutiles (0 -3px 12px, 0 4px 12px)
- [x] Border-radius modernos (14px para modales, 20px para botones)
- [x] Z-index apropiados (modales 1000, burbujas 2000)
- [x] Transiciones suaves (0.2s-0.3s ease-out)
- [x] Font-stack del sistema operativo

---

## 🔗 Integración con Backend

### Endpoint PUT `/api/contingencia/<id>/estado`

**Request:**
```json
{
  "estado": "Aprobado"
}
```

**Response:**
```json
{
  "success": true,
  "id": 123,
  "numero_plan": "PCA-2025-001",
  "estado": "Aprobado"
}
```

**Workflow:**
1. JS llama a confirmarEstado()
2. Envía PUT request con nuevo estado
3. Backend actualiza DB y retorna success
4. JS muestra burbuja de éxito
5. Después 800ms, ofrece modal de PDF (si es aprobación)

---

## 🚀 Performance

- **Animaciones GPU**: Uso de `transform` y `opacity` (no affectan layout)
- **Z-index optimizado**: Evita redibujados innecesarios
- **Auto-cleanup**: Burbujas se remueven del DOM después de 3s
- **Modal único**: Solo un modal activo por vez (se reemplaza previo)

