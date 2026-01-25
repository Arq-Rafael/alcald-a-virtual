/**
 * Script de integración: muestra las secciones oficiales en la tabla de planes
 * y permite acceso rápido a cada sección del wizard
 */

// Detectar cuando se carguen los planes y agregar información de secciones
const originalCargarPlanesExistentes = window.cargarPlanesExistentes;
window.cargarPlanesExistentes = async function() {
  await originalCargarPlanesExistentes.apply(this, arguments);
  
  // Después de cargar, agregar indicador de secciones completadas
  const tbody = document.getElementById('planesTbody');
  if (!tbody) return;
  
  const filas = tbody.querySelectorAll('tr');
  filas.forEach(fila => {
    const tdAcciones = fila.querySelector('td:last-child');
    if (!tdAcciones) return;
    
    // Extraer ID del primer botón
    const btnPDF = tdAcciones.querySelector('[onclick*="descargarPDF"]');
    if (!btnPDF) return;
    
    const match = btnPDF.getAttribute('onclick').match(/descargarPDF\((\d+)\)/);
    if (!match) return;
    
    const planId = match[1];
    
    // Agregar botón de acceso rápido a secciones
    const btnSecciones = document.createElement('button');
    btnSecciones.className = 'btn-ios';
    btnSecciones.style.cssText = 'background:#6366f1; color:#fff; padding:6px 10px; border:none; border-radius:8px; cursor:pointer; font-size:11px; margin-right:4px;';
    btnSecciones.innerHTML = '📋 Secciones';
    btnSecciones.onclick = () => mostrarMenuSecciones(planId);
    
    tdAcciones.insertBefore(btnSecciones, tdAcciones.firstChild);
  });
};

function mostrarMenuSecciones(planId) {
  const secciones = [
    { key: 'introduccion', label: '1. Introducción' },
    { key: 'objetivos', label: '2. Objetivos y Alcance' },
    { key: 'normativo', label: '3. Marco Normativo' },
    { key: 'organizacion', label: '4. Organización' },
    { key: 'riesgos', label: '5. Análisis de Riesgos' },
    { key: 'medidas', label: '6. Medidas de Reducción' },
    { key: 'respuesta', label: '7. Plan de Respuesta' },
    { key: 'actualizacion', label: '8. Actualización' },
    { key: 'anexos', label: '9. Anexos' }
  ];
  
  const modal = document.createElement('div');
  modal.className = 'ios-modal';
  modal.id = 'seccionesModal';
  
  let contenido = '<div class="ios-modal-content" style="width:90%; max-width:400px;"><div class="ios-modal-header"><h3>Secciones del Plan</h3></div><div class="ios-modal-body" style="padding:12px; display:grid; gap:8px;">';
  
  secciones.forEach(sec => {
    contenido += `
      <a href="/gestion-riesgo/planes-contingencia/editar/${planId}/${sec.key}" 
         style="display:block; padding:10px 12px; background:#1e293b; color:#e2e8f0; border-radius:8px; text-decoration:none; border-left:3px solid #38bdf8; cursor:pointer;">
        ${sec.label}
      </a>
    `;
  });
  
  contenido += '</div><div class="ios-modal-buttons"><button class="ios-modal-btn cancel" onclick="cerrarSeccionesModal()">Cerrar</button></div></div>';
  
  modal.innerHTML = contenido;
  document.body.appendChild(modal);
  modal.addEventListener('click', (e) => {
    if (e.target === modal) cerrarSeccionesModal();
  });
}

function cerrarSeccionesModal() {
  const modal = document.getElementById('seccionesModal');
  if (modal) modal.remove();
}

// Reinvocar después de que se carguen los planes por primera vez
document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('planesTbody')) {
    window.cargarPlanesExistentes();
  }
});
